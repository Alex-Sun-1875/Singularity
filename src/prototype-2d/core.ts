import {GameSession, type GameState} from '../cocos/assets/scripts/core/GameSession';
import type {AreaDef, GameEvent, InputFrame, InteractionDef, Point, WorldQuery} from '../cocos/assets/scripts/core/Contracts';
import {EQUIPMENT} from '../cocos/assets/scripts/data/Equipment';
import {Navigation} from '../cocos/assets/scripts/runtime/Navigation';

export {EQUIPMENT};
export type {AreaDef, GameEvent, InputFrame, InteractionDef, Point};

/** This isolated visual trial is not the first chapter or its completion state. */
export const DEMO_STORAGE_KEY = 'sword-fire:prototype-2d:entrance-trial:v1';
const SAVE_KIND = 'sword-fire-2d-entrance-fixture';
const DEMO_SEED = 73013;
const REWARD_RECEIPT = 'design_find_t02';

export const DEMO_AREA:AreaDef = {
 id:'S02', name:'白枝地下入口 · 2D样片', subtitle:'独立小场景 · 击退两名守军，打开东侧遗物匣',
 kind:'underground', palette:'cave', width:24, depth:16,
 spawn:{x:-7,z:-3}, atlas:{x:0,z:0}, checkpoint:true, exits:[], buildings:[],
 objects:[
  {id:'demo-camp',label:'入口营火 · 休整/换装',action:'checkpoint',description:'这是独立样片检查点；可在这里更换剑、弓或杖。',x:-7,z:-3},
  {id:'demo-mira',label:'弥菈',actor:'mira',action:'inspect',description:'“先清掉守在入口的两个人，再去取东侧的匣子。这里是2D玩法样片，完整地下城还在后面。”',x:-7,z:-1},
  {id:'demo-cache',label:'打开遗物匣',action:'cache',description:'击败本场两名敌人后领取黑契封印，结束这次样片。',item:'T02',amount:3,x:8,z:4},
 ],
 obstacles:[
  {kind:'column',x:-1,z:3,width:1.2,depth:1.2,height:2.8},
  {kind:'column',x:-1,z:-3,width:1.2,depth:1.2,height:2.8},
  {kind:'column',x:5,z:-3,width:1.2,depth:1.2,height:2.8},
  {kind:'wall',x:-12.25,z:0,width:.5,depth:16.5,height:2.8},
  {kind:'wall',x:12.25,z:0,width:.5,depth:16.5,height:2.8},
  {kind:'wall',x:0,z:-8.25,width:24,depth:.5,height:2.8},
  {kind:'wall',x:0,z:8.25,width:24,depth:.5,height:2.8},
 ],
 enemies:[
  {id:'demo-raider',kind:'raider',x:2,z:0},
  {id:'demo-archer',kind:'archer',x:6,z:2},
 ],
};

/** Structural type also permits a tiny in-memory storage in manual Node checks. */
export interface DemoStorage { getItem(key:string):string|null; setItem(key:string,value:string):void }
export interface DemoInspection {
 fixture:true; demoArea:true; scope:string; area:string;
 status:'playing'|'dead'|'complete'; completed:boolean; objective:string;
 enemiesRemaining:number; nearby:InteractionDef|null;
 weapon:string; canEquip:boolean; equipmentReason:string;
 player:GameState['player']; enemies:GameState['enemies'];
 storageKey:string; storageAvailable:boolean; hasSave:boolean;
}
export interface DemoBridge {
 game:GameSession;
 readonly area:AreaDef;
 readonly completed:boolean;
 advance(dt:number,input:InputFrame):GameEvent[];
 interact():GameEvent[];
 restart():GameEvent[];
 equip(id:string):boolean;
 save():boolean;
 load():boolean;
 nearby():InteractionDef|null;
 inspect():DemoInspection;
}

function browserStorage():DemoStorage|undefined {
 try{return (globalThis as typeof globalThis&{localStorage?:DemoStorage}).localStorage;}
 catch{return undefined;}
}

/** Reuse the game's Navigation footprints/pathfinding and its existing .15m
 * axis-slide integration from SceneBuilder; no rendering/physics dependency. */
function worldFor(area:AreaDef):WorldQuery {
 const navigation = new Navigation(area.width,area.depth,area.obstacles);
 return {
  height:()=>0,
  visible:(a,b)=>navigation.visible(a,b),
  path:(a,b)=>navigation.path(a,b),
  move:(from,delta,radius)=>{
   const steps=Math.max(1,Math.ceil(Math.hypot(delta.x,delta.z)/.15)),p={...from};
   for(let i=0;i<steps;i++){
    const x=p.x+delta.x/steps,z=p.z+delta.z/steps;
    if(!navigation.blocked({x,z:p.z},radius))p.x=x;
    if(!navigation.blocked({x:p.x,z},radius))p.z=z;
   }
   return p;
  },
 };
}

