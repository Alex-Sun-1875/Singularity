/** Offline balance measurements using the production rules, not a second damage formula.
 * Run: npx tsx tools/combat-balance.ts [output.json] [--stationary-thunder]
 */
import {writeFileSync} from 'node:fs';
import {TrainingRange} from '../assets/scripts/features/debug/common/TrainingRange';
import {COMBAT_SKILLS} from '../assets/scripts/features/combat/data/PureSkills';
import {COMBAT_LOADOUTS,prepareCombatLoadout,type CombatFamily} from '../assets/scripts/features/progression/common/CombatLoadouts';
import {skillRankSpent,cumulativeXp,unlockSkills,baseMaxHp} from '../assets/scripts/features/progression/common/Progression';
import {CAMPAIGN_MAX_LEVEL,attributePointBudget,skillPointBudget,combatBudgetLevel} from '../assets/scripts/features/progression/data/CampaignProgression';
import {BUILD_PROFILE} from '../assets/scripts/shared/BuildProfile';
import type {WorldQuery} from '../assets/scripts/core/Contracts';

if(BUILD_PROFILE.noSkillCooldown)throw new Error('Balance requires normal skill cooldowns');
const stationaryThunder=process.argv.includes('--stationary-thunder');
const families=stationaryThunder?['THU'] as CombatFamily[]:Object.keys(COMBAT_LOADOUTS) as CombatFamily[];
const world:WorldQuery={move:(p,d)=>({x:p.x+d.x,z:p.z+d.z}),visible:()=>true,height:()=>0};
const dt=.02,seconds=60,seeds=12;
type Build='entry'|'developed'|'specialized';
type Formation='single'|'cluster'|'line';

function measure(family:CombatFamily,build:Build,formation:Formation,seed:number){
 const range=new TrainingRange(world),game=range.session,s=game.state,p=s.progression,kit=COMBAT_LOADOUTS[family];
 s.seed=seed;range.formation=formation;range.distance=family==='WAR'?1.4:5.5;
 // The dedicated range is a fixture, but its level, attributes and skill plan
 // must still obey the same current campaign budget as a normal character.
 p.level=CAMPAIGN_MAX_LEVEL;p.totalXp=cumulativeXp(p.level);p.xpReceipts={training:p.totalXp};p.ultimateGiftClaimed=true;
 const attributes=attributePointBudget(p.level),share=Math.floor(attributes/4),extra=attributes%4;
 p.attributes={strength:10+share,dexterity:10+share,intellect:10+share,vitality:10+share+extra};p.unspentPoints=0;
 if(Object.values(p.attributes).some(value=>value>80))throw new Error('Shared equal-attribute fixture exceeds a base attribute cap');
 unlockSkills(p,true);s.player.maxHp=baseMaxHp(p);
 // Only the starter weapon's identity/perks differ; no armour, forging or pets.
 s.equipment={weapon:kit.weapon,offhand:null,head:null,chest:null,hands:null,feet:null,ringLeft:null,ringRight:null,necklace:null,spells:[null,null]};
 for(const id of Object.keys(p.learned))p.learned[id]=1;
 if(build!=='entry')for(const id of Object.keys(p.learned)){
  const d=COMBAT_SKILLS[id];if(d.style!==family)continue;
  p.learned[id]=build==='specialized'?1:id===family+'_01'||id===kit.ultimate?5:d.activation==='automatic'?2:id===family+'_P1'?4:3;
 }
 const pointBudget=skillPointBudget(p.level,p.secondChapter),investmentPriority=[family+'_01',kit.ultimate,family+'_P1',kit.activeSlots[1],kit.activeSlots[3],family+'_P2',kit.activeSlots[2],...Object.keys(p.learned).filter(id=>COMBAT_SKILLS[id].style===family&&COMBAT_SKILLS[id].activation==='automatic')];
 let remaining=pointBudget-Object.values(p.learned).reduce((n,r)=>n+skillRankSpent(r),0);
 if(remaining<0)throw new Error(`Over-budget developed fixture for ${family}`);
 if(build==='specialized')for(const id of investmentPriority){if(!id)continue;while(p.learned[id]<5&&remaining>=p.learned[id]){remaining-=p.learned[id];p.learned[id]++;}}
 if(build==='developed')for(const id of [...investmentPriority.slice(2),...investmentPriority]){if(!id||p.learned[id]>=5||remaining<p.learned[id])continue;remaining-=p.learned[id];p.learned[id]++;}
 const spent=Object.values(p.learned).reduce((n,r)=>n+skillRankSpent(r),0);
 if(spent>pointBudget)throw new Error(`Over-budget ${family}: ${spent}`);
 p.skillPoints=pointBudget-spent;
 prepareCombatLoadout(s.combat,kit.weapon,p,family);range.reset();range.unlimitedResource=false;
 for(const enemy of s.enemies)enemy.level=p.level;
 const positions=s.enemies.map(e=>({x:e.x,z:e.z})),origin={x:s.player.x,z:s.player.z};
 const priority=[family+'_01',kit.ultimate,...kit.activeSlots.filter((id):id is string=>!!id&&COMBAT_SKILLS[id].offensive&&id!==family+'_01'&&id!=='BOW_07')];
 const totals:Record<string,number>={},casts:Record<string,number>={};let burst=0,damage=0,minimumResource=s.player.focus;
 for(let step=0;step<seconds/dt;step++){
  // Immovable infinite-life dummies isolate geometry and damage, with a fixed
  // encounter regeneration from production rules, not infinite resources.
  if(!s.action){s.player.x=origin.x;s.player.z=origin.z;}
  s.enemies.forEach((e,i)=>{e.x=positions[i].x;e.z=positions[i].z;});
  s.combat.engagement={area:s.area,enemyIds:s.enemies.filter(e=>e.hp>0).map(e=>e.id)};
  range.prepareFrame();
  // Thunder's real preparation condition is movement, not an unconditional buff.
  if(family==='THU'&&!stationaryThunder)s.player.movingTime=2;
  if(!s.action){
   const ready=game.combatSkillView(priority).find(v=>v.ready);
   if(ready)game.castSkill(ready.id,positions[0],0);
  }
  const action=s.action,bowHold=family==='BOW'&&action?.kind==='bowAim'&&action.elapsed<.10;
  // Short taps use the normal bow press/release path; other weapons hold attack.
  const events=game.advance(dt,{x:0,z:0,aim:0,attack:family==='BOW'?(!action||bowHold):!action});
  minimumResource=Math.min(minimumResource,s.player.focus);
  for(const event of events){
   if(event.type==='skill_release'){const id=String(event.skillId);casts[id]=(casts[id]??0)+1;}
   if(event.type!=='hit')continue;
   const value=Number(event.hpLost??0),id=String(event.skillId??event.source);
   damage+=value;totals[id]=(totals[id]??0)+value;if(s.time<=6+1e-8)burst+=value;
  }
 }
 return {damage,burst,minimumResource,totals,casts,spent,pointBudget,attributes:{...p.attributes},learned:Object.fromEntries(Object.entries(p.learned).filter(([id])=>COMBAT_SKILLS[id].style===family))};
}

