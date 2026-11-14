import {Color,Material,Mesh,Texture2D,Vec4,gfx,primitives,utils} from 'cc';

export type PortalStoneGeometry=primitives.IGeometry&{
 positions:number[];normals:number[];uvs:number[];colors:number[];indices:number[];
};
export type PortalStoneOptions={tileMetres?:number;paintedBacking?:boolean};

/** Local collision envelope, before the caller applies its world yaw. */
export const PORTAL_STONE_SIZE=Object.freeze({width:1.6,height:2.65,depth:.38});
export const PORTAL_FLOOR_INLAY_SIZE=Object.freeze({width:1.7,height:.08,depth:1.7});
/** Broad flat part of the +Z face; a separate sigil can sit just above z. */
export const PORTAL_STONE_FACE=Object.freeze({width:.90,bottom:.40,top:1.95,z:.19});

const clamp01=(value:number)=>Math.max(0,Math.min(1,value));
const notch=(value:number,center:number,radius:number)=>Math.max(0,1-Math.abs(value-center)/radius);
const empty=():PortalStoneGeometry=>({positions:[],normals:[],uvs:[],colors:[],indices:[]});

function tileSize(options:PortalStoneOptions):number{
 const tile=options.tileMetres??.8;
 if(!Number.isFinite(tile)||tile<=0)throw new Error('Portal stone tileMetres must be positive');
 return tile;
}

/** Recompute area-weighted normals after deforming native box vertices.
 * Cocos duplicates vertices at the six face seams, so the stone keeps its
 * hard outer edges while the small bevels within each face stay gentle. */
function finish(geometry:PortalStoneGeometry,standing=false,mirrors:readonly [number,number][]=[]):PortalStoneGeometry{
 const {positions,indices}=geometry,normals=new Array<number>(positions.length).fill(0),tones=geometry.colors.splice(0);
 for(let i=0;i<indices.length;i+=3){
  const a=indices[i]*3,b=indices[i+1]*3,c=indices[i+2]*3;
  const abx=positions[b]-positions[a],aby=positions[b+1]-positions[a+1],abz=positions[b+2]-positions[a+2];
  const acx=positions[c]-positions[a],acy=positions[c+1]-positions[a+1],acz=positions[c+2]-positions[a+2];
  const nx=aby*acz-abz*acy,ny=abz*acx-abx*acz,nz=abx*acy-aby*acx;
  for(const vertex of [a,b,c]){normals[vertex]+=nx;normals[vertex+1]+=ny;normals[vertex+2]+=nz;}
 }
 // Mirror the area-weighted normals as well as the vertices. This keeps the
 // native face seams hard without an order-dependent left/right shade bias.
 for(const [right,left]of mirrors){
  const a=right*3,b=left*3;
  if(right===left){normals[a]=0;continue;}
  const nx=(normals[a]-normals[b])/2,ny=(normals[a+1]+normals[b+1])/2,nz=(normals[a+2]+normals[b+2])/2;
  normals[a]=nx;normals[b]=-nx;normals[a+1]=normals[b+1]=ny;normals[a+2]=normals[b+2]=nz;
 }
 const min={x:Infinity,y:Infinity,z:Infinity},max={x:-Infinity,y:-Infinity,z:-Infinity};
 let radiusSquared=0;
 for(let i=0;i<positions.length;i+=3){
  const x=positions[i],y=positions[i+1],z=positions[i+2],length=Math.hypot(normals[i],normals[i+1],normals[i+2]);
  if(length>1e-10){normals[i]/=length;normals[i+1]/=length;normals[i+2]/=length;}
  const nx=normals[i],ny=normals[i+1],nz=normals[i+2];
  const face=standing?.76+.19*Math.max(0,ny)+.15*Math.max(0,nz)-.14*Math.abs(nx)-.07*Math.max(0,-nz)
   :.84+.12*Math.max(0,ny)+.10*Math.max(0,nz)-.06*Math.max(0,nx)-.06*Math.max(0,-nz);
  const weather=1-.018*Math.abs(Math.sin((standing?Math.abs(x):x)*9.7+y*4.1+z*7.3)),foot=y<.18?.94:1;
  const shade=Math.min(1,face*weather*foot*(tones[i/3*4]??1));
  geometry.colors.push(shade,shade,shade*.985,1);
  min.x=Math.min(min.x,x);min.y=Math.min(min.y,y);min.z=Math.min(min.z,z);
  max.x=Math.max(max.x,x);max.y=Math.max(max.y,y);max.z=Math.max(max.z,z);
  radiusSquared=Math.max(radiusSquared,x*x+y*y+z*z);
 }
 geometry.normals=normals;geometry.minPos=min;geometry.maxPos=max;geometry.boundingRadius=Math.sqrt(radiusSquared);
 return geometry;
}

