import {viewportMetrics} from '../../../platform/ViewportMetrics';
import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,JsonAsset,Material,Mesh,MeshRenderer,Node,Quat,Rect,Size,SpriteFrame,Texture2D,Vec3,Vec4,gfx,geometry,primitives,utils} from 'cc';
import type {SceneBuilder,FlatEnvironmentObject,FlatEnvironmentPatch} from './SceneBuilder';
import {getMapArt,mapArtSurface,MAP_ART_SURFACES,type MapArtSurface,type MapArtProfile} from '../data/MapArt';
import {SurfaceMaterials} from './SurfaceMaterials';
import {PaintedTerrainDetails} from './PaintedTerrainDetails';

type Art={images:Record<string,{resource:string}>;sprites:Record<string,{image:string;rect:[number,number,number,number]}>;modelDimensions:Record<string,[number,number,number]>;limits:string[]};
type Previous={enabled:boolean;materials:Material[];cast:number;receive:number;priority:number};
type Card={node:Node;renderer:MeshRenderer;key:string;opaque:Material;occluder:boolean;fadedOut:boolean;base:Vec3;dimensions:Vec3;sourceRatio?:number;anchorToBase:boolean};
type CardGroup={node:Node;cards:Card[];bounds:geometry.AABB};
type GroundPaint={positions:number[];indices:number[];colors:number[]};

/** Reuses original walk-surface geometry/UVs, replacing environment volumes by
 * painted cutouts. Native unlit, alpha test, instancing and frustum culling own
 * rendering; no navigation, collision, terrain or game-state changes. */
