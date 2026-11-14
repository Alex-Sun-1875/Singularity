import {registerMessages} from '../../../shared/i18n/Localization';
import {zh,type EquipmentMessageKey} from './zh-CN';
import {en} from './en';
import type {EquipmentChange} from '../common/EquipmentChange';
const translate=registerMessages('equipment',zh,en);
// The current preference is specifically Story language. Gear remains Chinese until its full UI is localized.
export const equipmentText=(key:EquipmentMessageKey,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
export function equipmentChangeReason(change:EquipmentChange):string{
 switch(change.block){
  case 'busy':return change.reason;
  case 'level':return equipmentText('reason.level',{level:change.requiredLevel});
  case 'slot':return equipmentText('reason.slot');
  case 'unowned':return equipmentText('reason.unowned');
  case 'two-handed':return equipmentText('reason.twoHanded');
  case 'equipped':return equipmentText('reason.equipped');
  default:return equipmentText('reason.missing');
 }
}