type Point={x:number;y:number;z:number;shade?:number};

/** Retain native primitive indices/winding; only positions and per-face UV density
 * change. UVs use local metres, independent of how many segments a face has. */
function appendBox(target:PortalStoneGeometry,box:primitives.IGeometry,tile:number,
 transform:(x:number,y:number,z:number)=>Point):void{
 const start=target.positions.length/3;
 for(let i=0;i<box.positions.length;i+=3){
  const point=transform(box.positions[i],box.positions[i+1],box.positions[i+2]);
  const nx=box.normals![i],ny=box.normals![i+1],nz=box.normals![i+2];
  target.positions.push(point.x,point.y,point.z);
  const tone=point.shade??1;target.colors.push(tone,tone,tone,1);
  // Explicit projection also avoids the native box front UV's 180-degree
  // orientation. On +Z: U increases along +X, V increases along +Y.
  if(Math.abs(nz)>.5)target.uvs.push((nz>0?point.x:-point.x)/tile,point.y/tile);
  else if(Math.abs(nx)>.5)target.uvs.push((nx>0?-point.z:point.z)/tile,point.y/tile);
  else target.uvs.push(point.x/tile,point.z/tile);
 }
 for(const index of box.indices!)target.indices.push(start+index);
}

const crown=[2.20,2.24,2.50,2.58,2.65,2.58,2.50,2.24,2.20] as const;
const sideCuts=[.055,.03,0,.025,.07,.09,.035,.025,.06,.11,.08] as const;

function crownHeight(u:number):number{
 const step=clamp01(Math.abs(u))*4,index=Math.min(3,Math.floor(step));
 return crown[4+index]+(crown[5+index]-crown[4+index])*(step-index);
}

function edgeCut(cuts:readonly number[],t:number):number{
 const step=clamp01(t)*10,index=Math.min(9,Math.floor(step));
 return cuts[index]+(cuts[index+1]-cuts[index])*(step-index);
}

/** Reuse one half of the native box's faces, then reflect its topology. A
 * reflected triangle reverses winding; centreline vertices remain shared.
 * Mirrored UV U retains the same local metre projection on every box face. */
function mirrorStanding(source:PortalStoneGeometry):{geometry:PortalStoneGeometry;mirrors:[number,number][]}{
 const geometry=empty(),mapped=new Map<number,[number,number]>(),mirrors:[number,number][]=[];
 const vertex=(sourceIndex:number):[number,number]=>{
  const old=mapped.get(sourceIndex);if(old)return old;
  const i=sourceIndex*3,u=sourceIndex*2,c=sourceIndex*4,x=Math.abs(source.positions[i]),y=source.positions[i+1],z=source.positions[i+2],right=geometry.positions.length/3;
  geometry.positions.push(x,y,z);geometry.uvs.push(source.uvs[u],source.uvs[u+1]);geometry.colors.push(...source.colors.slice(c,c+4));
  let left=right;
  if(x>0){left=geometry.positions.length/3;geometry.positions.push(-x,y,z);geometry.uvs.push(-source.uvs[u],source.uvs[u+1]);geometry.colors.push(...source.colors.slice(c,c+4));}
  const pair:[number,number]=[right,left];mapped.set(sourceIndex,pair);mirrors.push(pair);return pair;
 };
 for(let i=0;i<source.indices.length;i+=3){
  const a=source.indices[i],b=source.indices[i+1],c=source.indices[i+2];
  if([a,b,c].some(index=>source.positions[index*3]<0))continue;
  const [ar,al]=vertex(a),[br,bl]=vertex(b),[cr,cl]=vertex(c);
  geometry.indices.push(ar,br,cr);
  if(ar!==al||br!==bl||cr!==cl)geometry.indices.push(al,cl,bl);
 }
 return {geometry,mirrors};
}

/** Opaque standing stone, x +/-0.8, y 0..2.65, z +/-0.19.
 * The local front is +Z; world yaw (e.g. 39.8 degrees) belongs to the caller.
 * All chips/bevels cut inward. This is one stone, with no separate plinth.
 * No collider or Node
 * is created. This fresh geometry can also join a caller-owned native batch. */
