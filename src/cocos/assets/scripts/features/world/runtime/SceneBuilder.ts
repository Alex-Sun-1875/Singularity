import {Asset} from 'cc';
import {gameResources} from '../../../shared/assets/GameResources';
import type {MapResources} from './MapResources';
import {Node,Mesh,MeshRenderer,MeshCollider,Material,Vec3,Vec4,Color,Quat,utils,primitives,BoxCollider,PhysicsSystem,geometry,Texture2D,math,DirectionalLight,PointLight,gfx,director} from 'cc';
import type {AreaDef,Point,Obstacle,WorldQuery,Building} from '../../../core/Contracts';
import {playableExits} from '../../journey/data/ChapterJourney';
import {Navigation} from '../../navigation/runtime/Navigation';
import {enemyHurtRadius} from '../../combat/common/EnemyCombat';
import {getTerrain,TerrainDef,BridgeDef} from './Terrain';
import {SurfaceMaterials} from './SurfaceMaterials';
import {withTangents} from '../../actors/runtime/MeshTangents';
import {EnvironmentAssets,PropSize} from './EnvironmentAssets';
import {FlatWorldLayers} from './FlatWorldLayers';
import {INN_OPENING,ScenePlacement} from '../data/SceneDressing';
import {EnvironmentPresentation,type PracticalSource} from './EnvironmentPresentation';
import {planExitSigils,type PortalMount,type PortalPlacementReport} from '../../portals/runtime/PortalPlacement';

