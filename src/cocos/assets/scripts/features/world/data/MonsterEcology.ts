import type {AreaDef,EnemySpawn} from '../../../core/Contracts';
import type {CampaignEnemyDef} from '../../campaign/data/Campaign';
import type {EnemyAttackDef,EnemyAttackStep,EnemyCombatProfile,EnemyGeometry} from '../../combat/data/EnemyCombat';
import {beastText as text} from '../locales';

/** Organic wildlife supplements the human campaign and the existing machines. */
export const MONSTER_ACTORS:Record<string,string>={BEAST_HOUND:'thorn-hound',BEAST_SPITTER:'marsh-spitter',BEAST_RIDGEBREAKER:'ridgebreaker',BEAST_BRAMBLE_BOAR:'bramble-boar',BEAST_CAVE_SPIDER:'cave-spider',BEAST_ROCK_SCORPION:'rock-scorpion'};
export const MONSTER_ENEMIES:CampaignEnemyDef[]=[
 {id:'BEAST_BRAMBLE_BOAR',name:text('beast.boar.name'),region:'R1',hp:42,baseHp:42,baseDamage:8,level:4,role:'兽群近战',counter:text('beast.boar.counter')},
 {id:'BEAST_CAVE_SPIDER',name:text('beast.spider.name'),region:'U1',hp:32,baseHp:32,baseDamage:6,level:2,role:'兽群近战',counter:text('beast.spider.counter')},
 {id:'BEAST_ROCK_SCORPION',name:text('beast.scorpion.name'),region:'R2',hp:54,baseHp:54,baseDamage:10,level:11,role:'兽群近战',counter:text('beast.scorpion.counter')},
 {id:'BEAST_HOUND',name:'荆背猎兽',region:'R1',hp:46,baseHp:46,baseDamage:10,level:5,role:'兽群近战',counter:'扑咬前压低肩背；侧移后趁落地收势横扫兽群。'},
 {id:'BEAST_SPITTER',name:'沼囊吐兽',region:'R3',hp:68,baseHp:68,baseDamage:12,level:23,role:'野兽远程',counter:'喉囊鼓起后才喷吐；横移避开黏液，近身可打断。'},
 {id:'BEAST_RIDGEBREAKER',name:'裂岳獠王',region:'R2',hp:290,baseHp:290,baseDamage:22,level:18,arena:'H17',mandatory:false,firstClearExperience:540,role:'巨兽首领',counter:'让开锁定的冲撞直道；冲撞和重击后的甲片张开，全部攻击伤害提升30%。半血后冲撞接两段各有提示的重击。'},
];
/** Variants reuse installed actors and move executors, with their own combat tuning. */
export const HUNT_VARIANTS=[
 {id:'BEAST_BRUSH_PUP',name:'棘丛幼兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R1',level:1,hp:32,damage:6,speed:2.1,biteOnly:true},
 {id:'BEAST_RED_FANG',name:'赤鬃撕咬兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R1',level:2,hp:42,damage:9,speed:2.6},
 {id:'BEAST_MOSS_SPITTER',name:'苔囊吐兽',base:'BEAST_SPITTER',actor:'marsh-spitter',region:'R1',level:3,hp:39,damage:8,speed:1.3},
 {id:'BEAST_DUSK_HOUND',name:'暮影猎兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R1',level:4,hp:38,damage:9,speed:3.4},
 {id:'BEAST_MIRE_SPITTER',name:'瘴沼喷囊兽',base:'BEAST_SPITTER',actor:'marsh-spitter',region:'R1',level:6,hp:52,damage:11,speed:1.1,slow:.28},
 {id:'BEAST_IRON_HIDE',name:'铁鬃撞兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R1',level:8,hp:78,damage:13,speed:2,armored:true},
 {id:'BEAST_THORN_ALPHA',name:'荆背群首',base:'BEAST_HOUND',actor:'thorn-hound',region:'R1',level:9,hp:112,damage:15,speed:2.8,elite:true},
 {id:'BEAST_SCREE_HOUND',name:'碎岩猎兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R2',level:11,hp:54,damage:12,speed:3},
 {id:'BEAST_ASH_SPITTER',name:'灰烬喷囊兽',base:'BEAST_SPITTER',actor:'marsh-spitter',region:'R2',level:12,hp:62,damage:13,speed:1.5,fire:true},
 {id:'BEAST_FROST_HOUND',name:'霜脊奔兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R2',level:14,hp:52,damage:12,speed:3.6,slow:.2},
 {id:'BEAST_QUARRY_MAW',name:'矿脊重颚兽',base:'BEAST_HOUND',actor:'thorn-hound',region:'R2',level:16,hp:86,damage:17,speed:2,armored:true},
 {id:'BEAST_ASH_ALPHA',name:'烬牙群首',base:'BEAST_HOUND',actor:'thorn-hound',region:'R2',level:19,hp:138,damage:20,speed:3,elite:true,fire:true},
 {id:'MACHINE_SCRAP_SCARAB',name:'锈壳齿甲',base:'U1-2',actor:'u1-2',region:'U1',level:6,hp:44,damage:9,speed:2.2},
 {id:'MACHINE_CINDER_CRAWLER',name:'炉渣钻爬机',base:'R2-3',actor:'mine-crawler',region:'R2',level:14,hp:72,damage:14,speed:1.6},
];
for(const variant of HUNT_VARIANTS){
 MONSTER_ACTORS[variant.id]=variant.actor;
 MONSTER_ENEMIES.push({id:variant.id,name:variant.name,region:variant.region,hp:variant.hp,baseHp:variant.hp,baseDamage:variant.damage,level:variant.level,role:variant.elite?'兽群精英':variant.base.startsWith('BEAST')?'野外怪物':'游荡机械',counter:variant.armored?'正面甲壳减伤；绕侧或在收势时攻击。':variant.fire?'注意赤焰预警，横移避开喷吐或扑咬。':variant.base.includes('SPITTER')?'横移避开喷吐，近身打断。':'让开扑咬路线，趁落地收势攻击。'});
}
export const MONSTER_TEMPLATES:Record<string,CampaignEnemyDef>=Object.fromEntries(MONSTER_ENEMIES.map(enemy=>[enemy.id,enemy]));
export const MONSTER_BOSS_REWARDS:Record<string,{gold:number;iron:number;name:string}>={BEAST_RIDGEBREAKER:{gold:120,iron:4,name:'裂岳獠王'}};

