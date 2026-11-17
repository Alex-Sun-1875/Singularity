import {assetManager,ImageAsset,Texture2D,Camera,Color,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string;family?:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable differentiated warrior kit, retaining the accepted silver wave material. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static guardTexture:Texture2D|null=null;
 private static whiteTexture:Texture2D|null=null;
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
  this.pending=Promise.all([load('blade'),load('guard'),load('white')]).then(([blade,guard,white])=>{this.texture=blade;this.guardTexture=guard;this.whiteTexture=white;});return this.pending;
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
 private spinMesh(span:number,width:number){
  const stamp='spin-mesh:'+span+':'+width,old=this.meshes.get(stamp);if(old)return old;
  const positions:number[]=[],normals:number[]=[],colors:number[]=[],uvs:number[]=[],indices:number[]=[],nx=64,nz=10;
  for(let i=0;i<=nx;i++)for(let j=0;j<=nz;j++){
   const s=i/nx,v=j/nz,theta=(s-.5)*span,taper=Math.pow(Math.max(0,Math.sin(Math.PI*s)),.67),radius=1-width*taper*v,curl=.14*Math.sin(Math.PI*v)*taper;
   positions.push(Math.sin(theta)*radius,curl+.035*Math.sin(theta),Math.cos(theta)*radius);normals.push(0,1,0);uvs.push(s,v);
   const cap=smooth(s/.065)*(1-smooth((s-.88)/.12)),density=cap*(v<.68?1:1-.82*smooth((v-.68)/.32));
   colors.push(.82+.15*(1-v),.86+.12*(1-v),.91+.08*(1-v),density);
  }
  for(let i=0;i<nx;i++)for(let j=0;j<nz;j++){const a=i*(nz+1)+j,b=a+nz+1;indices.push(a,b,a+1,b,b+1,a+1);}
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(-1,-.08,-1),maxPos:new Vec3(1,.22,1),boundingRadius:1.5});this.meshes.set(stamp,mesh);return mesh;
 }
 private spinArc(key:string,position:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,tilt=0){
  if(alpha<.02)return;const layer=this.acquire(key,'spin-band');if(!layer)return;
  const mesh=this.spinMesh(span,width);if(layer.renderer.mesh!==mesh)layer.renderer.mesh=mesh;layer.phase='spin-band';
  const mat=this.solid([1,1,1],alpha,true);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
  layer.node.setWorldPosition(position);layer.node.setWorldRotation(Quat.fromEuler(new Quat(),tilt,angle*180/Math.PI,0));layer.node.setWorldScale(radius,radius,radius);layer.node.active=true;layer.touched=true;
 }
 spinStudy(center:Vec3,angle:number,turn:number,time:number,contacts:{at:Vec3;age:number}[]=[]){
  const q=clamp((time-.48)/.96),active=time>=.48&&time<1.44,opening=smooth((time-.48)/.075),ending=1-smooth((time-1.32)/.12);
  if(active){
   const phase=angle+turn,front=center.clone().add(new Vec3(0,.94,0));
   this.spinArc('spin:primary',front,phase,2.15,2.30,.23,opening*ending,5*Math.sin(q*Math.PI*2));
   if(time>.56)this.spinArc('spin:secondary',center.clone().add(new Vec3(0,.65,0)),phase+Math.PI,1.96,2.05,.19,smooth((time-.56)/.09)*ending*.90,-7);
   this.spinArc('spin:trailing',front.clone().add(new Vec3(0,.035,0)),phase-.28,2.11,2.50,.27,opening*ending*.22,0);
  }
  if(time>=1.44&&time<1.80){
   const p=clamp((time-1.44)/.36),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),at=center.clone().add(forward.multiplyScalar(.30+2.15*smooth(p))).add(new Vec3(0,.86-.10*p,0));
   this.spinArc('spin:finisher',at,angle,1.48+.28*smooth(p),2.20,.23,1-smooth((p-.46)/.54),6);
  }
  if(this.camera)for(const [i,contact]of contacts.entries())if(contact.age>=0&&contact.age<.14){
   const fade=1-smooth(contact.age/.14),right=this.camera.node.right,up=this.camera.node.up,point=contact.at;
   this.bar('spin:contact:'+i+':a',point.clone().subtract(right.clone().multiplyScalar(.22)),point.clone().add(right.clone().multiplyScalar(.22)),.045,[.96,.98,1],fade);
   this.bar('spin:contact:'+i+':b',point.clone().subtract(up.clone().multiplyScalar(.16)),point.clone().add(up.clone().multiplyScalar(.16)),.035,[.96,.98,1],fade);
  }
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
  const p=clamp(t),power=clamp(alpha/245),fade=1-smooth((p-.72)/.28),forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  ground.y=this.ground(ground.x,ground.z,ground.y);
  const chunks=this.fractureChunks(key,ground,angle,radius);
  for(let i=0;i<chunks.length;i++)if(p>=i*.055){this.element(key+':ground-crack:'+i,chunks[i],'fracture:'+key+':'+i,ground,Vec3.UNIT_X,Vec3.UNIT_Y,1,1,[1,1,1],fade,true);}
  if(p<.24){const hit=ground.clone().add(new Vec3(0,1.08-.48*smooth(p/.20),0));this.wave(key+':downstroke',hit,Vec3.UNIT_Y,side,forward,radius*1.10,.22,radius*.18,1,p*2.5,power*(1-smooth(p/.24)));}
  this.chips(key,ground,angle,radius,clamp(p/.78),fade,8);
  if(p<.17)this.bar(key+':ground-flash',ground.clone().add(new Vec3(0,.04,0)).subtract(side.clone().multiplyScalar(radius*.25)),ground.clone().add(new Vec3(0,.04,0)).add(side.clone().multiplyScalar(radius*.25)),.13,[.91,.94,.96],1-smooth(p/.17),true);
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
 inspect(){return {capacity:64,allocated:this.layers.length,droppedLayers:this.droppedLayers,groundRecord:this.groundRecord,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-whirlwind-v17',opacityScale:MeleeBladeSurfaces.opacityScale,targetObtuseAngleDegrees:120,targetAcuteAngleDegrees:60,body:'Accepted silver wave material; skill-specific shapes and timing',active:this.layers.filter(layer=>layer.node.active).map(layer=>{
  const axis=Vec3.transformQuat(new Vec3(),Vec3.UNIT_X,layer.node.worldRotation),right=this.camera?.node.right,up=this.camera?.node.up;
  const screen=this.camera?.worldToScreen(layer.node.worldPosition),colour=layer.renderer.sharedMaterial?.getProperty('mainColor') as Vec4|undefined;
  const role=layer.key.startsWith('spin:')?layer.key:['basic-trail','focused-cut','finisher-sweep','finisher-rise','rush-streak','shield-outline','shield-rib','shield-hit','ground-crack','earth-chip','downstroke','ground-flash','armour-pulse','blade-glint'].find(s=>layer.key.includes(s))??(layer.key.includes('WAR_05')?'finisher-cross':'rush-cross');
  return {key:layer.key,role,mode:layer.phase,screenAxisDegrees:right&&up?Math.atan2(Vec3.dot(axis,up),Vec3.dot(axis,right))*180/Math.PI:undefined,projectedOrigin:screen?{x:screen.x,y:screen.y}:undefined,materialOpacity:colour?.w,renderers:1};
 })};}
 destroy(){MeleeBladeSurfaces.instances.delete(this);this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
