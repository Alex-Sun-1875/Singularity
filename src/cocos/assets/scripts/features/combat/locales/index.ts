import {registerMessages} from '../../../shared/i18n/Localization';
const zh={'boss.wardenSweep':'收盾横扫'};
const en:Record<keyof typeof zh,string>={'boss.wardenSweep':'Shield sweep'};
const translate=registerMessages('combat',zh,en);
export const combatText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