export class FlatWorldLayers {
 // Cutout geometry is independent of its image. Keep the small, finite UV
 // layouts across areas so Cocos can reuse their native instancing buffers.
 private static readonly cardMeshes=new Map<string,Mesh>();
 static releaseMeshes(){for(const mesh of this.cardMeshes.values())mesh.destroy();this.cardMeshes.clear();}
 private previous=new Map<MeshRenderer,Previous>();
 private materials=new Set<Material>();private meshes=new Set<Mesh>();private frames=new Set<SpriteFrame>();private textures=new Set<Texture2D>();
 private textureCache=new Map<string,Promise<Texture2D>>();private spriteMeshes=new Map<string,Mesh>();private spriteMaterials=new Map<string,Material>();private unlitMaterials=new Map<Material,Material>();
 private retained=new Set<MeshRenderer>();private cards:Card[]=[];private unmapped=new Set<string>();
 private cardGroups:CardGroup[]=[];private cullPosition=new Vec3(Infinity,Infinity,Infinity);private cullHeight=-1;private cullAspect=-1;
 private groupBoundsDirty=true;private cullWidth=-1;private cullViewportHeight=-1;private cullProjection=-1;private cullNear=-1;private cullFar=-1;
 private root:Node|null=null;private art:Art|null=null;private disposed=false;private lastRotation=new Quat(0,0,0,0);
 private readonly style:MapArtProfile;
 private surfaceTextures=new Map<string,Texture2D>();private structureMeshes=new Map<string,Mesh>();private structureMaterials=new Map<string,Material>();
 private groundPaint:GroundPaint={positions:[],indices:[],colors:[]};private paintedStructures=0;private groundAccents=0;private lampPools=0;
 private fadedMaterials=new Map<string,Material>();private lastFocus=new Vec3(Infinity,Infinity,Infinity);
 private readonly occlusionDelta=new Vec3();
 private terrainDetails:PaintedTerrainDetails|null=null;
 constructor(private world:SceneBuilder,private camera:Camera){
  this.style=getMapArt(world.area);
  for(const r of world.root.getComponentsInChildren(MeshRenderer))this.previous.set(r,{enabled:r.enabled,materials:r.sharedMaterials.slice(),cast:r.shadowCastingMode,receive:r.receiveShadow,priority:r.priority});
 }
 private texture(path:string):Promise<Texture2D>{
  const key=path+'/texture',cached=this.textureCache.get(key);if(cached)return cached;
  const pending=new Promise<Texture2D>((resolve,reject)=>this.world.loadAsset(key,Texture2D,(error,asset)=>{
   if(error){reject(new Error('Flat world texture '+key+': '+error.message));return;}
   // SurfaceMaterials owns its chapter-wide albedos. Releasing those here
   // invalidates that library's cached objects after the first area change.
   if(!this.disposed&&path.startsWith('flat2d/')&&!this.textures.has(asset)){
    asset.addRef();this.textures.add(asset);
    const tile=Object.values(MAP_ART_SURFACES).some(surface=>surface.resource===path);
    asset.setWrapMode(tile?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE,tile?Texture2D.WrapMode.REPEAT:Texture2D.WrapMode.CLAMP_TO_EDGE);
    asset.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);asset.setMipFilter(tile?Texture2D.Filter.LINEAR:Texture2D.Filter.NONE);if(tile)asset.setAnisotropy(4);
   }resolve(asset);
  }));this.textureCache.set(key,pending);return pending;
 }
 async build():Promise<void>{
  if(this.disposed||this.root)return;
  const json=await new Promise<JsonAsset>((resolve,reject)=>this.world.loadAsset('flat2d/terrain-v1/manifest',JsonAsset,(error,asset)=>error?reject(error):resolve(asset)));
  this.art=json.json as Art;if(!this.art?.sprites?.rocks||!this.world.flatMapSurfaces.length)throw new Error('Missing painted world metadata or walk-surface records');
  const needed=new Set<string>();for(const object of this.world.flatMapObjects){const key=this.spriteFor(object);if(key)needed.add(this.art.sprites[key].image);}
  const imagesPending=Promise.all(Array.from(needed,async name=>[name,await this.texture(this.art!.images[name].resource)]as const));
  const neededSurfaces=new Map<string,MapArtSurface>();
  for(const r of this.world.flatMapSurfaces){const s=mapArtSurface(this.style,r.node.name);if(s)neededSurfaces.set(s.resource,s);}
  for(const s of [this.style.wood,this.style.paving,this.style.water])neededSurfaces.set(s.resource,s);
  if(this.world.terrain.gorges.length)neededSurfaces.set(MAP_ART_SURFACES.bedrock.resource,MAP_ART_SURFACES.bedrock);
  const [imageEntries]=await Promise.all([imagesPending,Promise.all(Array.from(neededSurfaces.keys(),async path=>this.surfaceTextures.set(path,await this.texture(path))))]);const images=new Map(imageEntries);
  if(this.disposed||!this.world.root.isValid)return;
  this.root=new Node('FlatWorldLayers');this.world.root.addChild(this.root);
  this.terrainDetails=new PaintedTerrainDetails(this.world,this.root,this.style,this.surfaceTextures);
  for(const r of this.previous.keys())if(r.isValid)r.enabled=false;
  for(const r of this.world.flatMapSurfaces){
   const old=this.previous.get(r);if(!old||!r.isValid)continue;
   r.sharedMaterials.forEach((source,index)=>{if(source)r.setSharedMaterial(this.unlit(source,r.node.name),index);});r.enabled=old.enabled;r.shadowCastingMode=0;r.receiveShadow=0;
   // Transparent map ribbons have region-sized centres. Depth sorting those
   // centres against foot-anchored actors can paint a road over their bodies.
   // Native transparent priority draws map layers first; opaque tall props
   // keep depth-tested occlusion and actor priorities remain unchanged.
   r.priority=-100;this.retained.add(r);
  }
  for(const patch of this.world.flatMapPatches)this.patch(patch);
  this.terrainDetails.gorges();
  this.terrainDetails.bridges();
  const composites=new Set(this.world.flatMapObjects.filter(o=>o.kind==='building'||o.key==='wagon').map(o=>o.node));
  for(const object of this.world.flatMapObjects){
   if(object.node.name==='BridgeRail')continue;
   if(object.kind==='asset'&&this.hasAncestor(object.node,composites))continue;
   if(object.kind==='asset'&&this.insideForge(object))continue;
   const key=this.spriteFor(object);if(key)this.object(object,key,images.get(this.art.sprites[key].image)!);
  }
  this.paintBanks();this.paintLamps();this.finishGroundPaint();this.groupCards();this.update(this.camera);
 }
 private material(texture?:Texture2D,blend=false,vertexColors=false,cutout=false):Material{
  const m=new Material();m.name='FlatWorld-'+(cutout?'PaintedCutout':blend?'MapOverlay':'MapSurface');
  m.initialize({effectName:'builtin-unlit',technique:blend?1:0,defines:{USE_TEXTURE:!!texture,USE_VERTEX_COLOR:vertexColors,USE_ALPHA_TEST:cutout,ALPHA_TEST_CHANNEL:'a',USE_INSTANCING:cutout},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:!blend}}});
  if(!m.passes.length){m.destroy();throw new Error('Flat world requires bundled builtin-unlit');}
  m.setProperty('mainColor',Color.WHITE);m.setProperty('tilingOffset',new Vec4(1,1,0,0));if(texture)m.setProperty('mainTexture',texture);if(cutout)m.setProperty('alphaThreshold',.12);this.materials.add(m);return m;
 }
 private unlit(source:Material,name:string){
  const cached=this.unlitMaterials.get(source);if(cached)return cached;
  const blend=name==='Road'||name==='GrassCover',vertexColors=blend||name==='Ground'&&this.world.area.kind!=='interior',surface=mapArtSurface(this.style,name),texture=surface?this.surfaceTextures.get(surface.resource):source.getProperty('mainTexture')as Texture2D|undefined,m=this.material(texture,blend,vertexColors),tint=source.getProperty('mainColor')as Color|undefined;
  if(tint)m.setProperty('mainColor',tint);
  if(surface){
   // Keep the original collision mesh and metre-based UVs. Only its sampling
   // scale changes to the painted material's authored metres per tile.
   const oldTile=name==='Ground'?SurfaceMaterials.tileMetres(SurfaceMaterials.ground(this.world.area)):name==='GrassCover'?2:name==='Road'?SurfaceMaterials.tileMetres(this.world.area.kind==='town'||this.world.area.kind==='underground'?'cobble':'earth'):2;
   const scale=oldTile/surface.tileMetres;m.setProperty('tilingOffset',new Vec4(scale,scale,0,0));m.setProperty('mainColor',new Color().fromHEX(surface.tint));
  }
  this.unlitMaterials.set(source,m);return m;
 }
 private renderer(node:Node,mesh:Mesh,material:Material){const r=node.addComponent(MeshRenderer);r.mesh=mesh;r.setSharedMaterial(material,0);r.shadowCastingMode=0;r.receiveShadow=0;return r;}
 private patch(patch:FlatEnvironmentPatch){
  if(patch.kind==='water'){this.terrainDetails!.water(patch);return;}
  const source=patch.node,d=source.worldScale,surface=patch.kind==='bridge'&&patch.color!=='#a4b1ba'?this.style.wood:this.style.paving,texture=patch.kind==='rug'?undefined:this.surfaceTextures.get(surface.resource),tile=surface.tileMetres;
  const geometry=primitives.plane({width:d.x,length:d.z,widthSegments:1,lengthSegments:1});geometry.uvs=geometry.uvs!.map((v,i)=>v*(i%2?d.z:d.x)/tile);
  const mesh=utils.createMesh(geometry,undefined,{calculateBounds:true});this.meshes.add(mesh);const node=new Node('FlatPatch:'+source.name);this.root!.addChild(node);node.layer=source.layer;
  node.setWorldPosition(source.worldPosition.x,source.worldPosition.y+d.y/2+.003,source.worldPosition.z);node.setWorldRotation(source.worldRotation);
  const m=this.material(texture);m.setProperty('mainColor',new Color().fromHEX(patch.kind==='rug'?patch.color:surface.tint));this.renderer(node,mesh,m);
 }
 private spriteFor(object:FlatEnvironmentObject):string|null{
  const key=object.key;let sprite=key;
  if(object.kind==='building')sprite=['house','inn','workshop','barn','mill'].includes(key)?'house':key;
  else if(key==='tree'){const seed=Math.abs(Math.round(object.node.worldPosition.x*7+object.node.worldPosition.z*11));sprite=this.world.area.palette==='forest'?(seed%3?'birch':'oak'):['oak','birch','pine'][seed%3];}
  else if(key.startsWith('rocks-'))sprite='rocks-'+String.fromCharCode(97+parseInt(key.slice(6),10)%(object.decorative&&object.terrainRole!=='framing'?6:4));
  else if(key.startsWith('grass-'))sprite=(this.style.family==='reed-marsh'?'reed-':'grass-')+(parseInt(key.slice(6),10)%2?'b':'a');
  else if(key.startsWith('fern-'))sprite='fern-'+(parseInt(key.slice(5),10)%2?'b':'a');
  if(!this.art?.sprites[sprite]){this.unmapped.add(key);return null;}return sprite;
 }
 private hasAncestor(node:Node,roots:Set<Node>){for(let p=node.parent;p&&p!==this.world.root;p=p.parent)if(roots.has(p))return true;return false;}
 private insideForge(object:FlatEnvironmentObject){const p=object.node.worldPosition;return this.world.flatMapObjects.some(o=>o.key==='forge'&&o.dimensions&&Math.abs(p.x-o.node.worldPosition.x)<o.dimensions.x/2&&Math.abs(p.z-o.node.worldPosition.z)<o.dimensions.z/2);}
 private object(object:FlatEnvironmentObject,key:string,texture:Texture2D){
  const p=object.node.worldPosition.clone(),scale=object.node.worldScale,native=this.art!.modelDimensions[object.key]??[1,1,1],d=object.dimensions?.clone()??new Vec3(native[0]*scale.x,native[1]*scale.y,native[2]*scale.z);
  if(object.centered)p.y-=d.y/2;
  if(key==='signpost'){d.x=.95;d.z=.35;d.y=1.9;p.y=this.world.height(p);}
  if(object.node.name==='BridgeRail'){d.y=.85;p.y=this.world.height(p)+.02;}
  if(key==='stone-wall'){this.wall(object,p,d);return;}
  if(!['grass-a','grass-b','fern-a','fern-b','reed-a','reed-b','lantern','candlestick','books','bowl','jug'].includes(key)&&p.y-this.world.height(p)<.4){
   this.ellipse(p.x,p.z,Math.min(8,d.x*.48),Math.min(7,d.z*.48),[.12,.115,.09],object.kind==='building'?.2:.18);this.groundAccents++;
  }
  // Architecture is already painted in perspective. Its bottom contact must
  // stay at the recorded terrain base: subtracting the footprint along camera
  // up puts the door and foundation under the retained depth-tested ground.
  if(object.kind==='building'){if(!['tent','gate'].includes(object.key))this.foundation(object,p,d);this.card(p,d,key,texture,undefined,true);return;}
  // These paintings already contain their three-quarter perspective. Keep
  // their source aspect on a facing card instead of projecting them a second
  // time onto XZ or stretching each axis to a full world-space bounding box.
  if(['table','round-table','wagon'].includes(key)){const rect=this.art!.sprites[key].rect;this.card(p,d,key,texture,rect[3]/rect[2]);return;}
  if(['books','bowl','jug','candlestick'].includes(key)&&p.y-this.world.height(p)>.35&&this.world.flatMapObjects.some(o=>{
   if(o.key!=='table'&&o.key!=='round-table')return false;
   const q=o.node.worldPosition,s=o.node.worldScale,n=this.art!.modelDimensions[o.key];return !!n&&Math.abs(p.x-q.x)<=n[0]*s.x/2&&Math.abs(p.z-q.z)<=n[2]*s.z/2;
  }))p.y=this.world.height(p)+.45;
  if(key==='wood-fence'){
   const axis=d.x>=d.z?'x':'z',length=d[axis],count=Math.max(1,Math.ceil(length/2.5));
   for(let i=0;i<count;i++){const offset=new Vec3(axis==='x'?(i+.5)/count*length-length/2:0,0,axis==='z'?(i+.5)/count*length-length/2:0);Vec3.transformQuat(offset,offset,object.node.worldRotation);const q=p.clone().add(offset),size=d.clone();size[axis]=length/count;size.y=Math.min(1.8,Math.max(.7,size.y));this.card(q,size,key,texture);}return;
  }
  if((key==='rocks'||key.startsWith('rocks-'))&&Math.max(d.x,d.z)>4){
   const nx=Math.max(1,Math.ceil(d.x/3)),nz=Math.max(1,Math.ceil(d.z/3));
   for(let x=0;x<nx;x++)for(let z=0;z<nz;z++){const q=new Vec3(p.x+(x+.5)/nx*d.x-d.x/2,0,p.z+(z+.5)/nz*d.z-d.z/2);q.y=this.world.height(q)-.04;const variant='rocks-'+String.fromCharCode(97+(x*3+z+Math.abs(Math.round(p.x+p.z)))%4),rect=this.art!.sprites[variant].rect;this.card(q,new Vec3(d.x/nx,Math.min(d.y,3.2),d.z/nz),variant,texture,rect[3]/rect[2]);}return;
  }
  const natural=key.startsWith('rocks-')||/^(?:grass|fern|reed)-/.test(key)||key==='shipwreck',rect=this.art!.sprites[key].rect;
  this.card(p,d,key,texture,natural?rect[3]/rect[2]:undefined);
 }
 private foundation(object:FlatEnvironmentObject,base:Vec3,dimensions:Vec3){
  // The original building collider remains solid. Its low stone footprint is
  // still legible when the large painted roof/wall fades out in front of us.
  const {x:w,z:d}=dimensions,thickness=.38,height=object.key==='ruin'?.8:.6;
  for(const side of [-1,1])for(const axis of ['x','z']as const){
   const offset=new Vec3(axis==='x'?side*(w/2-thickness/2):0,0,axis==='z'?side*(d/2-thickness/2):0);Vec3.transformQuat(offset,offset,object.node.worldRotation);const p=base.clone().add(offset);p.y=this.world.height(p);
   this.wall(object,p,axis==='x'?new Vec3(thickness,height,d):new Vec3(w,height,thickness));
  }
 }
 private wall(object:FlatEnvironmentObject,base:Vec3,dimensions:Vec3){
  // A low cutaway prism retains the wall's real yaw and thickness. Unlike a
  // facing paper strip its ends join correctly around doorways and corners.
  const height=Math.min(dimensions.y,this.world.area.kind==='interior'?1.35:1.6),w=Math.max(.18,dimensions.x),d=Math.max(.18,dimensions.z),key=[w,height,d].join(',');
  let mesh=this.structureMeshes.get(key);
  if(!mesh){const g=primitives.box({width:w,height,length:d}),normals=g.normals!,tile=this.style.paving.tileMetres;g.colors=[];
   for(let i=0;i<normals.length;i+=3){const nx=Math.abs(normals[i]),ny=Math.abs(normals[i+1]),vertex=i/3;g.uvs![vertex*2]*=(nx>.5?d:w)/tile;g.uvs![vertex*2+1]*=(ny>.5?d:height)/tile;const shade=normals[i+1]>.5?1:normals[i+2]>.5?.82:normals[i]<-.5?.76:.9;g.colors.push(shade,shade,shade,1);}
   mesh=utils.createMesh(g,undefined,{calculateBounds:true});this.meshes.add(mesh);this.structureMeshes.set(key,mesh);
  }
  let m=this.structureMaterials.get('wall');if(!m){m=this.material(this.surfaceTextures.get(this.style.paving.resource),false,true);m.setProperty('mainColor',new Color().fromHEX(this.style.propTints.stone));this.structureMaterials.set('wall',m);}
  const node=new Node('PaintedStructure:Wall');this.root!.addChild(node);node.layer=object.node.layer;node.setWorldPosition(base.x,base.y+height/2,base.z);node.setWorldRotation(object.node.worldRotation);this.renderer(node,mesh,m);this.paintedStructures++;
  this.ellipse(base.x,base.z,w/2+.22,d/2+.22,[.12,.115,.09],.2,object.node.worldRotation);this.groundAccents++;
 }
 private ellipse(x:number,z:number,rx:number,rz:number,color:number[],alpha:number,rotation?:Quat){
  if(rx<.04||rz<.04)return;
  const g=this.groundPaint,start=g.positions.length/3,segments=16;
  const vertex=(px:number,pz:number,a:number)=>{g.positions.push(px,this.world.height({x:px,z:pz})+.047,pz);g.colors.push(color[0],color[1],color[2],a);};
  vertex(x,z,alpha);
  for(const radius of [.55,1])for(let j=0;j<segments;j++){const a=j*Math.PI*2/segments,offset=new Vec3(Math.cos(a)*rx*radius,0,Math.sin(a)*rz*radius);if(rotation)Vec3.transformQuat(offset,offset,rotation);vertex(x+offset.x,z+offset.z,radius===1?0:alpha*.65);}
  for(let j=0;j<segments;j++){const next=(j+1)%segments;g.indices.push(start,start+1+next,start+1+j);const a=start+1+j,b=start+1+next,c=a+segments,d=b+segments;g.indices.push(a,b,c,b,d,c);}
 }
 private paintBanks(){
  for(const water of this.world.terrain.waters){
   // Shallow damp marks cross the existing shoreline. The water's depth test
   // hides submerged parts; no new bank, blocker or traversable ledge is added.
   for(let side=0;side<4;side++){const horizontal=side%2===0,length=horizontal?water.width:water.depth;
    for(let along=.4;along<length;along+=1.1){const wobble=Math.sin(along*2.3+side)*.12,x=water.x+(horizontal?along-water.width/2:(side===1?1:-1)*(water.width/2+.16+wobble)),z=water.z+(horizontal?(side===0?1:-1)*(water.depth/2+.16+wobble):along-water.depth/2);
     this.ellipse(x,z,horizontal?.85:.5,horizontal?.5:.85,[.23,.28,.22],.24);this.groundAccents++;
    }
   }
  }
 }
 private paintLamps(){
  const used:Vec3[]=[],composites=new Set(this.world.flatMapObjects.filter(o=>o.kind==='building'||o.key==='wagon').map(o=>o.node));
  for(const source of this.world.practicalSources){const p=source.node.worldPosition;
   const object=this.world.flatMapObjects.find(o=>o.node===source.node);if(object&&(this.hasAncestor(object.node,composites)||this.insideForge(object)))continue;
   if(used.some(q=>Vec3.distance(q,p)<1.2))continue;used.push(p.clone());
   const radius=source.kind==='firepit'?2:source.kind==='candlestick'?.72:1.15;
   // Static unlit scenery receives a soft painted pool. Native flame particles
   // and the existing light budget still own motion and character lighting.
   this.ellipse(p.x,p.z,radius,radius,[1,.65,.27],source.kind==='firepit'?.16:.13);this.lampPools++;
  }
 }
 private finishGroundPaint(){
  const g=this.groundPaint;if(!g.indices.length)return;
  const mesh=utils.createMesh(g,undefined,{calculateBounds:true});this.meshes.add(mesh);const node=new Node('PaintedGroundContacts');this.root!.addChild(node);node.layer=this.world.root.layer;
  const r=this.renderer(node,mesh,this.material(undefined,true,true));r.priority=-90;
 }
 private card(base:Vec3,dimensions:Vec3,key:string,texture:Texture2D,sourceRatio?:number,anchorToBase=false){
  let mesh=this.spriteMeshes.get(key),material=this.spriteMaterials.get(key);
  if(!mesh){
   const rect=this.art!.sprites[key].rect,frame=new SpriteFrame();frame.reset({texture,rect:new Rect(...rect),originalSize:new Size(rect[2],rect[3])});frame.packable=false;this.frames.add(frame);
   const uv=frame.uv,uvs=[uv[0],uv[1],uv[4],uv[5],uv[6],uv[7],uv[2],uv[3]],layout=uvs.join(',');mesh=FlatWorldLayers.cardMeshes.get(layout);
   if(!mesh){const geometry=primitives.quad();geometry.uvs=uvs;mesh=utils.createMesh(geometry,undefined,{calculateBounds:true});FlatWorldLayers.cardMeshes.set(layout,mesh);}
   this.spriteMeshes.set(key,mesh);
  }
  if(!material){material=this.material(texture,false,false,true);const tint=key==='rocks'||key.startsWith('rocks-')?this.style.propTints.stone:['oak','birch','pine','grass-a','grass-b','fern-a','fern-b','reed-a','reed-b'].includes(key)?this.style.propTints.foliage:['house','wood-fence','wagon'].includes(key)?this.style.propTints.timber:undefined;if(tint)material.setProperty('mainColor',new Color().fromHEX(tint));this.spriteMaterials.set(key,material);}
  const node=new Node('PaintedWorld:'+key);this.root!.addChild(node);node.layer=1<<18;const renderer=this.renderer(node,mesh,material);
  const occluder=anchorToBase||['oak','birch','pine','pillar'].includes(key)||key.startsWith('rocks-')&&dimensions.y>.8;
  this.cards.push({node,renderer,key,opaque:material,occluder,fadedOut:false,base,dimensions,sourceRatio,anchorToBase});
 }
 private groupCards(){
  const groups=new Map<string,CardGroup>();
  for(const card of this.cards){
   const key=`${Math.floor(card.base.x/8)},${Math.floor(card.base.z/8)}`;let group=groups.get(key);
   if(!group){const node=new Node('PaintedCardGroup:'+key);node.layer=1<<18;this.root!.addChild(node);group={node,cards:[],bounds:new geometry.AABB()};groups.set(key,group);}
   // Group transforms remain identity; only these presentation nodes move.
   group.node.addChild(card.node);group.cards.push(card);
  }
  this.cardGroups=Array.from(groups.values());this.groupBoundsDirty=true;
 }
 private cullCards(rotationChanged:boolean){
  const position=this.camera.node.worldPosition,camera=this.camera.camera,viewport=viewportMetrics.windowSize;
  if(!rotationChanged&&!this.groupBoundsDirty&&Vec3.squaredDistance(position,this.cullPosition)<.0625&&Math.abs(this.camera.orthoHeight-this.cullHeight)<.05&&camera.aspect===this.cullAspect&&viewport.width===this.cullWidth&&viewport.height===this.cullViewportHeight&&this.camera.projection===this.cullProjection&&this.camera.near===this.cullNear&&this.camera.far===this.cullFar)return false;
  if(rotationChanged||this.groupBoundsDirty){
   const right=this.camera.node.right,up=this.camera.node.up,min=new Vec3(),max=new Vec3();
   for(const group of this.cardGroups){
    min.set(Infinity,Infinity,Infinity);max.set(-Infinity,-Infinity,-Infinity);
    for(const card of group.cards){
     const p=card.node.worldPosition,s=card.node.worldScale;
     const x=(Math.abs(right.x*s.x)+Math.abs(up.x*s.y))/2,y=(Math.abs(right.y*s.x)+Math.abs(up.y*s.y))/2,z=(Math.abs(right.z*s.x)+Math.abs(up.z*s.y))/2;
     // A two-metre apron keeps cards active before they can enter the view,
     // covering the sub-quarter-metre culling cadence and hit-camera motion.
     min.x=Math.min(min.x,p.x-x-2);min.y=Math.min(min.y,p.y-y-2);min.z=Math.min(min.z,p.z-z-2);
     max.x=Math.max(max.x,p.x+x+2);max.y=Math.max(max.y,p.y+y+2);max.z=Math.max(max.z,p.z+z+2);
    }
    geometry.AABB.fromPoints(group.bounds,min,max);
   }
   this.groupBoundsDirty=false;
  }
  // Component updates precede the render scene's camera update. Refresh its
  // public frustum here rather than testing against the previous frame.
  camera.update();
  let visibilityChanged=false;
  for(let i=0;i<this.cardGroups.length;i++){const group=this.cardGroups[i],active=geometry.intersect.aabbFrustum(group.bounds,camera.frustum)!==0;if(group.node.active!==active){group.node.active=active;visibilityChanged=true;}}
  this.cullPosition.set(position);this.cullHeight=this.camera.orthoHeight;this.cullAspect=camera.aspect;this.cullWidth=viewport.width;this.cullViewportHeight=viewport.height;this.cullProjection=this.camera.projection;this.cullNear=this.camera.near;this.cullFar=this.camera.far;
  return visibilityChanged;
 }
 /** Native frustum culling/instancing handles the active groups. Ordinary camera
  * following does not rebuild geometry; only its view rotation updates cards. */
 update(camera?:Camera){
  if(camera)this.camera=camera;if(this.disposed||!this.root)return;
  const rotation=this.camera.node.worldRotation,changed=!Quat.equals(rotation,this.lastRotation);if(changed)this.lastRotation.set(rotation);
  const right=this.camera.node.right,up=this.camera.node.up;
  if(changed){const bias=this.camera.node.forward.clone().multiplyScalar(-.035);
  for(let i=0;i<this.cards.length;i++){
   const card=this.cards[i];
   const d=card.dimensions,foot=Math.abs(up.x)*d.x+Math.abs(up.z)*d.z;let w=Math.max(.08,Math.abs(right.x)*d.x+Math.abs(right.z)*d.z),h=Math.max(.08,Math.abs(up.y)*d.y+foot),anchor=card.anchorToBase?h/2:(h-foot)/2;
   if(card.sourceRatio){
    // Uniformly fit low art inside the projected width and a low-object
    // height envelope. Its painted perspective already supplies depth; using
    // the full ground span again makes a table several metres tall.
    h=Math.max(.08,Math.min(w*card.sourceRatio,Math.abs(up.y)*d.y+.4*foot));w=h/card.sourceRatio;
    // Bottom contact stays at the original world base. Subtracting ground
    // span along camera.up would bury the wheels/feet below the walk surface.
    anchor=h/2;
   }
   const p=card.base.clone().add(Vec3.multiplyScalar(new Vec3(),up,anchor)).add(bias);card.node.setWorldPosition(p);card.node.setWorldRotation(rotation);card.node.setScale(w,h,1);
  }
  }
  const visibilityChanged=this.cullCards(changed);
  const player=this.world.root.getChildByName('player');if(!player)return;
  const focus=player.worldPosition;if(!changed&&!visibilityChanged&&Vec3.squaredDistance(focus,this.lastFocus)<.0025)return;this.lastFocus.set(focus);
  const head=focus.clone().add(new Vec3(0,1,0)),forward=this.camera.node.forward;
  // Indexed loops avoid the per-card iterator results emitted by the Web
  // transpiler; reuse scratch storage for this frame's occlusion checks.
  for(let i=0;i<this.cards.length;i++){const card=this.cards[i];if(!card.occluder||!card.node.activeInHierarchy)continue;
   const delta=Vec3.subtract(this.occlusionDelta,head,card.node.worldPosition),x=Vec3.dot(delta,right),y=Vec3.dot(delta,up),behind=Vec3.dot(delta,forward)>.05;
   const obscures=behind&&Math.abs(x)<card.node.scale.x/2+.3&&y>-card.node.scale.y/2-.3&&y<card.node.scale.y/2+.45;
   if(obscures===card.fadedOut)continue;card.fadedOut=obscures;
   if(obscures){let faded=this.fadedMaterials.get(card.key);if(!faded){faded=this.material(card.opaque.getProperty('mainTexture')as Texture2D,true);const tint=(card.opaque.getProperty('mainColor')as Color).clone();tint.a=card.anchorToBase?25:58;faded.setProperty('mainColor',tint);this.fadedMaterials.set(card.key,faded);}card.renderer.setSharedMaterial(faded,0);card.renderer.priority=-20;}
   else{card.renderer.setSharedMaterial(card.opaque,0);card.renderer.priority=0;}
  }
 }
 inspect(){return{mode:'painted-terrain-v1',ready:!!this.root?.isValid&&!this.disposed,area:this.world.area.id,width:this.world.area.width,depth:this.world.area.depth,terrainFamily:this.style.family,terrainDetails:this.terrainDetails?.inspect(),entranceClusters:this.world.flatEntranceClusters,fadedOccluders:this.cards.filter(c=>c.fadedOut).length,groundSurface:this.style.ground.key,roadSurface:this.style.road.key,groundTileMetres:this.style.ground.tileMetres,paintedStructures:this.paintedStructures,groundContacts:this.groundAccents,localLampPools:this.lampPools,hiddenEnvironmentRenderers:Array.from(this.previous.keys()).filter(r=>r.isValid&&!r.enabled).length,originalVolumeRenderersVisible:Array.from(this.previous.keys()).filter(r=>r.isValid&&r.enabled&&!this.retained.has(r)).length,retainedTexturedWalkSurfaces:this.retained.size,paintedCutouts:this.cards.length,footprintCutouts:0,aspectLockedCutouts:this.cards.filter(c=>!!c.sourceRatio).length,unmappedSourceKeys:Array.from(this.unmapped),artLimits:this.art?.limits??[]};}
 destroy(){
  if(this.disposed)return;this.disposed=true;this.terrainDetails?.destroy();this.terrainDetails=null;if(this.root?.isValid){this.root.active=false;this.root.destroy();}
  for(const[r,old]of this.previous)if(r.isValid){r.sharedMaterials=old.materials;r.enabled=old.enabled;r.shadowCastingMode=old.cast;r.receiveShadow=old.receive;r.priority=old.priority;}
  for(const mesh of this.meshes)mesh.destroy();for(const m of this.materials)m.destroy();for(const f of this.frames)f.destroy();for(const t of this.textures)t.decRef();
  this.previous.clear();this.cards=[];this.cardGroups=[];this.root=null;
 }
}
