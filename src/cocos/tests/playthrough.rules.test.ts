import {CAMPAIGN_EVENTS} from '../assets/scripts/features/campaign/data/CampaignEvents';
import {campaignExperienceSources,campaignExperienceQuote} from '../assets/scripts/features/progression/data/CampaignExperience';
import {CAMPAIGN_STAGES,campaignStageKey} from '../assets/scripts/features/journey/data/CampaignStages';
import {materialStock} from '../assets/scripts/features/crafting/common/CultivationRewards';
import {forgingLevelCap} from '../assets/scripts/features/crafting/data/EquipmentForging';
import {gemTierForLevel,gemSocketCapForLevel} from '../assets/scripts/features/gems/data/Gems';
import test from 'node:test';
import assert from 'node:assert/strict';
import {GameSession,type EnemyState} from '../assets/scripts/core/GameSession';
import {SaveStore,type KeyValueStore} from '../assets/scripts/features/persistence/common/SaveStore';
import {AREAS} from '../assets/scripts/features/world/data/WorldData';
import {Navigation} from '../assets/scripts/features/navigation/runtime/Navigation';
import {awardXp,cumulativeXp,baseMaxHp} from '../assets/scripts/features/progression/common/Progression';
import {COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import {EQUIPMENT,MERCHANTS,equipmentPowerMultiplier} from '../assets/scripts/features/equipment/data/Equipment';
import {mkdirSync,writeFileSync} from 'node:fs';
import {BUILD_PROFILE} from '../assets/scripts/shared/BuildProfile';
import {Automation} from '../assets/scripts/features/automation/common/Automation';
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
 saveRestore(){GameSession.restore(this.game.snapshot(),this.query);const memory=new Map<string,string>(),store:KeyValueStore={getItem:k=>memory.get(k)??null,setItem:(k,v)=>{memory.set(k,v);}};const saves=new SaveStore(store);assert.ok(saves.write(this.game).ok);const loaded=new SaveStore(store).load(this.query);assert.ok(loaded.session);this.game=loaded.session;this.game.enter(this.current,{x:this.game.state.player.x,z:this.game.state.player.z});}
}

