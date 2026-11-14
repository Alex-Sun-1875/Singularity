import {Color,Material,Mesh,MeshRenderer,Node,Texture2D,Vec4,gfx,primitives,utils} from 'cc';
import {MAP_ART_SURFACES,type MapArtProfile,type MapArtSurface} from '../data/MapArt';
import type {SceneBuilder,FlatEnvironmentPatch} from './SceneBuilder';
import type {BridgeDef} from './Terrain';

type Geometry={positions:number[];normals:number[];uvs:number[];colors:number[];indices:number[]};
type BridgeBatch={surface:MapArtSurface;tint:string;geometry:Geometry};
const smooth=(value:number)=>{const t=Math.max(0,Math.min(1,value));return t*t*(3-2*t);};

/** Painted water edges and continuous, metre-aligned bridge structures.
 * All geometry is visual only: the original terrain, decks and colliders keep
 * ownership of walkable space, water barriers and the broken-bridge gap. */
export class PaintedTerrainDetails {
 private readonly root:Node;
 private readonly meshes=new Set<Mesh>();
 private readonly materials=new Map<string,Material>();
 private readonly waterNodes=new Set<Node>();
 private readonly boxes=new Map<string,ReturnType<typeof primitives.box>>();
 private readonly bridgeBatches=new Map<string,BridgeBatch>();
 private disposed=false;
 private bridgesBuilt=false;
 private waterPatches=0;
 private waterVertices=0;
 private bridgeRailingRuns=0;
 private bridgeBeams=0;
 private bridgePosts=0;
 private bridgeSupportPiers=0;
 private bridgeBatchCount=0;
 private gorgePatches=0;
 private canalRims=0;

 constructor(private readonly world:SceneBuilder,parent:Node,private readonly style:MapArtProfile,private readonly textures:ReadonlyMap<string,Texture2D>){
  this.root=new Node('PaintedTerrainDetails');this.root.layer=world.root.layer;parent.addChild(this.root);
 }

 private texture(surface:MapArtSurface):Texture2D{
  const texture=this.textures.get(surface.resource);
  if(!texture)throw new Error('Missing painted terrain detail texture '+surface.resource);
  return texture;
 }