const fan=(radius:number,angle:number):EnemyGeometry=>({kind:'fan',origin:'caster',radiusMetres:radius,angleDegrees:angle});
const step=(id:string,windup:number,lock:number,damage:number,geometry:EnemyGeometry[],extra:Partial<EnemyAttackStep>={}):EnemyAttackStep=>({id,windup,lock,active:.18,baseDamage:damage,element:'physical',geometry,maxHitsPerTarget:1,requiresLineOfSight:true,requiresSameLayer:true,targetTracking:'untilFinalLock',...extra});
const attack=(id:string,label:string,steps:EnemyAttackStep[],recovery:number,extra:Partial<EnemyAttackDef>={}):EnemyAttackDef=>({id,label,steps,recovery,legacyKind:'swing',pose:'attack_sword',minRange:0,maxRange:2.1,interruptible:true,...extra});
const profile=(id:string,attacks:EnemyAttackDef[],speed:number,extra:Partial<EnemyCombatProfile>={}):EnemyCombatProfile=>({id,name:MONSTER_TEMPLATES[id].name,route:'profile',body:'beast',movement:{speed,turnRate:3.2,preferredRange:1.3,awarenessRange:14,damagedAwarenessRange:30},attackSlotCost:1,cycle:attacks.map(a=>a.id),attacks:Object.fromEntries(attacks.map(a=>[a.id,a])),policy:{playerForcedDisplacement:0,hitReactionMovesEnemy:false,teleport:false,spawnReinforcements:false,idleBetweenMoves:.25,offscreenTellSeconds:1},source:{catalog:'docs/design/monster-ecology-v1.md',catalogSha256:'d0bb11f8a541bc7c31463922f768330bffc4fbd1f5dffd7482dc83ee62b996ef',description:'User-requested organic monsters and an optional monster boss; existing authored geometry, movement, attack-slot and reward primitives.',adapterTuning:['Six actually drawn poses in four directions. Windup/active/recovery select their own authored poses.','Fixed instance levels; wildlife never spawns in safe settlements or the protected ancient-beast observation sites.']},...extra});

