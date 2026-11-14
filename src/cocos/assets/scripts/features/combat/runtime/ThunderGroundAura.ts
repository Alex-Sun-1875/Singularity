import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Color,Material,Mesh,MeshRenderer,Node,Quat,Texture2D,gfx,primitives,utils} from 'cc';
import type {Point} from '../../../core/Contracts';
import {THUNDER_COLORS} from './SkillEnergyStrokes';

type Layer={node:Node;renderer:MeshRenderer;material:Material;color:Color};
type Aura={key:string;root:Node;mist:Layer;residual:Layer;texturePhase:number;touched:boolean;radius:number;phase:number;alpha:number};
const LIMIT=32;
const PATH='vfx/production/thunder-ground-v1/';
const clamp=(value:number,min:number,max:number)=>Math.max(min,Math.min(max,value));
const keySeed=(key:string)=>{let value=2166136261;for(let i=0;i<key.length;i++)value=Math.imul(value^key.charCodeAt(i),16777619);return value>>>0;};

/** A low, soft residual cloud belongs to an already resolved impact/field. It
 * does not find targets, draw a preselection circle, tick damage, or illuminate
 * the entire map. Two native quads share cached masks; no Line budget is used. */
export class ThunderGroundAura {
 private static textures:Texture2D[]=[];
 private static pending:Promise<void>|null=null;
 private static revision=0;
 private readonly root:Node;
 private readonly mesh:Mesh;
 private readonly items:Aura[]=[];
 private readonly rotation=new Quat();
 private disposed=false;

 static preload():Promise<void>{
  if(this.pending)return this.pending;
  const revision=this.revision,paths=['haze','residual0','residual1','residual2','residual3'];
  this.pending=Promise.all(paths.map((name,index)=>new Promise<void>((resolve,reject)=>{
   resources.load(PATH+name+'/texture',Texture2D,(error,texture)=>{
    if(error){reject(new Error('Thunder residual '+name+': '+error.message));return;}
    if(revision!==this.revision){reject(new Error('Thunder residual load cancelled after disposal'));return;}
    texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);
    texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setMipFilter(Texture2D.Filter.NONE);
    texture.addRef();this.textures[index]=texture;resolve();
   });
  }))).then(()=>undefined).catch(error=>{this.dispose();throw error;});return this.pending;
 }

 /** Call only after every instance using these masks was destroyed. */
 static dispose(){this.revision++;for(const texture of this.textures)texture?.decRef();this.textures=[];this.pending=null;}

 constructor(parent:Node,private readonly groundHeight?:(point:Point)=>number){
  this.root=new Node('ThunderGroundResidual');this.root.layer=parent.layer;parent.addChild(this.root);
  const quad=primitives.quad();for(let i=1;i<quad.uvs!.length;i+=2)quad.uvs![i]=1-quad.uvs![i];
  this.mesh=utils.createMesh(quad);this.mesh.name='ThunderResidualSharedQuad';
 }

 private layer(parent:Node,name:string,color:string):Layer {
  const node=new Node(name);node.layer=parent.layer;parent.addChild(node);
  const material=new Material();material.name='ProjectProcedural:ThunderGround:'+name;
  material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{
   rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},
   // The haze is coloured translucent mist, not another additive light. A
   // fully additive cloud disappeared into bright terrain and left white
   // ground cracks; only its smaller residual filaments should add light.
   ...(name==='soft-haze'?{}:{blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}})
  }});
  const renderer=node.addComponent(MeshRenderer);renderer.mesh=this.mesh;renderer.setSharedMaterial(material,0);
  // Keep the actual ground depth, like character transparency. A higher global
  // priority would incorrectly paint a ground cloud over foreground bodies.
  renderer.priority=0;renderer.shadowCastingMode=0;renderer.receiveShadow=0;
  return{node,renderer,material,color:new Color().fromHEX(color)};
 }

 begin(){for(const item of this.items)item.touched=false;}

 /** Alpha is 0..255 and phase is normalized remaining presentation progress.
  * Radius is the supplied resolved patch footprint, never an expanded hit area.
  * A local patch around each true impact naturally overlaps into a loose cloud. */
 draw(key:string,point:Point,radius:number,alpha:number,phase:number){
  if(this.disposed||!this.root.isValid||!Number.isFinite(radius)||radius<=0||!Number.isFinite(alpha)||alpha<=0)return;
  if(!ThunderGroundAura.textures[0])throw new Error('ThunderGroundAura.preload must finish before drawing residuals');
  let item=this.items.find(item=>item.key===key);
  if(!item)item=this.items.find(item=>!item.touched&&!item.root.active);
  if(!item){
   if(this.items.length>=LIMIT){item=this.items.find(item=>!item.touched);if(!item)return;}
   else{
    const root=new Node('ThunderGroundPatch');root.layer=this.root.layer;root.active=false;this.root.addChild(root);
    const mist=this.layer(root,'soft-haze',THUNDER_COLORS.ground),residual=this.layer(root,'broken-discharge',THUNDER_COLORS.residual);
    mist.material.setProperty('mainTexture',ThunderGroundAura.textures[0]);
    item={key,root,mist,residual,texturePhase:-1,touched:false,radius,phase:0,alpha:0};this.items.push(item);
   }
  }
  phase=clamp(Number.isFinite(phase)?phase:0,0,1);alpha=clamp(alpha,0,255);
  item.key=key;item.touched=true;item.radius=radius;item.phase=phase;item.alpha=alpha;
  item.root.setWorldPosition(point.x,(this.groundHeight?.(point)??0)+.045,point.z);
  // Horizontal soft cloud, with slow internal drift. The image has a fully
  // feathered, irregular perimeter; this never produces a circular outline.
  const seed=keySeed(key),angle=phase*9+(seed%997)/997*360;
  item.root.setWorldRotation(Quat.fromEuler(this.rotation,-90,angle,0));
  const grow=.86+.14*Math.sin(Math.PI*Math.min(1,phase*1.5));
  item.mist.node.setPosition(0,0,0);item.mist.node.setScale(radius*2*grow,radius*1.88*grow,1);
  item.residual.node.setPosition(0,0,.008);item.residual.node.setScale(radius*1.88,radius*1.72,1);
  const texturePhase=(Math.floor(phase*12)+seed%4)%4;
  if(item.texturePhase!==texturePhase){item.texturePhase=texturePhase;item.residual.material.setProperty('mainTexture',ThunderGroundAura.textures[1+texturePhase]);}
  item.mist.color.a=Math.round(alpha*.95);item.residual.color.a=Math.round(alpha*.45);
  item.mist.material.setProperty('mainColor',item.mist.color);item.residual.material.setProperty('mainColor',item.residual.color);
  item.root.active=true;
 }

 end(){for(const item of this.items)if(!item.touched)item.root.active=false;}
 clear(){for(const item of this.items){item.root.active=false;item.touched=false;item.key='';}}
 inspect(){return{capacity:LIMIT,allocated:this.items.length,active:this.items.filter(item=>item.root.active).map(item=>({key:item.key,radius:item.radius,phase:item.phase,alpha:item.alpha,texturePhase:item.texturePhase,position:{x:item.root.worldPosition.x,y:item.root.worldPosition.y,z:item.root.worldPosition.z}}))};}
 destroy(){if(this.disposed)return;this.disposed=true;this.clear();for(const item of this.items){item.mist.material.destroy();item.residual.material.destroy();}this.items.length=0;this.root.destroy();this.mesh.destroy();}
}