 private material(surface:MapArtSurface,tint:string,blend=false):Material{
  const key=surface.resource+':'+tint+':'+blend,cached=this.materials.get(key);if(cached)return cached;
  const material=new Material();material.name=blend?'PaintedWaterEdge':'PaintedBridgeStructure';
  material.initialize({effectName:'builtin-unlit',technique:blend?1:0,
   defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:true,USE_INSTANCING:false},
   states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:!blend}}});
  if(!material.passes.length){material.destroy();throw new Error('Painted terrain details require builtin-unlit');}
  material.setProperty('mainColor',new Color().fromHEX(tint));material.setProperty('mainTexture',this.texture(surface));material.setProperty('tilingOffset',new Vec4(1,1,0,0));
  this.materials.set(key,material);return material;
 }

 private renderer(node:Node,mesh:Mesh,material:Material):MeshRenderer{
  const renderer=node.addComponent(MeshRenderer);renderer.mesh=mesh;renderer.setSharedMaterial(material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;return renderer;
 }

 /** Sample the narrow fade at sub-metre spacing; the interior needs only a
  * coarse grid because the water height and full-opacity color are constant. */
 private waterAxis(length:number):number[]{
  const half=length/2,distances=new Set<number>([0,length]);
  for(const distance of [.12,.25,.4,.6,.85])if(distance<half){distances.add(distance);distances.add(length-distance);}
  for(let distance=1.4;distance<length-1.2;distance+=1.4)distances.add(distance);
  return Array.from(distances).sort((a,b)=>a-b).map(distance=>distance-half);
 }

 water(patch:FlatEnvironmentPatch):void{
  if(this.disposed||!this.root.isValid||patch.kind!=='water'||!patch.node.isValid||this.waterNodes.has(patch.node))return;
  const source=patch.node,size=source.worldScale,position=source.worldPosition,width=Math.abs(size.x),depth=Math.abs(size.z);
  if(width<.02||depth<.02)return;
  const xs=this.waterAxis(width),zs=this.waterAxis(depth),positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[],tile=this.style.water.tileMetres;
  for(const z of zs)for(const x of xs){
   const wx=position.x+x,wz=position.z+z,distance=Math.min(width/2-Math.abs(x),depth/2-Math.abs(z));
   // Both frequencies stay within the requested fade envelope. All vertices
   // remain inside the old rectangle and at its original water elevation.
   const wave=Math.sin(wx*2.17+wz*.83)*.32+Math.sin(wx*.71-wz*2.63)*.18;
   const fadeWidth=.5+.3*wave,inset=.035+.045*(.5+.5*Math.sin(wx*3.1+wz*2.3));
   const alpha=smooth((distance-inset)/Math.max(.1,fadeWidth-inset));
   positions.push(x,0,z);normals.push(0,1,0);uvs.push(wx/tile,wz/tile);colors.push(1,1,1,alpha);
  }
  const stride=xs.length;
  for(let z=0;z<zs.length-1;z++)for(let x=0;x<xs.length-1;x++){const i=z*stride+x;indices.push(i,i+stride,i+1,i+1,i+stride,i+stride+1);}
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices},undefined,{calculateBounds:true});this.meshes.add(mesh);
  const node=new Node('PaintedWater:'+source.name);this.root.addChild(node);node.layer=source.layer;
  node.setWorldPosition(position.x,position.y+Math.abs(size.y)/2+.003,position.z);node.setWorldRotation(source.worldRotation);
  const renderer=this.renderer(node,mesh,this.material(this.style.water,this.style.water.tint,true));renderer.priority=-99;
  this.waterNodes.add(source);this.waterPatches++;this.waterVertices+=positions.length/3;
 }

 private batch(stone:boolean):BridgeBatch{
  const key=stone?'stone':'wood',cached=this.bridgeBatches.get(key);if(cached)return cached;
  const batch:BridgeBatch={surface:stone?this.style.paving:this.style.wood,tint:stone?this.style.propTints.stone:this.style.propTints.timber,geometry:{positions:[],normals:[],uvs:[],colors:[],indices:[]}};
  this.bridgeBatches.set(key,batch);return batch;
 }

 /** Cocos owns the native box's topology and per-face UVs. Only world-size UV
  * density, face values and translations are adapted before material batching. */
 private box(stone:boolean,x:number,y:number,z:number,width:number,height:number,depth:number):void{
  if(Math.min(width,height,depth)<=.005)return;
  const key=[width,height,depth].map(value=>value.toFixed(4)).join(',');let primitive=this.boxes.get(key);
  if(!primitive){primitive=primitives.box({width,height,length:depth});this.boxes.set(key,primitive);}
  const batch=this.batch(stone),g=batch.geometry,start=g.positions.length/3,normals=primitive.normals!,uvs=primitive.uvs!,tile=batch.surface.tileMetres;
  for(let vertex=0;vertex<primitive.positions.length/3;vertex++){
   const i=vertex*3,nx=normals[i],ny=normals[i+1],nz=normals[i+2],uScale=Math.abs(nx)>.5?depth:width,vScale=Math.abs(ny)>.5?depth:height;
   g.positions.push(primitive.positions[i]+x,primitive.positions[i+1]+y,primitive.positions[i+2]+z);g.normals.push(nx,ny,nz);
   g.uvs.push(uvs[vertex*2]*uScale/tile,uvs[vertex*2+1]*vScale/tile);
   const shade=ny>.5?1:ny<-.5?.72:nz>.5?.84:nx<-.5?.79:.92;g.colors.push(shade,shade,shade,1);
  }
  for(const index of primitive.indices!)g.indices.push(start+index);
 }

 private bridge(deck:BridgeDef,gapWidth=0):void{
  const axisX=deck.axis==='x',length=axisX?deck.width:deck.depth,span=axisX?deck.depth:deck.width,stone=deck.material==='stone';
  const gap=Math.max(0,Math.min(length,gapWidth));
  const intervals:readonly [number,number][]=gap>0?[[-length/2,-gap/2],[gap/2,length/2]]:[[-length/2,length/2]];
  const offset=Math.max(0,span/2-.22),postWidth=stone?.4:.18;
  const place=(along:number,cross:number,y:number,run:number,height:number,thickness:number)=>this.box(stone,
   deck.x+(axisX?along:cross),y,deck.z+(axisX?cross:along),axisX?run:thickness,height,axisX?thickness:run);
  for(const [start,end]of intervals){
   const run=end-start;if(run<postWidth)continue;
   for(const side of [-1,1]){
    const cross=side*offset,center=(start+end)/2;
    if(stone){
     place(center,cross,deck.deckHeight+.28,run,.56,.32);
     place(center,cross,deck.deckHeight+.60,run,.08,.4);
    }else{
     place(center,cross,deck.deckHeight+.43,run,.13,.12);
     place(center,cross,deck.deckHeight+.77,run,.14,.14);
    }
    this.bridgeRailingRuns++;this.bridgeBeams+=2;
    // Include both endpoints of every intact run. Post widths stay strictly
    // within those intervals, so a broken span never gains a rail or pillar.
    const first=start+postWidth/2,last=end-postWidth/2,steps=Math.max(1,Math.ceil((last-first)/(stone?2.8:2.4)));
    for(let index=0;index<=steps;index++){
     const along=first+(last-first)*index/steps,height=stone?.79:.94;
     place(along,cross,deck.deckHeight+height/2,postWidth,height,postWidth);this.bridgePosts++;
    }
   }
  }
  for(const support of deck.supports){
   const along=axisX?support.x-deck.x:support.z-deck.z,pierWidth=stone?.76:.24;
   if(gap>0&&Math.abs(along)<gap/2+pierWidth/2)continue;
   const water=this.world.terrain.waters.find(w=>Math.abs(support.x-w.x)<=w.width/2+2&&Math.abs(support.z-w.z)<=w.depth/2+2);
   const gorge=this.world.terrain.gorges.find(g=>Math.abs(support.x-g.x)<=g.width/2+2&&Math.abs(support.z-g.z)<=g.depth/2+2);
   const bottom=water?water.y-.12:gorge?gorge.y:Math.min(this.world.height(support),deck.deckHeight-.55),top=deck.deckHeight-.08;
   if(top>bottom){this.box(stone,support.x,(bottom+top)/2,support.z,pierWidth,top-bottom,pierWidth);this.bridgeSupportPiers++;}
  }
 }

 gorges():void{
  if(this.disposed||!this.root.isValid)return;
  const surface=MAP_ART_SURFACES.bedrock;
  const ground=this.world.flatMapSurfaces.find(r=>r.node.name==='Ground')?.mesh;
  const positions=ground?.readAttribute(0,gfx.AttributeName.ATTR_POSITION),normals=ground?.readAttribute(0,gfx.AttributeName.ATTR_NORMAL),indices=ground?.readIndices(0);
  if(!positions||!indices)throw new Error('Painted dry landforms require the actual ground mesh');
  for(const gorge of this.world.terrain.gorges){
   const g:Geometry={positions:[],normals:[],uvs:[],colors:[],indices:[]},mapped=new Map<number,number>(),bank=gorge.bankWidth;
   // Reuse the exact rendered ground triangles. Resampling the analytic
   // height on another grid crosses the ground on curved banks and creates
   // alternating pale triangles, even when every sampled vertex is above it.
   const vertex=(source:number)=>{
    const existing=mapped.get(source);if(existing!==undefined)return existing;
    const i=source*3,px=positions[i],pz=positions[i+2],edge=Math.min(gorge.width/2-Math.abs(px-gorge.x),gorge.depth/2-Math.abs(pz-gorge.z)),weight=smooth((edge+bank)/bank),shade=1-.36*weight,index=g.positions.length/3;
    g.positions.push(px,positions[i+1]+.017,pz);g.normals.push(normals?.[i]??0,normals?.[i+1]??1,normals?.[i+2]??0);g.uvs.push(px/surface.tileMetres,pz/surface.tileMetres);g.colors.push(shade,shade*.99,shade*.96,weight*.72);mapped.set(source,index);return index;
   };
   for(let triangle=0;triangle<indices.length;triangle+=3){
    const a=indices[triangle],b=indices[triangle+1],c=indices[triangle+2],px=(positions[a*3]+positions[b*3]+positions[c*3])/3,pz=(positions[a*3+2]+positions[b*3+2]+positions[c*3+2])/3;
    if(Math.abs(px-gorge.x)>gorge.width/2+bank+2||Math.abs(pz-gorge.z)>gorge.depth/2+bank+2)continue;
    // Keep edge triangles continuous beneath the deck. The ground is lowered
    // there and the opaque deck depth-tests over it; cutting whole triangles
    // at a centroid would leave pale sawteeth along the bridge boundary.
    g.indices.push(vertex(a),vertex(b),vertex(c));
   }
   const mesh=utils.createMesh(g,undefined,{calculateBounds:true});this.meshes.add(mesh);const node=new Node('PaintedDryGorge:'+gorge.id);this.root.addChild(node);node.layer=this.world.root.layer;const r=this.renderer(node,mesh,this.material(surface,'#FFFFFF',true));r.priority=-98;this.gorgePatches++;
  }
 }

 private canalEdges():void{
  for(const water of this.world.terrain.waters){if(water.kind!=='canal')continue;
   const alongZ=water.depth>=water.width,length=(alongZ?water.depth:water.width)-.3;
   for(const side of [-1,1]){
    const x=water.x+(alongZ?side*(water.width/2-.2):0),z=water.z+(alongZ?0:side*(water.depth/2-.2));
    // The whole stone rim stays in blocked water, leaving the dry approaches
    // untouched. Tide staining and the water fade meet this narrow masonry lip.
    this.box(true,x,water.y+.12,z,alongZ?.32:length,.72,alongZ?length:.32);this.canalRims++;
   }
  }
 }

 bridges():void{
  if(this.disposed||!this.root.isValid||this.bridgesBuilt)return;this.bridgesBuilt=true;
  for(const bridge of this.world.terrain.bridges)this.bridge(bridge);
  for(const bridge of this.world.terrain.brokenBridges)this.bridge(bridge,bridge.gapWidth);
  this.canalEdges();
  // All bridge boxes sharing a texture become one native draw batch. S11's
  // repaired wooden span and broken stone span therefore use only two batches.
  for(const [key,batch]of this.bridgeBatches){
   if(!batch.geometry.indices.length)continue;
   const mesh=utils.createMesh(batch.geometry,undefined,{calculateBounds:true});this.meshes.add(mesh);const node=new Node('PaintedBridge:'+key);this.root.addChild(node);node.layer=this.world.root.layer;
   this.renderer(node,mesh,this.material(batch.surface,batch.tint));this.bridgeBatchCount++;
  }
  this.boxes.clear();this.bridgeBatches.clear();
 }

 inspect(){return{ready:!this.disposed&&this.root.isValid,waterPatches:this.waterPatches,waterVertices:this.waterVertices,waterEdgeFadeMetres:[.35,.65],dryGorgePatches:this.gorgePatches,canalRims:this.canalRims,bridgeRailingRuns:this.bridgeRailingRuns,bridgeBeams:this.bridgeBeams,bridgePosts:this.bridgePosts,bridgeSupportPiers:this.bridgeSupportPiers,bridgeBatches:this.bridgeBatchCount};}

 destroy():void{
  if(this.disposed)return;this.disposed=true;if(this.root.isValid){this.root.active=false;this.root.destroy();}
  for(const mesh of this.meshes)if(mesh.isValid)mesh.destroy();for(const material of this.materials.values())if(material.isValid)material.destroy();
  this.meshes.clear();this.materials.clear();this.waterNodes.clear();this.boxes.clear();this.bridgeBatches.clear();
 }
}
