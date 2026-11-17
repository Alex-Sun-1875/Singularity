import {assetManager,ImageAsset,Texture2D,Camera,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable silver cross-slash and three-front shockwave study. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static guardTexture:Texture2D|null=null;
 private static pending:Promise<void>|null=null;
 private static instances=new Set<MeleeBladeSurfaces>();
 private static palettes=new Map<string,{blade:Texture2D;guard:Texture2D}>();
 private static opacityScale=.78;
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
  this.pending=Promise.all([load('blade'),load('guard')]).then(([blade,guard])=>{this.texture=blade;this.guardTexture=guard;});return this.pending;
 }
 static disposeAssets(){this.texture?.decRef();this.guardTexture?.decRef();this.texture=null;this.guardTexture=null;this.pending=null;}
 private root:Node;
 private layers:Layer[]=[];
 private meshes=new Map<string,Mesh>();
 private materials=new Map<string,Material>();
 private anchors=new Map<string,Vec3>();
 private rotation=new Quat();
 private droppedLayers=0;
 constructor(parent:Node,private readonly camera?:Camera){this.root=new Node('WarriorImpactDesign');this.root.layer=parent.layer;parent.addChild(this.root);MeleeBladeSurfaces.instances.add(this);}
 begin(){for(const layer of this.layers)layer.touched=false;}
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
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:!wave,USE_VERTEX_COLOR:wave},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  if(!wave)material.setProperty('mainTexture',guard?MeleeBladeSurfaces.guardTexture!:MeleeBladeSurfaces.texture!);material.setProperty('mainColor',new Vec4(1,1,1,level/32*(wave?MeleeBladeSurfaces.opacityScale:1)));
  this.materials.set(key,material);return material;
 }
 private pressureMesh(row:number,col:number){
  const key='wave:'+row+':'+col,cached=this.meshes.get(key);if(cached)return cached;
  const positions:number[]=[],normals:number[]=[],uvs:number[]=[],colors:number[]=[],indices:number[]=[];
  const across=64,depth=20;
  for(let i=0;i<=across;i++)for(let j=0;j<=depth;j++){
   const u=i/across*2-1,v=j/depth,edge=Math.max(0,1-u*u),arc=Math.sqrt(edge);
   // Two bowed boundaries meet at pointed tips. The open inner concavity is real geometry.
   const band=(row===2?.17:.52)*Math.pow(edge,.75);
   const z=.88*(arc-1)-v*band;
   positions.push(u*.5,.055*Math.sin(Math.PI*v)*arc,z);normals.push(0,1,0);
   uvs.push(i/across,v);
   const filament=.91+.09*Math.sin(u*24+v*8+col*.9);
   const flow=.78+.22*Math.pow(Math.max(0,Math.cos(v*Math.PI*4+u*1.4-col*.8)),4);
   const density=smooth(v/.065)*(1-smooth((v-.42)/.58))*Math.pow(edge,.19)*filament*flow;
   const front=1-smooth((v-.12)/.40);
   const silver=.50+.49*front;
   colors.push(silver*.975,silver*.987,silver,density);
  }
  for(let i=0;i<across;i++)for(let j=0;j<depth;j++){const a=i*(depth+1)+j,b=a+depth+1;indices.push(a,b,a+1,b,b+1,a+1);}
  const mesh=utils.createMesh({positions,normals,uvs,colors,indices,minPos:new Vec3(-.5,0,-1.1),maxPos:new Vec3(.5,.055,0),boundingRadius:1.3});this.meshes.set(key,mesh);return mesh;
 }
 private crossAxis(forward:Vec3,side:Vec3,degrees:number){
  if(!this.camera)return side.clone().multiplyScalar(Math.cos(degrees*Math.PI/180)).add(new Vec3(0,Math.sin(degrees*Math.PI/180),0)).normalize();
  const right=this.camera.node.right,up=this.camera.node.up,phi=degrees*Math.PI/180;
  const sx=Vec3.dot(side,right),sy=Vec3.dot(side,up),ux=right.y,uy=up.y;
  const a=sy*Math.cos(phi)-sx*Math.sin(phi),b=uy*Math.cos(phi)-ux*Math.sin(phi);
  const roll=Math.atan2(-a,b),axis=side.clone().multiplyScalar(Math.cos(roll)).add(new Vec3(0,Math.sin(roll),0));
  if(Vec3.dot(axis,right)*Math.cos(phi)+Vec3.dot(axis,up)*Math.sin(phi)<0)axis.multiplyScalar(-1);
  return axis.normalize();
 }
 private wave(key:string,position:Vec3,across:Vec3,normal:Vec3,forward:Vec3,span:number,lift:number,depth:number,row:number,phase:number,alpha:number){
  if(alpha<.012||span<.03||depth<.02)return;
  let layer=this.layers.find(item=>item.key===key);
  if(!layer){
   layer=this.layers.find(item=>!item.touched&&!item.node.active);
   if(!layer){if(this.layers.length>=64){this.droppedLayers++;return;}const node=new Node('SwordQiPressureWave');node.layer=this.root.layer;this.root.addChild(node);const renderer=node.addComponent(MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;layer={key,node,renderer,touched:false,phase:''};this.layers.push(layer);}layer.key=key;
  }
  const col=Math.max(0,Math.min(3,Math.floor(phase*4))),phaseKey='wave:'+row+':'+col;
  if(layer.phase!==phaseKey){layer.renderer.mesh=this.pressureMesh(row,col);layer.phase=phaseKey;}
  const material=this.material(alpha,false,true);if(layer.renderer.sharedMaterial!==material)layer.renderer.setSharedMaterial(material,0);
  // Keep the crescent readable like an anime energy cel while its centre travels in 3D.
  // This is a curved mesh with an empty concavity, never a rectangular sprite or shell.
  let faceAcross=across,faceNormal=normal,faceBow=forward;
  if(this.camera){
   const right=this.camera.node.right,up=this.camera.node.up;
   const phi=Math.atan2(Vec3.dot(across,up),Vec3.dot(across,right));
   faceAcross=right.clone().multiplyScalar(Math.cos(phi)).add(up.clone().multiplyScalar(Math.sin(phi))).normalize();
   faceBow=right.clone().multiplyScalar(-Math.sin(phi)).add(up.clone().multiplyScalar(Math.cos(phi))).normalize();
   if(Vec3.dot(faceBow,forward)<0)faceBow.multiplyScalar(-1);
   faceNormal=Vec3.cross(new Vec3(),faceBow,faceAcross).normalize();
  }
  Quat.fromAxes(this.rotation,faceAcross,faceNormal,faceBow);layer.node.setWorldPosition(position);layer.node.setWorldRotation(this.rotation);layer.node.setWorldScale(span,lift*1.65,depth*1.22);layer.touched=true;layer.node.active=true;
 }
 private layer(key:string,position:Vec3,xAxis:Vec3,yAxis:Vec3,width:number,height:number,row:number,phase:number,alpha:number,guard=false){
  if(alpha<.012||width<.01||height<.01)return;
  let layer=this.layers.find(item=>item.key===key);
  if(!layer){
   layer=this.layers.find(item=>!item.touched&&!item.node.active);
   if(!layer){
    if(this.layers.length>=64){this.droppedLayers++;return;}
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
 draw(key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(key.startsWith('echo:')||!MeleeBladeSurfaces.texture||radius<=0)return;
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress),power=clamp(alpha/245);
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  // Restore the reference's broad horizontal cut and upright descending cut.
  const hAcross=this.crossAxis(forward,side,6),vAcross=this.crossAxis(forward,side,78);
  const hNormal=Vec3.cross(new Vec3(),forward,hAcross).normalize();
  const vNormal=Vec3.cross(new Vec3(),forward,vAcross).normalize();
  for(let index=0;index<3;index++){
   const q=(t-index*.17)/.64;if(q<=0||q>=1)continue;
   const gain=[.68,.82,1][index],opening=smooth(q/.12),fade=1-smooth((q-.80)/.20);
   const pressure=power*gain*opening*fade;
   // The three fronts have different launch times and continuously separated positions.
   const front=center.clone().add(forward.clone().multiplyScalar(radius*(.14+.94*q))).add(new Vec3(0,-.10,0));
   const waveSpan=radius*(.64+.22*smooth(q/.4)),lift=radius*(stage===3?.17:.14),depth=radius*.22;
   const pulseKey=key+':pulse:'+index;
   this.wave(pulseKey+':horizontal',front,hAcross,hNormal,forward,waveSpan,lift,depth,0,q*.88,pressure*(stage===2?.86:1));
   const drop=smooth((q-.055)/.24),vFront=front.clone().add(new Vec3(0,.33*(1-drop),0));
   this.wave(pulseKey+':vertical',vFront,vAcross,vNormal,forward,Math.min(3.2,radius*.73)*(.82+.18*drop),radius*.12,radius*.10,1,q*.88,pressure*smooth((q-.045)/.09)*(stage===1?.94:1));
   if(q>.14){
    const wake=front.clone().subtract(forward.clone().multiplyScalar(radius*.12));
    this.wave(pulseKey+':wake',wake,hAcross,hNormal,forward,waveSpan*.94,lift*.4,depth,2,.45+q*.4,pressure*.12);
   }
   const contact=Math.sin(Math.PI*clamp((q-.76)/.19));
   if(q>.76&&q<.95){
    this.wave(pulseKey+':contact-h',front,hAcross,hNormal,forward,radius*.19,lift*.4,radius*.06,0,.4,pressure*contact*.65);
    this.wave(pulseKey+':contact-v',front,vAcross,vNormal,forward,radius*.20,lift*.4,radius*.05,1,.4,pressure*contact*.65);
   }
  }
 }
 drawSlash(key:string,start:Vec3,end:Vec3,width:number,alpha:number,progress:number){
  const delta=end.clone().subtract(start),r=Math.max(1,delta.length());this.draw(key,start,Math.atan2(delta.x,delta.z),r,0,width,alpha,progress);
 }
 cross(key:string,impact:Vec3,angle:number,length:number,t:number,alpha:number){
  const radius=Math.max(1.6,length*1.12),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  const origin=impact.clone().subtract(forward.multiplyScalar(radius*.90));
  this.draw(key+':stage:3',origin,angle,radius,Math.PI,.2,alpha,t);
 }
 rush(key:string,start:Vec3,current:Vec3,angle:number,t:number){
  const delta=current.clone().subtract(start),length=delta.length();if(length<.12)return;
  const forward=delta.normalize(),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  this.wave(key,current,side,Vec3.UNIT_Y,forward,.62,.12,length,0,.32+t*.5,.52*(1-smooth((t-.7)/.3)));
 }
 cleave(key:string,ground:Vec3,angle:number,radius:number,t:number,alpha:number){
  if(!this.camera)return;
  const size=Math.max(1.4,radius),p=clamp(t),power=clamp(alpha/245),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  const side=Vec3.cross(new Vec3(),forward,Vec3.UNIT_Y).normalize();
  const position=ground.clone().add(new Vec3(0,1.75-.52*smooth(p/.48),0));
  this.wave(key+':vertical',position,Vec3.UNIT_Y,side,forward,Math.max(3.1,size*1.5),.40,Math.max(.72,size*.36),1,p*.86,power*(1-smooth((p-.76)/.24)));
  for(let index=0;index<3;index++){
   const q=(p-.14-index*.16)/.48;if(q<=0||q>=1)continue;
   const fade=1-smooth((q-.52)/.48),gain=[.68,.82,1][index];
   const at=ground.clone().add(forward.clone().multiplyScalar(size*(.10+.94*q))).add(new Vec3(0,.10,0));
   this.wave(key+':pulse:'+index+':horizontal',at,side,Vec3.UNIT_Y,forward,size*(.68+.26*smooth(q/.4)),.16,size*.26,0,q*.88,power*gain*smooth(q/.12)*fade);
  }
 }
 guard(key:string,center:Vec3,angle:number,age:number,alpha:number,hit=false){
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  const normal=Vec3.cross(new Vec3(),forward,Vec3.UNIT_Y).normalize(),opening=smooth(age/.18);
  const opacity=hit?clamp(alpha/245):Math.min(1,.18+.82*(1-smooth((age-.38)/.72)))*smooth(age/.055);
  for(let i=0;i<3;i++){
   const position=center.clone().add(forward.clone().multiplyScalar(.46+(i===1?.08:0))).add(side.clone().multiplyScalar((i-1)*.25)).add(new Vec3(0,.06,0));
   this.wave(key+':guard:'+i,position,Vec3.UNIT_Y,normal,forward,(hit?1.98:1.76)*(.8+.2*opening),hit?.17:.12,hit?.38:.28,1,hit?.48:.26,opacity*(i===1?1:.80)*.65);
  }
 }
 pulse(key:string,center:Vec3,angle:number,t:number,alpha:number,iron=false,hand?:Vec3){
  if(!this.camera)return;
  const fade=Math.pow(1-clamp(t),1.4),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  if(iron){
   this.guard(key+':iron',center,angle,t*.42,alpha*fade,true);
  }else{
   const position=(hand??center).clone().add(forward.clone().multiplyScalar(.22));
   const axis=forward.clone().multiplyScalar(.7).add(new Vec3(0,.72,0)).normalize(),widthAxis=this.camera.node.right.clone();
   widthAxis.subtract(axis.clone().multiplyScalar(Vec3.dot(axis,widthAxis))).normalize();
   const normal=Vec3.cross(new Vec3(),forward,Vec3.UNIT_Y).normalize();
   this.wave(key+':mastery',position,Vec3.UNIT_Y,normal,forward,.76,.14,.28,1,.34+.45*t,clamp(alpha/245)*fade);
  }
 }
 end(){for(const layer of this.layers)if(!layer.touched)layer.node.active=false;}
 clear(){for(const layer of this.layers){layer.node.active=false;layer.touched=false;}this.anchors.clear();}
 inspect(){return {capacity:64,allocated:this.layers.length,droppedLayers:this.droppedLayers,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-silver-cross-v12',opacityScale:MeleeBladeSurfaces.opacityScale,targetScreenCrossAngle:72,wavefrontsPerCue:3,launchOffsetsNormalized:[0,.17,.34],shape:'curved-cross-slash-with-three-travelling-fronts',active:this.layers.filter(layer=>layer.node.active).map(layer=>{
  const axis=Vec3.transformQuat(new Vec3(),Vec3.UNIT_X,layer.node.worldRotation),right=this.camera?.node.right,up=this.camera?.node.up;
  return {key:layer.key,mode:'silver-cross-shockwave',pulseIndex:Number(layer.key.match(/:pulse:(\d+):/)?.[1]??-1),position:{x:layer.node.worldPosition.x,y:layer.node.worldPosition.y,z:layer.node.worldPosition.z},screenAxisDegrees:right&&up?Math.atan2(Vec3.dot(axis,up),Vec3.dot(axis,right))*180/Math.PI:undefined,renderers:1};
 })};}
 destroy(){MeleeBladeSurfaces.instances.delete(this);this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