function chapter(variant:'accept'|'copy'|'independent',build:Build='staff'){
 const p=new Pilot(73013,build);
 // Dialogue/build regression uses explicit preparation; natural pacing is exercised separately below.
 awardXp(p.game.state.progression,'fixture:command-route-preparation',cumulativeXp(10));
 const fixture=p.game.state.progression,attribute=build==='sword'?'strength':build==='bow'?'dexterity':'intellect';fixture.attributes[attribute]+=18;fixture.attributes.vitality+=9;fixture.unspentPoints=0;
 p.game.state.player.maxHp=baseMaxHp(fixture);p.game.state.player.hp=p.game.state.player.maxHp;
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

test('natural first chapter combines tasks and physical exploration before its boss without fixture experience',()=>{
 assert.equal(BUILD_PROFILE.name,'test');assert.equal(BUILD_PROFILE.monsterExperienceMultiplier,1);
 const p=new Pilot(73013,'staff'),milestones:Record<string,unknown>[]=[];
 const stageMilestones:Record<string,unknown>[]=[],observedStages=new Set<string>();
 const cultivationView=()=>({forgingEnhancements:p.game.state.forging.transactions.filter(transaction=>transaction.kind==='enhance').length,stoneSyntheses:p.game.state.forging.cultivation?.syntheses.length??0,gemTransactions:p.game.state.gems.transactions.length,harvestKills:Object.values(p.game.state.forging.cultivation?.harvests??{}).reduce((n,harvest)=>n+harvest.count,0),taskGifts:p.game.state.forging.cultivation?.tasks.length??0,stones:Object.fromEntries([1,2,3,4,5].map(tier=>[tier,materialStock(p.game.state,tier)])),gemBank:{...p.game.state.gems.bank},gemBankUnits:Object.values(p.game.state.gems.bank).reduce((n,units)=>n+units,0),shards:p.game.state.gems.shards,drills:p.game.state.gems.drills});
 const observeStages=()=>{
  const s=p.game.state;
  for(const stage of CAMPAIGN_STAGES.filter(stage=>stage.chapter===1)){
   const source=campaignStageKey(stage.id);if(observedStages.has(source)||s.receipts[source]!==true)continue;
   observedStages.add(source);
   stageMilestones.push({id:stage.id,source,name:stage.name,targetTotalXp:stage.targetTotalXp,time:s.time,level:s.progression.level,xp:s.progression.totalXp,mainXp:Object.entries(s.progression.xpReceipts).reduce((n,[id,amount])=>n+(campaignExperienceQuote(id).category==='main'?amount:0),0),stageXp:s.progression.xpReceipts[source]??0,unlocks:{forgingRank:forgingLevelCap(s.progression.level),gemTier:gemTierForLevel(s.progression.level),sockets:gemSocketCapForLevel(s.progression.level)},cultivation:cultivationView()});
  }
 };
 // Observation only: inputs, route and world time remain identical. Immediate
 // interactions are observed on the next normal50ms step or the final sample.
 const originalStep=p.step.bind(p);p.step=(input:InputFrame)=>{originalStep(input);observeStages();};
 const combat=new Automation() as unknown as {evade(g:GameSession,w:WorldQuery):{input:InputFrame}|null;fight(g:GameSession,w:WorldQuery,dt:number,scope:'clear'):{input:InputFrame}|null};
 p.fight=(target:EnemyState)=>{
  p.combat=true;
  for(let n=0;target.hp>0&&n<16000;n++){
   const s=p.game.state;if(!s.action&&s.player.hp/s.player.maxHp<=.45&&s.player.healthPotions>0&&!(s.cooldowns.consumable>0))p.game.useConsumable('health');
   const frame=combat.evade(p.game,p.query)??combat.fight(p.game,p.query,.05,'clear');p.step(frame?.input??{x:0,z:0});
  }
  assert.equal(target.hp,0,target.id);p.combat=false;p.game.cancelInput();
 };
 const record=(step:string)=>milestones.push({step,level:p.game.state.progression.level,xp:p.game.state.progression.totalXp,time:p.game.state.time,hp:p.game.state.player.hp,equipment:{...p.game.state.equipment},potions:p.game.state.player.healthPotions,gold:p.game.state.player.gold,iron:p.game.state.player.iron,runes:p.game.state.player.runes});
 const clearBattle=()=>{for(let wave=0;wave<8;wave++){p.clear();if(p.game.campaign.battleReady())return;for(let i=0;i<30;i++)p.step({x:0,z:0});}assert.fail('campaign waves did not complete');};
 const task=(id:string)=>{const object=p.current.objects.find(o=>o.action==='journey_task'&&o.eventId===id);assert.ok(object,id);p.walk(object);p.game.interact(object);assert.equal(p.game.state.receipts['journey:task:'+id],true,id);record(id);};
 const prepare=()=>{
  p.go('S04');p.walk(p.current.objects.find(o=>o.action==='checkpoint')!);
  for(let i=0;i<600&&!p.game.preparationAvailability().available;i++){
   const threat=p.game.state.enemies.filter(e=>e.hp>0&&distance(e,p.game.state.player)<16&&p.query.visible(e,p.game.state.player)).sort((a,b)=>distance(a,p.game.state.player)-distance(b,p.game.state.player))[0];
   if(threat)p.fight(threat);else p.step({x:0,z:0});
  }
  p.interact('checkpoint');
  const game=p.game,s=game.state,points=3*(s.progression.level-1),offence=Math.floor(points*2/3);
  assert.ok(game.applyAttributePlan({strength:10,dexterity:10,intellect:10+offence,vitality:10+points-offence},game.attributePlanToken()),JSON.stringify({access:game.preparationAvailability(),player:s.player,action:s.action,area:s.area,engagement:s.combat.engagement,enemies:s.enemies.filter(e=>e.hp>0).map(e=>({id:e.id,phase:e.phase,distance:distance(e,s.player)}))}));
  const plan={...s.progression.learned};let remaining=s.progression.level-1+(s.progression.secondChapter?2:0);
  for(const id of Object.keys(plan))if(plan[id])plan[id]=1;
  for(const id of ['FIR_01','FIR_03','FIR_P1','FIR_02'])if(plan[id])while(plan[id]<5&&remaining>=plan[id]){remaining-=plan[id];plan[id]++;}
  assert.ok(game.applySkillPlan(plan));
  const owned=Object.keys(s.inventory).map(id=>EQUIPMENT[id]).filter(d=>d&&(d.requiredLevel??1)<=s.progression.level);
  const weapon=owned.filter(d=>d.kind==='staff').sort((a,b)=>equipmentPowerMultiplier(b.id,s.progression.level)-equipmentPowerMultiplier(a.id,s.progression.level))[0];
  assert.ok(weapon);assert.ok(game.equip(weapon.id));
  for(const slot of ['head','chest','hands','feet','ringLeft','ringRight','necklace'] as const){const item=owned.filter(d=>d.slot===slot||slot==='ringRight'&&d.slot==='ringLeft').sort((a,b)=>(b.armor??0)-(a.armor??0)||(b.maxHp??0)-(a.maxHp??0))[0];if(item)game.equip(item.id,slot);}
  record('checkpoint-preparation');
  if(s.progression.level>=6&&!s.gems.transactions.some(t=>t.kind==='purchase')){
   p.go('S01');const merchant=p.current.objects.find(o=>o.merchant==='jeweler')!;p.walk(merchant);assert.ok(p.game.interact(merchant).some(e=>e.type==='shop'));
   const quote=p.game.trading.quote('jeweler','GEM_power_1');assert.ok(quote.allowed,quote.reason);assert.equal(quote.total,240);
   const purse=p.game.state.player.gold;assert.ok(p.game.trading.buy('jeweler','GEM_power_1',1,quote.token));assert.equal(p.game.state.player.gold,purse-240);
   const current=p.game.state.equipment.weapon,inlay=p.game.gems.inset(current,0,'power',1);assert.ok(inlay.allowed,inlay.reason);assert.ok(p.game.gems.inlay(current,0,'power',1,inlay.token));
   p.saveRestore();record('merchant-gem-preparation');p.go('S04');
  }
 };
 const event=(id:string)=>{
  const def=CAMPAIGN_EVENTS[id];assert.ok(def,id);p.go(def.area);p.step({x:0,z:0});
  // Domain pilot chooses the authored safe option explicitly; automation never solves it.
  const object=p.current.objects.find(object=>object.action==='campaign_event'&&object.eventId===id)!;assert.ok(object,id);
  for(const enemyId of def.defeatIds??[]){const enemy=p.game.state.enemies.find(enemy=>enemy.id===enemyId);if(enemy&&enemy.hp>0)p.fight(enemy);}
  p.walk(object);assert.ok(p.game.interactionAvailability(object).available,p.game.interactionAvailability(object).reason);p.game.interact(object);
  if(p.game.state.dialogue){const option=def.choices?.find(choice=>!choice.retry);assert.ok(option,id);p.game.choose(option.id);}
  p.step({x:0,z:0});assert.equal(p.game.state.receipts['campaign:'+id],true,id);
 };
 assert.equal(p.game.state.progression.level,1);p.go('S01-T1');p.prepare();p.interact('offer');p.game.choose('accept');
 p.go('S02');task('border-traces');event('c1-warning');
 p.go('S04');prepare();clearBattle();p.interact('recover');p.interact('letter');p.game.choose('read_letter');prepare();
 p.go('S07');clearBattle();task('border-mill');event('c1-mill-rescue');prepare();
 p.go('S08');for(let i=0;Number(p.game.state.receipts['journey:hunt:S08']??0)<6&&i<12;i++){
  const target=p.game.state.enemies.filter(e=>e.hp>0&&!!e.respawnSeconds).sort((a,b)=>distance(a,p.game.state.player)-distance(b,p.game.state.player))[0];assert.ok(target);p.fight(target);
 }
 assert.ok(Number(p.game.state.receipts['journey:hunt:S08']??0)>=6);task('border-hunt');event('c1-herd-crossing');
 p.go('S09');clearBattle();task('border-camp');event('c1-detention-roll');prepare();
 p.go('U1-03');clearBattle();task('border-watch');event('c1-old-sentinel');
 p.go('U1-04');p.interact('meeting');p.game.choose('cooperate');event('c1-table-truth');
 p.go('U1-05');event('c1-cell-route');p.interact('disable_trap');p.interact('release_workers');assert.ok(p.game.state.flags.workers_released);event('c1-exit-anchor');event('c1-exit-test');p.go('U1-04');
 const exploreUntil=(targetLevel:number)=>{
  for(let pass=0;pass<3&&p.game.state.progression.level<targetLevel;pass++){
   let completed=0;
   for(const source of campaignExperienceSources(1).filter(source=>source.category==='exploration'&&source.objectId)){
    const g=p.game,st=g.state;if(st.progression.level>=targetLevel)break;
    if(st.progression.xpReceipts[source.source]!==undefined||!source.area||source.area==='S10'&&!st.flags.captain_defeated)continue;
    const queue=[p.current.id],seen=new Set<string>();while(queue.length){const at=queue.shift()!;if(seen.has(at))continue;seen.add(at);for(const exit of AREAS[at].exits)if((!exit.requires||st.flags[exit.requires])&&(!exit.requiredLevel||st.progression.level>=exit.requiredLevel))queue.push(exit.to);}
    if(!seen.has(source.area))continue;
    const object=AREAS[source.area].objects.find(object=>object.id===source.objectId);if(!object)continue;
    if(object.action==='campaign_event'&&!g.campaignEventAvailability(object.eventId!,true).available)continue;
    p.go(source.area);p.walk(object);
    if(!g.interactionAvailability(object).available)continue;
    g.interact(object);
    if(g.state.dialogue?.id.startsWith('campaign:')){const option=g.state.dialogue.options.find(option=>!option.id.startsWith('cancel:'));if(option)g.choose(option.id);}
    if(g.state.progression.xpReceipts[source.source]!==undefined)completed++;
   }
   record('physical-exploration-'+pass);if(!completed)break;prepare();
  }
 };
 exploreUntil(10);prepare();assert.ok(p.game.state.progression.level>=10,'tasks plus real exploration must support boss preparation');record('before-S10');
 p.go('S10');clearBattle();assert.ok(p.game.state.flags.captain_defeated);p.interact('captain_gate');
 event('c1-town-return');event('c1-renewed-oath');p.go('U1-04');p.interact('finish');assert.ok(p.game.state.flags.chapter1_complete);assert.ok(p.game.state.progression.level>=11,'the complete main route reaches chapter-two entry without repeat grinding');record('chapter-complete');
 assert.ok(Object.keys(p.game.state.progression.xpReceipts).every(id=>!/^fixture:|^balance-|^local-playtest/.test(id)));
 p.saveRestore();
 const taskWeapon='LC1_T_E_FIR',taskSource='journey:equipment:border-mill:LC1_T_E';
 assert.equal(p.game.state.inventory[taskWeapon],1);assert.equal(p.game.state.provenance[taskWeapon],taskSource);
 assert.equal(p.game.state.receipts[taskSource],taskWeapon);assert.equal(p.game.state.equipment.weapon,taskWeapon);
 assert.ok(Object.values(p.game.state.provenance).every(source=>!source.startsWith('craft:')));
 const equipmentRewards=Object.entries(p.game.state.provenance).filter(([,source])=>source.startsWith('journey:equipment:')||source.startsWith('boss:fixed:')).map(([item,source])=>({item,source}));
 mkdirSync('test-results',{recursive:true});
 observeStages();
 writeFileSync('test-results/campaign-pacing-natural-first-chapter.json',JSON.stringify({buildProfile:BUILD_PROFILE,scope:'Real level-one GameSession/Pilot movement, production Automation combat, twelve v2 main stages, five preserved journey receipts, physical investigations and rescues, at least six native hunting kills and boss; only actual checkpoints/consumables, native task/Boss/loot equipment and one merchant-bought/inlaid tier-I gem. No fixture currency, experience, injected healing or equipment grants.',stageObservationResolutionSeconds:.05,stageMilestones,cultivation:cultivationView(),gems:p.game.state.gems,milestones,equipmentRewards,xpReceipts:p.game.state.progression.xpReceipts,inventory:p.game.state.inventory,equipment:p.game.state.equipment,combatActions:p.combatActions},null,2));
});

test('three real merchant anchors admit safe discovered trade without remote purchases',()=>{const p=new Pilot(1);p.game.state.player.gold=1000;p.go('S01-T1');p.interact('offer');p.game.choose('accept');p.interact('offer');assert.ok(p.game.choose('shop').some(e=>e.type==='shop'));assert.ok(p.game.buy('mira','J03'));
 p.go('S01-T3');p.interact('merchant');assert.ok(p.game.buy('lorn','A13'));p.go('S05');p.interact('merchant');assert.ok(p.game.state.discoveredMerchants.includes('nightqi'));const gold=p.game.state.player.gold,canAfford=gold>=MERCHANTS.nightqi.prices.A10;assert.equal(p.game.buy('nightqi','A10'),canAfford); // More hunting kills can now pay for this purchase.
 assert.equal(p.game.state.player.gold,gold-(canAfford?MERCHANTS.nightqi.prices.A10:0));const before=p.game.state.player.gold;p.walk({x:0,z:-12});assert.equal(p.game.buy('nightqi','A10'),false);assert.ok(p.game.state.player.gold>=before);
});
