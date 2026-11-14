import {registerMessages} from '../../../shared/i18n/Localization';
import {zhCN} from './zh-CN';
import {en} from './en';
const text=registerMessages('training',zhCN,en);
export function trainingText(key:string,values?:Record<string,string|number>){return text(key as keyof typeof zhCN,values);}