export function createPortalStoneGeometry(options:PortalStoneOptions={}):PortalStoneGeometry{
 const geometry=empty(),tile=tileSize(options);
 const body=primitives.box({width:1.6,height:2.65,length:.38,widthSegments:8,heightSegments:10,lengthSegments:2});
 appendBox(geometry,body,tile,(x,y,z)=>{
  const u=Math.sign(x)*Math.round(Math.abs(x/.8)*4)/4,t=Math.round(clamp01((y+1.325)/2.65)*10)/10;
  const px=u*(.8-edgeCut(sideCuts,t)),absolute=Math.abs(u);
  const foot=.045*notch(absolute,.75,.25)+.025*notch(absolute,.25,.2)+.02*notch(absolute,.95,.18);
  const py=foot+t*(crownHeight(u)-foot);
  const edge=clamp01((Math.abs(u)-.72)/.28),top=clamp01((t-.86)/.14),bottom=clamp01((.12-t)/.12);
  // A broad worn chamfer catches grey light; the exposed side is darker.
  // The center remains at z=+/-0.19, with no raised rectangular frame.
  const bevel=.075*edge+.045*top+.026*bottom;
  const pz=z/.19*(.19-bevel);
  const shade=z>0?1+.20*edge+.09*top:1;
  return{x:px,y:py,z:pz,shade};
 });
 const mirrored=mirrorStanding(geometry);
 if(options.paintedBacking)for(let i=0;i<mirrored.geometry.positions.length;i+=3){
  mirrored.geometry.positions[i]*=.8;mirrored.geometry.positions[i+1]*=.85;mirrored.geometry.positions[i+2]*=.8;
 }
 return finish(mirrored.geometry,true,mirrored.mirrors);
}

/** Thin embedded stone; centered on x/z, with its bottom at local y=0.
 * +Y top UV: U along +X and V along +Z. Its softly damaged corners remain
 * inside the exact 1.7 x .08 x 1.7 collision envelope. */
export function createPortalFloorInlayGeometry(options:PortalStoneOptions={}):PortalStoneGeometry{
 const geometry=empty(),tile=tileSize(options),half=.85;
 if(options.paintedBacking){
  const cylinder=primitives.cylinder(.64,.64,.08,{radialSegments:8,heightSegments:1}),angle=Math.PI/8,c=Math.cos(angle),s=Math.sin(angle);
  // Hide the native backing inside the painted threshold. Quantize only the
  // native circle's trigonometric roundoff so opposite octagon corners agree.
  const exact=(value:number)=>Math.round(value*1e12)/1e12;
  appendBox(geometry,cylinder,tile,(x,y,z)=>({x:exact(x*c+z*s),y:y+.04,z:exact(z*c-x*s)}));
  return finish(geometry);
 }
 const slab=primitives.box({width:1.7,height:.08,length:1.7,widthSegments:4,heightSegments:1,lengthSegments:4});
 appendBox(geometry,slab,tile,(x,y,z)=>{
  const u=x/half,v=z/half,corner=clamp01((Math.min(Math.abs(u),Math.abs(v))-.5)/.5);
  const chip=(u*v>0?.045:.065)*corner,top=y>0;
  const px=x-Math.sign(x)*chip,pz=z-Math.sign(z)*chip;
  const bevel=top?.009*Math.max(Math.abs(u),Math.abs(v)):0;
  return{x:px,y:top?.08-bevel:0,z:pz};
 });
 return finish(geometry);
}

/** Fresh native assets: share them across exit nodes and destroy once after
 * those nodes are gone. This module never retains or releases caller textures. */
export function createPortalStoneMesh(options:PortalStoneOptions={}):Mesh{
 const mesh=utils.createMesh(createPortalStoneGeometry(options));mesh.name='PortalStandingStone';return mesh;
}

export function createPortalFloorInlayMesh(options:PortalStoneOptions={}):Mesh{
 const mesh=utils.createMesh(createPortalFloorInlayGeometry(options));mesh.name='PortalFloorInlay';return mesh;
}

/** Bedrock is already a repeat+mip texture; keep its shared sampler unchanged.
 * Both textured and plain fallbacks are opaque, depth-writing and back-culled. */
export function createPortalStoneMaterial(texture?:Texture2D):Material{
 const material=new Material();material.name='PortalOldGreyStone';
 material.initialize({effectName:'builtin-unlit',technique:0,
  defines:{USE_TEXTURE:!!texture,USE_VERTEX_COLOR:true,USE_INSTANCING:true},
  states:{rasterizerState:{cullMode:gfx.CullMode.BACK},depthStencilState:{depthTest:true,depthWrite:true}}});
 if(!material.passes.length){material.destroy();throw new Error('Portal stone requires builtin-unlit');}
 material.setProperty('mainColor',texture?new Color(198,198,190,255):new Color(133,137,130,255));
 if(texture)material.setProperty('mainTexture',texture);
 material.setProperty('tilingOffset',new Vec4(1,1,0,0));
 return material;
}
