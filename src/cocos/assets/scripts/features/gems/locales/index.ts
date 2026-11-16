import {registerMessages} from '../../../shared/i18n/Localization';
import {zh,type GemMessageKey} from './zh-CN';
import {en} from './en';
const translate=registerMessages('gems',zh,en);
// The current setting controls story language; match the equipment UI language.
export const gemText=(key:GemMessageKey,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
export type {GemMessageKey};
