import {registerMessages} from '../../../shared/i18n/Localization';
const zh={'species.fox':'赤狐','species.turtle':'岩龟','species.sprite':'白兔'} as const;
const en:Record<keyof typeof zh,string>={'species.fox':'Red Fox','species.turtle':'Rock Turtle','species.sprite':'White Rabbit'};
const translate=registerMessages('pets',zh,en);
// The current language preference controls story; preparation UI remains Chinese.
export const petText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');