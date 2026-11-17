import {assetManager,ImageAsset,Texture2D,Camera,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable anime-inspired crescent study; never imported by the production game. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static guardTexture:Texture2D|null=null;
 private static pending:Promise<void>|null=null;
 private static instances=new Set<MeleeBladeSurfaces>();
 private static palettes=new Map<string,{blade:Texture2D;guard:Texture2D}>();
 private static opacityScale=.55;
 private static palette='A';
 private static ramps:{[key:string]:{front:number[];body:number[]}}={
  A:{front:[.91,.97,1],body:[.40,.62,.77]},
  B:{front:[1,.96,.87],body:[.77,.63,.42]},
  C:{front:[.91,1,.97],body:[.40,.70,.65]},
  D:{front:[.97,.93,1],body:[.66,.55,.80]},
 };
 static setPalette(name:string){
  if(!this.ramps[name])throw Error('Unknown crescent palette '+name);
  if(this.palette===name)return;
  this.palette=name;
  for(const instance of this.instances){
   const previous=[...instance.meshes.values()];
   instance.meshes.clear();
   for(const layer of instance.layers){
    const match=layer.phase.match(/^wave:(\d+):(\d+)$/);
    if(match)layer.renderer.mesh=instance.pressureMesh(Number(match[1]),Number(match[2]));
   }
   for(const mesh of previous)mesh.destroy();
  }
 }
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
   const density=smooth(v/.065)*(1-smooth((v-.42)/.58))*Math.pow(edge,.19)*filament;
   const front=1-smooth((v-.12)/.40);
   const ramp=MeleeBladeSurfaces.ramps[MeleeBladeSurfaces.palette];
   colors.push(...ramp.body.map((value,index)=>value+(ramp.front[index]-value)*front),density);
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
   if(!layer){if(this.layers.length>=24)return;const node=new Node('SwordQiPressureWave');node.layer=this.root.layer;this.root.addChild(node);const renderer=node.addComponent(MeshRenderer);renderer.shadowCastingMode=0;renderer.receiveShadow=0;layer={key,node,renderer,touched:false,phase:''};this.layers.push(layer);}layer.key=key;
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
 draw(key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(key.startsWith('echo:')||!MeleeBladeSurfaces.texture||radius<=0)return;
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress),power=clamp(alpha/245);
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),side=new Vec3(Math.cos(angle),0,-Math.sin(angle));
  // The long crescent axis crosses the projected travel direction, with a narrow ±12° split.
  const baseline=this.camera?Math.atan2(Vec3.dot(forward,this.camera.node.up),Vec3.dot(forward,this.camera.node.right))*180/Math.PI+90:0;
  const hAcross=this.crossAxis(forward,side,baseline+12),vAcross=this.crossAxis(forward,side,baseline-12);
  const hNormal=Vec3.cross(new Vec3(),forward,hAcross).normalize();
  const vNormal=Vec3.cross(new Vec3(),forward,vAcross).normalize();
  const distance=radius*(.18+.88*smooth(t/.42)),opening=smooth(t/.20),hFade=1-smooth((t-.64)/.36);
  const front=center.clone().add(forward.clone().multiplyScalar(distance)).add(new Vec3(0,-.12,0));
  const waveSpan=radius*(.42+.42*smooth(t/.45)),lift=radius*(stage===3?.20:.16),depth=radius*.34;
  const horizontal=power*hFade*(stage===2?.55:1);
  this.wave(key+':horizontal',front,hAcross,hNormal,forward,waveSpan,lift,depth,0,t*.88,horizontal*opening);
  if(t>.18){
   const wake=front.clone().subtract(forward.clone().multiplyScalar(radius*.13));
   this.wave(key+':horizontal-wake',wake,hAcross,hNormal,forward,waveSpan*.94,lift*.48,depth*.92,2,.45+t*.4,horizontal*.20);
  }
  const vertical=smooth((t-.20)/.42),vFade=1-smooth((t-.78)/.22);
  const verticalPower=power*smooth((t-.20)/.13)*vFade*(stage===1?.72:1);
  const vFront=front.clone().add(forward.clone().multiplyScalar(radius*.04)).add(new Vec3(0,.06,0));
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
  if(p>.20){
   const growth=smooth((p-.20)/.37),fade=1-smooth((p-.64)/.36);
   for(const [i,turn]of [-.8,0,.8].entries()){
    const a=angle+turn,f=new Vec3(Math.sin(a),0,Math.cos(a)),s=new Vec3(Math.cos(a),0,-Math.sin(a));
    const at=ground.clone().add(f.clone().multiplyScalar(size*(.16+.78*growth))).add(new Vec3(0,.06,0));
    this.wave(key+':horizontal-ground:'+i,at,s,Vec3.UNIT_Y,f,size*.88*growth,.20,size*.50,0,.35+p*.5,power*.86*fade);
   }
   const flash=ground.clone().add(new Vec3(0,.36,0)).add(this.camera.node.forward.clone().multiplyScalar(-.16));
   this.wave(key+':impact',flash,new Vec3(Math.cos(angle),0,-Math.sin(angle)),Vec3.UNIT_Y,forward,size*.85,.26,size*.44,0,.38+p*.45,power*.80*fade);
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
 inspect(){return {capacity:24,allocated:this.layers.length,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-crescent-v11',opacityScale:MeleeBladeSurfaces.opacityScale,targetScreenCrossAngle:24,shape:'pointed-crescent-with-open-inner-concavity',active:this.layers.filter(layer=>layer.node.active).map(layer=>{
  const axis=Vec3.transformQuat(new Vec3(),Vec3.UNIT_X,layer.node.worldRotation),right=this.camera?.node.right,up=this.camera?.node.up;
  return {key:layer.key,mode:'translucent-crescent',screenAxisDegrees:right&&up?Math.atan2(Vec3.dot(axis,up),Vec3.dot(axis,right))*180/Math.PI:undefined,renderers:1};
 })};}
 destroy(){MeleeBladeSurfaces.instances.delete(this);this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
