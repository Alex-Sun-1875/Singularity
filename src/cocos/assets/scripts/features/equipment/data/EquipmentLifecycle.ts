import type {ItemDef,EquipmentSlot} from './Equipment';

export type LootStyle='WAR'|'BOW'|'FIR'|'THU';
export type LifecycleQuality='史诗'|'传奇';
export interface LifecycleGroup {id:string;chapter:number;route:'task'|'battle';quality:LifecycleQuality;name:string;slot:EquipmentSlot;requiredLevel:number;task?:string;items:string[]}
export const LIFECYCLE_PHASES=[
 {chapter:1,level:1,endLevel:10,enhance:3},{chapter:2,level:11,endLevel:20,enhance:6},
 {chapter:3,level:21,endLevel:24,enhance:8},{chapter:4,level:25,endLevel:28,enhance:10},
 {chapter:5,level:29,endLevel:32,enhance:10},{chapter:6,level:33,endLevel:35,enhance:12},
 {chapter:7,level:36,endLevel:38,enhance:12},{chapter:8,level:39,endLevel:40,enhance:15},
] as const;
/** Only the first two content phases are released. Levels never open future maps. */
export const releasedEquipmentChapter=(level:number)=>level>=11?2:1;
export const lifecyclePhase=(level:number)=>LIFECYCLE_PHASES.find(p=>level<=p.endLevel)??LIFECYCLE_PHASES[7];
/** Native weapon-strength units; retain the accepted early growing curve. */
export function lifecycleWeaponBase(level:number){
 const l=Math.max(1,Math.min(40,level));if(l<=20)return (18+3*(l-1))/1.18;
 const anchors=[[20,75/1.18],[24,100],[28,135],[32,180],[35,238],[38,310],[40,400]];
 for(let i=1;i<anchors.length;i++)if(l<=anchors[i][0]){const [a,x]=anchors[i-1],[b,y]=anchors[i];return x+(y-x)*(l-a)/(b-a);}return 400;
}
const STYLES=[
 {id:'WAR' as const,kind:'sword' as const,family:'单手剑',art:'W05',suffix:'剑'},
 {id:'BOW' as const,kind:'bow' as const,family:'双手弓',art:'W10',suffix:'弓'},
 {id:'FIR' as const,kind:'staff' as const,family:'双手火杖',art:'W12',suffix:'火杖'},
 {id:'THU' as const,kind:'staff' as const,family:'双手雷杖',art:'W14',suffix:'雷杖'},
];
const SET_TEXT={oath:'守誓2件：最大生命 +8',wind:'疾风2件：暴击率 +1%',ember:'余烬2件：攻击/技能伤害 +1.5%',bell:'钟鸣2件：攻击/技能伤害 +1.5%'} as const;
export const LIFECYCLE_ITEMS:ItemDef[]=[];
export const LIFECYCLE_GROUPS:LifecycleGroup[]=[];
function group(chapter:number,route:'task'|'battle',quality:LifecycleQuality,tag:string,name:string,slot:EquipmentSlot,requiredLevel:number,task?:string){
 const id=`LC${chapter}_${route==='task'?'T':'B'}_${tag}`,items:string[]=[],weapon=slot==='weapon';
 const d:LifecycleGroup={id,chapter,route,quality,name,slot,requiredLevel,task,items};LIFECYCLE_GROUPS.push(d);
 const source=route==='task'?'完成对应任务后固定领取':'本章随机掉落；不保证获得指定款式';
 const description=`第${chapter}章 · ${quality} · 阶段装备，基础数值不随人物等级成长。\n${source}`;
 if(weapon)for(const style of STYLES){
  const key=`${id}_${style.id}`,power=Math.round(lifecycleWeaponBase(requiredLevel)*(quality==='传奇'?1.18:1.10));items.push(key);
  const set=style.id==='WAR'?'oath':style.id==='BOW'?'wind':style.id==='FIR'?'ember':'bell';
  LIFECYCLE_ITEMS.push({id:key,name:name+style.suffix,kind:style.kind,slot,level:Math.min(5,Math.ceil(requiredLevel/8)),quality,set,weaponFamily:style.family,twoHanded:style.kind!=='sword',artSource:style.art,requiredLevel,power,chapter,growthMode:'fixed',lifecycleGroup:id,passive:quality==='传奇'?(route==='battle'?'recovery-strike':'steady-strike'):undefined,description:`${description}\n武器强度 ${power} · 攻击/技能威力 +${Number((power/3).toFixed(1))}%${quality==='传奇'?route==='battle'?'\n破阵：直接攻击命中恢复或失衡中的敌人，伤害 +8%。':'\n稳攻：直接攻击与主动技能伤害 +4%。':''}\n${SET_TEXT[set]}（同主题跨章节计数）`,source});
 }else{
  const kind=slot==='ringLeft'?'ring' as const:slot==='necklace'?'necklace' as const:'armor' as const;
  const maxHp=Math.round((10+requiredLevel)*(quality==='传奇'?1:0.8));items.push(id);
  const set=slot==='chest'?'oath':slot==='necklace'?'wind':slot==='ringLeft'?'bell':'ember';
  LIFECYCLE_ITEMS.push({id,name,kind,slot,level:Math.min(5,Math.ceil(requiredLevel/8)),quality,set,requiredLevel,chapter,growthMode:'fixed',lifecycleGroup:id,maxHp,armor:slot==='chest'?3:slot==='hands'?1:quality==='传奇'?1:0,artSource:slot==='ringLeft'?'J03':slot==='necklace'?'J06':slot==='hands'?'A09':'A02',passive:quality==='传奇'?(slot==='ringLeft'?'oath-guard':'hunt-renewal'):undefined,description:`${description}\n最大生命 +${maxHp}${quality==='传奇'?slot==='ringLeft'?'\n誓守：受到的直接伤害降低2%。':'\n猎归：直接击杀回复已损失生命的3%，间隔5秒。':''}\n${SET_TEXT[set]}（同主题跨章节计数）`,source});
 }
}
group(1,'task','史诗','E','守夜者之约','weapon',6,'border-mill');
group(1,'task','传奇','L','石桥誓戒','ringLeft',8,'border-watch');
group(1,'battle','史诗','E','猎场守卫甲','chest',8);
group(1,'battle','传奇','L','暮林猎坠','necklace',8);
group(2,'task','史诗','E','熔镜护手','hands',14,'highland-workers');
group(2,'task','传奇','L','断岳之誓','weapon',16,'highland-oath');
group(2,'battle','史诗','E','矿火征途','weapon',16);
group(2,'battle','传奇','L','山桥破阵','weapon',18);
const taskNames=['沉钟余响','无眠誓约','诸城盟誓','城垣余烬','长夜守望','破晓之誓'];
const battleNames=['河湾破阵','王座裁决','裂旗破阵','黑冠终令','斩翼黎明','永夜终结'];
for(const phase of LIFECYCLE_PHASES.slice(2)){
 const c=phase.chapter,l=phase.level,mid=Math.floor((l+phase.endLevel)/2),end=phase.endLevel;
 group(c,'task','史诗','E1',taskNames[c-3]+'护甲','chest',l);
 group(c,'task','史诗','E2',taskNames[c-3]+'指环','ringLeft',l);
 group(c,'task','传奇','L1',taskNames[c-3],'weapon',mid);
 group(c,'task','传奇','L2',taskNames[c-3]+'护手','hands',end);
 group(c,'battle','史诗','E1',battleNames[c-3]+'护甲','chest',l);
 group(c,'battle','史诗','E2',battleNames[c-3],'weapon',mid);
 group(c,'battle','传奇','L1',battleNames[c-3]+'战坠','necklace',mid);
 group(c,'battle','传奇','L2',battleNames[c-3],'weapon',end);
}
export const LIFECYCLE_BY_ID:Record<string,ItemDef>=Object.fromEntries(LIFECYCLE_ITEMS.map(d=>[d.id,d]));
export const lifecycleGroup=(id:string)=>LIFECYCLE_GROUPS.find(g=>g.id===id);
export const lifecycleTaskSource=(id:string)=>`lifecycle:task:${id}`;
export function lifecycleBattlePool(chapter:number,quality:LifecycleQuality,style:LootStyle){
 return LIFECYCLE_GROUPS.filter(g=>g.chapter===chapter&&g.route==='battle'&&g.quality===quality).flatMap(g=>g.slot==='weapon'?g.items.filter(id=>id.endsWith('_'+style)):g.items);
}