const pounce=attack('hound-pounce','压肩扑咬',[step('pounce',.72,.24,11,[fan(1.1,85)],{active:.25,selfMove:{mode:'charge',distance:1.9,duration:.25,collisionStops:true,collisionStaggerSeconds:.55}})],.9,{legacyKind:'charge',minRange:1.65,maxRange:2.75});
const bite=attack('hound-bite','近身撕咬',[step('bite',.65,.22,9,[fan(1.45,100)])],.8);
const spit=attack('marsh-spit','鼓囊喷吐',[step('spit',1.2,.32,12,[{kind:'line',origin:'caster',lengthMetres:18,widthMetres:.5}],{active:.12,projectile:{kind:'spell',speed:8,range:18,radius:.25,count:1,spreadDegrees:0,element:'physical',status:{kind:'slow',percent:.18,seconds:.8},collidesWithWalls:true,homing:false}})],1.3,{legacyKind:'shot',pose:'spell',minRange:4,maxRange:14,cooldown:2.4});
const flail=attack('marsh-flail','甩首护身',[step('flail',.8,.25,9,[fan(1.6,125)])],1.15);
const rush=attack('ridge-charge','刨地冲撞',[step('charge',1.1,.35,22,[fan(1.75,85)],{active:.58,selfMove:{mode:'charge',distance:6.5,duration:.58,collisionStops:true,collisionStaggerSeconds:2}})],1.9,{legacyKind:'charge',minRange:2.2,maxRange:7.4,interruptible:false,cooldown:4.5});
const claw=attack('ridge-sweep','裂岩横扫',[step('sweep',1,.3,18,[fan(2.55,150)])],1.45,{maxRange:3,interruptible:false});
const wave=attack('ridge-quake','踏地震波',[step('quake',1.35,.45,18,[{kind:'ring',origin:'caster',radiusMetres:4.3,innerRadiusMetres:1.4,gapAngleDegrees:95,gapDirectionDegrees:180}],{active:.22})],1.8,{maxRange:4.5,interruptible:false,cooldown:5});
const crush=attack('ridge-double','前扑追击 · 重踏',[step('first',.85,.3,16,[fan(1.6,130)],{active:.28,selfMove:{mode:'charge',distance:2.2,duration:.28,collisionStops:true,collisionStaggerSeconds:1.2}}),step('second',1.05,.6,20,[{kind:'circle',origin:'lockedTarget',radiusMetres:1.65}],{active:.18})],2.05,{maxRange:4.4,interruptible:false});
const boarCharge=attack('boar-charge',text('move.boar.charge'),[step('charge',.95,.32,9,[fan(1.05,85)],{active:.35,selfMove:{mode:'charge',distance:2.6,duration:.35,collisionStops:true,collisionStaggerSeconds:.8}})],1.25,{legacyKind:'charge',minRange:1.6,maxRange:2.92,cooldown:2.6});
const boarBite=attack('boar-bite',text('move.boar.bite'),[step('bite',.75,.25,8,[fan(1.35,100)])],1,{maxRange:1.7});
const spiderLeap=attack('spider-leap',text('move.spider.leap'),[step('leap',.8,.25,6,[fan(.95,95)],{active:.25,selfMove:{mode:'charge',distance:1.5,duration:.25,collisionStops:true,collisionStaggerSeconds:.5}})],1.1,{legacyKind:'charge',minRange:1.25,maxRange:2.25,cooldown:2.2});
const spiderBite=attack('spider-bite',text('move.spider.bite'),[step('bite',.7,.22,6,[fan(1.25,100)])],.9,{maxRange:1.6});
const scorpionSting=attack('scorpion-sting',text('move.scorpion.sting'),[step('sting',1.1,.35,10,[{kind:'rectangle',origin:'caster',lengthMetres:2,widthMetres:.7}],{active:.18})],1.45,{maxRange:2.32});
const scorpionClaw=attack('scorpion-claw',text('move.scorpion.claw'),[step('claw',.8,.25,8,[fan(1.4,95)])],1.05,{maxRange:1.7});
export const MONSTER_COMBAT_PROFILES:Record<string,EnemyCombatProfile>={
 BEAST_BRAMBLE_BOAR:profile('BEAST_BRAMBLE_BOAR',[boarCharge,boarBite],2.4,{hurtRadius:.42}),
 BEAST_CAVE_SPIDER:profile('BEAST_CAVE_SPIDER',[spiderLeap,spiderBite],2.7,{hurtRadius:.4}),
 BEAST_ROCK_SCORPION:profile('BEAST_ROCK_SCORPION',[scorpionSting,scorpionClaw],1.75,{hurtRadius:.45,movement:{speed:1.75,turnRate:2.8,preferredRange:1.7,awarenessRange:12,damagedAwarenessRange:30}}),
 BEAST_HOUND:profile('BEAST_HOUND',[pounce,bite],2.8,{hurtRadius:.35}),
 BEAST_SPITTER:profile('BEAST_SPITTER',[spit,flail],1.35,{hurtRadius:.4,movement:{speed:1.35,turnRate:2.8,preferredRange:7,awarenessRange:15,damagedAwarenessRange:30}}),
 BEAST_RIDGEBREAKER:profile('BEAST_RIDGEBREAKER',[rush,claw,wave,crush],2,{hurtRadius:.95,solidBody:true,recoveryDamageMultiplier:1.3,attackSlotCost:2,movement:{speed:2,turnRate:2,preferredRange:2.3,awarenessRange:17,damagedAwarenessRange:32},cycle:[rush.id,claw.id,wave.id],halfHealth:{threshold:.5,once:true,queuedAttackId:crush.id,followUpAfter:{[rush.id]:crush.id}}}),
};
/** Also called after the generated mechanical profiles have been installed. */
export function installHuntProfiles(profiles:Record<string,EnemyCombatProfile>){
 for(const variant of HUNT_VARIANTS){
  const original=profiles[variant.base];if(!original)continue;
  const tuned:EnemyCombatProfile=JSON.parse(JSON.stringify(original));
  tuned.id=variant.id;tuned.name=variant.name;tuned.movement={...tuned.movement,speed:variant.speed,awarenessRange:12,damagedAwarenessRange:30};
  if(variant.biteOnly)tuned.cycle=['hound-bite'];
  if(variant.armored)tuned.defense={guardArcDegrees:110,frontalDamageMultiplier:.65,breakOpenSeconds:1};
  const ratio=variant.damage/(variant.base==='BEAST_HOUND'?10:variant.base==='BEAST_SPITTER'?12:12);
  for(const move of Object.values(tuned.attacks))for(const phase of move.steps){
   phase.baseDamage=Math.round(phase.baseDamage*ratio);
   if(variant.fire){phase.element='fire';if(phase.projectile){phase.projectile.element='fire';phase.projectile.status={kind:'burn',baseDamagePerSecond:2,seconds:2};}}
   if(variant.slow&&phase.projectile)phase.projectile.status={kind:'slow',percent:variant.slow,seconds:1};
  }
  // Lowland spitters keep a shorter tell and firing lane than late marsh beasts.
  if(variant.region==='R1'&&variant.base==='BEAST_SPITTER'){tuned.movement.preferredRange=5;for(const move of Object.values(tuned.attacks))if(move.legacyKind==='shot'){move.maxRange=9;for(const phase of move.steps)if(phase.projectile)phase.projectile.range=12;}}
  // Hunting support advances with its pack and leaves a real melee approach
  // window after firing, instead of endlessly trading long-range tells.
  if(variant.base==='BEAST_SPITTER'){
   tuned.movement.preferredRange=3.6;
   for(const move of Object.values(tuned.attacks))if(move.legacyKind==='shot'){move.minRange=3;move.recovery=Math.max(move.recovery,1.65);}
  }
  profiles[variant.id]=tuned;
 }
}