const rows=[];
for(const build of ['entry','developed','specialized'] as const)for(const formation of ['single','cluster','line'] as const)for(const family of families){
 const runs=Array.from({length:seeds},(_,i)=>measure(family,build,formation,73014+i*7919));
 const average=(key:'damage'|'burst')=>runs.reduce((n,r)=>n+r[key],0)/runs.length;
 const totals:Record<string,number>={};for(const run of runs)for(const [id,value] of Object.entries(run.totals))totals[id]=(totals[id]??0)+value/runs.length;
 rows.push({build,formation,family,dps:+(average('damage')/seconds).toFixed(2),burst6:+average('burst').toFixed(2),spent:runs[0].spent,pointBudget:runs[0].pointBudget,attributes:runs[0].attributes,learned:runs[0].learned,minimumResource:+Math.min(...runs.map(r=>r.minimumResource)).toFixed(2),damageBySource:Object.fromEntries(Object.entries(totals).map(([id,n])=>[id,+n.toFixed(2)])),casts:runs[0].casts});
}
const report={characterLevel:CAMPAIGN_MAX_LEVEL,combatBudgetLevel:combatBudgetLevel(CAMPAIGN_MAX_LEVEL),attributePointBudget:attributePointBudget(CAMPAIGN_MAX_LEVEL),skillPointBudget:skillPointBudget(CAMPAIGN_MAX_LEVEL,true),seconds,seeds,dt,thunderPreparation:stationaryThunder?'stationary: no movement preparation':'movement-ready: fixture supplies movingTime before a cast',scope:'Current campaign maximum level, shared legal attribute and skill-point budgets, equal offensive attributes, starter weapons, no armour/forging/pets, stationary invulnerable dummies, fixed combat regeneration, no potions or infinite resources. Entry = all rank 1; developed = balanced legal investment; specialized = legal active-damage priority with rank 5 maximum. No over-budget all-rank-5 profile. WAR at 1.4m, ranged at 5.5m. Targets and between-action player positions are anchored; rush movement still runs during its action. Bow uses short tap basics. Movement-ready thunder is a conditional ceiling, not evidence of real movement execution. Not a moving-enemy or device acceptance.',rows};
const output=process.argv.slice(2).find(arg=>!arg.startsWith('--'));
if(output)writeFileSync(output,JSON.stringify(report,null,2)+'\n');
console.table(rows.map(({build,formation,family,dps,burst6,spent,minimumResource})=>({build,formation,family,dps,burst6,spent,minimumResource})));
