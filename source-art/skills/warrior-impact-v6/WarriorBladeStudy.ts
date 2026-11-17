import {assetManager,ImageAsset,Texture2D,Camera,Material,Mesh,MeshRenderer,Node,Vec3,Vec4,Quat,gfx,utils} from 'cc';

type Layer={key:string;node:Node;renderer:MeshRenderer;touched:boolean;phase:string};
const clamp=(x:number)=>Math.max(0,Math.min(1,x));
const smooth=(x:number)=>{const t=clamp(x);return t*t*(3-2*t);};

/** Disposable design renderer. All artwork and surfaces are new for this study. */
export class MeleeBladeSurfaces {
 private static texture:Texture2D|null=null;
 private static pending:Promise<void>|null=null;
 static preload():Promise<void>{
  if(this.pending)return this.pending;
  this.pending=new Promise((resolve,reject)=>{
   const url=(globalThis as any).location.origin+'/review/atlas.png';
   assetManager.loadRemote<ImageAsset>(url,{ext:'.png'},(error,image)=>{
    if(error){reject(error);return;}
    const texture=new Texture2D();texture.image=image;
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);texture.addRef();
    this.texture=texture;resolve();
   });
  });return this.pending;
 }
 static disposeAssets(){this.texture?.decRef();this.texture=null;this.pending=null;}
 private root:Node;
 private layers:Layer[]=[];
 private meshes=new Map<string,Mesh>();
 private materials=new Map<number,Material>();
 private anchors=new Map<string,Vec3>();
 private rotation=new Quat();
 constructor(parent:Node,private readonly camera?:Camera){this.root=new Node('WarriorImpactDesign');this.root.layer=parent.layer;parent.addChild(this.root);}
 begin(){for(const layer of this.layers)layer.touched=false;}
 drawFromHand(hand:Vec3|undefined,key:string,center:Vec3,angle:number,radius:number,span:number,width:number,alpha:number,progress:number,up?:Vec3){
  if(!this.anchors.has(key)&&hand){if(this.anchors.size>=64)this.anchors.clear();this.anchors.set(key,hand.clone());}
  this.draw(key,center,angle,radius,span,width,alpha,progress,up);
 }
 private mesh(row:number,col:number){
  const key=row+':'+col;const cached=this.meshes.get(key);if(cached)return cached;
  const u0=col/4,u1=(col+1)/4,v0=(row+1)/3,v1=row/3;
  const mesh=utils.createMesh({positions:[-.5,-.5,0,.5,-.5,0,.5,.5,0,-.5,.5,0],normals:[0,0,1,0,0,1,0,0,1,0,0,1],uvs:[u0,v0,u1,v0,u1,v1,u0,v1],indices:[0,1,2,0,2,3],minPos:new Vec3(-.5,-.5,-.002),maxPos:new Vec3(.5,.5,.002),boundingRadius:.71});
  this.meshes.set(key,mesh);return mesh;
 }
 private material(alpha:number){
  const level=Math.max(1,Math.min(32,Math.round(clamp(alpha)*32)));const cached=this.materials.get(level);if(cached)return cached;
  const material=new Material();
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false}}});
  material.setProperty('mainTexture',MeleeBladeSurfaces.texture!);material.setProperty('mainColor',new Vec4(1.08,1.04,.97,level/32));
  this.materials.set(level,material);return material;
 }
 private layer(key:string,position:Vec3,xAxis:Vec3,yAxis:Vec3,width:number,height:number,row:number,phase:number,alpha:number){
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
  const col=Math.min(3,Math.max(0,Math.floor(phase*4))),phaseKey=row+':'+col;
  if(layer.phase!==phaseKey){layer.renderer.mesh=this.mesh(row,col);layer.phase=phaseKey;}
  const mat=this.material(alpha);if(layer.renderer.sharedMaterial!==mat)layer.renderer.setSharedMaterial(mat,0);
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
 end(){for(const layer of this.layers)if(!layer.touched)layer.node.active=false;}
 clear(){for(const layer of this.layers){layer.node.active=false;layer.touched=false;}this.anchors.clear();}
 inspect(){return {capacity:24,allocated:this.layers.length,meshes:this.meshes.size,materials:this.materials.size,artwork:'warrior-impact-v6',active:this.layers.filter(layer=>layer.node.active).map(layer=>({key:layer.key,mode:'new-blade',renderers:1}))};}
 destroy(){this.clear();this.root.destroy();for(const mesh of this.meshes.values())mesh.destroy();for(const mat of this.materials.values())mat.destroy();}
}
