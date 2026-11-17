import {Color,Material,Mesh,MeshRenderer,Node,utils,primitives,gfx} from 'cc';
import type {GameSession} from '../../../core/GameSession';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';
import {earlyWorldStates,type EarlyWorldState} from '../common/EarlyChapterState';
import {FEEDBACK_PALETTE} from '../../../shared/ui/FeedbackPalette';

type Geometry={positions:number[];indices:number[];colors:number[]};
type Visual={node:Node;renderer:MeshRenderer;mesh:Mesh;complete:boolean};
const WOOD='#64503c',DARK='#414c55',METAL='#a4b1ba',LINEN='#d8d8ca';
/** A single merged mesh per workstation, refreshed only when its saved state
 * changes. Lazy creation keeps the cutout terrain's initial renderer snapshot
 * from hiding these native props. No live light, collider, HUD or update tween. */
export class EarlyChapterPresentation {
 private root:Node|null=null;private material:Material|null=null;
 private visuals=new Map<string,Visual>();private signature='';private disposed=false;
 constructor(private readonly world:SceneBuilder){}
 private box(g:Geometry,x:number,y:number,z:number,w:number,h:number,d:number,color:string,angle=0){
  const part=primitives.box(),offset=g.positions.length/3,c=Math.cos(angle),s=Math.sin(angle),tint=new Color().fromHEX(color);
  for(let i=0;i<part.positions.length;i+=3){const px=part.positions[i]*w,py=part.positions[i+1]*h;g.positions.push(x+px*c-py*s,y+px*s+py*c,z+part.positions[i+2]*d);g.colors.push(tint.r/255,tint.g/255,tint.b/255,1);}
  for(const index of part.indices!)g.indices.push(index+offset);
 }
 private geometry(state:EarlyWorldState):Geometry {
  const g:Geometry={positions:[],indices:[],colors:[]},done=state.complete,accent=done?FEEDBACK_PALETTE['state.success']:FEEDBACK_PALETTE['state.paused'];
  const box=(x:number,y:number,z:number,w:number,h:number,d:number,color:string,angle=0)=>this.box(g,x,y,z,w,h,d,color,angle);
  if(state.kind==='lamp'){
   box(0,.58,0,.12,1.16,.12,DARK);box(0,1.13,0,.6,.1,.45,WOOD);box(0,1.43,0,.48,.1,.4,DARK);
   for(const x of [-.22,.22])box(x,1.28,0,.045,.32,.4,DARK);
   box(0,1.28,0,.36,.24,.3,done?FEEDBACK_PALETTE['damage.fire']:'#343e43');
   if(done){box(0,.045,0,1.25,.035,.9,'#b69662');box(0,1.28,.17,.26,.15,.025,FEEDBACK_PALETTE['impact.core']);}
  }else if(state.kind==='wheel'){
   for(const x of [-.72,.72])box(x,.57,0,.16,1.14,.42,WOOD);
   box(0,.72,0,1.7,.16,.2,METAL);
   const angle=done?0:.22;
   for(let i=0;i<8;i++){const a=i*Math.PI/4+angle;box(Math.cos(a)*.65,.85+Math.sin(a)*.65,.18,.63,.14,.18,WOOD,a+Math.PI/2);box(Math.cos(a)*.35,.85+Math.sin(a)*.35,.18,.8,.07,.1,METAL,a);}
   box(0,.85,.18,.28,.28,.26,done?METAL:DARK);
   if(!done)box(.83,.14,.22,.88,.1,.18,DARK,-.28);else box(0,.055,.48,1.7,.045,.35,'#567e91');
  }else if(state.kind==='bench'){
   box(0,.75,0,1.65,.16,.7,WOOD);
   for(const x of [-.65,.65])for(const z of [-.24,.24])box(x,.36,z,.12,.72,.12,DARK);
   box(-.4,.9,0,.26,.2,.28,METAL);box(-.27,.92,.13,.14,.12,.27,done?METAL:'#695c54');
   box(.35,.86,0,.6,.07,.11,METAL,done?0:.4);box(.35,.91,0,.15,.15,.15,done?WOOD:DARK);
   box(.62,.875,-.2,.17,.06,.17,accent);
  }else if(state.kind==='switch'){
   box(0,.12,0,.78,.24,.62,DARK);box(0,.58,0,.48,.75,.36,METAL);box(0,1,0,.66,.1,.48,DARK);
   box(0,.77,-.2,.3,.15,.035,done?FEEDBACK_PALETTE['state.success']:FEEDBACK_PALETTE['state.paused']);
   const angle=done?-.55:.55;box(Math.sin(angle)*.17,1.2,.03,.1,.5,.1,WOOD,angle);box(Math.sin(angle)*.32,1.42,.03,.25,.1,.18,DARK);
   box(.47,.16,0,.12,.2,.18,done?METAL:DARK);
  }else{
   box(0,.57,0,.12,1.14,.12,WOOD);box(0,1.05,0,1.1,.68,.12,WOOD);box(0,1.05,-.075,.9,.5,.035,LINEN);
   box(0,1.05,-.102,.72,.035,.02,DARK);box(0,.95,-.102,.72,.035,.02,DARK);
   if(done){box(.21,1.16,-.11,.38,.045,.025,FEEDBACK_PALETTE['state.success'],.36);box(-.04,1.11,-.11,.2,.045,.025,FEEDBACK_PALETTE['state.success'],-.52);}
   else box(.25,1.19,-.11,.28,.09,.025,FEEDBACK_PALETTE['state.paused']);
  }
  return g;
 }
 update(game:GameSession):void {
  if(this.disposed)return;
  const states=earlyWorldStates(this.world.area.id,game.state.flags),signature=states.map(state=>state.id+':'+Number(state.visible)+Number(state.complete)).join('|');
  if(signature===this.signature)return;this.signature=signature;
  for(const state of states){
   const old=this.visuals.get(state.id);if(!state.visible){if(old)old.node.active=false;continue;}
   const object=this.world.area.objects.find(object=>object.eventId===state.eventId);if(!object)continue;
   if(old&&old.complete===state.complete){old.node.active=true;continue;}
   if(!this.root){this.root=new Node('EarlyChapterSavedState');this.world.root.addChild(this.root);}
   if(!this.material){this.material=new Material();this.material.name='EarlyChapter-SavedState';this.material.initialize({effectName:'builtin-unlit',defines:{USE_VERTEX_COLOR:true},states:{rasterizerState:{cullMode:gfx.CullMode.BACK}}});this.material.setProperty('mainColor',Color.WHITE);}
   const mesh=utils.createMesh(this.geometry(state),undefined,{calculateBounds:true});
   if(old){old.renderer.mesh=mesh;old.mesh.destroy();old.mesh=mesh;old.complete=state.complete;old.node.active=true;continue;}
   const node=new Node('SavedState:'+state.id);node.layer=this.world.root.layer;this.root.addChild(node);node.setPosition(object.x,this.world.height(object)+.02,object.z);
   const renderer=node.addComponent(MeshRenderer);renderer.mesh=mesh;renderer.setSharedMaterial(this.material,0);renderer.shadowCastingMode=0;renderer.receiveShadow=0;
   this.visuals.set(state.id,{node,renderer,mesh,complete:state.complete});
  }
 }
 inspect(){return {area:this.world.area.id,states:Array.from(this.visuals,([id,v])=>({id,visible:v.node.active,complete:v.complete})),liveLights:0};}
 destroy(){if(this.disposed)return;this.disposed=true;this.root?.destroy();for(const v of this.visuals.values())v.mesh.destroy();this.visuals.clear();this.material?.destroy();this.root=null;this.material=null;}
}
