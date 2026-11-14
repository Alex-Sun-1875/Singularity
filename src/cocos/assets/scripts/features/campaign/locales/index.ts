import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'battle.complete':'{title} · 战线稳固',
 'battle.incoming':'{title} · 下一阵即将到来',
 'battle.progress':'{title} · 第{wave}/{total}阵 · 剩余{alive}',
 'wave.mill':'兽潮冲入 · 一鼓作气清开粮道',
 'wave.workshopMachine':'矿械压近 · 集中击破重型爬机',
 'wave.workshopBeasts':'兽潮最后一阵 · 工匠正在撤离',
 'wave.oath':'矿械与洞穴群 · 打穿最后防线',
};
const en:Record<keyof typeof zh,string>={
 'battle.complete':'{title} · Battle won',
 'battle.incoming':'{title} · Next wave incoming',
 'battle.progress':'{title} · Wave {wave}/{total} · {alive} remaining',
 'wave.mill':'Beasts incoming · Clear the grain road',
 'wave.workshopMachine':'Machines approaching · Focus the heavy crawler',
 'wave.workshopBeasts':'Final beast wave · Workers evacuating',
 'wave.oath':'Machines and cave beasts · Break the final line',
};
const translate=registerMessages('campaign',zh,en);
export const campaignText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
