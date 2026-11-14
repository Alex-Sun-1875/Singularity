import {gameResources as resources} from '../../../shared/assets/GameResources';
import {Camera,Color,Material,Mesh,MeshRenderer,Node,Texture2D,gfx,primitives,utils} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {SIGIL_FRAME,type PortalMount} from './PortalPlacement';

type State='open'|'locked';
type SigilMaterials={core:Material;glow:Material};
type Portal={mount:PortalMount;holder:Node;card:Node;core:MeshRenderer;glow:MeshRenderer;state:State};
const RESOURCE='flat2d/waypoints-v1/rune-sigil-v8',GLOW_RESOURCE='flat2d/waypoints-v1/rune-glow-v8';
const SIZE=SIGIL_FRAME.size,CENTER_HEIGHT=SIGIL_FRAME.centerHeight,LABEL_TOP=2.5,YAW=SIGIL_FRAME.yaw,PITCH=SIGIL_FRAME.pitch,LAYER_GAP=.006;
const PULSE_PERIOD=8,GLOW_ALPHA=120,GLOW_AMPLITUDE=10,LOCKED_GLOW_ALPHA=18;

/** The original ExitDef owns interaction and travel. This fixed world-space
 * rune circle is only two transparent quads and never creates an obstacle. */
export class PortalPresentation {
 private root:Node|null=null;
 private texture:Texture2D|null=null;
 private glowTexture:Texture2D|null=null;
 private readonly meshes=new Set<Mesh>();
 private readonly materials=new Map<State,SigilMaterials>();
 private readonly portals:Portal[]=[];
 private building:Promise<void>|null=null;
 private disposed=false;
 private time=0;
 private flags:Record<string,boolean>={};
 constructor(private readonly world:SceneBuilder,private camera:Camera){}

 build():Promise<void>{if(this.disposed)return Promise.resolve();return this.building??=this.load();}
 private async load():Promise<void>{
  const textures=await Promise.all([RESOURCE,GLOW_RESOURCE].map(path=>new Promise<Texture2D>((resolve,reject)=>this.world.loadAsset(path+'/texture',Texture2D,(error,asset)=>error?reject(new Error('Rune sigil '+path+': '+error.message)):resolve(asset)))));
  if(this.disposed||!this.world.root.isValid)return;
  [this.texture,this.glowTexture]=textures;
  for(const texture of textures){texture.addRef();texture.setFilters(Texture2D.Filter.LINEAR,Texture2D.Filter.LINEAR);texture.setWrapMode(Texture2D.WrapMode.CLAMP_TO_EDGE,Texture2D.WrapMode.CLAMP_TO_EDGE);}
  this.root=new Node('PortalPresentation');this.root.layer=this.world.root.layer;this.world.root.addChild(this.root);
  const geometry=primitives.quad();for(let i=1;i<geometry.uvs!.length;i+=2)geometry.uvs![i]=1-geometry.uvs![i];
  const quad=utils.createMesh(geometry);quad.name='RuneSigilQuad';this.meshes.add(quad);
  this.stateMaterials('open');this.stateMaterials('locked');
  const pitch=PITCH*Math.PI/180;
  for(const mount of this.world.portalMounts){
   const state:State=mount.exit.requiredLevel!==undefined?(mount.exit.requiredLevel>1?'locked':'open'):mount.exit.requires?'locked':'open',m=this.stateMaterials(state),holder=this.node('ExitSigilMount:'+mount.id,this.root);
   holder.setPosition(mount.exit.x,this.world.height(mount.exit),mount.exit.z);holder.setRotationFromEuler(0,YAW,0);
   const card=this.node('ExitSigil:'+mount.id,holder);card.setPosition(0,CENTER_HEIGHT,0);card.setRotationFromEuler(PITCH,0,0);card.setScale(SIZE,SIZE,1);
   const glowNode=this.node('ExitSigilGlow:'+mount.id,holder);
   // Place the glow just behind the main plane along its fixed local normal.
   glowNode.setPosition(0,CENTER_HEIGHT+Math.sin(pitch)*LAYER_GAP,-Math.cos(pitch)*LAYER_GAP);glowNode.setRotationFromEuler(PITCH,0,0);glowNode.setScale(SIZE,SIZE,1);
   const glow=this.renderer(glowNode,quad,m.glow,-6),core=this.renderer(card,quad,m.core,-5);
   this.portals.push({mount,holder,card,core,glow,state});
  }
  this.update(this.camera);
 }

