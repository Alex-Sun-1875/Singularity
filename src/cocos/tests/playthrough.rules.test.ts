import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession,type EnemyState} from '../assets/scripts/core/GameSession';
import {SaveStore,type KeyValueStore} from '../assets/scripts/features/persistence/common/SaveStore';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {Navigation} from '../assets/scripts/features/navigation/runtime/Navigation';
import {awardXp,cumulativeXp,baseMaxHp} from '../assets/scripts/features/progression/common/Progression';
import {COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import type {InputFrame,Point,WorldQuery} from '../assets/scripts/core/Contracts';
const distance=(a:Point,b:Point)=>Math.hypot(a.x-b.x,a.z-b.z);
type Build='staff'|'sword'|'bow'|'spell';

/** The pilot only issues the same movement, attack and interaction commands as the runtime. */
class Pilot {
 current=AREAS.S01;nav=new Navigation(this.current.width,this.current.depth,this.current.obstacles);game:GameSession;
 combat=false;combatActions:Record<string,number>={};
 query:WorldQuery={move:(p,d,r)=>{r=Math.max(r,.42);const result={...p},steps=Math.max(1,Math.ceil(Math.hypot(d.x,d.z)/.1));for(let i=0;i<steps;i++){if(!this.nav.blocked({x:result.x+d.x/steps,z:result.z},r))result.x+=d.x/steps;if(!this.nav.blocked({x:result.x,z:result.z+d.z/steps},r))result.z+=d.z/steps;}return result;},visible:(a,b)=>this.nav.visible(a,b),height:()=>0,path:(a,b)=>this.nav.path(a,b)};
 constructor(seed:number,readonly build:Build='staff'){this.game=new GameSession(seed,this.query);this.game.enter(this.current);if(build==='staff')assert.ok(this.game.equip('W11'));}
 step(input:InputFrame){const events=this.game.advance(.05,input);if(this.combat)for(const e of events){const key=e.type==='action'?e.kind==='staff'?'':String(e.kind):e.type==='projectile'?String(e.kind):e.type==='skill_release'?String(e.skillId):e.type==='hurt'?'hurt':'';if(key)this.combatActions[key]=(this.combatActions[key]??0)+1;}assert.notEqual(this.game.state.status,'dead',`${this.build} ${this.current.id} pilot died: ${JSON.stringify(this.game.state.enemies)}`);}
 prepare(){assert.equal(this.current.id,'S01-T1');assert.ok(this.game.equip(this.build==='sword'?'W01':this.build==='bow'?'W07':'W11'));}
 vector(target:Point){const p=this.game.state.player,d=distance(p,target),scale=Math.min(1,d/.18);return d>.01?{x:(target.x-p.x)/d*scale,z:(target.z-p.z)/d*scale}:{x:0,z:0};}
 approach(target:Point){const p=this.game.state.player,route=this.nav.path(p,target);assert.ok(route.length,`no path ${this.current.id} ${JSON.stringify(p)} -> ${JSON.stringify(target)}`);let next=route[1]??target;for(let i=2;i<route.length;i++){if(!this.nav.visible(p,route[i],.42))break;next=route[i];}return this.vector(next);}
 fight(e:EnemyState){
  this.combat=true;
  for(let n=0;e.hp>0&&n<16000;n++){
   const p=this.game.state.player,d=distance(p,e),angle=Math.atan2(e.x-p.x,e.z-p.z);let movement={x:0,z:0};
   const closeCombat=this.build==='sword',danger=closeCombat&&['windup','active'].includes(e.phase);
   if(!this.nav.visible(p,e)||(!danger&&d>(closeCombat?1.35:6.2)))movement=this.approach(e);
   else if(danger||!closeCombat&&(d<4.5||e.kind==='captain'&&(e.attackKind==='charge'&&['windup','active'].includes(e.phase)))){
    let best=-Infinity,target:Point|null=null;
    for(let k=0;k<24;k++){const a=k*Math.PI/12,q={x:p.x+Math.sin(a)*1.6,z:p.z+Math.cos(a)*1.6};if(!this.nav.visible(p,q,.42))continue;const closest=Math.min(...this.game.state.enemies.filter(e=>e.hp>0).map(e=>distance(q,e)));let score=closest-Math.abs(distance(q,e)-5)*.25;
     if(e.kind==='captain'&&e.attackKind==='charge')score+=Math.abs(Math.sin(a-e.targetAngle))*2;
     if(score>best){best=score;target=q;}}
    if(target)movement=this.vector(target);
   }
   const state=this.game.state,needsStaff=(this.build==='staff'||this.build==='spell')&&!(this.combatActions.staff>0);
   if(!state.action&&p.hp/p.maxHp<.45&&p.healthPotions>0&&!(state.cooldowns.consumable>0))this.game.useConsumable('health');
   const views=this.game.combatSkillView(),ready=(id:string|null)=>id?views.find(v=>v.id===id)?.ready:false;
   let attack=!closeCombat||!danger&&d<1.65,combatSlot:0|1|2|3|undefined,ultimate=false;
   // Slot input is a press pulse. Between ready skills keep issuing normal
   // attacks; holding a cooling/rejected slot must not suppress basic attacks.
   if(!needsStaff&&!state.action&&n%2===0){
    if(p.hp/p.maxHp<.65&&ready('COM_02')&&!(state.combat.buffs.healCount>0))this.game.castSkill('COM_02');
    const support=state.combat.activeSlots[2],supportDef=support&&COMBAT_SKILLS[support];
    if(!state.action&&supportDef&&!supportDef.offensive&&ready(support)&&p.shield<p.maxHp*.08&&d<6)combatSlot=2;
    if(!state.action&&combatSlot===undefined&&(!closeCombat||!danger&&d<2.4)){
     const nearby=state.enemies.filter(enemy=>enemy.hp>0&&distance(enemy,e)<3.5).length;
     if(nearby>=3&&ready(state.combat.ultimate))ultimate=true;
     else for(const slot of nearby>1?[3,0,1]:[0,1,3]){
      const id=state.combat.activeSlots[slot],view=views.find(v=>v.id===id);
      if(id&&COMBAT_SKILLS[id].offensive&&view?.ready&&d<=view.range+.3){combatSlot=slot as 0|1|2|3;break;}
     }
    }
    if(combatSlot!==undefined||ultimate)attack=false;
   }
   if(this.build==='bow'&&combatSlot===undefined&&!ultimate){const a=state.action;attack=!a||a.kind==='bowAim'&&a.elapsed<.82;}
   const dash=danger&&!state.action&&ready('COM_01')&&(movement.x!==0||movement.z!==0);
   this.step({...movement,aim:angle,attack,combatSlot,ultimate,dash,target:{x:e.x,z:e.z}});
  }
  assert.equal(e.hp,0,`${this.current.id} failed to defeat ${JSON.stringify(e)} player${JSON.stringify(this.game.state.player)} action${JSON.stringify(this.game.state.action)} projectiles${JSON.stringify(this.game.state.projectiles)}`);
  this.combat=false;
 }
 walk(target:Point){
  let route=this.nav.path(this.game.state.player,target).slice(1);
  for(let n=0;distance(this.game.state.player,target)>.7&&n<12000;n++){
   const threat=this.game.state.enemies.filter(e=>e.hp>0&&distance(e,this.game.state.player)<6.8).sort((a,b)=>distance(a,this.game.state.player)-distance(b,this.game.state.player))[0];
   if(threat){this.fight(threat);route=this.nav.path(this.game.state.player,target).slice(1);continue;}
   while(route.length&&distance(this.game.state.player,route[0])<.16)route.shift();
   this.step({...route.length?this.vector(route[0]):this.approach(target)});
  }
  assert.ok(distance(this.game.state.player,target)<=.7,`walk timeout ${this.current.id} at${JSON.stringify(this.game.state.player)} to${JSON.stringify(target)} route${JSON.stringify(route)}`);this.game.cancelInput();
 }
 interact(action:string){const o=this.current.objects.find(o=>o.action===action);assert.ok(o,`${this.current.id} missing ${action}`);this.walk(o);return this.game.interact(o);}
 clear(){while(this.game.state.enemies.some(e=>e.hp>0&&!e.respawnSeconds)){const target=this.game.state.enemies.filter(e=>e.hp>0&&!e.respawnSeconds).sort((a,b)=>distance(a,this.game.state.player)-distance(b,this.game.state.player))[0];this.fight(target);}this.game.cancelInput();}
 go(id:string){
  const queue:[string,string[]][]=[[this.current.id,[]]],seen=new Set<string>();let path:string[]|undefined;
  while(queue.length){const [at,route]=queue.shift()!;if(at===id){path=route;break;}if(seen.has(at))continue;seen.add(at);for(const exit of AREAS[at].exits)if(!exit.requires||this.game.state.flags[exit.requires])queue.push([exit.to,[...route,exit.id]]);}
  assert.ok(path,`no open route ${this.current.id}->${id}`);
  for(const exitId of path){const exit=this.current.exits.find(e=>e.id===exitId)!;this.walk(exit);const events=this.game.travel(exit);assert.ok(events.some(e=>e.type==='travel'),`travel failed ${exitId}`);this.current=AREAS[exit.to];this.nav=new Navigation(this.current.width,this.current.depth,this.current.obstacles);this.game.enter(this.current,exit.entry);}
 }
 saveRestore(){const memory=new Map<string,string>(),store:KeyValueStore={getItem:k=>memory.get(k)??null,setItem:(k,v)=>{memory.set(k,v);}};const saves=new SaveStore(store);assert.ok(saves.write(this.game).ok);const loaded=new SaveStore(store).load(this.query);assert.ok(loaded.session);this.game=loaded.session;this.game.enter(this.current,{x:this.game.state.player.x,z:this.game.state.player.z});}
}

function chapter(variant:'accept'|'copy'|'independent',build:Build='staff'){
 const p=new Pilot(73013,build);
 p.go('S01-T1');p.prepare();p.interact('offer');
 if(variant==='copy'){p.game.choose('ask_letter');assert.ok(p.game.state.flags.saw_copy);p.game.choose('accept');}else p.game.choose(variant==='accept'?'accept':'reject');
 if(variant==='independent'){p.go('S01-T2');p.interact('independent_clue');assert.equal(p.game.state.player.gold,0);}
 p.go('S04');p.clear();p.interact('recover');p.interact('letter');p.game.choose('read_letter');assert.ok(p.game.state.flags.read_letter);p.saveRestore();
 // Descend before the captain, proving the underground is not quest-locked.
 p.go('U1-04');p.interact('meeting');if(variant==='copy')assert.match(p.game.state.dialogue!.text,/姓名/);p.game.choose(variant==='independent'?'star_copy':'cooperate');
 p.go('U1-05');p.interact('disable_trap');p.interact('release_workers');assert.ok(p.game.state.flags.workers_released);p.saveRestore();
 // This scripted command route omits the multi-session hunting preparation.
 if(p.game.state.progression.level<10){awardXp(p.game.state.progression,'fixture:captain-preparation',cumulativeXp(10)-p.game.state.progression.totalXp);p.game.state.player.maxHp=baseMaxHp(p.game.state.progression);}
 p.go('S10');p.clear();assert.ok(p.game.state.flags.captain_defeated);assert.equal(p.game.state.inventory.W02,undefined);p.interact('captain_gate');assert.equal(p.game.state.inventory.W02,1);
 p.go('U1-04');p.interact('finish');assert.ok(p.game.state.flags.chapter1_complete);assert.equal(p.game.state.flags.complete,undefined);assert.ok(p.game.state.player.gold>=(variant==='independent'?60:120));assert.equal(!!p.game.state.receipts.design_reward_coin_ch01_obj01,variant!=='independent');p.saveRestore();assert.ok(p.game.state.flags.chapter1_complete);
 if(build==='sword'){assert.equal(p.game.state.inventory.T01,undefined);assert.equal(p.game.state.equipment.weapon,'W01');assert.ok(p.combatActions.WAR_01>0);assert.equal(p.combatActions.push??0,0);}
 if(build==='bow'){assert.ok(p.combatActions.bowAim>0);assert.ok(p.combatActions.arrow>0);assert.equal(p.combatActions.staff??0,0);}
 if(build==='spell'){assert.equal(p.game.state.inventory.T01,undefined);assert.ok(p.combatActions.FIR_01>0);assert.ok(p.combatActions.staff>0);assert.equal(p.combatActions.spell??0,0);}
}
for(const variant of ['accept','copy','independent'] as const)test(`real world command playthrough: ${variant}`,()=>chapter(variant));
for(const build of ['sword','bow','spell'] as const)test(`real world full chapter build: ${build}`,()=>chapter('accept',build));

test('three real merchant anchors admit safe discovered trade without remote purchases',()=>{const p=new Pilot(1);p.go('S01-T1');p.interact('offer');p.game.choose('accept');p.interact('offer');assert.ok(p.game.choose('shop').some(e=>e.type==='shop'));assert.ok(p.game.buy('mira','J03'));
 p.go('S01-T3');p.interact('merchant');assert.ok(p.game.buy('lorn','A13'));p.go('S05');p.interact('merchant');assert.ok(p.game.state.discoveredMerchants.includes('nightqi'));const gold=p.game.state.player.gold,canAfford=gold>=40;assert.equal(p.game.buy('nightqi','A10'),canAfford); // More hunting kills can now pay for this purchase.
 assert.equal(p.game.state.player.gold,gold-(canAfford?40:0));const before=p.game.state.player.gold;p.walk({x:0,z:-12});assert.equal(p.game.buy('nightqi','A10'),false);assert.ok(p.game.state.player.gold>=before);
});
