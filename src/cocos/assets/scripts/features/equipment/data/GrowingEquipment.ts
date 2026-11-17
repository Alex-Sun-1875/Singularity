import type {ItemDef} from './Equipment';
import type {CampaignEventDef} from '../../campaign/data/CampaignEvents';
import type {AreaDef} from '../../../core/Contracts';
import {lifecycleWeaponBase,mainBossChapter} from './EquipmentLifecycle';
import {equipmentText} from '../locales';
import {FIELD_QUEST_EVENTS} from '../../campaign/data/FieldQuests';
import {weaponPowerMultiplier,weaponPowerBonusPercent} from './WeaponPower';
import {CAMPAIGN_MAX_LEVEL,combatBudgetLevel} from '../../progression/data/CampaignProgression';

export const GROWING_IDS=['DG_L01','DG_L02','DG_L03','DG_L04','DG_L05','DG_L06','DG_A01','DG_A02','DG_A03','DG_A04','DG_A05'] as const;
export const GROWING_ITEMS:ItemDef[]=[
 {id:'DG_L01',name:'最后一班岗',kind:'sword',slot:'weapon',level:1,quality:'传奇',weaponFamily:'单手剑',artSource:'W06',growthAttribute:'strength',description:'守岗：一次近战战技命中2敌（Boss只需1名），6秒内下一战技首次命中给予8%最大生命护盾3秒，间隔8秒。',source:'灰披队长 / 断岳前堡Boss随机掉落'},
 {id:'DG_L02',name:'逐月之弦',kind:'bow',slot:'weapon',level:1,quality:'传奇',weaponFamily:'双手弓',twoHanded:true,artSource:'W10',growthAttribute:'dexterity',description:'踏风：实际移动2秒后，5秒内下一弓术首次命中伤害+20%，间隔6秒；不增加箭矢或目标。',source:'鹰背岩林督猎Boss / S19猎人箭匣随机'},
 {id:'DG_L03',name:'长夜圣烛',kind:'staff',slot:'weapon',level:1,quality:'传奇',weaponFamily:'双手火杖',twoHanded:true,artSource:'W12',growthAttribute:'intellect',description:'余烬收束：火术命中燃烧目标时，提前结算剩余燃烧的50%并增强该部分20%，最多0.45倍技能威力，间隔5秒。',source:'H03旧巡灯匣随机发现；既有支线所得保留'},
 {id:'DG_L04',name:'雨前的静默',kind:'staff',slot:'weapon',level:1,quality:'传奇',weaponFamily:'双手雷杖',twoHanded:true,artSource:'W14',growthAttribute:'intellect',description:'迟雷：雷术首次命中留下1.2秒后爆发的雷印；另一次雷术命中可提前引爆并增强，间隔5秒。',source:'鸣岩洞厅雷痕铜匣 / 三誓守卫Boss随机'},
 {id:'DG_L05',name:'迟归者的指环',kind:'ring',slot:'ringLeft',level:1,quality:'传奇',artSource:'J03',description:'归途未尽：直接攻击或本人燃烧击杀后回复已损失生命的12%，间隔5秒；装备附伤击杀不触发。',source:'S06营地旧物匣随机发现；既有支线所得保留'},
 {id:'DG_L06',name:'逆钟之坠',kind:'necklace',slot:'necklace',level:1,quality:'传奇',artSource:'J06',description:'逆拍：精准闪避真实攻击后，4秒内下一主动技能首次命中伤害+20%，间隔8秒。',source:'鸣岩洞厅 / 绞盘井随机发现「逆行的钟声」，完成后固定奖励'},
 {id:'DG_A01',name:'王庭的黄昏',kind:'sword',slot:'weapon',level:1,quality:'神器',weaponFamily:'双手大剑',twoHanded:true,artSource:'L01',growthAttribute:'strength',description:'黄昏重演：每4次有效近战战技在原判定锚点留下延迟0.45秒的影斩，最多2名原目标，各0.65倍技能威力，最短间隔5秒。',source:'任意Boss共享掉落 / S18封存军械箱极稀有随机'},
 {id:'DG_A02',name:'第二次黎明',kind:'necklace',slot:'necklace',level:1,quality:'神器',artSource:'J08',description:'未完的归途：敌方致命伤保留1生命并给予20%最大生命护盾2秒，间隔120秒；换装、休整、重载不重置。',source:'任意Boss共享掉落；既有隐藏任务所得保留'},
];
for(const [id,name,kind,family,art,attribute]of [
 ['DG_A03','王庭的逐星','bow','双手弓','W10','dexterity'],
 ['DG_A04','王庭的余烬','staff','双手火杖','W12','intellect'],
 ['DG_A05','王庭的惊雷','staff','双手雷杖','W14','intellect'],
] as const)GROWING_ITEMS.push({id,name,kind,slot:'weapon',level:1,quality:'神器',weaponFamily:family,twoHanded:true,artSource:art,growthAttribute:attribute,description:'王庭重演：每4次有效主动战技在命中处留下延迟0.45秒的残影，最多2名原目标，各0.65倍技能威力，间隔5秒。',source:'任意Boss均有机会掉落，不受章节与武器掉落偏好限制'});
for(const item of GROWING_ITEMS){item.growthMode='level';if(item.quality==='神器')item.source=equipmentText('loot.artifactBossSource');else if(['DG_L01','DG_L02','DG_L04'].includes(item.id))item.source=equipmentText('loot.growingLegendBossSource');}
export const ARTIFACT_WEAPONS=['DG_A01','DG_A03','DG_A04','DG_A05'] as const;
export const artifactWeaponForStyle={WAR:'DG_A01',BOW:'DG_A03',FIR:'DG_A04',THU:'DG_A05'} as const;
export const GROWING_EQUIPMENT:Record<string,ItemDef>=Object.fromEntries(GROWING_ITEMS.map(i=>[i.id,i]));
export function growingStats(id:string,level:number){
 const item=GROWING_EQUIPMENT[id],l=Math.max(1,Math.min(CAMPAIGN_MAX_LEVEL,level)),budget=combatBudgetLevel(l);
 const artifact=item?.quality==='神器';
 const power=item?.slot==='weapon'?Math.max(Math.round((18+3*(budget-1))*(artifact?1.08:1)),Math.round(lifecycleWeaponBase(l)*(artifact?1.25:1.18))):0;
 const attribute=item?.growthAttribute?1+Math.floor((budget-1)/8):0;
 const maxHp=id==='DG_L05'?8+Math.floor(budget):id==='DG_L06'?12+Math.floor(budget):id==='DG_A02'?16+Math.floor(1.2*budget):0;
 return {power,attribute,maxHp,multiplier:weaponPowerMultiplier(power)};
}
export function growingDescription(item:ItemDef,level:number){
 if(!GROWING_EQUIPMENT[item.id])return item.description;
 const s=growingStats(item.id,level),a={strength:'力量',dexterity:'敏捷',intellect:'智力'};
 return `全等级可用 · 当前按Lv${level}成长 · 本旅程唯一\n${s.power?`武器强度 ${s.power}；基础攻击/技能威力 +${weaponPowerBonusPercent(s.power).toFixed(1)}%；${a[item.growthAttribute!]} +${s.attribute}。`: `最大生命 +${s.maxHp}。`}\n${item.description}\n来源：${item.source}`;
}
export interface GrowingScene {id:string;area:string;label:string;x:number;z:number;item?:string;flag?:string;chance:number}
export const GROWING_SCENES:GrowingScene[]=[
 {id:'hunter-case',area:'S19',label:'遗失的猎人箭匣',x:9,z:-30,item:'DG_L02',chance:.06},
 {id:'thunder-case',area:'U1-02',label:'雷痕铜匣',x:9,z:-30,item:'DG_L04',chance:.06},
 {id:'royal-case',area:'S18',label:'封存军械箱',x:9,z:-30,item:'DG_A01',chance:.005},
 {id:'lamp-relic',area:'H03',label:'旧巡灯匣',x:0,z:-28,item:'DG_L03',chance:.06},
 {id:'letter-relic',area:'S06',label:'营地旧物匣',x:0,z:-28,item:'DG_L05',chance:.06},
 {id:'clock-echo',area:'U1-02',label:'调查逆向钟纹',x:-9,z:-28,flag:'dg:clock-found',chance:.35},
 {id:'clock-chain',area:'U1-09',label:'听辨绞盘中的钟声',x:-9,z:-28,flag:'dg:clock-found',chance:.35},
 {id:'dawn-stone',area:'S03',label:'未写完的墓志',x:9,z:-30,flag:'dg:dawn-found',chance:.05},
 {id:'dawn-plinth',area:'S12',label:'空基座上的姓名残片',x:9,z:-30,flag:'dg:dawn-found',chance:.05},
];
const quest=(id:string,area:string,label:string,description:string,requires:string[],flag:string,item?:string,clear=false):CampaignEventDef=>({id,area,label,description,requires,sets:[flag],optional:true,...(clear?{clearEncounter:true}:{}),...(item?{items:[item]}:{})});
export const GROWING_QUESTS:CampaignEventDef[]=[
 ...FIELD_QUEST_EVENTS,
 quest('dg-clock-mark-a','U1-02','逆行的钟声：核对第一处钟纹','顺着偶然听见的逆向钟声，记录第一处钟纹。',['dg:clock-found'],'dg:clock-a'),
 quest('dg-clock-mark-b','U1-03','逆行的钟声：核对第二处钟纹','沿可折返矿廊记录另一处钟纹，与洞厅刻线交叉核对。',['dg:clock-a'],'dg:clock-b'),
 quest('dg-clock-axis','U1-02','逆行的钟声：寻找断轴，领取逆钟之坠','在两处钟纹交点找到断轴，固定获得成长传奇「逆钟之坠」。',['dg:clock-b'],'dg:clock-complete','DG_L06'),
];
export function growingQuestVisible(eventId:string,flags:Record<string,boolean>){
 const q=GROWING_QUESTS.find(q=>q.id===eventId);return !q||!(q.sets??[]).every(f=>flags[f])&&(q.requires??[]).every(f=>flags[f])&&(!q.requiresAny?.length||q.requiresAny.some(f=>flags[f]));
}
export function growingJournal(area:string,flags:Record<string,boolean>,receipts:Record<string,string|number|boolean>,inventory:Record<string,number>){
 const quests=GROWING_QUESTS.filter(q=>!receipts[`campaign:${q.id}`]&&growingQuestVisible(q.id,flags)&&(q.area===area||(q.requires?.length??0)>0));
 return `成长装备 ${GROWING_IDS.filter(id=>inventory[id]).length} / ${GROWING_IDS.length} · 每件本旅程唯一${quests.length?'\n'+quests.slice(0,3).map(q=>`${q.area} · ${q.label}`).join('\n'):''}`;
}
export function installGrowingSources(areas:Record<string,AreaDef>){
 for(const s of GROWING_SCENES)areas[s.area].objects.push({id:`growing-scene:${s.id}`,eventId:s.id,action:'growing_scene',label:s.label,description:'仔细调查这处独立发现；抽取结果会保存，本旅程每件成长装备只能获得一次。',x:s.x,z:s.z,radius:1.35});
 for(const area of Object.values(areas))for(const e of area.enemies)if(e.bossId)area.objects.push({id:`growing-rematch:${e.bossId}`,eventId:e.id,action:'growing_rematch',label:equipmentText(mainBossChapter(e.bossId)?'loot.mainRematchLabel':'loot.randomRematchLabel'),description:equipmentText(mainBossChapter(e.bossId)?'loot.mainRematchSource':'loot.randomRematchSource'),x:area.spawn.x+3,z:area.spawn.z,radius:1.35});
}
