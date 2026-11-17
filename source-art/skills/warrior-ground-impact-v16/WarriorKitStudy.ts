import {assetManager,ImageAsset,Texture2D,Camera,Color,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string;family?:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable differentiated warrior kit, retaining the accepted silver wave material. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static guardTexture:Texture2D|null=null;
 private static whiteTexture:Texture2D|null=null;
 private static studyTextures=new Map<string,Texture2D>();
 private static pending:Promise<void>|null=null;
 private static instances=new Set<MeleeBladeSurfaces>();
 private static palettes=new Map<string,{blade:Texture2D;guard:Texture2D}>();
 private static opacityScale=1;
 static setOpacityScale(value:number){
  this.opacityScale=clamp(value);
  for(const instance of this.instances)for(const [key,material]of instance.materials){
   if(key.startsWith('w:'))material.setProperty('mainColor',new Vec4(1,1,1,Number(key.slice(2))/32*this.opacityScale));
  }
 }
 static async usePalette(name:string):Promise<void>{
  let pair=this.palettes.get(name);
  if(!pair){
   const load=(kind:string)=>new Promise<Texture2D>((resolve,reject)=>{
    const url=(globalThis as any).location.origin+'/review/'+name+'/'+kind+'.png';
    assetManager.loadRemote<ImageAsset>(url,{ext:'.png'},(error,image)=>{
     if(error){reject(error);return;}
     const texture=new Texture2D();texture.image=image;texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);texture.addRef();resolve(texture);
    });
   });
   const [blade,guard]=await Promise.all([load('blade'),load('guard')]);pair={blade,guard};this.palettes.set(name,pair);
  }
  this.texture=pair.blade;this.guardTexture=pair.guard;
  for(const instance of this.instances)for(const [key,material]of instance.materials)material.setProperty('mainTexture',key.startsWith('g:')?pair.guard:pair.blade);
 }
 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const load=(name:string)=>new Promise<Texture2D>((resolve,reject)=>{
   const url=(globalThis as any).location.origin+'/review/'+name+'.png';
   assetManager.loadRemote<ImageAsset>(url,{ext:'.png'},(error,image)=>{
    if(error){reject(error);return;}
    const texture=new Texture2D();texture.image=image;
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);texture.addRef();
    resolve(texture);
   });
  });
  this.pending=Promise.all([load('blade'),load('guard'),load('white'),...['rupture','ground-reference','dust','flash'].map(name=>load(name).then(texture=>{this.studyTextures.set(name,texture);return texture;}))]).then(([blade,guard,white])=>{this.texture=blade;this.guardTexture=guard;this.whiteTexture=white;this.studyTextures.set('blade',blade);});return this.pending;
 }
 static disposeAssets(){this.texture?.decRef();this.guardTexture?.decRef();this.texture=null;this.guardTexture=null;this.pending=null;}
 private root:Node;
 private layers:Layer[]=[];
 private meshes=new Map<string,Mesh>();
 private materials=new Map<string,Material>();
 private anchors=new Map<string,Vec3>();
 private rotation=new Quat();
 private terrain?:((x:number,z:number)=>number);
 private terrainMeshes=new Set<string>();
 private droppedLayers=0;
 private groundRecord:null|{centre:{x:number;y:number;z:number};radius:number;chunks:number;maxGroundOffset:number;maxDistance:number}=null;
 constructor(parent:Node,private readonly camera?:Camera){this.root=new Node('WarriorImpactDesign');this.root.layer=parent.layer;parent.addChild(this.root);MeleeBladeSurfaces.instances.add(this);}
 begin(){for(const layer of this.layers)layer.touched=false;}
 setGroundSampler(sample:(x:number,z:number)=>number){this.terrain=sample;}
 private ground(x:number,z:number,fallback:number){return this.terrain?.(x,z)??fallback;}
 private acquire(key:string,family:string){
  let layer=this.layers.find(item=>item.key===key);if(layer)return layer;
  layer=this.layers.find(item=>!item.touched&&!item.node.active&&item.family===family);
  if(!layer){if(this.layers.length>=64){this.droppedLayers++;return undefined;}const node=new Node('WarriorSkillElement');node.layer=this.root.layer;this.root.addChild(node);const renderer=node.addComponent(MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;layer={key,node,renderer,touched:false,phase:'',family};this.layers.push(layer);}layer.key=key;return layer;
 }
 private solid(colour:number[],alpha:number,vertex=false){
  const level=Math.max(1,Math.round(clamp(alpha)*32)),key='solid:'+colour.join(',')+':'+level+':'+vertex;
  const cached=this.materials.get(key);if(cached)return cached;
  const mat=new Material();mat.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:vertex},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
  mat.setProperty('mainTexture',MeleeBladeSurfaces.whiteTexture!);mat.setProperty('tilingOffset',new Vec4(1,1,0,0));
  mat.setProperty('mainColor',new Color(colour[0]*255,colour[1]*255,colour[2]*255,level/32*255));this.materials.set(key,mat);return mat;
 }
 private unitQuad(){
  const key='solid-quad',cached=this.meshes.get(key);if(cached)return cached;
  const mesh=utils.createMesh({positions:[-.5,-.5,0,.5,-.5,0,.5,.5,0,-.5,.5,0],normals:[0,0,1,0,0,1,0,0,1,0,0,1],uvs:[0,0,1,0,1,1,0,1],indices:[0,1,2,0,2,3],minPos:new Vec3(-.5,-.5,0),maxPos:new Vec3(.5,.5,0),boundingRadius:.72});this.meshes.set(key,mesh);return mesh;
 }
 private element(key:string,mesh:Mesh,phase:string,position:Vec3,xAxis:Vec3,yAxis:Vec3,width:number,height:number,colour:number[],alpha:number,vertex=false){
  if(alpha<.015||width<.002||height<.002)return;const layer=this.acquire(key,phase.startsWith('fracture:')?'fracture':'solid-quad');if(!layer)return;
  if(layer.phase!==phase){layer.renderer.mesh=mesh;layer.phase=phase;}
  const material=this.solid(colour,alpha,vertex);if(layer.renderer.sharedMaterial!==material)layer.renderer.setSharedMaterial(material,0);
  const normal=Vec3.cross(new Vec3(),xAxis,yAxis).normalize();Quat.fromAxes(this.rotation,xAxis,yAxis,normal);layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(width,height,1);layer.touched=true;layer.node.active=true;
 }
 private bar(key:string,a:Vec3,b:Vec3,width:number,colour:number[],alpha:number,ground=false){
  const axis=b.clone().subtract(a),length=axis.length();if(length<.004)return;axis.multiplyScalar(1/length);
  let side=ground?Vec3.cross(new Vec3(),Vec3.UNIT_Y,axis):this.camera?.node.up.clone()??Vec3.UNIT_Y.clone();
  side.subtract(axis.clone().multiplyScalar(Vec3.dot(side,axis))).normalize();if(side.length()<.1)side=new Vec3(1,0,0);
  this.element(key,this.unitQuad(),'solid-quad',a.clone().add(b).multiplyScalar(.5),axis,side,length,width,colour,alpha);
 }
 private imageMaterial(kind:string,alpha:number,tint:number[],vertex=false){
  const level=Math.max(1,Math.round(clamp(alpha)*32)),key='image:'+kind+':'+tint.join(',')+':'+level+':'+vertex;
  const old=this.materials.get(key);if(old)return old;
  const mat=new Material();mat.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:vertex,USE_INSTANCING:false},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
  mat.setProperty('mainTexture',MeleeBladeSurfaces.studyTextures.get(kind)!);mat.setProperty('mainColor',new Color(tint[0]*255,tint[1]*255,tint[2]*255,level/32*255));mat.setProperty('tilingOffset',new Vec4(1,1,0,0));this.materials.set(key,mat);return mat;
 }
 private piece(key:string,mesh:Mesh,family:string,kind:string,position:Vec3,rotation:Quat,scale:Vec3,alpha:number,tint=[1,1,1],vertex=false){
  if(alpha<.02)return;const layer=this.acquire(key,family);if(!layer)return;
  if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;layer.phase=family;
  const mat=this.imageMaterial(kind,alpha,tint,vertex);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  layer.node.setWorldPosition(position);layer.node.setWorldRotation(rotation);layer.node.setWorldScale(scale);layer.touched=true;layer.node.active=true;
 }
 private sprite(key:string,kind:string,position:Vec3,width:number,height:number,alpha:number,tint:number[],flat=false,angle=0){
  if(!this.camera)return;
  const x=flat?new Vec3(Math.cos(angle),0,-Math.sin(angle)):this.camera.node.right.clone(),y=flat?new Vec3(Math.sin(angle),0,Math.cos(angle)):this.camera.node.up.clone(),z=Vec3.cross(new Vec3(),x,y).normalize();
  const rotation=Quat.fromAxes(new Quat(),x,y,z);
  this.piece(key,this.unitQuad(),'sprite',kind,position,rotation,new Vec3(width,height,1),alpha,tint);
 }
 private slabMesh(){
  const key='textured-slab',old=this.meshes.get(key);if(old)return old;
  const rim=[[-.52,-.40],[.28,-.53],[.58,-.12],[.42,.44],[-.28,.54],[-.60,.10]],positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[];
  const vertex=(x:number,y:number,z:number,shade:number)=>{positions.push(x,y,z);normals.push(0,1,0);uvs.push(x*.70+.5,z*.70+.5);colors.push(shade,shade,shade,1);return positions.length/3-1;};
  for(let i=0;i<rim.length;i++){
   const a=rim[i],b=rim[(i+1)%rim.length],start=positions.length/3;
   vertex(0,.16,0,1);vertex(a[0],.10+a[1]*.12,a[1],1);vertex(b[0],.10+b[1]*.12,b[1],.95);indices.push(start,start+1,start+2);
   const side=positions.length/3,shade=.67+.05*(i%3);vertex(a[0],.10+a[1]*.12,a[1],shade);vertex(a[0]*.78,-.30,a[1]*.78,shade);vertex(b[0]*.78,-.30,b[1]*.78,shade);vertex(b[0],.10+b[1]*.12,b[1],shade);indices.push(side,side+1,side+2,side,side+2,side+3);
  }
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(-.60,-.30,-.53),maxPos:new Vec3(.58,.22,.54),boundingRadius:.9});this.meshes.set(key,mesh);return mesh;
 }
 private ruptureMesh(key:string,ground:Vec3,angle:number,radius:number,stage:number){
  const stamp='rupture:'+key+':'+stage,old=this.meshes.get(stamp);if(old)return old;
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[],nx=20,nz=32;let maxDistance=0;
  for(let j=0;j<=nz;j++)for(let i=0;i<=nx;i++){
   const u=i/nx,v=j/nz,x=(u-.5)*radius*1.24,z=(v*1.52-.49)*radius,at=ground.clone().add(side.clone().multiplyScalar(x)).add(forward.clone().multiplyScalar(z));
   const distance=Math.hypot(x,z),disk=clamp((radius-.025-distance)/.18),reveal=smooth((.24+stage*.21-Math.abs(z)/radius)/.24),alpha=disk*reveal;
   positions.push(at.x-ground.x,this.ground(at.x,at.z,ground.y)-ground.y+.045,at.z-ground.z);normals.push(0,1,0);uvs.push(u,v);colors.push(1,1,1,alpha);if(alpha>.01)maxDistance=Math.max(maxDistance,distance);
  }
  for(let j=0;j<nz;j++)for(let i=0;i<nx;i++){const a=j*(nx+1)+i,b=a+nx+1;indices.push(a,a+1,b,a+1,b+1,b);}
  const xs=positions.filter((_,i)=>i%3===0),ys=positions.filter((_,i)=>i%3===1),zs=positions.filter((_,i)=>i%3===2),mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(Math.min(...xs),Math.min(...ys),Math.min(...zs)),maxPos:new Vec3(Math.max(...xs),Math.max(...ys),Math.max(...zs)),boundingRadius:radius*1.6});
  this.meshes.set(stamp,mesh);this.terrainMeshes.add(stamp);this.groundRecord={centre:{x:ground.x,y:ground.y,z:ground.z},radius,chunks:6,maxGroundOffset:.045,maxDistance};return mesh;
 }
 private brokenSlabs(key:string,ground:Vec3,angle:number,radius:number,p:number,fade:number){
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle)),mesh=this.slabMesh();
  for(let i=0;i<8;i++){
   const sign=i%2?1:-1,section=Math.floor(i/2),q=clamp((p-section*.035)/.78);if(p<section*.035)continue;
   const opening=smooth(q/.19),settle=1-smooth((q-.42)/.58),along=radius*(-.24+section*.28),offset=radius*(.22+.022*Math.sin(i*2.1)+.06*opening),at=ground.clone().add(forward.clone().multiplyScalar(along)).add(side.clone().multiplyScalar(sign*offset));
   const floor=this.ground(at.x,at.z,ground.y),rise=radius*.17*Math.sin(Math.PI*q)*settle;at.y=floor+.09+rise;
   const size=.32+.11*(.5+.5*Math.sin(i*2.7)),rotation=Quat.fromEuler(new Quat(),sign*(8+14*opening*settle),angle*180/Math.PI+Math.sin(i)*15,sign*opening*settle*42);
   this.piece(key+':raised-slab:'+i,mesh,'raised-slab','ground-reference',at,rotation,new Vec3(size,.80*size,size*1.20),fade,[1.04,1.02,1],true);
   const shadow=new Vec3(at.x,floor+.018,at.z);this.sprite(key+':contact-shadow:'+i,'dust',shadow,size*1.32,size*.92,.26*fade*(1-rise/.8),[.22,.20,.18],true,angle);
  }
  for(let i=0;i<12;i++){
   const delay=(i%4)*.014;if(p<delay)continue;const q=clamp((p-delay)/.78);if(q>=1)continue;
   const sign=i%2?1:-1,along=radius*(-.26+(i%6)*.15),away=radius*(.12+q*(.26+.28*(.5+.5*Math.sin(i*3.1)))),at=ground.clone().add(forward.clone().multiplyScalar(along+q*.25)).add(side.clone().multiplyScalar(sign*away));
   at.y=this.ground(at.x,at.z,ground.y)+.06+(.30+.64*(.5+.5*Math.sin(i*1.7)))*Math.sin(Math.PI*q);
   const size=.10+.11*(.5+.5*Math.sin(i*2.3)),rotation=Quat.fromEuler(new Quat(),i*47+q*230,i*31+q*190,i*69+q*160);
   this.piece(key+':ballistic-debris:'+i,mesh,'ballistic-debris','ground-reference',at,rotation,new Vec3(size,size*.85,size*1.15),fade*(1-smooth((q-.65)/.35)),[1,1,1],true);
  }
 }
 private chipMesh(){
  const key='rock-chip',cached=this.meshes.get(key);if(cached)return cached;
  const corners=[new Vec3(-.5,-.32,-.34),new Vec3(.5,-.32,-.3),new Vec3(.34,-.32,.44),new Vec3(-.4,-.32,.4),new Vec3(.06,.65,.02)];
  const faces=[[0,1,4],[1,2,4],[2,3,4],[3,0,4],[0,3,2],[0,2,1]],positions:number[]=[],normals:number[]=[],colors:number[]=[],indices:number[]=[];
  for(let i=0;i<faces.length;i++){const shade=[.40,.29,.34,.48,.20,.20][i];for(const id of faces[i]){const p=corners[id];positions.push(p.x,p.y,p.z);normals.push(0,1,0);colors.push(shade,shade*.91,shade*.80,1);indices.push(indices.length);}}
  const mesh=utils.createMesh({positions,normals,colors,uvs:Array(positions.length/3*2).fill(.5),indices,minPos:new Vec3(-.5,-.32,-.34),maxPos:new Vec3(.5,.65,.44),boundingRadius:.95});this.meshes.set(key,mesh);return mesh;
 }
 private chips(key:string,ground:Vec3,angle:number,radius:number,p:number,alpha:number,count=6){
  const q=clamp(p),fade=1-smooth((q-.64)/.36);if(q>=1)return;
  for(let i=0;i<count;i++){
   const a=angle+(i/count)*Math.PI*2+.23*Math.sin(i*4.1),distance=radius*(.18+.58*q)*(.65+.25*Math.sin(i*3.7));
   const x=ground.x+Math.sin(a)*distance,z=ground.z+Math.cos(a)*distance,scale=.13+.07*(.5+.5*Math.sin(i*2.3));
   const position=new Vec3(x,this.ground(x,z,ground.y)+.04+(.22+.10*(i%3))*Math.sin(Math.PI*q),z);
   const layer=this.acquire(key+':earth-chip:'+i,'rock-chip');if(!layer)continue;
   if(layer.phase!=='rock-chip'){layer.renderer.mesh=this.chipMesh();layer.phase='rock-chip';}
   const mat=this.solid([.54,.49,.42],alpha*fade,false);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
   layer.node.setWorldPosition(position);layer.node.setWorldRotation(Quat.fromEuler(new Quat(),i*48+q*140,i*73+q*190,i*19+q*100));layer.node.setWorldScale(scale,scale*.8,scale);layer.touched=true;layer.node.active=true;
  }
 }
 private fractureChunks(key:string,centre:Vec3,angle:number,radius:number){
  const cached=Array.from({length:5},(_,i)=>this.meshes.get('fracture:'+key+':'+i));if(cached.every(Boolean))return cached as Mesh[];
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const chunks=Array.from({length:5},()=>({positions:[] as number[],normals:[] as number[],colors:[] as number[],indices:[] as number[]}));
  let maxOffset=0,maxDistance=0;
  const strip=(chunk:typeof chunks[0],a:Vec3,b:Vec3,width:number,colour:number[],lift:number)=>{
   const dx=b.x-a.x,dz=b.z-a.z,len=Math.hypot(dx,dz),sx=-dz/len*width/2,sz=dx/len*width/2;
   const points=[[a.x+sx,a.z+sz],[b.x+sx,b.z+sz],[b.x-sx,b.z-sz],[a.x-sx,a.z-sz]],offset=chunk.positions.length/3;
   for(const [x,z]of points){const y=this.ground(x,z,centre.y)+lift;chunk.positions.push(x-centre.x,y-centre.y,z-centre.z);chunk.normals.push(0,1,0);chunk.colors.push(...colour,1);maxOffset=Math.max(maxOffset,lift);maxDistance=Math.max(maxDistance,Math.hypot(x-centre.x,z-centre.z));}
   chunk.indices.push(offset,offset+1,offset+2,offset,offset+2,offset+3);
  };
  const segment=(chunk:typeof chunks[0],a:Vec3,b:Vec3,width:number)=>{
   strip(chunk,a,b,width*1.7,[.31,.27,.22],.060);strip(chunk,a,b,width,[.075,.064,.055],.065);
   const edge=b.clone().subtract(a).normalize(),offset=new Vec3(-edge.z,0,edge.x).multiplyScalar(width*.58);
   strip(chunk,a.clone().add(offset),b.clone().add(offset),width*.17,[.58,.59,.57],.070);
  };
  for(const sign of [-1,1]){
   let previous=centre.clone();
   for(let i=0;i<5;i++){
    const f=(i+1)/5,point=centre.clone().add(forward.clone().multiplyScalar(sign*radius*.87*f)).add(side.clone().multiplyScalar(Math.sin(i*2.1+sign*.7)*radius*.065*f));
    segment(chunks[i],previous,point,.15-.024*i);
    if(i===1||i===3){let branch=point.clone();for(let j=0;j<2;j++){const next=branch.clone().add(side.clone().multiplyScalar(sign*radius*.20)).add(forward.clone().multiplyScalar(radius*(j===0?.10:-.07)));segment(chunks[i],branch,next,j===0?.060:.035);branch=next;}}
    previous=point;
   }
  }
  this.groundRecord={centre:{x:centre.x,y:centre.y,z:centre.z},radius,chunks:5,maxGroundOffset:maxOffset,maxDistance};
  return chunks.map((data,i)=>{
   const xs=data.positions.filter((_,k)=>k%3===0),ys=data.positions.filter((_,k)=>k%3===1),zs=data.positions.filter((_,k)=>k%3===2);
   const mesh=utils.createMesh({...data,uvs:Array(data.positions.length/3*2).fill(.5),minPos:new Vec3(Math.min(...xs),Math.min(...ys),Math.min(...zs)),maxPos:new Vec3(Math.max(...xs),Math.max(...ys),Math.max(...zs)),boundingRadius:Math.max(...data.positions.map(Math.abs))+radius});
   const name='fracture:'+key+':'+i;this.meshes.set(name,mesh);this.terrainMeshes.add(name);return mesh;
  });
 }
 drawFromHand(hand:Vec3|undefined,key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(!this.anchors.has(key)&&hand){if(this.anchors.size>=64)this.anchors.clear();this.anchors.set(key,hand.clone());}
  this.draw(key,center,angle,radius,span,width,alpha,progress,up);
 }
 private mesh(row:number,col:number,guard=false){
  const key=(guard?'g:':'b:')+row+':'+col;const cached=this.meshes.get(key);if(cached)return cached;
  const cols=guard?2:4,rows=guard?2:3,u0=col/cols,u1=(col+1)/cols,v0=(row+1)/rows,v1=row/rows;
  const mesh=utils.createMesh({positions:[-.5,-.5,0,.5,-.5,0,.5,.5,0,-.5,.5,0],normals:[0,0,1,0,0,1,0,0,1,0,0,1],uvs:[u0,v0,u1,v0,u1,v1,u0,v1],indices:[0,1,2,0,2,3],minPos:new Vec3(-.5,-.5,-.002),maxPos:new Vec3(.5,.5,.002),boundingRadius:.71});
  this.meshes.set(key,mesh);return mesh;
 }
 private material(alpha:number,guard=false,wave=false){
  const level=Math.max(1,Math.min(32,Math.round(clamp(alpha)*32))),key=(guard?'g:':wave?'w:':'b:')+level;const cached=this.materials.get(key);if(cached)return cached;
  const material=new Material();
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true,USE_VERTEX_COLOR:wave},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  material.setProperty('mainTexture',guard?MeleeBladeSurfaces.guardTexture!:MeleeBladeSurfaces.texture!);material.setProperty('mainColor',new Vec4(1,1,1,level/32*(wave?MeleeBladeSurfaces.opacityScale:1)));
  this.materials.set(key,material);return material;
 }
 private pressureMesh(row:number,col:number){
  const key='wave:'+row+':'+col,cached=this.meshes.get(key);if(cached)return cached;
  const positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[];
  const across=40,depth=12;
  for(let i=0;i<=across;i++)for(let j=0;j<=depth;j++){
   const u=i/across*2-1,v=j/depth,edge=Math.pow(Math.max(0,1-u*u),.65);
   const curl=Math.pow(Math.max(0,Math.sin(Math.PI*v)),.8)*Math.sqrt(Math.max(0,1-u*u));
   positions.push(u*.5,curl,-u*u*.42-v);normals.push(0,1,0);
   uvs.push((col+i/across)/4,(row+v)/3);
   const rear=v<.16?1:v<.55?1-.78*smooth((v-.16)/.39):.22*(1-smooth((v-.55)/.45));
   const density=smooth(v/.07)*rear*edge,light=1-.18*smooth((v-.18)/.82);
   colors.push(light,light,light,density);
  }
  for(let i=0;i<across;i++)for(let j=0;j<depth;j++){const a=i*(depth+1)+j,b=a+depth+1;indices.push(a,b,a+1,b,b+1,a+1);}
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(-.5,0,-1.42),maxPos:new Vec3(.5,1,0),boundingRadius:1.9});this.meshes.set(key,mesh);return mesh;
 }
 private wave(key:string,position:Vec3,across:Vec3,normal:Vec3,forward:Vec3,span:number,lift:number,depth:number,row:number,phase:number,alpha:number){
  if(alpha<.012||span<.03||depth<.02)return;
  const layer=this.acquire(key,'wave');if(!layer)return;
  const col=Math.max(0,Math.min(3,Math.floor(phase*4))),phaseKey='wave:'+row+':'+col;
  if(layer.phase!==phaseKey){layer.renderer.mesh=this.pressureMesh(row,col);layer.phase=phaseKey;}
  const body=!key.includes('wake')&&!key.includes('impact');
  const material=this.material(body?Math.min(1,alpha*1.8):alpha,false,true);if(layer.renderer.sharedMaterial!==material)layer.renderer.setSharedMaterial(material,0);
  Quat.fromAxes(this.rotation,across,normal,forward);layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(span,lift,depth);layer.touched=true;layer.node.active=true;
 }
 private layer(key:string,position:Vec3,xAxis:Vec3,yAxis:Vec3,width:number,height:number,row:number,phase:number,alpha:number,guard=false){
  if(alpha<.012||width<.01||height<.01)return;
  let layer=this.layers.find(item=>item.key===key);
  if(!layer){
   layer=this.layers.find(item=>!item.touched&&!item.node.active);
   if(!layer){
    if(this.layers.length>=24)return;
    const node=new Node('NewBladeLayer');node.layer=this.root.layer;this.root.addChild(node);
    const renderer=node.addComponent(MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
    layer={key,node,renderer,touched:false,phase:''};this.layers.push(layer);
   }layer.key=key;
  }
  const cols=guard?2:4,col=Math.min(cols-1,Math.max(0,Math.floor(phase*cols))),phaseKey=(guard?'g:':'b:')+row+':'+col;
  if(layer.phase!==phaseKey){layer.renderer.mesh=this.mesh(row,col,guard);layer.phase=phaseKey;}
  const mat=this.material(alpha,guard);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  const normal=Vec3.cross(new Vec3(),xAxis,yAxis).normalize();Quat.fromAxes(this.rotation,xAxis,yAxis,normal);
  layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(width,height,1);layer.node.active=true;layer.touched=true;
 }
 private crossingAxis(forward:Vec3,side:Vec3){
  if(!this.camera)return side.clone().multiplyScalar(Math.cos(Math.PI/3)).add(new Vec3(0,Math.sin(Math.PI/3),0)).normalize();
  const right=this.camera.node.right,up=this.camera.node.up;
  const sx=Vec3.dot(side,right),sy=Vec3.dot(side,up),phi=Math.atan2(sy,sx)-Math.PI/3;
  const a=sy*Math.cos(phi)-sx*Math.sin(phi),b=up.y*Math.cos(phi)-right.y*Math.sin(phi);
  const roll=Math.atan2(-a,b),axis=side.clone().multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0));
  if(Vec3.dot(axis,right)*Math.cos(phi)+Vec3.dot(axis,up)*Math.sin(phi)<0)axis.multiplyScalar(-1);
  return axis.normalize();
 }
 private singleCut(key:string,center:Vec3,angle:number,radius:number,alpha:number,t:number,roll:number,size:number,role:string){
  const f=new Vec3(Math.sin(angle),0,Math.cos(angle)),s=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const across=s.clone().multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0)),normal=Vec3.cross(new Vec3(),f,across).normalize();
  const front=center.clone().add(f.clone().multiplyScalar(radius*(.38+.50*smooth(t/.65))));
  const fade=smooth(t/.10)*(1-smooth((t-.62)/.38));
  this.wave(key+':'+role,front,across,normal,f,radius*size*(.64+.36*smooth(t/.38)),radius*.14,radius*.32,0,t*.85,clamp(alpha/245)*fade);
 }
 draw(key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(key.startsWith('echo:')||!MeleeBladeSurfaces.texture||radius<=0)return;
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress);
  if(key.startsWith('basic:')){this.singleCut(key,center,angle,Math.min(radius,1.8),alpha,t,[.35,-.40,1.35][stage-1],.62,'basic-trail');return;}
  if(key.includes('WAR_05')){
   if(stage===1)this.singleCut(key,center,angle,radius,alpha,t,.10,1.14,'finisher-sweep');
   else if(stage===2)this.singleCut(key,center,angle,radius,alpha,t,1.38,.95,'finisher-rise');
   else{this.crossed(key,center,angle,radius,span,width,alpha,t,up);const f=new Vec3(Math.sin(angle),0,Math.cos(angle)),at=center.clone().add(f.multiplyScalar(radius*.90));at.y=this.ground(at.x,at.z,center.y-1.02);this.chips(key,at,angle,radius*.50,t,clamp(alpha/245),4);}
   return;
  }
  this.singleCut(key,center,angle,radius,alpha,t,stage===2?-.28:.22,.78,'focused-cut');
 }
 private crossed(key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(key.startsWith('echo:')||!MeleeBladeSurfaces.texture||radius<=0)return;
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress),power=clamp(alpha/245);
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const distance=radius*(.60+.44*smooth(t/.33)),opening=smooth(t/.28),hFade=1-smooth((t-.62)/.38);
  const front=center.clone().add(forward.clone().multiplyScalar(distance)).add(new Vec3(0,-.12,0));
  const waveSpan=radius*(.42+.42*smooth(t/.45)),lift=radius*(stage===3?.20:.16),depth=radius*.34;
  const horizontal=power*hFade*(stage===2?.55:1);
  this.wave(key+':horizontal',front,side,Vec3.UNIT_Y,forward,waveSpan,lift,depth,0,t*.88,horizontal*opening);
  if(t>.18){
   const wake=front.clone().subtract(forward.clone().multiplyScalar(radius*.31));
   this.wave(key+':horizontal-wake',wake,side,Vec3.UNIT_Y,forward,waveSpan*.88,lift*.48,depth*.84,0,.45+t*.4,horizontal*.19);
  }
  const vertical=smooth((t-.20)/.42),vFade=1-smooth((t-.78)/.22);
  const verticalPower=power*smooth((t-.20)/.13)*vFade*(stage===1?.72:1);
  const vFront=center.clone().add(forward.clone().multiplyScalar(radius*(.88+.13*vertical))).add(new Vec3(0,.37*(1-vertical),0));
  const vAcross=this.crossingAxis(forward,side),vNormal=Vec3.cross(new Vec3(),forward,vAcross).normalize();
  this.wave(key+':vertical',vFront,vAcross,vNormal,forward,Math.min(3.8,radius*.94)*(.70+.30*vertical),radius*.14,radius*.27,1,clamp((t-.20)/.72),verticalPower);
  if(t>.31&&t<.85&&this.camera){
   const p=clamp((t-.31)/.54),hit=center.clone().add(forward.clone().multiplyScalar(radius*.91)).add(this.camera.node.forward.clone().multiplyScalar(-.18));
   this.wave(key+':impact',hit,side,Vec3.UNIT_Y,forward,radius*.28,radius*.08,radius*.19,0,.30+p*.5,power*(1-smooth(p))*.76);
  }
 }
 drawSlash(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number){
  const delta=end.clone().subtract(start),r=Math.max(1,delta.length());this.draw(key,start,Math.atan2(delta.x,delta.z),r,0,width,alpha,progress);
 }
 cross(key:string,impact:Vec3,angle:number,length:number,t:number,alpha:number){
  const radius=Math.max(1.6,length*1.12),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  const origin=impact.clone().subtract(forward.multiplyScalar(radius*.90));
  this.crossed(key+':stage:3',origin,angle,radius,Math.PI,.2,alpha,t);
 }
 rush(key:string,start:Vec3,current:Vec3,angle:number,t:number){
  const delta=current.clone().subtract(start),length=delta.length();if(length<.12)return;
  const forward=delta.normalize(),side=new Vec3(Math.cos(angle),0,-Math.sin(angle)),fade=.78*(1-smooth((t-.72)/.28));
  for(let i=0;i<3;i++){const offset=side.clone().multiplyScalar((i-1)*.24),a=start.clone().add(offset),b=current.clone().add(offset).subtract(forward.clone().multiplyScalar(.16));a.y=this.ground(a.x,a.z,start.y-.18)+.055;b.y=this.ground(b.x,b.z,current.y-.18)+.055;this.bar(key+':rush-streak:'+i,a,b,i===1?.065:.038,[.80,.86,.91],fade,true);}
 }
 cleave(key:string,ground:Vec3,angle:number,radius:number,t:number,alpha:number){
  if(!this.camera)return;
  const p=clamp(t),power=clamp(alpha/245),fade=1-smooth((p-.76)/.24),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  ground.y=this.ground(ground.x,ground.z,ground.y);
  const stage=Math.min(5,Math.floor(p/.30*6));this.piece(key+':rupture-surface',this.ruptureMesh(key,ground,angle,radius,stage),'rupture-surface','rupture',ground,Quat.IDENTITY,Vec3.ONE,fade,[1,1,1],true);
  this.brokenSlabs(key,ground,angle,radius,p,fade);
  if(p<.19){const hit=ground.clone().add(new Vec3(0,1.72-.70*smooth(p/.19),0));this.wave(key+':slam-edge',hit,Vec3.UNIT_Y,side,forward,radius*1.43,.25,radius*.19,1,p*3.4,1-smooth(p/.19));}
  if(p<.55){
   const travel=smooth(p/.45),at=ground.clone().add(forward.clone().multiplyScalar(radius*(.10+.87*travel))).add(new Vec3(0,.14,0)),strength=1-smooth((p-.12)/.43),rotation=Quat.fromAxes(new Quat(),side,Vec3.UNIT_Y,forward),span=radius*(1.05+.25*travel);
   this.piece(key+':ground-pressure-edge',this.pressureMesh(0,Math.min(3,Math.floor(p*6.8))),'wave','blade',at,rotation,new Vec3(span*1.07,.36,radius*.34),strength,[.67,.73,.78],true);
   this.wave(key+':ground-pressure',at.clone().add(new Vec3(0,.018,0)),side,Vec3.UNIT_Y,forward,span,.32,radius*.32,0,p*1.7,strength*.94);
  }
  if(p<.18)this.sprite(key+':impact-flash','flash',ground.clone().add(new Vec3(0,.18,0)),.92,.72,1-smooth(p/.18),[.96,.98,1]);
  for(let i=0;i<6;i++){
   const delay=.035+(i%3)*.025;if(p<delay)continue;const q=clamp((p-delay)/.87),sign=i%2?1:-1,along=radius*(-.18+(i%3)*.28),away=radius*(.16+.37*q),at=ground.clone().add(forward.clone().multiplyScalar(along)).add(side.clone().multiplyScalar(sign*away));
   at.y=this.ground(at.x,at.z,ground.y)+.20+.36*q;const opacity=smooth(q/.11)*(1-smooth((q-.14)/.58))*.85;
   this.sprite(key+':dust-roll:'+i,'dust',at,.80+q*1.30,.55+q*.78,opacity*fade,[.48,.45,.40]);
  }
 }
 guard(key:string,center:Vec3,angle:number,age:number,alpha:number,hit=false){
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const opening=.82+.18*smooth(age/.15),opacity=hit?clamp(alpha/245):.72*smooth(age/.08);
  const at=center.clone().add(forward.clone().multiplyScalar(.56)),points=[[-.44,.44],[0,.64],[.44,.44],[.34,-.24],[0,-.57],[-.34,-.24]];
  const vertices=points.map(([x,y])=>at.clone().add(side.clone().multiplyScalar(x*opening)).add(new Vec3(0,y*opening,0)));
  for(let i=0;i<vertices.length;i++)this.bar(key+':'+(hit?'shield-hit':'shield-outline')+':'+i,vertices[i],vertices[(i+1)%vertices.length],hit?.065:.035,hit?[.98,.99,1]:[.68,.77,.84],opacity);
  if(!hit){this.bar(key+':shield-rib:0',vertices[1],vertices[4],.025,[.78,.85,.90],opacity*.8);this.bar(key+':shield-rib:1',vertices[0],vertices[2],.025,[.78,.85,.90],opacity*.8);}
 }
 pulse(key:string,center:Vec3,angle:number,t:number,alpha:number,iron=false,hand?:Vec3){
  if(!this.camera)return;
  const fade=Math.pow(1-clamp(t),1.4),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  if(iron){
   const at=center.clone().add(forward.clone().multiplyScalar(.43)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
   for(let i=0;i<3;i++){const a=at.clone().add(side.clone().multiplyScalar((i-1)*.20)).add(new Vec3(0,.20-.12*i,0)),b=a.clone().add(side.clone().multiplyScalar(.22)).add(new Vec3(0,-.26,0));this.bar(key+':armour-pulse:'+i,a,b,.04,[.92,.96,1],clamp(alpha/245)*fade);}
  }else{
   const position=(hand??center).clone().add(forward.clone().multiplyScalar(.22));
   const axis=forward.clone().multiplyScalar(.7).add(new Vec3(0,.72,0)).normalize(),widthAxis=this.camera.node.right.clone();
   widthAxis.subtract(axis.clone().multiplyScalar(Vec3.dot(axis,widthAxis))).normalize();
   this.bar(key+':blade-glint',position.clone().subtract(axis.clone().multiplyScalar(.27)),position.clone().add(axis.clone().multiplyScalar(.38)),.045,[.96,.98,1],clamp(alpha/245)*fade);
   this.bar(key+':blade-glint-tip',position.clone().subtract(widthAxis.clone().multiplyScalar(.12)),position.clone().add(widthAxis.clone().multiplyScalar(.12)),.025,[.96,.98,1],clamp(alpha/245)*fade);
  }
 }
 end(){for(const layer of this.layers)if(!layer.touched)layer.node.active=false;}
 clear(){for(const layer of this.layers){layer.node.active=false;layer.touched=false;layer.phase='';}this.anchors.clear();for(const key of this.terrainMeshes){this.meshes.get(key)?.destroy();this.meshes.delete(key);}this.terrainMeshes.clear();this.groundRecord=null;this.droppedLayers=0;}
 inspect(){return {capacity:64,allocated:this.layers.length,droppedLayers:this.droppedLayers,groundRecord:this.groundRecord,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-ground-impact-v16',opacityScale:MeleeBladeSurfaces.opacityScale,targetObtuseAngleDegrees:120,targetAcuteAngleDegrees:60,body:'Accepted silver wave material; skill-specific shapes and timing',active:this.layers.filter(layer=>layer.node.active).map(layer=>{
  const axis=Vec3.transformQuat(new Vec3(),Vec3.UNIT_X,layer.node.worldRotation),right=this.camera?.node.right,up=this.camera?.node.up;
  const screen=this.camera?.worldToScreen(layer.node.worldPosition),colour=layer.renderer.sharedMaterial?.getProperty('mainColor') as Vec4|undefined;
  const role=['rupture-surface','raised-slab','ballistic-debris','contact-shadow','slam-edge','ground-pressure','impact-flash','dust-roll','basic-trail','focused-cut','finisher-sweep','finisher-rise','rush-streak','shield-outline','shield-rib','shield-hit','ground-crack','earth-chip','downstroke','ground-flash','armour-pulse','blade-glint'].find(s=>layer.key.includes(s))??(layer.key.includes('WAR_05')?'finisher-cross':'rush-cross');
  return {key:layer.key,role,mode:layer.phase,screenAxisDegrees:right&&up?Math.atan2(Vec3.dot(axis,up),Vec3.dot(axis,right))*180/Math.PI:undefined,projectedOrigin:screen?{x:screen.x,y:screen.y}:undefined,materialOpacity:colour?.w,renderers:1};
 })};}
 destroy(){MeleeBladeSurfaces.instances.delete(this);this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
