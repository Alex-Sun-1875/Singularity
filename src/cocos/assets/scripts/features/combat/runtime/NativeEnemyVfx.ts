import {Node,MeshRenderer,Vec3,Camera} from 'cc';
import type {GameEvent,Point} from '../../../core/Contracts';
import type {GameSession,EnemyState,ProjectileState} from '../../../core/GameSession';
import {enemyProfile,enemyContains,type EnemyResolvedGeometry,type EnemyHazardState} from '../common/EnemyCombat';
import type {SkillVfxHost} from './NativeSkillVfx';
import {VfxAssets} from '../../../shared/assets/VfxAssets';
import {FEEDBACK_PALETTE} from '../../../shared/ui/FeedbackPalette';
import type {SceneBuilder} from '../../world/runtime/SceneBuilder';

const TAU=Math.PI*2,LOCK=FEEDBACK_PALETTE['telegraph.windup'],ACTIVE=FEEDBACK_PALETTE['telegraph.active'];
const local=(p:Point,a:number,side:number,f:number):Point=>({x:p.x+Math.cos(a)*side+Math.sin(a)*f,z:p.z-Math.sin(a)*side+Math.cos(a)*f});
const dist=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
type Cue={at:Point;until:number;duration:number;kind:'contact'|'support';targetId?:string;angle:number};
type Anchor={kind:string;node:Node;key?:string;touched:boolean};

/** Native presentation adapter for resolved enemy moves. No target selection,
 * hit submission, range overlays, or independent movement simulation. */
