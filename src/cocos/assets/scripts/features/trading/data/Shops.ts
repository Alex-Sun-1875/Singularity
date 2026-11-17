import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT,MERCHANTS} from '../../equipment/data/Equipment';
import {SUPPLIES,type SupplyId} from '../../equipment/data/Supplies';
import {GEM_STATS,gemName,gemValueText,type GemStat} from '../../gems/data/Gems';
import {GEM_PRICES,GEM_TRADE_LEVELS,GEM_TRADE_CHAPTERS,SHOP_PRICES} from '../../economy/data/Economy';
import {playableArea,chapterForArea} from '../../journey/data/ChapterJourney';

export interface ShopProduct {id:string;kind:'equipment'|'gem'|'drills'|'supply';name:string;description:string;price:number;level:number;chapter:number;item?:string;stat?:GemStat;tier?:number;supply?:SupplyId}
export const SHOP_SERVICES:Record<string,{area:string;objectId:string;label:string;service:string;public?:boolean;gems?:boolean;supplies?:boolean}>={
 supplies:{area:'S01',objectId:'s01-supplies',label:'布兰 · 杂货商',service:'补给与护具',public:true,supplies:true},
 jeweler:{area:'S01',objectId:'s01-jeweler',label:'琳娜 · 宝石商',service:'宝石与镶嵌',public:true,gems:true},
 mira:{area:'S01-T1',objectId:'t1-mira',label:'弥菈',service:'契约探险装备'},
 lorn:{area:'S01-T3',objectId:'t3-lorn',label:'洛恩',service:'装备与培养',public:true},
 nightqi:{area:'S05',objectId:'s05-nightqi',label:'夜祈',service:'猎装与狩猎委托'},
 severin:{area:'H02',objectId:'h02-severin',label:'瑟维恩',service:'宝石与法术饰品',gems:true},
 elise:{area:'B03',objectId:'b03-elise',label:'艾莉丝',service:'鉴定与法术防具'},
};
export function shopChapter(s:GameState):number {
 let chapter=playableArea(s.area)?chapterForArea(s.area):1;
 for(const [key,value]of Object.entries(s.flags))if(value&&key.startsWith('visited:')&&playableArea(key.slice(8)))chapter=Math.max(chapter,chapterForArea(key.slice(8)));
 return chapter;
}
export function gemTradeTier(s:GameState):number {const chapter=shopChapter(s);return [1,2,3,4,5].filter(t=>s.progression.level>=GEM_TRADE_LEVELS[t]&&chapter>=GEM_TRADE_CHAPTERS[t]).length;}
export const gemProductId=(stat:GemStat,tier:number)=>`GEM_${stat}_${tier}`;
export function shopProducts(merchant:string):ShopProduct[]{
 const definition=MERCHANTS[merchant],service=SHOP_SERVICES[merchant];if(!definition||!service)return [];
 const products:ShopProduct[]=Object.keys(definition.stock).map(id=>{const d=EQUIPMENT[id];return {id,kind:'equipment',item:id,name:d.name,description:`穿戴需求 Lv${d.requiredLevel??d.level}\n${d.description}`,price:definition.prices[id],level:1,chapter:merchant==='severin'?2:1};});
 if(service.supplies)for(const [id,d]of Object.entries(SUPPLIES))products.push({id,kind:'supply',supply:id as SupplyId,name:d.name,description:'旅行途中按需补充；安全整备处仍提供基础配给。',price:SHOP_PRICES.resource,level:1,chapter:1});
 if(service.gems){
  for(let tier=1;tier<=5;tier++)for(const stat of GEM_STATS)products.push({id:gemProductId(stat,tier),kind:'gem',name:gemName(tier),description:`标准宝石1颗 · 晶质5份\n${gemValueText(stat,tier)}\n可无损拆卸，三个同属性同阶宝石确定合成。`,price:GEM_PRICES[tier],level:GEM_TRADE_LEVELS[tier],chapter:GEM_TRADE_CHAPTERS[tier],stat,tier});
  products.push({id:'DRILLS',kind:'drills',name:'开孔材料',description:'用于开启装备额外孔位，不兑换宝石。任务与首领也可获得。',price:SHOP_PRICES.drills,level:6,chapter:1});
 }
 return products;
}
export const shopProduct=(merchant:string,id:string)=>shopProducts(merchant).find(p=>p.id===id);