const colors={grass:'#73916f',forest:'#426c56',dirt:'#947b63',stone:'#a4b1ba',darkStone:'#596b79',wood:'#64503c',timber:'#414c55',roof:'#9ba8b5',teal:'#315e68',brass:'#c9ae7b',water:'#3c7285',cave:'#536779',linen:'#d8d8ca'};
const rgb=(s:string)=>new Color().fromHEX(s);
const noise=(a:number,b:number)=>{const n=Math.sin(a*127.1+b*311.7)*43758.5453;return n-Math.floor(n);};
/** Presentation metadata only. Physics and navigation retain their original nodes. */
export type FlatEnvironmentObject={node:Node;key:string;kind:'asset'|'building'|'structure';dimensions?:Vec3;centered?:boolean;decorative?:boolean;terrainRole?:'verge'|'ground-cluster'|'framing'};
export type FlatEnvironmentPatch={node:Node;kind:'water'|'bridge'|'paving'|'rug';color:string};
export class SceneBuilder implements WorldQuery {
 static preload(painted=false){return painted?EnvironmentAssets.loadLayout():EnvironmentAssets.load();}
 static releaseAssets(){EnvironmentAssets.dispose();FlatWorldLayers.releaseMeshes();}
 private approaches:Point[][]=[];
 private roadNetwork:Point[][]=[];
 private roadNavigation:Navigation|null=null;
 // Scene collision boxes are immutable after assembly. Share the existing
 // navigation footprint query instead of reading every Cocos transform on
 // every axis of every movement substep. A newly added obstacle invalidates it.
 private movementNavigation:Navigation|null=null;
 private physicsDirty=true;
 private readonly visibilityDirection=new Vec3();
 private readonly visibilityRay=new geometry.Ray();
 // Exact endpoints, one render frame, fixed capacity. Static group-2 scenery
 // is the only raycast target; overflow simply performs the original query.
 private visibilityFrame=-1;
 private readonly visibilityKeys=new Float64Array(128*4);
 private readonly visibilityFlags=new Uint8Array(128);
 private scenePlacements=new Map<Obstacle,ScenePlacement>();
 readonly layoutObstacles:Obstacle[]=[];
 root:Node; area:AreaDef; navigation:Navigation; terrain:TerrainDef;readonly meshes=new Map<string,Mesh>();readonly materials=new Map<string,Material>();
 propNodes=new Map<string,Node>();colliders:BoxCollider[]=[];
 readonly generatedMeshes=new Set<Mesh>();private textures=new Set<Texture2D>();
 readonly practicalSources:PracticalSource[]=[];presentation:EnvironmentPresentation;
 readonly flatMapSurfaces:MeshRenderer[]=[];
 readonly groundChunks:MeshRenderer[]=[];
 readonly flatMapPatches:FlatEnvironmentPatch[]=[];
 readonly flatMapObjects:FlatEnvironmentObject[]=[];
 readonly flatEntranceClusters:Point[]=[];
 private readonly mountedPortals:PortalMount[]=[];
 private portalPlacementReport:PortalPlacementReport|null=null;
 get portalMounts():readonly PortalMount[]{return this.mountedPortals;}
 get portalPlacementReview():Readonly<PortalPlacementReport>|null{return this.portalPlacementReport;}
 loadAsset<T extends Asset>(path:string,type:{new(...args:any[]):T},complete:(error:Error|null,asset:T)=>void){if(this.resourceScope)this.resourceScope.load(this.area.id,path,type,complete);else gameResources.load(path,type,complete);}
 constructor(parent:Node,area:AreaDef,private readonly painted=false,private readonly resourceScope?:MapResources){this.area={...area,exits:playableExits(area)};this.terrain=getTerrain(area);if(area.id==='S01-T1')for(const placement of INN_OPENING)this.registerPlacement(placement);
  if(area.id==='S01')this.prepareStreetFrontages();
  this.navigation=new Navigation(area.width,area.depth,[...area.obstacles,...this.terrain.barriers,...this.layoutObstacles],true);this.root=new Node(area.id);parent.addChild(this.root);this.build();}
 private registerPlacement(placement:ScenePlacement){
  const angle=(placement.yaw??0)*Math.PI/180,c=Math.abs(Math.cos(angle)),s=Math.abs(Math.sin(angle));
  const o:Obstacle={kind:'furniture',x:placement.x,z:placement.z,width:placement.width*c+placement.depth*s,depth:placement.width*s+placement.depth*c,height:placement.height};
  this.layoutObstacles.push(o);this.scenePlacements.set(o,placement);
 }
 private prepareStreetFrontages(){
  for(const [index,b] of this.area.buildings.entries()){
   const angle=(b.rotation??0)*Math.PI/180,c=Math.cos(angle),s=Math.sin(angle);
   const place=(key:string,x:number,z:number,width:number,height:number,depth:number,yaw=0)=>this.registerPlacement({key,x:b.x+x*c+z*s,z:b.z-x*s+z*c,width,height,depth,yaw:(b.rotation??0)+yaw});
   // Paired objects belong to a doorway/work bay, never a random street pile.
   const side=index%2?-1:1,x=side*b.width*.33,z=-b.depth/2-.64;
   place(index===2?'stump':'barrel',x,z,index===2?.85:.74,index===2?.48:.92,index===2?.78:.74,11+index*19);
   if(index!==4)place(index===3?'chest':'stool',x-side*1.05,z+.12,index===3?.9:.6,index===3?.58:.46,index===3?.65:.6,-8);
  }
 }
 height(p:Point):number {
  const outside=Math.max(0,Math.abs(p.x)-this.area.width/2,Math.abs(p.z)-this.area.depth/2);
  return this.terrain.height(p)+(this.area.kind==='interior'?0:Math.min(6,outside*.23)*(this.area.palette==='stone'?1.2:.6));
 }
 material(name:string,color:string,grain=false):Material {
  const key=name+color;if(this.materials.has(key))return this.materials.get(key)!;
  const surface=name==='GrassCover'?'grass':name==='Flagstone'||name==='ResidenceStoneFloor'?'cobble':name==='HearthStone'?'cobble':name==='Road'&&this.area.kind==='underground'?'cobble':SurfaceMaterials.scenery(name,this.area);
  const ground=name==='Ground',road=name==='Road',cover=name==='GrassCover',blended=road||cover;
  const natural=ground||road||cover||surface==='wood'||surface==='rock'||surface==='cobble';
  const tint=natural?new Color(255,255,255):rgb(color);
  // Keep the source PBR texture detail. Only large surface dyes change: subdued
  // green verges and neutral masonry/structural wood, with earth left warm.
  // Grass007 already contains vivid green: attenuate green relative to red/blue
  // instead of multiplying a second green dye over the photographed groundcover.
  if(surface==='grass')tint.set(255,216,246,255);
  if(this.area.kind==='underground'&&surface==='rock')tint.set(223,226,228,255);
  if(this.area.kind==='underground'&&ground)tint.set(177,180,182,255);
  if(this.area.kind==='underground'&&road)tint.set(199,201,201,255);
  if(name==='ResidenceStoneFloor')tint.set(207,208,207,255);
  if(surface==='wood'&&/Timber|DoorFrame|WindowFrame/.test(name))tint.set(162,164,165,255);
  // Shared Material assets must receive pipeline overrides at initialization.
  // Runtime overridePipelineStates is only supported on material instances.
  const states=blended?{depthStencilState:{depthWrite:false},blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}:undefined;
  // Painted source surfaces can render briefly during async preparation. They
  // need neither lighting nor instancing of their unique procedural meshes.
  let m:Material;
  if(this.painted){m=new Material();m.name=name;m.initialize({effectName:'builtin-unlit',technique:blended?1:0,defines:{USE_VERTEX_COLOR:blended},states});m.setProperty('mainColor',tint);m.setProperty('tilingOffset',new Vec4(1,1,0,0));}
  else{m=SurfaceMaterials.create(name,surface,tint,1,undefined,false,states,cover);if(ground)m.setProperty('normalStrength',this.area.kind==='interior'?.45:.35);}
  this.materials.set(key,m);return m;
 }
 mesh(kind:string,size?:Vec3,tile?:number):Mesh {
  const key=kind==='box'&&size&&tile?kind+':'+size.x+','+size.y+','+size.z+':'+tile:kind;
  if(!this.meshes.has(key)){
   const g=kind==='sphere'?primitives.sphere(.5,{segments:14}):kind==='cylinder'?primitives.cylinder(.5,.5,1,{radialSegments:12}):kind==='cone'?primitives.cylinder(.03,.5,1,{radialSegments:14}):primitives.box();
   if(kind==='box'&&size&&tile&&g.uvs&&g.normals){
    // Keep the native box's face orientation. Its +/-Z faces use X/Y UV axes,
    // +/-X use Z/Y, and +/-Y use X/Z. Positive scaling preserves its tangents.
    for(let i=0;i<g.uvs.length/2;i++){
     const nx=Math.abs(g.normals[i*3]),ny=Math.abs(g.normals[i*3+1]);
     g.uvs[i*2]*=(nx>.5?size.z:size.x)/tile;
     g.uvs[i*2+1]*=(ny>.5?size.z:size.y)/tile;
    }
   }
   this.meshes.set(key,utils.createMesh(withTangents(g),undefined,{calculateBounds:true}));
  }return this.meshes.get(key)!;
 }
 shape(name:string,kind:string,p:Vec3,size:Vec3,color:string,parent=this.root,rotation?:Vec3):Node {
  const n=new Node(name);parent.addChild(n);n.setPosition(p);n.setScale(size);if(rotation)n.setRotationFromEuler(rotation);
  const surface=name==='Flagstone'||name==='HearthStone'?'cobble':SurfaceMaterials.scenery(name,this.area);
  // Painted scenery consumes the transform/layout metadata below. Its final
  // cards and surfaces are built by FlatWorldPresentation; no hidden 3D volume
  // mesh, material or render component is needed for these placeholders.
  if(!this.painted){const renderer=n.addComponent(MeshRenderer);renderer.mesh=this.mesh(kind,kind==='box'&&surface?size:undefined,surface?SurfaceMaterials.tileMetres(surface):undefined);renderer.setMaterial(this.material(name,color,name==='Ground'||name==='Road'||name.includes('Stone')||name.includes('Timber')),0);renderer.shadowCastingMode=1;renderer.receiveShadow=1;}
  if(name==='RiverWater'||name==='BridgeDeck'||name==='Flagstone'||name==='HearthStone'||name==='WovenRugTrim')this.flatMapPatches.push({node:n,kind:name==='RiverWater'?'water':name==='BridgeDeck'?'bridge':name==='WovenRugTrim'?'rug':'paving',color});
  if(parent===this.root&&['PlasterWall','PillarStone','ResidencePierStone','ResidenceWallFootStone','BridgeRail','Waypost'].includes(name))this.flatMapObjects.push({node:n,key:name==='PlasterWall'||name==='ResidenceWallFootStone'?'stone-wall':name==='BridgeRail'?'wood-fence':name==='Waypost'?'signpost':'pillar',kind:'structure',dimensions:size.clone(),centered:true});
  return n;
 }
 box(name:string,x:number,y:number,z:number,w:number,h:number,d:number,color:string,parent=this.root){return this.shape(name,'box',new Vec3(x,y,z),new Vec3(w,h,d),color,parent);}
 obstacle(o:Obstacle){const n=new Node('Collision:'+o.kind);this.root.addChild(n);n.setPosition(o.x,this.height(o)+o.height/2,o.z);const c=n.addComponent(BoxCollider);c.size=new Vec3(o.width,o.height,o.depth);c.setGroup(o.kind==='water'||o.kind==='gorge'?4:2);c.setMask(8);this.colliders.push(c);this.physicsDirty=true;this.movementNavigation=null;this.visibilityFrame=-1;}
 private surface(name:string,positions:number[],indices:number[],uvs:number[],color:string,vertexColors?:number[],groundCollision=true){
  const geometry={positions,indices,uvs,...(vertexColors?{colors:vertexColors}:{})};
  // Painted surfaces use an unlit effect. Avoid four extra height samples per
  // vertex and tangent generation for attributes that shader never reads.
  const normals:number[]=[];
  if(!this.painted)for(let i=0;i<positions.length;i+=3){const x=positions[i],z=positions[i+2],dx=this.height({x:x-.04,z})-this.height({x:x+.04,z}),dz=this.height({x,z:z-.04})-this.height({x,z:z+.04});const n=new Vec3(dx/.08,1,dz/.08).normalize();normals.push(n.x,n.y,n.z);}
  const mesh=utils.createMesh(this.painted?geometry:withTangents({...geometry,normals}),undefined,{calculateBounds:true});
  const n=new Node(name);this.root.addChild(n);const r=n.addComponent(MeshRenderer);r.mesh=mesh;r.setMaterial(this.material(name,color,true),0);r.receiveShadow=1;this.flatMapSurfaces.push(r);this.generatedMeshes.add(mesh);
  if(name==='Ground'&&groundCollision){const collider=n.addComponent(MeshCollider);collider.mesh=mesh;collider.convex=false;collider.setGroup(4);collider.setMask(8);this.physicsDirty=true;}return r;
 }
 private chunkedGround(positions:number[],indices:number[],uvs:number[],color:string,nx:number,nz:number){
  // Keep the original collision triangles in one continuous Bullet shape.
  // Collision needs positions/indices only, and has no render component.
  const collisionMesh=utils.createMesh({positions,indices},undefined,{calculateBounds:true}),node=new Node('GroundCollision');this.generatedMeshes.add(collisionMesh);this.root.addChild(node);
  const collider=node.addComponent(MeshCollider);collider.mesh=collisionMesh;collider.convex=false;collider.setGroup(4);collider.setMask(8);this.physicsDirty=true;
  // Partition the existing 1.5m grid, preserving every triangle and global UV.
  // Native Cocos bounds/frustum culling then submits only intersecting chunks.
  const cells=16;
  for(let z=0;z<nz;z+=cells)for(let x=0;x<nx;x+=cells){
   const width=Math.min(cells,nx-x),depth=Math.min(cells,nz-z),p:number[]=[],t:number[]=[],uv:number[]=[];
   for(let dz=0;dz<=depth;dz++)for(let dx=0;dx<=width;dx++){const i=(z+dz)*(nx+1)+x+dx;p.push(positions[i*3],positions[i*3+1],positions[i*3+2]);uv.push(uvs[i*2],uvs[i*2+1]);}
   for(let dz=0;dz<depth;dz++)for(let dx=0;dx<width;dx++){const i=dz*(width+1)+dx;t.push(i,i+width+1,i+1,i+1,i+width+1,i+width+2);}
   this.groundChunks.push(this.surface('Ground',p,t,uv,color,undefined,false));
  }
 }
 private ground(){const {width:logicalW,depth:logicalD}=this.area,w=logicalW+(this.area.kind==='interior'?0:70),d=logicalD+(this.area.kind==='interior'?0:70),positions:number[]=[],indices:number[]=[],uvs:number[]=[];const step=1.5,nx=Math.ceil(w/step),nz=Math.ceil(d/step),tile=SurfaceMaterials.tileMetres(SurfaceMaterials.ground(this.area));for(let z=0;z<=nz;z++)for(let x=0;x<=nx;x++){const px=-w/2+w*x/nx,pz=-d/2+d*z/nz;positions.push(px,this.height({x:px,z:pz})-(this.terrain.bridges.some(b=>Math.abs(px-b.x)<=b.width/2+.01&&Math.abs(pz-b.z)<=b.depth/2+.01)?.08:0),pz);uvs.push(px/tile,pz/tile);}for(let z=0;z<nz;z++)for(let x=0;x<nx;x++){const i=z*(nx+1)+x;indices.push(i,i+nx+1,i+1,i+1,i+nx+1,i+nx+2);}const color=this.area.kind==='interior'?(this.area.id==='S01-T6'?'#938776':'#927353'):this.area.palette==='forest'?colors.forest:this.area.palette==='cave'?colors.cave:this.area.palette==='stone'?colors.stone:this.area.palette==='marsh'?'#697966':colors.grass;if(this.painted&&this.area.kind!=='interior')this.chunkedGround(positions,indices,uvs,color,nx,nz);else this.surface('Ground',positions,indices,uvs,color);
  if(this.area.kind==='interior'){this.indoorFloor();return;}
  for(const e of this.area.exits)this.road(this.area.spawn,e);
  for(const o of this.area.objects)this.road(this.area.spawn,o,1.2,true);
  if(this.area.kind!=='underground'&&(this.area.palette==='forest'||this.area.palette==='marsh'||this.area.palette==='meadow'&&this.area.kind!=='town'))this.forestGroundCover();
 }
 private forestGroundCover(){
  // One shared mesh holds irregular, alpha-faded patches above the existing
  // walk surface. Source UVs stay at the original two-metre grass tile scale.
  const positions:number[]=[],indices:number[]=[],uvs:number[]=[],vertexColors:number[]=[],used=new Set<string>(),tile=SurfaceMaterials.tileMetres('grass'),marsh=this.area.palette==='marsh',limit=marsh?20:38;let patches=0;
  for(const route of this.approaches)for(let i=1;i<route.length;i++){
   const a=route[i-1],b=route[i],dx=b.x-a.x,dz=b.z-a.z,length=Math.hypot(dx,dz);if(length<3)continue;
   for(let along=4;along<length&&patches<limit;along+=8+noise(i,Math.floor(along))*7)for(const side of [-1,1]){
    if(patches>=limit)break;
    // Missing patches and varied shoulders form a broken verge, rather than
    // two evenly spaced strings following every generated approach route.
    if(noise(Math.floor(along)+i*19,side+17)<.42)continue;
    const shoulder=2.6+noise(along,i+side)*2.2,x=a.x+dx/length*along-dz/length*side*shoulder,z=a.z+dz/length*along+dx/length*side*shoulder,key=Math.round(x/4)+','+Math.round(z/4);
    if(used.has(key)||!this.clearForDecoration(x,z,.7))continue;used.add(key);
    const start=positions.length/3,seed=patches++,rx=1.15+noise(seed,41)*1.25,rz=.8+noise(seed,42)*.9,segments=12;
    const vertex=(px:number,pz:number,alpha:number)=>{positions.push(px,this.height({x:px,z:pz})+.018,pz);uvs.push(px/tile,pz/tile);vertexColors.push(1,1,1,alpha);};
    vertex(x,z,.34);
    for(const ring of [.6,1])for(let j=0;j<segments;j++){const angle=(j+noise(j,seed+51)*.45)*Math.PI*2/segments,r=ring*(.65+noise(j,seed)*.65);vertex(x+Math.cos(angle)*rx*r,z+Math.sin(angle)*rz*r,ring===1?0:.38);}
    for(let j=0;j<segments;j++){const next=(j+1)%segments;indices.push(start,start+1+next,start+1+j);const inner=start+1+j,innerNext=start+1+next,outer=start+1+segments+j,outerNext=start+1+segments+next;indices.push(inner,innerNext,outer,innerNext,outerNext,outer);}
   }
  }
  if(indices.length)this.surface('GrassCover',positions,indices,uvs,'#ffffff',vertexColors);
 }
 private road(a:Point,b:Point,width=2.2,branch=false){
  const original=this.navigation.path(a,b);this.approaches.push(original);let path=original;
  if(branch&&original.length>1&&this.roadNetwork.length){
   // Extra visual-route queries use a separate cache. The original navigation
   // calls and approach paths still drive exactly the same dressing clearance.
   const nav=this.roadNavigation??=new Navigation(this.navigation.width,this.navigation.depth,this.navigation.obstacles);
   let closest:Point|undefined,best=Infinity;
   for(const route of this.roadNetwork)for(let i=1;i<route.length;i++){
    const u=route[i-1],v=route[i],dx=v.x-u.x,dz=v.z-u.z,t=Math.max(0,Math.min(1,((b.x-u.x)*dx+(b.z-u.z)*dz)/(dx*dx+dz*dz||1))),candidate={x:u.x+dx*t,z:u.z+dz*t},distance=Math.hypot(candidate.x-b.x,candidate.z-b.z);
    if(distance<best&&!nav.blocked(candidate,.32)){closest=candidate;best=distance;}
   }
   if(closest){const connected=nav.path(closest,b);if(connected.length>1)path=connected;}
  }
  if(path.length>1)this.roadNetwork.push(path);
  for(let i=1;i<path.length;i++)this.roadSegment(path[i-1],path[i],width);
 }
 private asset(key:string,x:number,y:number,z:number,size:PropSize={},parent=this.root){const node=EnvironmentAssets.place(key,parent,new Vec3(x,y,z),size,this.painted);this.flatMapObjects.push({node,key,kind:'asset'});if(key==='lantern'||key==='candlestick'||key==='firepit')this.practicalSources.push({node,kind:key,height:size.height??.4});return node;}
 private decoration(key:string,x:number,y:number,z:number,size:PropSize,terrainRole:'verge'|'ground-cluster'|'framing'){
  const node=this.asset(key,x,y,z,size),record=this.flatMapObjects[this.flatMapObjects.length-1];record.decorative=true;record.terrainRole=terrainRole;return node;
 }
 private carpet(x:number,z:number,w:number,d:number,tint='#6a4c55'){
  // World-sized UVs keep a small woven rug from becoming one stretched swatch.
  const y=this.height({x,z})+.035,tile=SurfaceMaterials.tileMetres('fabric');
  this.surface('WovenRug',[x-w/2,y,z-d/2,x+w/2,y,z-d/2,x-w/2,y,z+d/2,x+w/2,y,z+d/2],[0,2,1,1,2,3],[0,0,w/tile,0,0,d/tile,w/tile,d/tile],tint);
  const trim=(xx:number,zz:number,ww:number,dd:number,color:string)=>{const part=this.box('WovenRugTrim',xx,y+.018,zz,ww,.008,dd,color);if(!this.painted)part.getComponent(MeshRenderer)!.shadowCastingMode=0;};
  for(const side of [-1,1]){trim(x+side*(w/2-.13),z,.055,d-.15,'#889797');trim(x,z+side*(d/2-.13),w-.15,.055,'#889797');}
  for(const side of [-1,1]){trim(x+side*(w/2-.24),z,.025,d-.4,'#394954');trim(x,z+side*(d/2-.24),w-.4,.025,'#394954');}
 }
 private indoorFloor(){
  const {width:w,depth:d,id}=this.area;if(id==='S01-T6')return;
  const inn=id==='S01-T1';
  if(inn){
   this.carpet(0,-12,1.55,2.9,'#476d68');
   this.carpet(-2.8,-9.8,3.7,3.5,'#526579');
   this.carpet(1.8,-2.8,3.2,3.0,'#70515c');
  }else if(id==='S01-T2')this.carpet(0,-4.5,2.7,4.2,'#6a555a');
  else if(id==='S01-T3'){
   // Non-combustible working pads belong to the forge and repair table. Their
   // shallow presentation meshes do not add a second floor collider or step.
   this.box('HearthStone',-12,.026,10,8,.035,7,'#898a83');
   this.box('Flagstone',10,.024,-10,7,.032,4.4,'#93928a');
  }
  // Paving defines door thresholds and working zones without adding blockers.
  for(const exit of this.area.exits)this.box('Flagstone',exit.x,this.height(exit)+.023,exit.z,2.8,.025,2.7,'#aaa28c');
  if(inn){
   for(const table of INN_OPENING.filter(p=>p.key==='round-table')){
    const x=table.x+.42,z=table.z+.12,y=table.height+.02;this.asset('lantern',x,y,z,{height:.34});
    const lamp=new Node('TavernFixture');this.root.addChild(lamp);lamp.setPosition(x,y+.43,z);const light=lamp.addComponent(PointLight);light.color=new Color(255,205,143);light.range=2.8;
    // Set lumens, not nits: luminance=1400 produced a 55,270 lm floodlight.
    light.term=0;light.luminousFlux=95;
   }
   this.carpet(-5,3,5.2,3.3,'#5b6e73');this.box('HearthStone',12,.025,11.3,9,.04,7,'#a0adb5');
   // Panelled hearth, shutters and hanging lamps stay inside existing wall footprints.
   for(const z of [-11,-5,3,11])for(const x of [-w/2+.32,w/2-.32]){
    this.asset('lantern',x,1.55,z,{height:.58,yaw:x>0?90:-90});
   }
   for(const x of [-11,-5,1,7,13]){
    this.box('WindowFrame',x,2.04,-d/2+.34,1.7,1.45,.1,colors.timber);
    this.box('WindowGlow',x,2.04,-d/2+.4,1.4,1.15,.04,'#b7d3df');
    for(const side of [-1,1])this.box('WindowShutter',x+side*.92,2.04,-d/2+.42,.38,1.42,.09,'#67533b');
    this.box('Mullion',x,2.04,-d/2+.46,.065,1.2,.05,colors.timber);
    this.box('Mullion',x,2.04,-d/2+.47,1.45,.06,.05,colors.timber);
   }
  }
  // Narrow skirting interrupts the floor at the room boundary and grounds the walls.
  for(const x of [-w/2+.4,w/2-.4])this.box('FloorSkirting',x,.08,0,.24,.12,d-.5,'#554430');
  for(const z of [-d/2+.4,d/2-.4])this.box('FloorSkirting',0,.08,z,w-.5,.12,.24,'#554430');
 }
 private tableware(x:number,y:number,z:number,w:number,d:number,parent=this.root){
  for(const side of [-1,1])this.asset('bowl',x+side*w*.27,y,z+d*.18,{width:.29,height:.12,depth:.28},parent);
  this.asset('jug',x+w*.12,y,z-d*.18,{width:.3,height:.32,depth:.24,yaw:25},parent);
  this.asset('candlestick',x-w*.25,y,z-d*.15,{height:.36},parent);
 }
 private furnishing(o:Obstacle):boolean {
  const x=o.x,z=o.z,w=o.width,d=o.depth,h=o.height,y=this.height(o);
  const placement=this.scenePlacements.get(o);
  if(placement){
   const {key,width,height,depth,yaw}=placement;
   this.asset(key,x,y,z,{width,height,depth,yaw});
   if(placement.dressing==='supper'){
    this.asset('jug',x-.2,y+height+.018,z-.15,{height:.25,width:.22,depth:.21,yaw:25});
    this.asset('bowl',x+.22,y+height+.018,z+.28,{height:.10,width:.27,depth:.26});
   }else if(placement.dressing==='ledger'){
    this.asset('books',x-.12,y+height+.018,z-.03,{width:.42,height:.13,depth:.32,yaw:-12});
    this.asset('bowl',x+.25,y+height+.018,z+.28,{height:.09,width:.23,depth:.23});
   }else if(placement.dressing==='sideboard'){
    this.asset('jug',x-.62,y+height+.01,z,{height:.29,width:.22,depth:.2});
    this.asset('bowl',x+.35,y+height+.01,z,{height:.1,width:.28,depth:.25});
    this.asset('books',x,y+.13,z-.1,{width:.58,height:.16,depth:.32});
   }
   return true;
  }
  if(o.kind==='table'){
   if(this.area.id==='S01-T1'){
    // The stock dining table includes a bright checker cloth. Bare wood groups
    // suit this inn without multiplying a dark tint over the source photograph.
    const count=w>3?2:1,diameter=Math.min(d,w/count-.12);
    for(let i=0;i<count;i++)this.asset('round-table',x+(i-(count-1)/2)*w/count,y,z,{width:diameter,height:h,depth:diameter});
    this.asset('jug',x-.3,y+h+.018,z+.1,{height:.28,width:.24,depth:.22});
    this.asset('books',x+.38,y+h+.018,z-.1,{width:.52,height:.15,depth:.34});return true;
   }
   this.asset(this.layoutObstacles.includes(o)&&o.x>0?'round-table':'table',x,y,z,{width:w,height:h,depth:d});this.tableware(x,y+h+.018,z,w,d);
   return true;
  }
  if(o.kind==='bench'){
   const seats=Math.max(2,Math.floor(w/1.1));for(let i=0;i<seats;i++)this.asset(i%2===0?'chair':'stool',x-w/2+(i+.5)*w/seats,y,z,{width:Math.min(.65,w/seats-.1),height:i%2===0?h*2.4:h,depth:Math.min(.65,d),yaw:180});return true;
  }
  if(o.kind==='shelf'){
   const bays=Math.max(1,Math.round(w/1.7));for(let i=0;i<bays;i++){
    const xx=x-w/2+(i+.5)*w/bays;this.asset('shelf',xx,y,z,{width:w/bays-.08,height:h,depth:d});
    for(let level=0;level<3;level++){
     const yy=y+h*(.1+level*.27);
     if((i+level)%3===0)this.asset('jug',xx,yy,z-d*.08,{height:h*.21,width:w/bays*.24,depth:d*.48,yaw:i*53});
     else this.asset('books',xx,yy,z-d*.13,{width:w/bays*.72,height:h*.21,depth:d*.57});
    }
   }return true;
  }
  if(o.kind==='forge'){
   this.flatMapObjects.push({node:this.colliders[this.colliders.length-1].node,key:'forge',kind:'structure',dimensions:new Vec3(w,h,d),centered:true});
   this.box('ForgeStone',x,y+.34,z,w,.68,d,colors.darkStone);this.asset('firepit',x,y+.69,z,{width:w*.72,height:.52,depth:d*.78});
   this.box('Anvil',x-w*.28,y+1.12,z-d*.21,w*.28,.28,d*.3,'#565957');return true;
  }
  if(o.kind==='wall'){
   const indoor=this.area.kind==='interior',height=indoor&&((w>d&&z>this.area.depth*.23)||(d>w&&x>this.area.width*.23))?Math.min(h,1.1):h;
   this.box('PlasterWall',x,y+height/2,z,w,height,d,indoor?'#c4cbd0':colors.stone);this.box('WallFootStone',x,y+.18,z,w+.04,.36,d+.04,colors.darkStone);
   const horizontal=w>d,length=horizontal?w:d;for(let k=-length/2+.2;k<length/2;k+=3.5){
    this.box('TimberPost',x+(horizontal?k:0),y+height/2,z+(horizontal?0:k),horizontal?.16:w+.045,height,horizontal?d+.045:.16,colors.timber);
    if(indoor&&height>2){const panel=this.box('TimberBrace',x+(horizontal?k+.75:0),y+height*.7,z+(horizontal?0:k+.75),horizontal?1.6:w+.06,.09,horizontal?d+.06:1.6,colors.timber);panel.setRotationFromEuler(horizontal?0:35,0,horizontal?35:0);}
   }
   this.box('TimberBeam',x,y+height-.1,z,w+.05,.16,d+.05,colors.timber);
   if(indoor&&height>2)this.box('TimberDado',x,y+.88,z,w+.06,.09,d+.06,colors.timber);return true;
  }
  return false;
 }
 private roadSegment(a:Point,b:Point,width:number){
  const dx=b.x-a.x,dz=b.z-a.z,len=Math.hypot(dx,dz);if(len<.5)return;
  const positions:number[]=[],indices:number[]=[],uvs:number[]=[],vertexColors:number[]=[],steps=Math.ceil(len/.65);
  for(let i=0;i<=steps;i++){
   const t=i/steps,x=a.x+dx*t,z=a.z+dz*t;
   for(const [side,alpha] of [[-1,0],[-.54,.86],[.54,.86],[1,0]]){
    const edge=width/2+.22+noise(x*.5,z*.5)*.12,px=x-dz/len*edge*side,pz=z+dx/len*edge*side;
    positions.push(px,this.height({x:px,z:pz})+.035,pz);const tile=SurfaceMaterials.tileMetres(this.area.kind==='town'||this.area.kind==='underground'?'cobble':'earth');uvs.push(px/tile,pz/tile);vertexColors.push(1,1,1,alpha);
   }
   if(i<steps&&!this.terrain.bridges.some(b=>Math.abs(x+dx/steps/2-b.x)<b.width/2&&Math.abs(z+dz/steps/2-b.z)<b.depth/2))for(let k=0;k<3;k++){const j=i*4+k;indices.push(j,j+1,j+4,j+1,j+5,j+4);}
  }
  if(indices.length)this.surface('Road',positions,indices,uvs,this.area.kind==='underground'?'#77756a':colors.dirt,vertexColors);
 }
 private building(b:Building){const n=new Node(b.name);this.root.addChild(n);n.setPosition(b.x,this.height(b),b.z);if(b.rotation)n.setRotationFromEuler(0,b.rotation,0);const w=b.width,d=b.depth,h=b.height;this.flatMapObjects.push({node:n,key:this.area.kind==='underground'?'ruin':b.style,kind:'building',dimensions:new Vec3(w,h,d)});
  if(b.style==='tent'){this.shape('Canvas','cone',new Vec3(0,h/2,0),new Vec3(w,h,d),this.area.id==='S09'?'#596c78':'#bfc9c6',n);this.box('Door',0,h*.28,-d*.43,w*.28,h*.5,.06,colors.timber,n);return;}
  if(b.style==='ruin'){for(const x of [-w/2,w/2])this.box('BrokenStone',x,h*.32,0,.65,h*.64,d,colors.stone,n);this.box('BrokenStone',0,h*.2,d/2,w,h*.4,.65,colors.darkStone,n);for(let i=0;i<5;i++)this.asset('rocks-'+i,(noise(i,3)-.5)*w,0,(noise(i,4)-.5)*d,{width:1.3,height:.7,depth:1.1,yaw:i*47},n);return;}
  if(this.area.kind==='underground'){this.undergroundMasonry(b,n);return;}
  if(this.area.id==='S01'){this.townFacade(b,n);return;}
  const stone=b.style==='tower'||b.style==='gate'||b.style==='workshop';this.box('Plaster',0,h/2,0,w,h,d,stone?'#a9b5bd':'#c6cdd0',n);this.box('FoundationStone',0,.4,0,w+.16,.8,d+.16,colors.darkStone,n);
  for(const x of [-w*.48,w*.48])for(const z of [-d*.48,d*.48])this.box('Timber',x,h/2,z,.18,h,.18,colors.timber,n);
  for(const y of [1.1,h-.2]){this.box('Timber',0,y,-d/2-.035,w,.12,.1,colors.timber,n);this.box('Timber',-w/2-.035,y,0,.1,.12,d,colors.timber,n);}
  this.box('DoorFrame',0,1.2,-d/2-.09,1.35,2.4,.18,colors.timber,n);this.asset('door',0,0,-d/2-.2,{width:1.2,height:2.4,depth:.15},n);
  for(const side of [-1,1]){this.box('WindowFrame',side*w*.28,1.8,-d/2-.1,1.1,1.25,.12,colors.timber,n);this.box('WindowGlow',side*w*.28,1.8,-d/2-.18,.85,.95,.06,'#a9c7d5',n);this.box('Mullion',side*w*.28,1.8,-d/2-.22,.07,1.05,.05,colors.timber,n);}
  const pitch=30;for(const side of [-1,1])this.shape('Roof','box',new Vec3(side*w*.25,h+.65,0),new Vec3(w*.61,.18,d+.7),colors.roof,n,new Vec3(0,0,side*pitch));
  this.box('RoofRidge',0,h+1.4,0,.16,.2,d+.8,colors.timber,n);
  this.box('ChimneyStone',w*.28,h+1.3,d*.2,.65,2,.7,colors.stone,n);
  this.asset('lantern',w*.16,1.35,-d/2-.33,{height:.58},n);
  for(const side of [-1,1])this.shape('TimberBrace','box',new Vec3(side*w*.3,h*.54,-d/2-.055),new Vec3(w*.37,.14,.12),colors.timber,n,new Vec3(0,0,side*37));
  if(b.style==='mill'){const hub=new Node('Waterwheel');n.addChild(hub);hub.setPosition(w/2+.55,1.7,0);this.flatMapObjects.push({node:hub,key:'waterwheel',kind:'structure',dimensions:new Vec3(3.4,3.4,1.2),centered:true});for(let i=0;i<10;i++){const a=i*36;this.shape('WheelSpoke','box',new Vec3(0,0,0),new Vec3(.16,.15,3.2),colors.wood,hub,new Vec3(a,0,0));}for(const x of [-.35,.35])this.shape('WheelRim','cylinder',new Vec3(x,0,0),new Vec3(3.4,.12,3.4),colors.wood,hub,new Vec3(0,0,90));}
  if(b.style==='gate'){this.box('GatePostStone',-w*.7,2.6,0,1.1,5.2,1.6,colors.stone,n);this.box('GatePostStone',w*.7,2.6,0,1.1,5.2,1.6,colors.stone,n);this.box('GateLintel',0,4.7,0,w*1.5,.9,1.5,colors.stone,n);}
 }
 private undergroundMasonry(b:Building,n:Node){
  // Retain the blocked building footprint, but use cellar masonry and original
  // rock caps rather than above-ground cottage roofs inside the cavern.
  const w=b.width,d=b.depth,h=Math.min(4.4,b.height),front=-d/2;
  this.box('DungeonWallStone',0,h*.45,0,w,h*.9,d,'#777b70',n);
  this.box('DungeonWallFootStone',0,.28,0,w+.02,.56,d+.02,colors.darkStone,n);
  for(const x of [-w/2+.32,w/2-.32])this.box('DungeonPierStone',x,h*.47,front+.22,.62,h*.94,.48,colors.stone,n);
  const bays=Math.max(2,Math.round(w/5));
  for(let i=0;i<bays;i++)this.asset('rocks-'+i%6,-w/2+(i+.5)*w/bays,h*.73,0,{width:w/bays*.99,height:h*.38,depth:d*.96,yaw:i*41},n);
  for(const side of [-1,1]){
   const x=side*w*.29;this.box('DungeonRecess',x,1.8,front-.018,1.05,.8,.035,'#202c39',n);
   this.box('DungeonLintelStone',x,2.27,front+.04,1.4,.17,.19,colors.stone,n);
   for(const bar of [-.28,0,.28])this.box('DungeonIronGrille',x+bar,1.8,front-.05,.045,.8,.045,'#4e5e6b',n);
  }
  this.box('DungeonDoorFrameStone',0,1.28,front+.1,1.8,2.56,.28,colors.darkStone,n);
  this.asset('door',0,0,front-.055,{width:1.22,height:2.24,depth:.12},n);
  this.box('DungeonThresholdStone',0,.07,front+.05,1.95,.14,.28,colors.stone,n);
  this.asset('lantern',1.15,1.58,front-.24,{height:.47},n);
 }
 private townFacade(b:Building,n:Node){
  const w=b.width,d=b.depth,h=b.height,front=-d/2,workshop=b.style==='workshop',warehouse=b.style==='barn';
  // Recess the plaster rather than expanding the ground-level footprint. Every
  // sill, jamb and post remains inside the existing Navigation/Bullet building.
  this.box('Plaster',0,h/2,.3,w,h,d-.6,workshop?'#9aabb1':'#c3cbce',n);
  this.box('FoundationStone',0,.37,0,w,.74,d,colors.darkStone,n);
  this.box('WallFootStone',0,.85,front+.25,w,.22,.5,colors.stone,n);
  for(const x of [-w/2+.15,w/2-.15])for(const z of [front+.15,d/2-.15])this.box('TimberPost',x,h/2,z,.25,h,.25,colors.timber,n);
  for(const x of [-w*.42,-w*.14,w*.14,w*.42])this.box('TimberPost',x,h/2,front+.27,.18,h,.24,colors.timber,n);
  for(const y of [1.02,3.22,h-.18])this.box('TimberBeam',0,y,front+.24,w,.15,.26,colors.timber,n);
  this.box('DoorFrame',0,1.34,front+.36,1.65,2.68,.38,colors.timber,n);
  this.asset('door',0,0,front+.08,{width:1.24,height:2.45,depth:.12},n);
  this.box('ThresholdStone',0,.07,front+.23,2.15,.14,.46,colors.stone,n);
  for(const side of [-1,1]){
   const x=side*w*.28;
   this.box('WindowFrame',x,1.98,front+.36,2.32,1.75,.32,colors.timber,n);
   this.box('WindowWell',x,2.0,front+.13,1.96,1.39,.045,'#2d4050',n);
   this.box('WindowPane',x,2.0,front+.105,1.78,1.25,.025,workshop?'#7694a1':'#92acb7',n);
   this.box('Mullion',x,2.0,front+.078,.085,1.4,.04,colors.timber,n);
   this.box('Mullion',x,2.0,front+.076,1.98,.075,.04,colors.timber,n);
   this.box('WindowSillStone',x,1.08,front+.24,2.58,.16,.47,colors.stone,n);
   this.box('WindowShutter',x+side*1.42,2.0,front+.15,.48,1.65,.18,colors.wood,n);
   const brace=this.box('TimberBrace',x,h*.61,front+.25,w*.22,.12,.19,colors.timber,n);brace.setRotationFromEuler(0,0,side*38);
  }
  // A narrow canopy gives the doorway a shadow and human scale. Its posts sit
  // in the wall band; the projecting fabric is overhead, above the player.
  const awning=this.box(warehouse?'TimberAwning':'Canvas',0,2.92,front-.34,warehouse?3.8:3.4,.12,1.22,warehouse?colors.wood:workshop?'#536d7b':'#607d73',n);awning.setRotationFromEuler(-9,0,0);
  for(const side of [-1,1])this.box('TimberPost',side*1.4,1.4,front+.13,.14,2.8,.19,colors.timber,n);
  this.asset('lantern',1.03,1.8,front-.25,{height:.49},n);
  for(const side of [-1,1])this.shape('Roof','box',new Vec3(side*w*.25,h+.65,0),new Vec3(w*.61,.18,d+1.1),colors.roof,n,new Vec3(0,0,side*30));
  this.box('TimberEave',0,h-.03,front-.35,w+.45,.21,.6,colors.timber,n);
  this.box('RoofRidge',0,h+1.4,0,.16,.2,d+1.1,colors.timber,n);
  this.box('ChimneyStone',w*.28,h+1.3,d*.2,.65,2,.7,colors.stone,n);
 }
 private tree(x:number,z:number,s:number,seed:number,framing=false){
  const size={height:s*1.55,yaw:seed*67};if(framing)this.decoration('tree',x,this.height({x,z}),z,size,'framing');else this.asset('tree',x,this.height({x,z}),z,size);
  if(seed%3===0)this.asset('fern-'+Math.abs(seed%4),x+s*.23,this.height({x:x+s*.23,z}),z,{height:.55,yaw:seed*39});
 }
 private prop(o:any){
  const n=new Node(o.id);this.root.addChild(n);n.setPosition(o.x,this.height(o),o.z);this.propNodes.set(o.id,n);if(o.actor&&o.action!=='meeting')return;
  if(o.action==='checkpoint'){
   // The interact/spawn point is clear ground beside the hearth, never its fire.
   this.asset('firepit',1.65,0,.1,{width:1.3,height:.32,depth:1.3},n);
   for(let i=0;i<3;i++)this.shape('Firewood','cylinder',new Vec3(1.65,.17+i*.055,.1),new Vec3(.12,1.05,.12),colors.wood,n,new Vec3(90,i*60,0));
   this.asset('stool',-1.7,0,-1.1,{height:.48},n);this.asset('jug',-1.7,.49,-1.1,{height:.2},n);this.asset('lantern',2.6,0,.65,{height:.4},n);return;
  }
  if(o.action==='cache'||o.action==='recover'||o.check==='inn-lockbox'){
   if(o.action==='recover')this.flatMapObjects.push({node:n,key:'wagon',kind:'structure',dimensions:new Vec3(2.8,1.9,4.4)});
   this.asset('chest',0,0,0,{width:1.05,height:.68,depth:.72},n);
   if(o.action==='recover'){
    // The broken cart keeps its original gameplay footprint; scanned parcels replace cubes.
    this.box('CartBed',0,.75,2.7,1.7,.16,2.7,colors.wood,n);
    for(const side of [-1,1]){this.box('CartSide',side*.85,1.12,2.7,.1,.65,2.7,colors.wood,n);this.box('CartShaft',side*.58,.8,.3,.1,.12,2.6,colors.timber,n);for(const zz of [1.8,3.6])this.shape('CartWheel','cylinder',new Vec3(side*1.02,.48,zz),new Vec3(.95,.12,.95),colors.timber,n,new Vec3(0,0,90));}
    this.asset('barrel',-.36,.85,2.3,{height:.9,width:.65,depth:.65,yaw:15},n);this.asset('crate',.35,.85,3.1,{width:.85,height:.6,depth:1.05,yaw:-8},n);
    this.box('BrokenAxle',-.4,.16,4.2,2.5,.18,.18,colors.timber,n);
   }return;
  }
  if(o.action==='captain_gate'){this.flatMapObjects.push({node:n,key:'gate',kind:'structure',dimensions:new Vec3(3.7,2.5,.6)});this.box('GateBar',0,1.15,0,3.7,.2,.22,colors.wood,n);for(const x of [-1.6,1.6])this.box('GatePost',x,1.25,0,.25,2.5,.3,colors.timber,n);return;}
  if(o.action==='meeting'){this.asset('table',0,0,0,{width:3.5,height:.9,depth:1.5},n);this.box('TimberDiningBoard',0,.925,0,3.56,.05,1.53,colors.wood,n);this.tableware(0,.96,0,3.5,1.5,n);if(this.area.id==='U1-04')this.dinnerResidence(o,n);return;}
  const cup=/thirdcup|cup|dinner|living/.test(o.id),ledger=/book|ledger|registry|contract|letter|copy/.test(o.id);
  this.asset('stool',0,0,0,{width:.72,height:.72,depth:.65},n);
  if(cup)this.asset('jug',0,.73,0,{height:.24,width:.24,depth:.2},n);
  else if(ledger)this.asset('books',0,.74,0,{width:.62,height:.2,depth:.38},n);
  else{this.box('Paper',0,.74,0,.55,.018,.37,colors.linen,n);this.asset('candlestick',.22,.75,.12,{height:.3},n);}
 }
 private dinnerResidence(o:Point,parent:Node){
  // A worn residence floor gives this story location its own place in the
  // cavern. The two small pier/wall ends clear every existing approach route.
  this.addDressingObstacle('table',o.x,o.z,3.56,1.53,.95);
  const corners=[[-4.8,-3.2],[-4.2,-3.8],[4.2,-3.8],[4.8,-3.2],[4.8,3.2],[4.2,3.8],[-4.2,3.8],[-4.8,3.2]],positions:number[]=[o.x,this.height(o)+.029,o.z],uvs:number[]=[o.x/2,o.z/2],indices:number[]=[];
  for(const [x,z]of corners){const q={x:o.x+x,z:o.z+z};positions.push(q.x,this.height(q)+.029,q.z);uvs.push(q.x/2,q.z/2);}
  for(let i=0;i<corners.length;i++)indices.push(0,1+(i+1)%corners.length,1+i);
  this.surface('ResidenceStoneFloor',positions,indices,uvs,'#b6ad97');
  for(const side of [-1,1]){
   const x=o.x+side*4.25,z=o.z+3.5,y=this.height({x,z}),h=side<0?2.15:1.55,wx=o.x+side*3.25,wz=o.z+3.5,wy=this.height({x:wx,z:wz}),wallClear=this.clearForDecoration(wx,wz,.9,true);
   if(this.clearForDecoration(x,z,.52,true)){
    this.box('ResidencePierStone',x,y+h/2,z,.76,h,.7,colors.darkStone);this.box('ResidencePierFootStone',x,y+.15,z,.94,.3,.88,colors.stone);
    this.asset('rocks-'+(side<0?1:3),x,y+h-.12,z,{width:.82,height:.36,depth:.76,yaw:side*33});this.addDressingObstacle('stone',x,z,.94,.88,h);
   }
   if(wallClear){this.box('ResidenceWallFootStone',wx,wy+.32,wz,1.75,.64,.48,colors.stone);this.addDressingObstacle('stone',wx,wz,1.75,.48,.64);if(side<0)this.asset('lantern',wx-.5,wy+.65,wz,{height:.42});}
   const chairX=o.x+side*1.25,chairZ=o.z-1.3;
   if(this.clearForDecoration(chairX,chairZ,.3)){this.asset('chair',chairX,this.height({x:chairX,z:chairZ}),chairZ,{height:.95,width:.57,depth:.55,yaw:0});this.addDressingObstacle('chair',chairX,chairZ,.57,.55,.95);}
  }
  this.asset('books',-.4,.965,.15,{height:.11,width:.48,depth:.31,yaw:8},parent);
 }
 private bridge(deck:BridgeDef,gap=0){
  const {x,z,width:w,depth:d,deckHeight:y}=deck,stone=deck.material==='stone',color=stone?colors.stone:colors.wood,axis=deck.axis==='x',length=axis?w:d;
  const slab=(center:number,len:number)=>{const node=this.box('BridgeDeck',x+(axis?center:0),y-.16,z+(axis?0:center),axis?len:w,.32,axis?d:len,color);if(!gap){const collider=node.addComponent(BoxCollider);collider.setGroup(4);collider.setMask(8);this.physicsDirty=true;}};
  if(gap){const len=(length-gap)/2;for(const side of [-1,1])slab(side*(gap/2+len/2),len);}else slab(0,length);
  for(let along=-length/2+.4;along<length/2;along+=stone?2:.55){if(gap&&Math.abs(along)<gap/2)continue;this.box('BridgeJoint',x+(axis?along:0),y+.012,z+(axis?0:along),axis?.025:w-.12,.018,axis?d-.12:.025,stone?colors.darkStone:colors.timber);}
  for(const side of [-1,1])for(let along=-length/2+.5;along<length/2;along+=stone?2.5:2){if(gap&&Math.abs(along)<gap/2+.2)continue;const xx=x+(axis?along:side*(w/2-.2)),zz=z+(axis?side*(d/2-.2):along);this.box(stone?'BridgeStonePost':'BridgeTimberPost',xx,y+.48,zz,stone?.38:.16,.96,stone?.38:.16,color);if(along+2<length/2&&(!gap||Math.abs(along+1)>gap/2))this.box('BridgeRail',xx+(axis?1:0),y+.84,zz+(axis?0:1),axis?2.2:.12,.14,axis?.12:2.2,color);}
  for(const p of deck.supports){const bottom=this.terrain.waters.find(water=>Math.abs(p.x-water.x)<water.width/2+2&&Math.abs(p.z-water.z)<water.depth/2+2)?.y??y-1.2;this.box('BridgePier',p.x,(bottom+y)/2-.46,p.z,stone?1.1:.35,y-bottom+.28,stone?1.1:.35,stone?colors.darkStone:colors.timber);}
 }
 private waterworks(){for(const w of this.terrain.waters){const n=this.box('RiverWater',w.x,w.y,w.z,w.width,.04,w.depth,colors.water);if(!this.painted)n.getComponent(MeshRenderer)!.shadowCastingMode=0;for(let i=0;i<10;i++){const xx=w.x+(noise(i,17)-.5)*w.width*.8,zz=w.z+(noise(i,19)-.5)*w.depth*.9;this.box('WaterCurrent',xx,w.y+.028,zz,Math.min(1.4,w.width*.16),.008,.06,'#91b5bf');}}for(const deck of this.terrain.bridges)this.bridge(deck);for(const deck of this.terrain.brokenBridges)this.bridge(deck,deck.gapWidth);}
 private waterfrontLandmarks(){
  if(this.area.id!=='B14')return;
  const water=this.terrain.waters.find(w=>w.kind==='harbor')??this.terrain.waters[0];if(!water||water.width<6||water.depth<4)return;
  const width=Math.min(7,water.width-.8),depth=Math.min(2.6,water.depth-.8),x=water.x+Math.max(0,water.width/2-width/2-.6),z=water.z,y=water.y+.045;
  // The wreck remains wholly inside the already blocked water footprint.
  // Native timber ribs serve the retained 3D comparison; 2D uses its own
  // painted transparent hull rather than relabelling a wagon as a boat.
  const n=new Node('RiverShipwreck');this.root.addChild(n);n.setPosition(x,y,z);
  this.flatMapObjects.push({node:n,key:'shipwreck',kind:'structure',dimensions:new Vec3(width,1.3,depth)});
  this.box('WreckWoodKeel',0,.08,0,width*.9,.16,.22,colors.timber,n);
  for(let i=0;i<6;i++){
   const along=(i/5-.5)*width*.78;
   this.box('WreckTimberRib',along,.22,0,.14,.16,depth*.86,colors.wood,n);
   for(const side of [-1,1])if(!(side>0&&i===4))this.box('WreckWoodHull',along,.4+Math.abs(i-2.5)*.04,side*depth*.42,width*.15,.5,.15,colors.wood,n);
  }
 }
 private clearForDecoration(x:number,z:number,radius=1,tall=false){
  // Late dressing must reserve authored encounter/respawn footprints too. The
  // stone collider is wider than the candidate radius, so keep a full metre.
  if(tall&&this.area.enemies.some(e=>Math.abs(e.x-x)<1+Math.max(.4,enemyHurtRadius(e))&&Math.abs(e.z-z)<1+Math.max(.4,enemyHurtRadius(e))))return false;
  if([...this.area.obstacles,...this.terrain.barriers,...this.layoutObstacles].some(o=>Math.abs(o.x-x)<o.width/2+radius&&Math.abs(o.z-z)<o.depth/2+radius))return false;
  if(this.area.objects.some(o=>Math.hypot(o.x-x,o.z-z)<(tall?2:1.4)+radius)||this.area.exits.some(e=>Math.hypot(e.x-x,e.z-z)<2.2+radius))return false;
  if(Math.hypot(this.area.spawn.x-x,this.area.spawn.z-z)<(tall?2.6:1.6))return false;
  if(this.terrain.waters.some(w=>Math.abs(x-w.x)<w.width/2+.5&&Math.abs(z-w.z)<w.depth/2+.5))return false;
  return !this.approaches.some(route=>route.some((b,i)=>{if(!i)return false;const a=route[i-1],dx=b.x-a.x,dz=b.z-a.z,t=Math.max(0,Math.min(1,((x-a.x)*dx+(z-a.z)*dz)/(dx*dx+dz*dz||1)));return Math.hypot(x-a.x-dx*t,z-a.z-dz*t)<(tall?1.25:.65)+radius;}));
 }
 private setDressing(){
  if(this.area.kind==='interior')return;
  // Small dressing grows out of an edge, bank or an existing solid footprint.
  // These are non-blocking groups: the broad floor and travel lanes stay calm.
  const anchors:{x:number;z:number;seed:number}[]=[];
  for(const [i,o]of [...this.area.obstacles,...this.area.buildings].entries()){
   const solid='kind'in o?['tree','rock','wall','building'].includes(o.kind):true;if(!solid)continue;
   for(const side of [-1,1])anchors.push({x:o.x+side*(o.width/2+.95),z:o.z+(noise(i,side+43)-.5)*o.depth,seed:i*2+(side>0?1:0)});
  }
  for(let side=0;side<4;side++)for(let i=0;i<5;i++){
   const horizontal=side%2===0,length=horizontal?this.area.width:this.area.depth,t=-length/2+(i+.35+noise(i,side)*.45)*length/5;
   anchors.push({x:horizontal?t:(side===1?1:-1)*(this.area.width/2-3.5),z:horizontal?(side===0?1:-1)*(this.area.depth/2-3.5):t,seed:200+side*5+i});
  }
  for(const [i,water]of this.terrain.waters.entries())for(let side=0;side<4;side++)for(let j=0;j<3;j++){
   const horizontal=side%2===0,t=(j+.35+noise(i+j,side)*.3)/3-.5;
   anchors.push({x:water.x+(horizontal?t*water.width:(side===1?1:-1)*(water.width/2+1.2)),z:water.z+(horizontal?(side===0?1:-1)*(water.depth/2+1.2):t*water.depth),seed:400+i*12+side*3+j});
  }
  const used=new Set<string>();
  for(const p of anchors){const key=Math.round(p.x/3)+','+Math.round(p.z/3);if(used.has(key))continue;used.add(key);this.groundCluster(p.x,p.z,p.seed,'ground-cluster');}
  this.pathsideDressing();
  this.entranceDressing();
  // Storefront activity occupies the buildings' already blocked footprints.
  if(this.area.kind==='town'||this.area.kind==='camp')for(const b of this.area.buildings){
   const yaw=b.rotation??0,a=yaw*Math.PI/180,dx=Math.sin(a),dz=Math.cos(a),tx=Math.cos(a),tz=-Math.sin(a);
   for(let i=0;i<3;i++){const side=i===2?-1:1,along=b.width*.34*side,x=b.x+tx*along-dx*(b.depth/2-.35),z=b.z+tz*along-dz*(b.depth/2-.35);
    this.asset(i===1?'crate':'barrel',x,this.height({x,z})+(i===1?.83:0),z,{width:.85,height:i===1?.62:1.05,depth:.85,yaw:yaw+i*19});
   }
  }
 }
 private entranceDressing(){
  // Dress the normal camera's near edges after the established framing
  // colliders have been placed. These additions never create new blockers.
  const spawn=this.area.spawn,warm=this.area.kind==='underground'&&this.area.palette==='warm',candidates:Point[]=[];
  if(warm){
   for(const object of this.flatMapObjects.filter(o=>o.key==='stone-wall')){
    const p=object.node.worldPosition,d=object.dimensions??new Vec3(1,1,1),horizontal=d.x>d.z,inverse=new Quat(),local=new Vec3(spawn.x-p.x,0,spawn.z-p.z);Quat.invert(inverse,object.node.worldRotation);Vec3.transformQuat(local,local,inverse);
    const along=Math.max(-(horizontal?d.x:d.z)/2+.25,Math.min((horizontal?d.x:d.z)/2-.25,horizontal?local.x:local.z));
    for(const side of [-1,1]){
     const offset=new Vec3(horizontal?along:side*(d.x/2+.6),0,horizontal?side*(d.z/2+.6):along);Vec3.transformQuat(offset,offset,object.node.worldRotation);candidates.push({x:p.x+offset.x,z:p.z+offset.z});
    }
   }
  }else{
   // A nearby real bank takes precedence over generic approach-side tufts.
   if(this.area.palette==='marsh')for(const water of this.terrain.waters)for(const side of [-1,1]){
    candidates.push({x:water.x+side*(water.width/2+1.3),z:Math.max(water.z-water.depth/2+.8,Math.min(water.z+water.depth/2-.8,spawn.z+.6))});
    candidates.push({x:Math.max(water.x-water.width/2+.8,Math.min(water.x+water.width/2-.8,spawn.x-.7)),z:water.z+side*(water.depth/2+1.3)});
   }
   const main=this.approaches.slice(0,this.area.exits.length).find(route=>route.length>1),step=main?.find((p,i)=>i>0&&Math.hypot(p.x-spawn.x,p.z-spawn.z)>.1),dx=step?step.x-spawn.x:0,dz=step?step.z-spawn.z:1,length=Math.hypot(dx,dz)||1,fx=dx/length,fz=dz/length;
   // Three compositions and a few offset alternatives, not a circular scatter.
   for(const [side,along]of [[-2.8,1.9],[3.5,-.8],[-1.9,-4.3],[3.1,3.2],[-4.4,-.7],[1.7,-4.4],[-3.8,3.5],[4.7,.9]])candidates.push({x:spawn.x-fz*side+fx*along,z:spawn.z+fx*side+fz*along});
  }
  for(const p of candidates){
   const distance=Math.hypot(p.x-spawn.x,p.z-spawn.z);if(distance<3||distance>6||this.flatEntranceClusters.some(q=>Math.hypot(q.x-p.x,q.z-p.z)<2.1)||!this.clearForDecoration(p.x,p.z,.4))continue;
   const before=this.flatMapObjects.length;this.groundCluster(p.x,p.z,700+this.flatEntranceClusters.length*13,'verge',true);
   if(this.flatMapObjects.length>before)this.flatEntranceClusters.push(p);
   if(this.flatEntranceClusters.length>=(warm?2:3))break;
  }
 }
 private groundCluster(x:number,z:number,seed:number,role:'verge'|'ground-cluster',entrance=false){
  const cave=this.area.kind==='underground',stone=this.area.palette==='stone',forest=this.area.palette==='forest',marsh=this.area.palette==='marsh',warm=cave&&this.area.palette==='warm';
  if(Math.abs(x)>this.area.width/2-1||Math.abs(z)>this.area.depth/2-1||!this.clearForDecoration(x,z,.35))return;
  const count=warm?2:cave||stone?3:marsh||forest&&entrance?5:forest?4:3;
  for(let j=0;j<count;j++){
   const angle=noise(seed+j,29)*Math.PI*2,radius=j===0?0:.3+noise(seed,j+19)*.65,gx=x+Math.cos(angle)*radius,gz=z+Math.sin(angle)*radius;
   if(!this.clearForDecoration(gx,gz,.28))continue;
   const y=this.height({x:gx,z:gz}),n=seed*7+j;
   if(cave||stone||(entrance&&forest&&j===0)||(!forest&&!marsh&&j===count-1&&seed%3===0)){
    this.decoration('rocks-'+(entrance?4+n%2:n%6),gx,y-.035,gz,{width:.35+noise(n,11)*.6,height:.1+noise(n,8)*.18,depth:.3+noise(n,9)*.55,yaw:n*73},role);
   }else if((forest||marsh)&&j===count-1){
    this.decoration('fern-'+n%4,gx,y-.015,gz,{height:.22+noise(n,13)*.18,yaw:n*43},role);
   }else this.decoration('grass-'+n%4,gx,y-.02,gz,{height:(marsh?(entrance?.42:.25):.14)+noise(n,8)*(marsh?.22:.13),yaw:n*137},role);
  }
 }
 private pathsideDressing(){
  const cave=this.area.kind==='underground',stone=this.area.palette==='stone',town=this.area.kind==='town'||this.area.kind==='camp',points:{x:number;z:number;seed:number}[]=[],used=new Set<string>();
  // Keep the established framing/collider candidates stable. Low decoration
  // selects separated groups from these candidates instead of filling each one.
  for(const route of this.approaches)for(let i=1;i<route.length;i++){
   const a=route[i-1],b=route[i],dx=b.x-a.x,dz=b.z-a.z,len=Math.hypot(dx,dz);if(len<1)continue;
   for(let along=2;along<len;along+=4.2)for(const side of [-1,1]){
    const x=a.x+dx/len*along-dz/len*side*(1.9+noise(along,i)*.5),z=a.z+dz/len*along+dx/len*side*(1.9+noise(along,i)*.5),key=Math.round(x)+','+Math.round(z);
    if(used.has(key))continue;used.add(key);points.push({x,z,seed:points.length});
   }
  }
  // Include the entrance/checkpoint vicinity even when the first route is long.
  for(let i=0;i<24;i++){const a=i*Math.PI/12,r=3.4+(i%3)*1.4;points.push({x:this.area.spawn.x+Math.sin(a)*r,z:this.area.spawn.z+Math.cos(a)*r,seed:i+1000});}
  points.sort((a,b)=>Math.hypot(a.x-this.area.spawn.x,a.z-this.area.spawn.z)-Math.hypot(b.x-this.area.spawn.x,b.z-this.area.spawn.z));
  let groups=0,tall=0;const lowGroups:Point[]=[];
  for(const p of points){
   const {x,z,seed}=p;
   if(groups<(cave?14:town?18:30)&&seed<1000&&noise(seed,121)>.56&&Math.hypot(x-this.area.spawn.x,z-this.area.spawn.z)>4.5&&!lowGroups.some(q=>Math.hypot(q.x-x,q.z-z)<6.5)&&this.clearForDecoration(x,z,.35)){
    this.groundCluster(x,z,seed,'verge');lowGroups.push({x,z});groups++;
   }
   if(tall>=(cave||town?10:18)||seed%3!==0)continue;
   // Place framing objects a little farther from the verge; their footprint is
   // shared by Bullet and Navigation. Keep the whole route corridor untouched.
   const fromSpawn={x:x-this.area.spawn.x,z:z-this.area.spawn.z},length=Math.hypot(fromSpawn.x,fromSpawn.z)||1,xx=x+fromSpawn.x/length*.9,zz=z+fromSpawn.z/length*.9;
   if(!this.clearForDecoration(xx,zz,.55,true))continue;
   const yy=this.height({x:xx,z:zz});
   if(!cave&&!stone&&!town){
    this.asset('tree',xx,yy,zz,{height:3.7+noise(seed,36)*1.5,yaw:seed*67});
    this.addDressingObstacle('tree',xx,zz,.75,.75,3.3);
   }else if(cave){
    if(this.area.palette==='warm'){
     this.asset(seed%2?'crate':'barrel',xx,yy,zz,{width:.85,height:seed%2?.65:1,depth:.8,yaw:seed*13});
     this.asset('lantern',xx,yy+(seed%2?.67:1.02),zz,{height:.36});
     this.addDressingObstacle('crate',xx,zz,.85,.8,1);
    }else{
     const rockHeight=1.3+noise(seed,37)*1.3;this.asset('rocks-'+seed%6,xx,yy-.1,zz,{width:1.1,height:rockHeight,depth:.9,yaw:seed*43});
     if(tall%2===0)this.asset('lantern',xx,yy+rockHeight-.14,zz,{height:.42,yaw:seed*29});
     this.addDressingObstacle('rock',xx,zz,1.1,.9,1.4);
    }
   }else if(town){
    this.asset('barrel',xx,yy,zz,{width:.75,height:.9,depth:.75,yaw:seed*37});
    this.asset('crate',xx+.12,yy+.9,zz,{width:.55,height:.35,depth:.55,yaw:seed*51});
    this.addDressingObstacle('barrel',xx,zz,.85,.85,1.2);
   }else{
    this.asset('rocks-'+seed%6,xx,yy-.12,zz,{width:1.3,height:.7+noise(seed,38)*.7,depth:1.1,yaw:seed*43});
    this.addDressingObstacle('rock',xx,zz,1.3,1.1,1);
   }
   tall++;
  }
 }
 private addDressingObstacle(kind:string,x:number,z:number,width:number,depth:number,height:number){const o={kind,x,z,width,depth,height};this.layoutObstacles.push(o);this.obstacle(o);}
 private build(){
  this.ground();this.waterworks();this.waterfrontLandmarks();for(const b of this.area.buildings)this.building(b);
  for(const o of [...this.area.obstacles,...this.terrain.barriers,...this.layoutObstacles]){
   this.obstacle(o);if(o.kind==='building'||o.kind==='water'||o.kind==='gorge')continue;if(this.furnishing(o))continue;
   if(o.kind==='tree')this.tree(o.x,o.z,Math.max(2.6,o.height),Math.round(o.x+o.z));
   else if(o.kind==='barrel')this.asset('barrel',o.x,this.height(o),o.z,{width:o.width,height:Math.min(o.height,1.4),depth:o.depth,yaw:o.x*13});
   else if(o.kind==='crate')this.asset('crate',o.x,this.height(o),o.z,{width:o.width,height:o.height,depth:o.depth,yaw:0});
   else if(o.kind==='rock')this.asset('rocks-'+Math.abs(Math.round(o.x+o.z)%6),o.x,this.height(o)-.08,o.z,{width:o.width,height:o.height,depth:o.depth,yaw:o.x*7});
   else this.box('PillarStone',o.x,this.height(o)+o.height/2,o.z,o.width,o.height,o.depth,colors.stone);
  }
  if(this.area.kind!=='interior')for(let side=0;side<4;side++)for(let i=0;i<9;i++){
   const horizontal=side%2===0,length=horizontal?this.area.width:this.area.depth,t=-length/2+(i+.2+noise(i+side*13,65)*.6)*length/9,x=horizontal?t:(side===1?1:-1)*(this.area.width/2+7+noise(i,side)*3),z=horizontal?(side===0?1:-1)*(this.area.depth/2+7+noise(i,side)*3):t;
   if(this.area.exits.some(e=>Math.hypot(e.x-x,e.z-z)<12))continue;
   if(this.area.kind==='underground'||this.area.palette==='stone')this.decoration('rocks-'+(i+side)%6,x,this.height({x,z})-.25,z,{width:8+noise(i,1)*5,height:6+noise(i,2)*5,depth:8+noise(i,3)*4,yaw:i*51},'framing');
   else this.tree(x,z,6.5+noise(i,8)*3,i+side*30,true);
  }
  for(const o of this.area.objects)this.prop(o);
  this.setDressing();
  const portalPlan=planExitSigils(this.area,point=>this.height(point));
  this.mountedPortals.push(...portalPlan.mounts);this.portalPlacementReport=portalPlan.report;
  // Road planning happened before dressing; discard those cached routes now that
  // the final collider footprints are known.
  this.navigation=new Navigation(this.area.width,this.area.depth,[...this.area.obstacles,...this.terrain.barriers,...this.layoutObstacles],true);
  this.presentation=new EnvironmentPresentation(this,this.practicalSources);
 }
 // Static geometry is synchronized when created or queried; capsule motion remains explicit.
 syncPhysics(){if(this.physicsDirty){const physics=PhysicsSystem.instance;physics.syncSceneToPhysics();if(!physics.autoSimulation)physics.step(physics.fixedTimeStep);this.physicsDirty=false;}}
 move(from:Point,delta:Point,radius:number):Point {
  this.syncPhysics();
  const distance=Math.hypot(delta.x,delta.z),steps=Math.max(1,Math.ceil(distance/.15));const p={...from};
  const navigation=this.movementNavigation??=new Navigation(this.area.width,this.area.depth,this.colliders.map(c=>{const v=c.node.worldPosition,s=c.size;return {x:v.x,z:v.z,width:s.x,depth:s.z,height:s.y};}),true);
  for(let i=0;i<steps;i++){const x=p.x+delta.x/steps,z=p.z+delta.z/steps;if(x!==p.x&&!navigation.blockedAt(x,p.z,radius))p.x=x;if(z!==p.z&&!navigation.blockedAt(p.x,z,radius))p.z=z;}return p;
 }
 visible(from:Point,to:Point):boolean {
  this.syncPhysics();
  const frame=director.getTotalFrames();if(frame!==this.visibilityFrame){this.visibilityFrame=frame;this.visibilityFlags.fill(0);}
  const npc=typeof(to as Point&{actor?:unknown}).actor==='string',keys=this.visibilityKeys,flags=this.visibilityFlags;
  let slot=((from.x*73856093)^(from.z*19349663)^(to.x*83492791)^(to.z*15485863)^(npc?31:0))&127,insert=-1;
  for(let probe=0;probe<4;probe++,slot=(slot+1)&127){
   const flag=flags[slot],offset=slot*4;if(!flag){insert=slot;break;}
   if(!!(flag&2)===npc&&keys[offset]===from.x&&keys[offset+1]===from.z&&keys[offset+2]===to.x&&keys[offset+3]===to.z)return !!(flag&4);
  }
  const startY=this.height(from)+.9,endY=this.height(to)+(npc?1.65:.9),d=this.visibilityDirection.set(to.x-from.x,endY-startY,to.z-from.z),length=d.length();
  // Conversation anchors belong to a standing NPC. Aim at their shoulders over
  // furniture; combat/projectile points keep their ordinary waist-height ray.
  let visible=true;
  if(!(length<.001)){d.normalize();const ray=this.visibilityRay;ray.o.set(from.x,startY,from.z);ray.d.set(d);visible=!PhysicsSystem.instance.raycastClosest(ray,2,length,false);}
  if(insert>=0){const offset=insert*4;keys[offset]=from.x;keys[offset+1]=from.z;keys[offset+2]=to.x;keys[offset+3]=to.z;flags[insert]=1|(npc?2:0)|(visible?4:0);}
  return visible;
 }
 path(from:Point,to:Point){return this.navigation.path(from,to);}
 recoverPosition(point:Point,radius:number):Point|undefined {
  const nav=this.navigation;if(!nav.blocked(point,radius))return point;
  // Use the final terrain/dressing footprints and existing navigation. A nearby
  // empty pocket across water or on another floor is not a valid recovery site.
  const height=this.height(point);
  for(let distance=.5;distance<=6;distance+=.5)for(let i=0;i<24;i++){
   const angle=i*Math.PI/12,candidate={x:point.x+Math.cos(angle)*distance,z:point.z+Math.sin(angle)*distance};
   if(!nav.blocked(candidate,radius)&&Math.abs(this.height(candidate)-height)<.6&&nav.path(this.area.spawn,candidate).length>1)return candidate;
  }
  return undefined;
 }
 destroy(){this.navigation.dispose();this.movementNavigation?.dispose();this.roadNavigation?.dispose();this.presentation?.destroy();this.root.destroy();const unique=new Set<Mesh>();this.meshes.forEach(mesh=>unique.add(mesh));this.generatedMeshes.forEach(mesh=>unique.add(mesh));unique.forEach(mesh=>mesh.destroy());for(const material of this.materials.values())material.destroy();for(const texture of this.textures)texture.destroy();this.meshes.clear();this.generatedMeshes.clear();this.materials.clear();this.textures.clear();}
}
