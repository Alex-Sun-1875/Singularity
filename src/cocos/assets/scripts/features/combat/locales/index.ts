import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'boss.wardenSweep':'收盾横扫',
 'feedback.evasion':'闪避','feedback.critical':'暴击','feedback.absorbed':'吸收',
};
const en:Record<keyof typeof zh,string>={
 'boss.wardenSweep':'Shield sweep',
 'feedback.evasion':'Evade','feedback.critical':'Critical','feedback.absorbed':'Absorbed',
};
const translate=registerMessages('combat',zh,en);
export const combatText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
