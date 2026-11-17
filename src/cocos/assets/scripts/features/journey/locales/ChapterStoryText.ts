import {registerMessages} from '../../../shared/i18n/Localization';

const zh={
 'chapter.title':'第{chapter}章 · {name}',
 'chapter1.name':'兽潮之夜',
 'chapter1.story':'兽群逼近石桥镇，近期求援信却来自十八年前的阵亡者。夺回磨坊，追查灰披营地的扣押令，与伊芙琳和弥菈核对隐瞒的约定；亲自救出工匠、打开关口，再确认回来的人真正有地方可去。',
 'chapter2.name':'群山战火',
 'chapter2.story':'军队征用工匠与矿械，古代炉卫响应陌生号令。核验征用令、停稳过载工位，在采坑救援证人或保全货签；让前哨与三誓阵的选择留下后果。战胜守桥铠卫、亲手放桥，最后验证一次可以主动中止的核心接触。',
 'chapter3.story':'第三章的故事与任务正在筹备，宠物系统计划随本章正式开放。敬请期待。',
 'upcoming.name':'敬请期待',
 'upcoming.story':'新的旅程正在筹备，故事与任务将在后续版本开放。敬请期待。',
};
const en:Record<keyof typeof zh,string>={
 'chapter.title':'Chapter {chapter} · {name}',
 'chapter1.name':'Night of the Beast Tide',
 'chapter1.story':'Beasts approach Stonebridge, but a recent appeal comes from someone declared dead eighteen years ago. Reclaim the mill, trace the detention order and question Mira and Evelyn. Rescue the workers, open the pass, then make sure those who returned have somewhere to go.',
 'chapter2.name':'War in the Highlands',
 'chapter2.story':'The army requisitions workers and machines while old guardians answer an unfamiliar command. Verify the orders, stop the overloaded workshop and preserve a witness or cargo tags. Let your choices at the post and Oath Array matter. Defeat the bridge guard, lower the bridge yourself and verify a contact you can end.',
 'chapter3.story':'Chapter 3\'s story and quests are in preparation. The pet system is planned to open with this chapter\'s release. Stay tuned.',
 'upcoming.name':'Coming soon',
 'upcoming.story':'A new journey is in preparation. Its story and quests will open in a future update. Stay tuned.',
};
const translate=registerMessages('chapter-story',zh,en);
export const chapterStoryText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
