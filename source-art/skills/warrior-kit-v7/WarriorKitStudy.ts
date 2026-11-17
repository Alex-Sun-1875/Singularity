import {assetManager,ImageAsset,Texture2D,Camera,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable design renderer. All artwork and surfaces are new for this study. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static guardTexture:Texture2D|null=null;
 private static pending:Promise<void>|null=null;
 private static instances=new Set<MeleeBladeSurfaces>();
 private static palettes=new Map<string,{blade:Texture2D;guard:Texture2D}>();
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
 private material(alpha:number,guard=false){
  const level=Math.max(1,Math.min(32,Math.round(clamp(alpha)*32))),key=(guard?'g:':'b:')+level;const cached=this.materials.get(key);if(cached)return cached;
  const material=new Material();
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  material.setProperty('mainTexture',guard?MeleeBladeSurfaces.guardTexture!:MeleeBladeSurfaces.texture!);material.setProperty('mainColor',new Vec4(1,1,1,level/32));
  this.materials.set(key,material);return material;
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
  const stage=Number(key.match(/:stage:(\d)/)?.[1]??1),t=clamp(progress),power=clamp(alpha/255);
  const a=angle+(stage===2?-.09:.12)*(1-smooth(t/.55));
  const forward=new Vec3(Math.sin(a),0,Math.cos(a)),side=new Vec3(Math.cos(a),0,-Math.sin(a));
  const vertical=Vec3.UNIT_Y;
  const grow=.22+.78*smooth(t/.32);
  const hand=this.anchors.get(key);
  const start=hand?hand.clone().add(forward.clone().multiplyScalar(.26)):center.clone().add(forward.clone().multiplyScalar(radius*.12));
  const aim=center.clone().add(forward.clone().multiplyScalar(radius*1.22));
  const direction=aim.clone().subtract(start).normalize(),length=Vec3.distance(aim,start)*grow;
  const horizontalCenter=start.clone().add(direction.clone().multiplyScalar(length*.5));
  const sweptSide=side.clone().multiplyScalar(.94).add(new Vec3(0,.34,0)).normalize();
  sweptSide.subtract(direction.clone().multiplyScalar(Vec3.dot(direction,sweptSide))).normalize();
  const hFade=1-smooth((t-.64)/.36),hPower=power*hFade*(stage===2?.58:.93);
  this.layer(key+':horizontal',horizontalCenter,direction,sweptSide,length,radius*.66,0,Math.min(.82,t*.84),hPower);
  const v=smooth((t-.20)/.42),vFade=1-smooth((t-.79)/.21);
  const vPower=power*smooth((t-.20)/.14)*vFade*(stage===1?.68:1);
  const hit=center.clone().add(forward.clone().multiplyScalar(radius*.90));
  const vCenter=hit.clone().add(new Vec3(0,.58*(1-v)+.06,0));
  if(this.camera)vCenter.add(this.camera.node.forward.clone().multiplyScalar(-.24));
  // A true vertical plane with a small forward rake, distinct from the ground-cutting plane.
  const vX=this.camera?this.camera.node.right.clone().normalize():side.clone();
  const vUp=new Vec3(-forward.x*.10,.995,-forward.z*.10).normalize();
  vUp.subtract(vX.clone().multiplyScalar(Vec3.dot(vX,vUp))).normalize();
  this.layer(key+':vertical',vCenter,vX,vUp,radius*.46,radius*1.16*(.46+.54*v),1,clamp((t-.20)/.72),vPower);
  if(t>.30&&t<.84&&this.camera){
   const p=smooth((t-.30)/.54),kick=(1-smooth(p))*.85*power;
   const impact=hit.clone().add(this.camera.node.forward.clone().multiplyScalar(-.30));
   this.layer(key+':impact',impact,this.camera.node.right.clone(),this.camera.node.up.clone(),radius*.43,radius*.43,2,p,kick);
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
  const forward=delta.normalize(),side=new Vec3(Math.cos(angle),.16,-Math.sin(angle)).normalize(),center=start.clone().add(current).multiplyScalar(.5);
  side.subtract(forward.clone().multiplyScalar(Vec3.dot(side,forward))).normalize();
  this.layer(key,center,forward,side,length,.62,0,.38+.4*t,.62*(1-smooth((t-.7)/.3)));
 }
 cleave(key:string,ground:Vec3,angle:number,radius:number,t:number,alpha:number){
  if(!this.camera)return;
  const size=Math.max(1.4,radius),p=clamp(t),power=clamp(alpha/255),right=this.camera.node.right.clone();
  const position=ground.clone().add(new Vec3(0,2.05-.92*smooth(p/.48),0)).add(this.camera.node.forward.clone().multiplyScalar(-.2));
  this.layer(key+':vertical',position,right,Vec3.UNIT_Y,Math.max(1.5,size*.76),Math.max(3.3,size*1.7),1,Math.min(.82,p*.88),power*(1-smooth((p-.78)/.22)));
  if(p>.20){
   const growth=smooth((p-.20)/.37),fade=1-smooth((p-.64)/.36);
   for(const [i,turn] of [-.80,0,.80].entries()){
    const a=angle+turn,f=new Vec3(Math.sin(a),0,Math.cos(a)),s=new Vec3(Math.cos(a),0,-Math.sin(a));
    const at=ground.clone().add(f.clone().multiplyScalar(size*.55*growth)).add(new Vec3(0,.065,0));
    this.layer(key+':ground-cut:'+i,at,f,s,size*1.24*growth,size*.46,0,.48+p*.40,power*.76*fade);
   }
   const flash=ground.clone().add(new Vec3(0,.34,0)).add(this.camera.node.forward.clone().multiplyScalar(-.2));
   this.layer(key+':impact',flash,right,this.camera.node.up.clone(),size*1.0,size*.8,2,clamp((p-.20)/.8),power*.82*fade);
  }
 }
 guard(key:string,center:Vec3,angle:number,age:number,alpha:number,hit=false){
  if(!this.camera||!MeleeBladeSurfaces.guardTexture)return;
  const forward=new Vec3(Math.sin(angle),0,Math.cos(angle)),position=center.clone().add(forward.multiplyScalar(.32)).add(this.camera.node.forward.clone().multiplyScalar(-.22));
  const opening=smooth(age/.18),frame=hit?2:age<.14?0:1;
  const opacity=hit?clamp(alpha/255)*.90:Math.min(.78,.18+.58*(1-smooth((age-.38)/.72)))*smooth(age/.055);
  const width=(hit?1.70:1.58)*(.76+.24*opening),height=(hit?2.10:2.02)*(.88+.12*opening);
  this.layer(key+':guard',position,this.camera.node.right.clone(),Vec3.UNIT_Y,width,height,Math.floor(frame/2),(frame%2)*.5+.02,opacity,true);
 }
 pulse(key:string,center:Vec3,angle:number,t:number,alpha:number,iron=false,hand?:Vec3){
  if(!this.camera)return;
  const fade=Math.pow(1-clamp(t),1.4),forward=new Vec3(Math.sin(angle),0,Math.cos(angle));
  if(iron){
   const position=center.clone().add(forward.multiplyScalar(.38)).add(this.camera.node.forward.clone().multiplyScalar(-.28));
   this.layer(key+':iron',position,this.camera.node.right.clone(),Vec3.UNIT_Y,1.34+ t*.14,1.84,1,.02,clamp(alpha/255)*fade*.92,true);
  }else{
   const position=(hand??center).clone().add(forward.clone().multiplyScalar(.22));
   const axis=forward.clone().multiplyScalar(.7).add(new Vec3(0,.72,0)).normalize(),widthAxis=this.camera.node.right.clone();
   widthAxis.subtract(axis.clone().multiplyScalar(Vec3.dot(axis,widthAxis))).normalize();
   this.layer(key+':mastery',position,axis,widthAxis,.88+.20*t,.50,0,.34+.45*t,clamp(alpha/255)*fade*.85);
  }
 }
 end(){for(const layer of this.layers)if(!layer.touched)layer.node.active=false;}
 clear(){for(const layer of this.layers){layer.node.active=false;layer.touched=false;}this.anchors.clear();}
 inspect(){return {capacity:24,allocated:this.layers.length,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-kit-v7-cyan',active:this.layers.filter(layer=>layer.node.active).map(layer=>({key:layer.key,mode:'cyan-steel',renderers:1}))};}
 destroy(){MeleeBladeSurfaces.instances.delete(this);this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