export function createDemo(storage:DemoStorage|undefined=browserStorage()):DemoBridge {
 const area:AreaDef=JSON.parse(JSON.stringify(DEMO_AREA));
 const world=worldFor(area);
 let hasSave=false;
 try{hasSave=!!storage?.getItem(DEMO_STORAGE_KEY);}catch{}
 const fresh=()=>{const game=new GameSession(DEMO_SEED,world);game.enter(area);return game;};
 const notice=(text:string):GameEvent[]=>[{type:'notice',text}];
 const bridge:DemoBridge={
  game:fresh(),area,
  get completed(){return !!bridge.game.state.receipts[REWARD_RECEIPT]&&bridge.game.state.enemies.every(e=>e.hp<=0);},
  advance(dt,input){return bridge.game.advance(dt,input);},
  nearby(){
   const p=bridge.game.state.player;
   return area.objects.filter(o=>Math.hypot(o.x-p.x,o.z-p.z)<=Math.min(1.35,o.radius??1.35)&&world.visible(p,o))
    .sort((a,b)=>Math.hypot(a.x-p.x,a.z-p.z)-Math.hypot(b.x-p.x,b.z-p.z))[0]??null;
  },
  interact(){
   const object=bridge.nearby();
   if(!object)return notice('靠近弥菈、入口营火或东侧遗物匣后交互');
   if(object.id==='demo-cache'&&bridge.game.state.enemies.some(e=>e.hp>0))return notice('先击退本场的两名守军，再打开遗物匣');
   const wasComplete=bridge.completed,events=bridge.game.interact(object);
   if(!wasComplete&&bridge.completed)events.push({type:'demo_complete',id:'demo-cache',text:'2D样片完成 · 已领取黑契封印。这不是完整首章通关。'});
   else if(wasComplete&&object.id==='demo-cache')events.push({type:'notice',text:'遗物匣已领取 · 这次2D样片已经完成'});
   return events;
  },
  restart(){bridge.game=fresh();return [{type:'area',id:area.id,text:area.name},{type:'notice',text:'样片已重新开始；剑、弓、杖可在入口营火切换'}];},
  equip(id){return bridge.game.equip(id);},
  save(){
   if(!storage)return false;
   try{
    storage.setItem(DEMO_STORAGE_KEY,JSON.stringify({kind:SAVE_KIND,version:1,demoArea:true,state:bridge.game.snapshot()}));
    hasSave=true;bridge.game.dirty=false;return true;
   }catch{return false;}
  },
  load(){
   if(!storage)return false;
   try{
    const raw=storage.getItem(DEMO_STORAGE_KEY);if(!raw)return false;
    const saved=JSON.parse(raw);
    if(saved.kind!==SAVE_KIND||saved.version!==1||saved.demoArea!==true||saved.state?.area!==area.id)return false;
    const restored=GameSession.restore(saved.state,world),s=restored.state;
    // Keep this slot isolated even if a valid full-game snapshot is pasted in.
    if(s.flags.complete||s.status==='complete'||s.checkpoint.area!==area.id||s.enemies.length!==area.enemies.length||
     s.enemies.some(e=>!area.enemies.some(def=>def.id===e.id&&def.kind===e.kind))||
     Object.keys(s.encounters).some(id=>id!==area.id)||!world.visible(s.player,s.player)||
     Math.abs(s.player.x)>area.width/2||Math.abs(s.player.z)>area.depth/2)return false;
    const checkpoint={...s.checkpoint};
    restored.enter(area,{x:s.player.x,z:s.player.z});
    // enter() establishes area bindings; loading must retain the saved camp.
    restored.state.checkpoint=checkpoint;restored.dirty=false;
    bridge.game=restored;hasSave=true;return true;
   }catch{return false;}
  },
  inspect(){
   const s=bridge.game.state,availability=bridge.game.equipmentAvailability(),enemiesRemaining=s.enemies.filter(e=>e.hp>0).length;
   return {
    fixture:true,demoArea:true,scope:'独立2D入口玩法样片；不代表完整首章通关',area:area.id,
    status:bridge.completed?'complete':s.status,completed:bridge.completed,
    objective:bridge.completed?'样片完成 · 已领取黑契封印':s.status==='dead'?'试炼失败 · 重新开始':enemiesRemaining?`击退入口守军 ${2-enemiesRemaining}/2`:'前往东侧遗物匣领取样片奖励',
    enemiesRemaining,nearby:bridge.nearby(),weapon:s.equipment.weapon,
    canEquip:availability.available,equipmentReason:availability.reason,
    player:{...s.player},enemies:s.enemies.map(e=>({...e})),
    storageKey:DEMO_STORAGE_KEY,storageAvailable:!!storage,hasSave,
   };
  },
 };
 return bridge;
}