export class NativeEnemyVfx {
 reducedMotion=false;
 private cues:Cue[]=[];private anchors:Anchor[]=[];private seen=new Set<string>();
 private paths=new Map<string,{points:Point[];time:number}>();
 private now=0;
 constructor(private host:SkillVfxHost,private world:SceneBuilder,private root:Node,private camera?:Camera){}
 handles(e:EnemyState){return enemyProfile(e)?.route==='profile';}
 private stroke(points:Point[],color:string,width=.035,alpha=180,height=.065){this.host.line(points.map(p=>this.host.at(p,height)),color,width,alpha);}
 private anchor(h:EnemyHazardState){
  const kind=h.anchorKind??'stake';let item=this.anchors.find(a=>a.key===h.id);
  if(!item){item=this.anchors.find(a=>!a.key&&a.kind===kind);
   if(!item&&this.anchors.length>=12){const idle=this.anchors.findIndex(a=>!a.key);if(idle>=0){this.anchors[idle].node.destroy();this.anchors.splice(idle,1);}}
   if(!item&&this.anchors.length<12){
   const node=new Node('EnemyAnchor:'+kind);this.root.addChild(node);item={node,kind,touched:false};this.anchors.push(item);
   const part=(name:string,mesh:string,p:Vec3,s:Vec3,color:string)=>{const n=new Node(name);node.addChild(n);n.setPosition(p);n.setScale(s);const r=n.addComponent(MeshRenderer);r.mesh=this.world.mesh(mesh);r.setSharedMaterial(VfxAssets.solid(color),0);};
   if(kind==='mirrorFrame'){
    part('Existing timber stand','box',new Vec3(0,.38,0),new Vec3(.10,.76,.10),'#806344');
    part('Bronze mirror frame','box',new Vec3(0,.77,0),new Vec3(.62,.75,.10),'#8f744e');
    part('Silver mirror panel','box',new Vec3(0,.77,.061),new Vec3(.49,.61,.035),'#b1c2bb');
   }else{
    part('Existing wooden stake','cylinder',new Vec3(0,.42,0),new Vec3(.12,.84,.12),'#806344');
    part(kind==='chainLock'?'Iron lock':'Iron stake head','box',new Vec3(0,.76,0),new Vec3(.25,.24,.18),'#a69b81');
   }
  }if(!item)return;item.key=h.id;}
  item.touched=true;item.node.active=true;item.node.setPosition(h.x,this.world.height(h),h.z);
  item.node.setRotationFromEuler(0,(h.geometry[0]?.angle??0)*180/Math.PI,0);
  const right=this.camera?.node.right??new Vec3(1,0,0),point=(side:number)=>({x:h.x+right.x*side,z:h.z+right.z*side});
  this.stroke([point(-.35),point(.35)],'#3e3024',.065,230,1.3);
  this.stroke([point(-.35),point(-.35+.7*Math.max(0,h.hp/h.maxHp))],LOCK,.035,240,1.3);
 }
 private hazard(h:EnemyHazardState,decorate=true){
  if(h.maxHp>0&&h.hp>0)this.anchor(h);
  if(!h.maxTicks)return;
  // Every live field keeps a visible material effect, even without outlines.
  // Nearby fields are detailed; other fields retain one low-cost emitter.
  const points:Point[]=[];
  for(const g of h.geometry){
   if(g.kind==='line'||g.kind==='rectangle')for(let i=0;i<4;i++)points.push(local(g,g.angle,0,g.length*(i+.5)/4));
   else {points.push({x:g.x,z:g.z});for(let i=0;i<5;i++)points.push(local(g,i/5*TAU,0,g.kind==='ring'?(g.radius+g.innerRadius)/2:g.radius*.55));}
  }
  const valid=points.filter(p=>h.geometry.some(g=>enemyContains(g,p,0)&&this.world.visible(g,p)&&Math.abs(this.world.height(g)-this.world.height(p))<1.2)).slice(0,decorate?6:1);
  const kind=h.element==='fire'?'fireRoll':h.element==='physical'?'dust':'charge',color=h.moveId.includes('spit')?'#b6c17d':h.element==='physical'?'#a58e73':LOCK;
  valid.forEach((p,i)=>this.host.loop(`enemy:hazard:${h.id}:${i}`,kind,p,.13,h.element==='fire'?.45:.32,color));
 }
 event(event:GameEvent,game:GameSession){
  if(!event.type.startsWith('enemy_'))return false;this.now=game.state.time;
  const key=`${event.type}:${event.castId??event.id}:${event.stepIndex??''}:${event.targetId??''}:${event.action??''}:${this.now.toFixed(4)}`;
  if(this.seen.has(key))return true;this.seen.add(key);if(this.seen.size>512)this.seen.delete(this.seen.values().next().value!);
  const e=game.state.enemies.find(e=>e.id===event.enemyId),from=(event.from as Point|undefined)??event.at??e??game.state.player,angle=Number(event.angle??e?.targetAngle??0);
  if(event.type==='enemy_anchor_hit'||event.type==='enemy_anchor_broken'){
   this.host.burst('spark',event.at??from,.45,event.type==='enemy_anchor_broken'?10:4,.55,ACTIVE);
   if(event.type==='enemy_anchor_broken')this.host.burst('dust',event.at??from,.1,8,.65);return true;
  }
  if(event.type==='enemy_attack_hit'){
   const p=game.state.player;this.host.burst(event.element==='fire'?'ember':'spark',p,.8,6,.5,LOCK);
   this.host.burst('flash',p,.8,1,.4,ACTIVE);this.cues.push({at:{...p},until:this.now+.16,duration:.16,kind:'contact',angle});
  }else if(event.type==='enemy_attack_release'){
   const geometry=(event.geometry??[]) as EnemyResolvedGeometry[],g=geometry[0],p=g?.origin==='caster'?from:g??from;
   if(e&&enemyProfile(e)?.body==='beast'){
    const heavy=!!e.bossId;this.host.burst('dust',p,.08,heavy?12:5,heavy?1.1:.4,'#a58e73');
   }else if(event.element==='fire')this.host.burst('fireRoll',p,.3,2,.65);
   else if(event.pose==='attack_sword'||event.moveId==='oath-cut')this.host.burst('slash',local(from,angle,0,.5),.8,1,.75,'#e4b98a',-angle);
   this.host.burst('dust',from,.08,5,.55);
  }else if(event.type==='enemy_status'&&event.targetId){
   const target=event.targetId==='player'?game.state.player:game.state.enemies.find(e=>e.id===event.targetId);
   if(target)this.cues.push({at:{...target},targetId:String(event.targetId),until:this.now+Math.min(3,Number(event.duration)||.3),duration:Math.min(3,Number(event.duration)||.3),kind:'support',angle});
  }
  if(this.cues.length>48)this.cues.splice(0,this.cues.length-48);return true;
 }
 projectile(p:ProjectileState,time:number){
  if(!p.enemyId)return false;
  const physical=p.kind==='crossbow',spit=p.enemyMoveId==='marsh-spit',color=spit?'#b6c17d':LOCK,h=physical?1.05:spit?.55:.75;if(physical)this.host.body(p);
  else if(p.enemyElement==='fire')this.host.loop('enemy:projectile:'+p.id,'fireRoll',p,h,.5);
  else this.host.loop('enemy:projectile:'+p.id,'charge',p,h,spit?.3:.55,color);
  let path=this.paths.get(p.id);if(!path){path={points:[],time};this.paths.set(p.id,path);}path.time=time;path.points.unshift({x:p.x,z:p.z});path.points.length=Math.min(4,path.points.length);
  let length=0;for(let i=1;i<path.points.length;i++){const a=path.points[i-1],b=path.points[i],step=dist(a,b);if(length+step>.9){const t=(.9-length)/Math.max(.001,step);path.points[i]={x:a.x+(b.x-a.x)*t,z:a.z+(b.z-a.z)*t};path.points.length=i+1;break;}length+=step;}
  this.stroke(path.points,physical?'#d6b690':color,physical?.016:spit?.05:.035,150,h);return true;
 }
 update(game:GameSession){
  const s=game.state;this.now=s.time;
  for(const e of s.enemies){
   if(e.hp<=0||e.templateId!=='ELITE_06'&&enemyProfile(e)?.id!=='ELITE_06')continue;
   const c=e.combat;if(!c)continue;
   // This sheet has no separate raised-blade windup. A small blade glint
   // supplies anticipation; the released ground cut is the attack itself.
   if(e.phase==='windup')this.host.loop(`enemy:blade-charge:${e.id}`,'charge',local(e,e.targetAngle,0,.35),1.1,c.locked?1.4:1,LOCK);
   if(e.phase==='active'&&c.moveId==='oath-cut')for(const g of c.geometry){
    if(g.kind!=='rectangle')continue;
    let end:Point=g;for(let d=.35;d<g.length+.35;d+=.35){const p=local(g,g.angle,0,Math.min(d,g.length));if(!this.world.visible(end,p))break;end=p;}
    const progress=Math.min(1,c.stepElapsed/.16);
    this.host.slash?.(`enemy:oath-cut:${c.castId}`,this.host.at(g,.085),this.host.at(end,.085),g.width,Math.round(230*(1-progress*.5)),progress);
   }
  }
  for(const anchor of this.anchors)anchor.touched=false;
  const hazards=(s.enemyHazards??[]).filter(h=>h.remaining>0&&!(h.maxHp>0&&h.hp<=0));
  // Keep the real field material effects; never draw enemy hitbox boundaries.
  const fields=hazards.filter(h=>h.maxTicks>0).sort((a,b)=>Number(b.geometry.some(g=>enemyContains(g,s.player)))-Number(a.geometry.some(g=>enemyContains(g,s.player)))||dist(a,s.player)-dist(b,s.player));
  fields.forEach((h,i)=>this.hazard(h,i<3));for(const h of hazards)if(h.maxHp>0&&!fields.includes(h))this.anchor(h);
  for(const a of this.anchors)if(!a.touched){a.key=undefined;a.node.active=false;}
  this.cues=this.cues.filter(c=>c.until>this.now);
  for(const c of this.cues){
   const target=c.targetId==='player'?s.player:s.enemies.find(e=>e.id===c.targetId&&e.hp>0),p=target??c.at,alpha=Math.round(170*(c.until-this.now)/c.duration);
   if(c.kind==='contact')for(const side of [-1,1])this.stroke([local(p,c.angle,side*.05,0),local(p,c.angle,side*.22,.08)],LOCK,.018,alpha,.8);
   else for(const side of [-1,1])this.stroke([local(p,c.angle,side*.22,-.05),local(p,c.angle,side*.22,.13)],ACTIVE,.019,Math.max(45,alpha),.85);
  }
  if((s.combat.buffs.enemyBurnUntil??0)>this.now)this.host.loop('enemy:playerBurn','ember',s.player,.18,.25);
  if((s.combat.buffs.enemySlowUntil??0)>this.now)for(const side of [-1,1])this.stroke([local(s.player,s.player.angle,side*.16,-.1),local(s.player,s.player.angle,side*.16,.1)],LOCK,.018,120,.08);
  for(const [id,path]of this.paths)if(this.now-path.time>.3)this.paths.delete(id);
 }
 inspect(){return{attackerLimit:0,geometryLimit:0,attackers:[],geometryCount:0,reducedMotion:this.reducedMotion};}
 clear(){this.cues=[];this.paths.clear();for(const a of this.anchors){a.node.active=false;a.key=undefined;}this.seen.clear();}
 destroy(){this.clear();for(const a of this.anchors)a.node.destroy();this.anchors=[];}
}
