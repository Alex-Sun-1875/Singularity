import {registerMessages} from '../../../shared/i18n/Localization';
import type {QuestRewardView} from '../common/QuestRewardView';
const zh={
 'cultivation':'培养：{tier}阶强化石 ×{stones}；宝石由商店或兑换码获得',
 'entry':'探索与成长','entryChapter':'第{chapter}章 · 探索与成长','entryHint':'查看已到访地点的一次性奖励与装备成长。',
 'title':'第{chapter}章 · 探索与成长','progress':'探索奖励 {done}/{total} · 已获经验 {earned}/{available}',
 'permanent':'一次性奖励永久保留，没有日期门槛。','pace':'主线、探索与自由狩猎均可成长，按自己的节奏推进。',
 'areas':'已到访地点','areaProgress':'已领取 {done}/{total} · 未领取 {pending}',
 'remaining':'待获得：{reward}','unknown':'尚未到访的地点','unknownDetail':'还有{count}处地点可探索；到访后显示具体内容。',
 'empty':'到访新的地点后，可在这里查看探索奖励。','claimed':'已领取','pending':'未领取','sourceReward':'奖励：{reward}',
 'sourceHint':'完成现场交互或固定战斗后自动结算，同一来源只领取一次。',
 'backChapter':'返回本章','backGrowth':'返回探索与成长','backArea':'返回地点清单','map':'在地图查看地点',
 'main':'主线奖励','exploration':'探索奖励','location':'地点：{area}','xp':'经验 {value}','gold':'金币 {value}','iron':'铁 {value}','runes':'符文 {value}','cores':'核心 {value}',
 'gear':'装备成长','gearTarget':'本章目标：主武器 +{weapon} · 其他部位 +{other} · 强化上限 +{cap}',
 'gearHint':'沿用已有装备与培养，按实际任务和首胜结算；无需等待日期。',
 'cultivationLevel':'Lv{level} · 当前培养上限',
 'cultivationCaps':'强化＋{rank} · 宝石{tier}阶 · 最多{holes}孔（另受装备品质限制）',
 'cultivationNext':'Lv{level}开放强化＋{rank}',
 'cultivationMax':'等级培养能力已全部开放，材料仍需实际获得。',
 'gearSummary':'中期主线任务获得阶段装备；关底首胜另结算固定装备。',
 'gearMid':'中期任务装备','gearBoss':'关底首胜装备','gearTask':'完成「{task}」后按当前职业获得。','gearTaskEntry':'查看任务',
 'gearOwned':'已获得：{item}','gearAwaitTask':'尚待完成任务','gearAwaitBoss':'尚待关底首胜','gearBossEntry':'查看关底奖励',
 'unopened':'本章尚未开放，暂无可领取的成长奖励。','noReward':'无额外奖励',
 'extraRewards':'额外探索奖励：{reward}','stepRewards':'奖励随各步实际完成结算，每个来源仅一次。','bossSeparate':'首领装备另按对应奖池结算，不包含在任务材料内。',
};
const en:Record<keyof typeof zh,string>={
 'cultivation':'Cultivation: tier {tier} upgrade stones ×{stones}; gems come from shops or redemption codes',
 'entry':'Exploration and growth','entryChapter':'Chapter {chapter} · Exploration and growth','entryHint':'View one-time rewards at visited locations and equipment growth.',
 'title':'Chapter {chapter} · Exploration and growth','progress':'Exploration rewards {done}/{total} · XP earned {earned}/{available}',
 'permanent':'One-time rewards remain available without date limits.','pace':'Progress through quests, exploration and hunting at your own pace.',
 'areas':'Visited locations','areaProgress':'Claimed {done}/{total} · Unclaimed {pending}',
 'remaining':'Available: {reward}','unknown':'Unvisited locations','unknownDetail':'{count} more locations to explore. Visit them to reveal their contents.',
 'empty':'Visit new locations to reveal their exploration rewards here.','claimed':'Claimed','pending':'Unclaimed','sourceReward':'Reward: {reward}',
 'sourceHint':'Rewards are paid automatically after the site action or fixed encounter, once per source.',
 'backChapter':'Back to chapter','backGrowth':'Back to exploration','backArea':'Back to location','map':'View location on map',
 'main':'Main quest reward','exploration':'Exploration reward','location':'Location: {area}','xp':'XP {value}','gold':'Gold {value}','iron':'Iron {value}','runes':'Runes {value}','cores':'Cores {value}',
 'gear':'Equipment growth','gearTarget':'Chapter target: main weapon +{weapon} · other slots +{other} · upgrade cap +{cap}',
 'gearHint':'Keep existing equipment and cultivation. Rewards follow actual quests and first victories, without date gates.',
 'cultivationLevel':'Lv{level} · Current cultivation limits',
 'cultivationCaps':'Upgrade +{rank} · tier {tier} gems · up to {holes} sockets, subject to item quality',
 'cultivationNext':'Upgrade +{rank} unlocks at Lv{level}',
 'cultivationMax':'All level gates are open. Materials must still be earned.',
 'gearSummary':'Mid-chapter quests award stage equipment. The chapter first victory awards its separate fixed equipment.',
 'gearMid':'Mid-chapter quest equipment','gearBoss':'Chapter first-victory equipment','gearTask':'Complete “{task}” for equipment matching your current profession.','gearTaskEntry':'View quest',
 'gearOwned':'Obtained: {item}','gearAwaitTask':'Quest not yet complete','gearAwaitBoss':'Awaiting the chapter first victory','gearBossEntry':'View chapter boss rewards',
 'unopened':'This chapter is not open. Its growth rewards are unavailable.','noReward':'No additional reward',
 'extraRewards':'Additional exploration rewards: {reward}','stepRewards':'Each source pays once when its quest step is completed.','bossSeparate':'Boss equipment is settled separately through its own reward pool.',
};
const translate=registerMessages('campaign-pacing-ui',zh,en);
export const pacingText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
export function pacingRewardText(reward:{experience?:number;gold:number;iron:number;runes?:number;cores?:number}):string {
 const parts:string[]=[];
 if(reward.experience!==undefined&&reward.experience>0)parts.push(pacingText('xp',{value:reward.experience}));
 for(const key of ['gold','iron','runes','cores'] as const)if(reward[key])parts.push(pacingText(key,{value:reward[key]!}));
 return parts.join(' · ')||pacingText('noReward');
}
export function pacingQuestRewardText(view:QuestRewardView):string {
 const parts:string[]=[];
 if(view.hasRegistered)parts.push(pacingRewardText(view.registered));
 if(view.hasExtra)parts.push(pacingText('extraRewards',{reward:pacingRewardText(view.extra)}));
 if(view.hasBoss)parts.push(pacingText('bossSeparate'));
 for(const [tier,gift]of Object.entries(view.cultivation))parts.push(pacingText('cultivation',{tier,stones:gift.stones,gems:gift.gems}));
 return parts.join('\n')||pacingText('noReward');
}
