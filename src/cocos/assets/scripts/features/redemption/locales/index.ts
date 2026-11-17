import {registerMessages} from '../../../shared/i18n/Localization';
import {zh,type RedemptionMessageKey} from './zh-CN';
import {en} from './en';
const translate=registerMessages('redemption',zh,en);
export const redemptionText=(key:RedemptionMessageKey,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
export type {RedemptionMessageKey};
