import {registerMessages} from '../../../shared/i18n/Localization';
const zh={cargoRush:'矿机突进'};
const en:Record<keyof typeof zh,string>={cargoRush:'Reclaimer rush'};
const translate=registerMessages('side-boss-combat',zh,en);
export const sideBossCombatText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