const spawn=(id:string,templateId:string,x:number,z:number,level:number):EnemySpawn=>({id,kind:templateId==='BEAST_RIDGEBREAKER'?'captain':'raider',templateId,contentId:templateId,x,z,level,...(templateId==='BEAST_RIDGEBREAKER'?{bossId:templateId}:{})});
export const MONSTER_ENCOUNTERS:Record<string,EnemySpawn[]>={
 S08:[spawn('beast-s08-hound-1','BEAST_HOUND',-16,5,5),spawn('beast-s08-hound-2','BEAST_HOUND',-14,6,5)],
 H04:[spawn('beast-h04-hound-1','BEAST_HOUND',10,-11,13),spawn('beast-h04-hound-2','BEAST_HOUND',15,-7,13)],
 H17:[spawn('beast-h17-ridgebreaker','BEAST_RIDGEBREAKER',0,42,18)],
 B12:[spawn('beast-b12-spitter-1','BEAST_SPITTER',-12,3,24),spawn('beast-b12-spitter-2','BEAST_SPITTER',12,18,24)],
 B13:[spawn('beast-b13-spitter','BEAST_SPITTER',7,-10,25),spawn('beast-b13-hound','BEAST_HOUND',-8,-7,25)],
};

export const HUNT_PACK_SIZE=8;
export const HUNT_LAYOUT_VERSION='eight-spaced-v3';
export const HUNT_SCENE_BUDGET=29;
/** Two or three compact packs per ground. Stable slots reuse corpses/nodes. */
export const HUNTING_GROUNDS:Record<string,{level:number;packs:string[][]}>={
 S02:{level:1,packs:[['BEAST_BRUSH_PUP','BEAST_BRUSH_PUP','BEAST_RED_FANG'],['BEAST_BRUSH_PUP','BEAST_BRUSH_PUP','BEAST_BRUSH_PUP'],['BEAST_BRUSH_PUP','BEAST_BRUSH_PUP','BEAST_RED_FANG']]},
 S03:{level:2,packs:[['BEAST_RED_FANG','BEAST_BRUSH_PUP','BEAST_BRUSH_PUP'],['BEAST_MOSS_SPITTER','BEAST_RED_FANG','BEAST_RED_FANG'],['BEAST_BRUSH_PUP','BEAST_RED_FANG','BEAST_BRUSH_PUP']]},
 S04:{level:2,packs:[['BEAST_RED_FANG','BEAST_RED_FANG','BEAST_BRUSH_PUP'],['BEAST_BRUSH_PUP','BEAST_MOSS_SPITTER','BEAST_RED_FANG'],['BEAST_BRUSH_PUP','BEAST_BRUSH_PUP','BEAST_RED_FANG']]},
 S07:{level:4,packs:[['BEAST_DUSK_HOUND','BEAST_RED_FANG','BEAST_RED_FANG'],['BEAST_MOSS_SPITTER','BEAST_DUSK_HOUND','BEAST_RED_FANG'],['BEAST_RED_FANG','BEAST_RED_FANG','BEAST_DUSK_HOUND']]},
 S08:{level:5,packs:[['BEAST_HOUND','BEAST_HOUND','BEAST_DUSK_HOUND'],['BEAST_MIRE_SPITTER','BEAST_HOUND','BEAST_HOUND'],['BEAST_HOUND','BEAST_DUSK_HOUND','BEAST_DUSK_HOUND']]},
 S09:{level:7,packs:[['BEAST_IRON_HIDE','BEAST_HOUND','BEAST_HOUND'],['BEAST_MIRE_SPITTER','BEAST_DUSK_HOUND','BEAST_HOUND']]},
 S11:{level:7,packs:[['BEAST_DUSK_HOUND','BEAST_DUSK_HOUND','BEAST_HOUND'],['BEAST_MIRE_SPITTER','BEAST_IRON_HIDE','BEAST_HOUND']]},
 S12:{level:8,packs:[['BEAST_IRON_HIDE','BEAST_HOUND','BEAST_HOUND'],['BEAST_MIRE_SPITTER','BEAST_HOUND','BEAST_HOUND']]},
 S13:{level:8,packs:[['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','BEAST_IRON_HIDE'],['BEAST_HOUND','BEAST_IRON_HIDE','BEAST_HOUND']]},
 S15:{level:7,packs:[['BEAST_MIRE_SPITTER','BEAST_HOUND','BEAST_HOUND'],['BEAST_MIRE_SPITTER','BEAST_DUSK_HOUND','BEAST_HOUND']]},
 S17:{level:9,packs:[['BEAST_THORN_ALPHA','BEAST_HOUND','BEAST_HOUND'],['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB']]},
 S18:{level:3,packs:[['BEAST_RED_FANG','BEAST_RED_FANG','BEAST_BRUSH_PUP'],['BEAST_MOSS_SPITTER','BEAST_RED_FANG','BEAST_RED_FANG']]},
 S19:{level:5,packs:[['BEAST_DUSK_HOUND','BEAST_HOUND','BEAST_HOUND'],['BEAST_MOSS_SPITTER','BEAST_HOUND','BEAST_HOUND'],['BEAST_HOUND','BEAST_DUSK_HOUND','BEAST_HOUND']]},
 S20:{level:9,packs:[['BEAST_THORN_ALPHA','BEAST_IRON_HIDE','BEAST_HOUND'],['BEAST_MIRE_SPITTER','BEAST_HOUND','BEAST_IRON_HIDE']]},
 H03:{level:11,packs:[['BEAST_SCREE_HOUND','BEAST_SCREE_HOUND','BEAST_ASH_SPITTER'],['MACHINE_CINDER_CRAWLER','BEAST_SCREE_HOUND','BEAST_SCREE_HOUND'],['BEAST_SCREE_HOUND','BEAST_SCREE_HOUND','BEAST_SCREE_HOUND']]},
 H04:{level:13,packs:[['BEAST_SCREE_HOUND','BEAST_SCREE_HOUND','BEAST_ASH_SPITTER'],['MACHINE_CINDER_CRAWLER','BEAST_SCREE_HOUND','BEAST_SCREE_HOUND'],['BEAST_ASH_SPITTER','BEAST_SCREE_HOUND','BEAST_FROST_HOUND']]},
 H05:{level:14,packs:[['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_ASH_SPITTER'],['BEAST_FROST_HOUND','BEAST_FROST_HOUND','BEAST_SCREE_HOUND']]},
 H07:{level:15,packs:[['BEAST_FROST_HOUND','BEAST_FROST_HOUND','BEAST_ASH_SPITTER'],['BEAST_QUARRY_MAW','BEAST_SCREE_HOUND','BEAST_SCREE_HOUND']]},
 H10:{level:16,packs:[['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_QUARRY_MAW'],['BEAST_ASH_SPITTER','BEAST_QUARRY_MAW','BEAST_FROST_HOUND']]},
 H11:{level:15,packs:[['BEAST_QUARRY_MAW','BEAST_FROST_HOUND','BEAST_FROST_HOUND'],['BEAST_ASH_SPITTER','BEAST_SCREE_HOUND','BEAST_SCREE_HOUND']]},
 H12:{level:16,packs:[['BEAST_QUARRY_MAW','BEAST_FROST_HOUND','BEAST_FROST_HOUND'],['BEAST_ASH_SPITTER','BEAST_ASH_SPITTER','BEAST_FROST_HOUND']]},
 H13:{level:17,packs:[['BEAST_QUARRY_MAW','BEAST_FROST_HOUND','BEAST_FROST_HOUND'],['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_ASH_SPITTER']]},
 H14:{level:18,packs:[['BEAST_ASH_ALPHA','BEAST_FROST_HOUND','BEAST_QUARRY_MAW'],['BEAST_ASH_SPITTER','BEAST_FROST_HOUND','BEAST_FROST_HOUND']]},
 H15:{level:18,packs:[['BEAST_QUARRY_MAW','BEAST_QUARRY_MAW','BEAST_FROST_HOUND'],['MACHINE_CINDER_CRAWLER','BEAST_ASH_SPITTER','BEAST_FROST_HOUND']]},
 H17:{level:19,packs:[['BEAST_ASH_ALPHA','BEAST_QUARRY_MAW','BEAST_FROST_HOUND'],['BEAST_ASH_SPITTER','BEAST_QUARRY_MAW','BEAST_FROST_HOUND'],['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_ASH_SPITTER']]},
 'U1-01':{level:6,packs:[['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB'],['BEAST_MIRE_SPITTER','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB']]},
 'U1-02':{level:7,packs:[['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','BEAST_HOUND'],['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','BEAST_MIRE_SPITTER']]},
 'U1-03':{level:8,packs:[['MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB'],['BEAST_IRON_HIDE','BEAST_HOUND','BEAST_HOUND']]},
 'U1-06':{level:16,packs:[['MACHINE_CINDER_CRAWLER','MACHINE_SCRAP_SCARAB','MACHINE_SCRAP_SCARAB'],['BEAST_QUARRY_MAW','MACHINE_CINDER_CRAWLER','BEAST_FROST_HOUND']]},
 'U1-07':{level:19,packs:[['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_ASH_SPITTER'],['BEAST_ASH_ALPHA','BEAST_QUARRY_MAW','BEAST_FROST_HOUND']]},
 'U1-09':{level:18,packs:[['MACHINE_CINDER_CRAWLER','MACHINE_CINDER_CRAWLER','BEAST_FROST_HOUND'],['BEAST_ASH_SPITTER','BEAST_QUARRY_MAW','BEAST_FROST_HOUND']]},
};
// Keep the original three identities and stable slot IDs. Every pack has six
// close fighters and two ranged supports, using already installed actors/moves.
for(const [id,ground]of Object.entries(HUNTING_GROUNDS))for(const pack of ground.packs){
 const filler=pack.find(template=>!/SPITTER|ALPHA|IRON_HIDE|QUARRY_MAW|CINDER_CRAWLER/.test(template))??(id.startsWith('S')?'BEAST_HOUND':id.startsWith('U1')?'MACHINE_SCRAP_SCARAB':'BEAST_SCREE_HOUND');
 while(pack.length<HUNT_PACK_SIZE)pack.push(filler);
 const support=id.startsWith('S')?(ground.level<=4?'BEAST_MOSS_SPITTER':'BEAST_MIRE_SPITTER'):ground.level<11?'BEAST_MIRE_SPITTER':'BEAST_ASH_SPITTER';
 let ranged=pack.filter(template=>template.includes('SPITTER')).length;
 for(let slot=pack.length-1;slot>=3&&ranged<2;slot--)if(!pack[slot].includes('SPITTER')){pack[slot]=support;ranged++;}
}
export const HUNT_ENCOUNTERS:Record<string,EnemySpawn[]>={};
// A new silhouette replaces an existing ordinary slot, sharing that slot's
// authored HP budget. The value comes from content, never from saved fields.
const huntHealth=new Map<string,{templateId:string;baseHp:number}>();
export function huntingBaseHp(e:Pick<EnemySpawn,'id'|'templateId'>){const saved=huntHealth.get(e.id);return saved&&saved.templateId===e.templateId?saved.baseHp:undefined;}
function variedHuntMember(area:string,level:number,pack:number,slot:number,original:string){
 if(slot<3||slot>4||/SPITTER|ALPHA/.test(original))return original;
 if(area.startsWith('U1'))return slot===3?'BEAST_CAVE_SPIDER':level>=11?'BEAST_ROCK_SCORPION':original;
 if(area.startsWith('H'))return slot===3?'BEAST_ROCK_SCORPION':pack%2?'BEAST_CAVE_SPIDER':'BEAST_BRAMBLE_BOAR';
 if(slot===3)return pack%2===0?'BEAST_CAVE_SPIDER':level>=3?'BEAST_BRAMBLE_BOAR':'BEAST_CAVE_SPIDER';
 return level>=3?(pack%2===0?'BEAST_BRAMBLE_BOAR':'BEAST_CAVE_SPIDER'):original;
}
export function locationEntryLevel(id:string){return id==='S10'?10:id==='H08'?20:id.startsWith('H')?11:id.startsWith('B')?21:id.startsWith('F')?31:/^U1-(06|07|08|09|10)$/.test(id)?11:/^U2-0[2-9]$/.test(id)?21:1;}
function installHuntingGrounds(areas:Record<string,AreaDef>){
 for(const [id,ground]of Object.entries(HUNTING_GROUNDS)){
  const area=areas[id],placed:EnemySpawn[]=[];
  if(area.enemies.length+ground.packs.flat().length>HUNT_SCENE_BUDGET)throw new Error(`Hunting budget exceeded: ${id}`);
  // Assign an entire pack to an approach. Never distribute its members among
  // unrelated gates or leave all ranged support at the scene centre.
  // Keep pack anchors across both released chapters independent of boss gates.
  const gates=area.exits.filter(e=>locationEntryLevel(e.to)<=20&&!/^(B|F|U2)/.test(e.to));
  // Give each member 20% more room while retaining the same pack shape.
  const formation=[{x:0,z:-2.52},{x:-1.8,z:-1.56},{x:1.8,z:-1.56},{x:-2.52,z:.24},{x:0,z:-.36},{x:2.52,z:.24},{x:-1.2,z:1.68},{x:1.2,z:1.68}];
  for(const [pack,templates]of ground.packs.entries()){
   const gate=gates[pack%gates.length]??area.spawn,d=Math.hypot(gate.x,gate.z)||1,inward={x:-gate.x/d,z:-gate.z/d},inset=25+Math.floor(pack/Math.max(1,gates.length))*18;
   const desired={x:gate.x+inward.x*inset,z:gate.z+inward.z*inset};
   // Ranged members occupy the back row, within the same AoE-sized footprint.
   const order=templates.map((original,slot)=>({template:variedHuntMember(id,ground.level,pack,slot,original),slot,original})).sort((a,b)=>Number(a.template.includes('SPITTER'))-Number(b.template.includes('SPITTER'))||a.slot-b.slot);
   const positions=(center:{x:number;z:number})=>order.map((_,i)=>({x:center.x+inward.z*formation[i].x+inward.x*formation[i].z,z:center.z-inward.x*formation[i].x+inward.z*formation[i].z}));
   const valid=(p:{x:number;z:number})=>Math.abs(p.x)<area.width/2-5&&Math.abs(p.z)<area.depth/2-5&&Math.hypot(p.x-area.spawn.x,p.z-area.spawn.z)>16&&!area.obstacles.some(o=>Math.abs(p.x-o.x)<o.width/2+1&&Math.abs(p.z-o.z)<o.depth/2+1)&&!area.exits.some(e=>Math.hypot(p.x-e.x,p.z-e.z)<18)&&!area.objects.some(o=>Math.hypot(p.x-o.x,p.z-o.z)<(o.actor||o.action==='checkpoint'?16:3))&&!area.enemies.some(e=>Math.hypot(p.x-e.x,p.z-e.z)<2)&&!placed.some(e=>Math.hypot(p.x-e.x,p.z-e.z)<10);
   const candidates=[desired];for(let r=3;r<=36;r+=3)for(let a=0;a<16;a++)candidates.push({x:desired.x+Math.cos(a*Math.PI/8)*r,z:desired.z+Math.sin(a*Math.PI/8)*r});
   const center=candidates.find(p=>!area.obstacles.some(o=>Math.abs(p.x-o.x)<o.width/2+3&&Math.abs(p.z-o.z)<o.depth/2+3)&&positions(p).every(valid));
   if(!center)throw new Error(`No safe hunting pack: ${id}/${pack}`);
   const points=positions(center),members=order.map(({template,slot,original},i)=>{const key=`hunt-${id}-${pack}-${slot}`;if(template!==original)huntHealth.set(key,{templateId:template,baseHp:MONSTER_TEMPLATES[original].baseHp??MONSTER_TEMPLATES[original].hp});return {...spawn(key,template,points[i].x,points[i].z,ground.level),kind:template.includes('SPITTER')?'archer' as const:'raider' as const,packId:`hunt-${id}-${pack}`,respawnSeconds:template.includes('ALPHA')?50:28};});
   placed.push(...members.sort((a,b)=>a.id.localeCompare(b.id)));
  }
  HUNT_ENCOUNTERS[id]=placed;area.enemies.push(...placed);
 }
 // Story actions still operate their original mechanisms, while walking routes use levels.
 for(const area of Object.values(areas))for(const exit of area.exits){
  exit.requiredLevel=locationEntryLevel(exit.to);
  exit.label=`前往${areas[exit.to].name}${exit.requiredLevel>1?` · Lv${exit.requiredLevel}`:''}`;
 }
}
export function installMonsterEcology(areas:Record<string,AreaDef>){
 for(const [id,spawns]of Object.entries(MONSTER_ENCOUNTERS))for(const enemy of spawns)if(!areas[id].enemies.some(e=>e.id===enemy.id))areas[id].enemies.push({...enemy});
 areas.H17.objects.push({id:'beast-h17-warning',action:'inspect',label:'兽穴警示 · 裂岳獠王',evidence:'ridgebreaker-tracks',x:-6,z:25,radius:2.5,description:'北侧废窑传来刨地声。獠王冲撞前会压低獠牙，最后一步锁定方向；向侧面让开，趁它收势、肩甲张开时反击。半血后会前扑追击再重踏，两段分别预警。狩猎可获540经验、120金币、铁4与一份高地装备；可以沿两侧道路绕行。'});
 installHuntingGrounds(areas);
}
