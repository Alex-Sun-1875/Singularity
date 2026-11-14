import {Camera,Color,Material,Mesh,MeshRenderer,Node,Quat,Vec3,gfx,primitives,utils} from 'cc';
import {VfxAssets} from '../../../shared/assets/VfxAssets';
import {THUNDER_COLORS} from './SkillEnergyStrokes';

type Layer={node:Node;renderer:MeshRenderer;material:Material;color:Color};
type Contact={key:string;root:Node;halo:Layer;star:Layer;kernel:Layer;touched:boolean;alpha:number;size:number};
const LIMIT=24;

/** Reference-style blue corona and white-hot contact. Existing CC0 light masks
 * and native transparent quads; no particles, targets, damage or global bloom. */
export class ThunderContactLights {
 private readonly root:Node;
 private readonly mesh:Mesh;
 private readonly items:Contact[]=[];
 private readonly rotation=new Quat();
 private disposed=false;
 constructor(parent:Node,private readonly camera?:Camera){
  this.root=new Node('ThunderContactLights');this.root.layer=parent.layer;parent.addChild(this.root);
  this.mesh=utils.createMesh(primitives.quad());this.mesh.name='ThunderContactSharedQuad';
 }
 private layer(parent:Node,name:string,mask:'light_01'|'star_01',color:string,priority:number):Layer {
  const node=new Node(name);node.layer=parent.layer;parent.addChild(node);
  const material=new Material();material.name='KenneyCC0:ThunderContact:'+name;
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}});
  material.setProperty('mainTexture',VfxAssets.lightTexture(mask));
  const renderer=node.addComponent(MeshRenderer);renderer.mesh=this.mesh;renderer.setSharedMaterial(material,0);renderer.priority=priority;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  return{node,renderer,material,color:new Color().fromHEX(color)};
 }
 begin(){for(const item of this.items)item.touched=false;}
 draw(key:string,center:Vec3,rank:number,alpha:number,time:number){
  if(this.disposed||alpha<=0)return;
  let item=this.items.find(item=>item.key===key);
  if(!item)item=this.items.find(item=>!item.touched&&!item.root.active);
  if(!item&&this.items.length>=LIMIT){item=this.items.find(item=>!item.touched);if(!item)return;}
  if(!item){
   const root=new Node('ThunderContact');root.layer=this.root.layer;root.active=false;this.root.addChild(root);
   item={key,root,halo:this.layer(root,'blue-corona','light_01',THUNDER_COLORS.halo,1),star:this.layer(root,'hot-star','star_01',THUNDER_COLORS.core,2),kernel:this.layer(root,'white-kernel','star_01',THUNDER_COLORS.flare,2),touched:false,alpha:0,size:0};this.items.push(item);
  }
  item.key=key;item.touched=true;item.alpha=Math.max(0,Math.min(255,alpha));item.size=.86+.045*rank;
  item.root.setWorldPosition(center);
  if(this.camera?.node.isValid)item.root.setWorldRotation(this.camera.node.worldRotation);else item.root.setRotationFromEuler(-35,40,0);
  const flicker=.96+.04*Math.sin(time*73+rank*2),size=item.size*flicker;
  item.halo.node.setScale(size*1.42,size*1.42,1);
  item.star.node.setScale(size*.76,size,1);item.star.node.setRotation(Quat.fromEuler(this.rotation,0,0,17));
  item.kernel.node.setScale(size*.42,size*.42,1);item.kernel.node.setRotation(Quat.fromEuler(this.rotation,0,0,-27));
  for(const [layer,gain]of [[item.halo,.55],[item.star,1],[item.kernel,.98]]as const){layer.color.a=Math.round(item.alpha*gain);layer.material.setProperty('mainColor',layer.color);}
  item.root.active=true;
 }
 end(){for(const item of this.items)if(!item.touched)item.root.active=false;}
 clear(){for(const item of this.items){item.root.active=false;item.touched=false;item.key='';}}
 inspect(){return{capacity:LIMIT,allocated:this.items.length,active:this.items.filter(item=>item.root.active).map(item=>({key:item.key,alpha:item.alpha,size:item.size,position:{x:item.root.worldPosition.x,y:item.root.worldPosition.y,z:item.root.worldPosition.z}}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.clear();for(const item of this.items)for(const layer of [item.halo,item.star,item.kernel])layer.material.destroy();this.items.length=0;this.root.destroy();this.mesh.destroy();}
}
