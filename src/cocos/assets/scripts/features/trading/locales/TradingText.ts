import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 priceAscending:'价格↑',priceDescending:'价格↓',tierSuffix:'阶',ownedCompact:'持有 {count}',unitPrice:'单价 {gold}',afterCompact:'余 {gold}',shortfall:'还差 {gold} 金币',total:'合计',
 title:'商人服务',hint:'选择商人，前往现场交谈。',unknown:'尚未发现',go:'前往商人',all:'全部',
 windowTitle:'{name} · 交易',wallet:'金币 {gold}',itemDetail:'商品详情',itemCount:'共 {count} 件商品',materials:'材料',pendingShort:'待领 {gold}',
 wares:'宝石货架',ownedBadge:'格子角标为背包持有数量',ownedAmount:'背包持有 {count} {unit}',stableStock:'稳定供货 · 购买后存入背包',
 equipment:'装备',gem:'宝石',supply:'补给',drills:'开孔材料',categories:'货架分类',stock:'每件装备一旅程一份；补给、宝石与开孔材料稳定供货。',
 balance:'金币 {gold} · 待领 {pending}',end:'结束交易',back:'返回货架',buy:'确认购买',detail:'查看商品',quantity:'购买数量 ×{count}',
 price:'单价 {price} · 数量 {count} · 合计 {total}',after:'购买后金币 {gold}',capacity:'可重复购买的商品提供1／5／10份，购买前检查余额与容量。',
 known:'地点：{area} · {service}',travel:'前往 {name}',collect:'领取待领金币 {gold}',cultivate:'宝石培养',forge:'装备培养',
 out:'售罄',remaining:'本旅程余货 {count}',chapter:'第{chapter}章供货 · Lv{level}',rule:'宝石可购买或通过兑换码领取；打怪与任务提供强化材料。',
 saved:'交易完成，已保存。',failed:'交易未完成，请重新查看条件。',empty:'当前货架没有商品',
 greet:'我把每件货物的用途和价钱都写清楚了。挑路上用得上的，也可以先问问。',returned:'回镇的工匠已经重新开工，镇上的路和货架也渐渐恢复了。',
 firstGem:'宝石培养已开放，可在石桥镇广场找琳娜；商人服务里可以查看路线。',
};
const en:Record<keyof typeof zh,string>={
 priceAscending:'Cost ↑',priceDescending:'Cost ↓',tierSuffix:' tier',ownedCompact:'Owned {count}',unitPrice:'Each {gold}',afterCompact:'Left {gold}',shortfall:'Need {gold} gold',total:'Total',
 title:'Merchant services',hint:'Choose a merchant and speak in person.',unknown:'Undiscovered',go:'Visit merchant',all:'All',
 windowTitle:'{name} · Trade',wallet:'Gold {gold}',itemDetail:'Item details',itemCount:'{count} goods',materials:'Materials',pendingShort:'Pending {gold}',
 wares:'Gem wares',ownedBadge:'Grid badges show your current inventory',ownedAmount:'Owned: {count} {unit}',stableStock:'Always in stock · Sent to inventory',
 equipment:'Equipment',gem:'Gems',supply:'Supplies',drills:'Drilling materials',categories:'Categories',stock:'Equipment is stocked once per journey. Other goods remain available.',
 balance:'Gold {gold} · Pending {pending}',end:'End trade',back:'Back to wares',buy:'Confirm purchase',detail:'Inspect goods',quantity:'Quantity ×{count}',
 price:'Each {price} · Quantity {count} · Total {total}',after:'Gold after purchase {gold}',capacity:'Repeatable goods support quantities 1, 5 and 10, within wallet and carrying limits.',
 known:'Location: {area} · {service}',travel:'Visit {name}',collect:'Collect pending gold {gold}',cultivate:'Gem cultivation',forge:'Equipment cultivation',
 out:'Sold out',remaining:'Journey stock {count}',chapter:'Chapter {chapter} supply · Lv{level}',rule:'Gems come from shops or redemption codes. Combat and quests provide upgrade materials.',
 saved:'Trade complete and saved.',failed:'Trade failed. Review the current requirements.',empty:'No goods in this category',
 greet:'Every item has its purpose and price listed. Browse what you need for the road, or ask first.',returned:'The rescued craftspeople are back at work. Roads and trade are recovering.',
 firstGem:'Gem cultivation is available. Find Lina in Stonebridge square; Merchant services can guide you.',
};
const translate=registerMessages('trading',zh,en);
export const tradingText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
