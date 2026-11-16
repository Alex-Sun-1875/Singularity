import {registerMessages} from '../../../shared/i18n/Localization';

const zh={
 'chapter.title':'第{chapter}章 · {name}',
 'chapter1.name':'兽潮之夜',
 'chapter1.story':'兽群逼近石桥镇，白昼亮起的旧哨塔牵出地下遗卫的异动。追查渡口遗物，夺回磨坊与灰披营地，深入采掘廊，最后挑战守住裂隘关的灰披队长。',
 'chapter2.name':'群山战火',
 'chapter2.story':'军队征用工匠与矿械，古代炉卫响应陌生号令。守住熔镜工位，在采坑救援证人或保全货签，选择交涉、破坏警报或战斗突破前哨，再解决三誓阵，面对断岳前堡的守桥铠卫。',
 'chapter3.story':'第三章的故事与任务正在筹备，宠物系统计划随本章正式开放。敬请期待。',
 'upcoming.name':'敬请期待',
 'upcoming.story':'新的旅程正在筹备，故事与任务将在后续版本开放。敬请期待。',
};
const en:Record<keyof typeof zh,string>={
 'chapter.title':'Chapter {chapter} · {name}',
 'chapter1.name':'Night of the Beast Tide',
 'chapter1.story':'Beasts approach Stonebridge as an old watchtower shines in daylight and ancient sentinels stir underground. Examine the river-crossing relics, reclaim the mill and Greycloak camp, explore the mining hall, then face the Greycloak Captain at the pass.',
 'chapter2.name':'War in the Highlands',
 'chapter2.story':'The army requisitions workers and mining machines while ancient guardians answer an unfamiliar command. Defend the workshop, rescue a quarry witness or preserve cargo tags, choose negotiation, alarm sabotage or battle at the ridge post, resolve the Oath Array, then face the armored bridge guard at the fortress.',
 'chapter3.story':'Chapter 3\'s story and quests are in preparation. The pet system is planned to open with this chapter\'s release. Stay tuned.',
 'upcoming.name':'Coming soon',
 'upcoming.story':'A new journey is in preparation. Its story and quests will open in a future update. Stay tuned.',
};
const translate=registerMessages('chapter-story',zh,en);
export const chapterStoryText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