 private node(name:string,parent:Node):Node{const node=new Node(name);node.layer=this.world.root.layer;parent.addChild(node);return node;}
 private renderer(node:Node,mesh:Mesh,material:Material,priority:number):MeshRenderer{const renderer=node.addComponent(MeshRenderer);renderer.mesh=mesh;renderer.setSharedMaterial(material,0);renderer.priority=priority;renderer.shadowCastingMode=0;renderer.receiveShadow=0;return renderer;}
 private stateMaterials(state:State):SigilMaterials{
  const cached=this.materials.get(state);if(cached)return cached;
  const make=(role:keyof SigilMaterials,texture:Texture2D,additive=false)=>{
   const material=new Material();material.name='RuneSigil:'+state+':'+role;
   material.initialize({effectName:'builtin-unlit',technique:1,defines:{USE_TEXTURE:true},states:{rasterizerState:{cullMode:gfx.CullMode.NONE},depthStencilState:{depthTest:true,depthWrite:false},...(additive?{blendState:{targets:[{blend:true,blendSrc:gfx.BlendFactor.SRC_ALPHA,blendDst:gfx.BlendFactor.ONE,blendSrcAlpha:gfx.BlendFactor.ONE,blendDstAlpha:gfx.BlendFactor.ONE_MINUS_SRC_ALPHA}]}}:{})}});
   material.setProperty('mainTexture',texture);return material;
  };
  const materials={core:make('core',this.texture!),glow:make('glow',this.glowTexture!,true)};
  materials.core.setProperty('mainColor',state==='open'?new Color(255,255,255,238):new Color(164,158,188,96));
  materials.glow.setProperty('mainColor',new Color(255,255,255,state==='open'?GLOW_ALPHA:LOCKED_GLOW_ALPHA));
  this.materials.set(state,materials);return materials;
 }

 update(camera?:Camera,game?:GameSession):void{
  if(camera)this.camera=camera;if(this.disposed||!this.root?.isValid)return;
  if(game){this.time=game.state.time;this.flags=game.state.flags;}
  for(const portal of this.portals){
   const state:State=game?(game.exitRequirement(portal.mount.exit)?'locked':'open'):portal.mount.exit.requiredLevel!==undefined?(portal.mount.exit.requiredLevel>1?'locked':'open'):portal.mount.exit.requires&&!this.flags[portal.mount.exit.requires]?'locked':'open';
   if(state!==portal.state){const m=this.stateMaterials(state);portal.core.setSharedMaterial(m.core,0);portal.glow.setSharedMaterial(m.glow,0);portal.state=state;}
  }
  const glow=this.materials.get('open')?.glow;
  glow?.setProperty('mainColor',new Color(255,255,255,GLOW_ALPHA+GLOW_AMPLITUDE*Math.sin(this.time*Math.PI*2/PULSE_PERIOD)));
 }

 inspect(){
  const alpha=(state:State)=>(this.materials.get(state)?.glow.getProperty('mainColor') as Color|undefined)?.a??0;
  const pulse={time:this.time,period:PULSE_PERIOD,wave:Math.sin(this.time*Math.PI*2/PULSE_PERIOD),glowAlpha:alpha('open'),lockedGlowAlpha:alpha('locked'),minimumAlpha:GLOW_ALPHA-GLOW_AMPLITUDE,maximumAlpha:GLOW_ALPHA+GLOW_AMPLITUDE,coreStatic:true};
  return {ready:!!this.root?.isValid&&!this.disposed,resource:RESOURCE,glowResource:GLOW_RESOURCE,resources:{core:RESOURCE,glow:GLOW_RESOURCE},style:'bg3-inspired-rune-circle',shape:'open-center-circle',symmetry:'bilateral-fixed-world-circle',materialRoles:['core','glow'],count:this.portals.length,open:this.portals.filter(p=>p.state==='open').length,locked:this.portals.filter(p=>p.state==='locked').length,colliders:0,solidCarriers:0,placement:this.world.portalPlacementReview,orientation:'fixed-world-surface',visualYaw:YAW,visualPitch:PITCH,visualDimensions:{width:SIZE,height:SIZE},centerHeight:CENTER_HEIGHT,labelTop:LABEL_TOP,meshCount:this.meshes.size,renderers:this.portals.length*2,groundGlyphCopies:0,pulse,animation:{time:this.time,period:PULSE_PERIOD,mode:'glow-opacity-only',coreStatic:true},
   entries:this.portals.map(p=>({id:p.mount.id,to:p.mount.exit.to,label:p.mount.exit.label,position:{x:p.mount.exit.x,y:this.world.height(p.mount.exit),z:p.mount.exit.z},mount:{kind:p.mount.kind,position:p.mount.position,yaw:YAW,width:p.mount.width,height:p.mount.height,depth:p.mount.depth,offset:0,collider:null},state:p.state,requires:p.mount.exit.requires??null,interactionRadius:1.35,cardDimensions:{width:SIZE,height:SIZE},cardPitch:PITCH,cardPosition:{x:p.card.worldPosition.x,y:p.card.worldPosition.y,z:p.card.worldPosition.z},anchorPosition:{x:p.holder.worldPosition.x,y:p.holder.worldPosition.y,z:p.holder.worldPosition.z},glowAlpha:alpha(p.state)}))};
 }

 destroy():void{
  if(this.disposed)return;this.disposed=true;if(this.root?.isValid){this.root.active=false;this.root.destroy();}
  for(const mesh of this.meshes)mesh.destroy();for(const m of this.materials.values())for(const material of Object.values(m))material.destroy();
  this.texture?.decRef();this.glowTexture?.decRef();this.texture=null;this.glowTexture=null;this.root=null;this.meshes.clear();this.materials.clear();this.portals.length=0;
 }
}
