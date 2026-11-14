import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'talk.merchant':'来了？要不要看看货物，挑件路上用得上的？','talk.shop':'看看货物','talk.noThanks':'暂时不用，谢谢',
 'talk.task':'要仔细调查一下这里的线索吗？','talk.proceed':'准备好继续了吗？','talk.ready':'我准备好了','talk.later':'稍后再说',
 'talk.kael':'我正在复核退路。你要不要一起看看这张通路图？','talk.route':'让我看看通路图',
 'beast.boar.name':'棘牙野猪','beast.spider.name':'灰纹洞穴蛛','beast.scorpion.name':'岩尾蝎',
 'beast.boar.counter':'低头刨地后短距冲撞；侧移避开，趁停步收势反击。',
 'beast.spider.counter':'前足抬起后短扑；让开正面，落地时用群攻清理。',
 'beast.scorpion.counter':'尾钩后卷后向前刺击；横移避开窄直道，收尾时近身攻击。',
 'move.boar.charge':'刨地拱撞','move.boar.bite':'獠牙挑咬',
 'move.spider.leap':'伏身短扑','move.spider.bite':'前足钳咬',
 'move.scorpion.sting':'蓄尾直刺','move.scorpion.claw':'双钳夹击',
};
const en:Record<keyof typeof zh,string>={
 'talk.merchant':'Welcome. Would you like to browse my wares for the road ahead?','talk.shop':'Browse wares','talk.noThanks':'No thanks for now',
 'talk.task':'Shall we take a closer look at these clues?','talk.proceed':'Ready to continue?','talk.ready':'I am ready','talk.later':'Talk later',
 'talk.kael':'I am checking the way back. Would you like to look over this route map with me?','talk.route':'Show me the route map',
 'beast.boar.name':'Bramble Boar','beast.spider.name':'Slate Cave Spider','beast.scorpion.name':'Rock Scorpion',
 'beast.boar.counter':'Sidestep its head-down charge, then punish the recovery.',
 'beast.spider.counter':'Move aside when its front legs rise; sweep the group after it lands.',
 'beast.scorpion.counter':'Sidestep its narrow tail thrust, then close in during recovery.',
 'move.boar.charge':'Tusk charge','move.boar.bite':'Tusk bite',
 'move.spider.leap':'Short pounce','move.spider.bite':'Fang bite',
 'move.scorpion.sting':'Tail thrust','move.scorpion.claw':'Pincer crush',
};
const translate=registerMessages('world',zh,en);
export const beastText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
export const worldText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
