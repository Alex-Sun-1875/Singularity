import {EQUIPMENT} from '../../equipment/data/Equipment';
import type {CombatSkillDef} from '../data/PureSkills';

type Requirement=Pick<CombatSkillDef,'compatibleWeapons'>;
export function skillWeaponCompatible(skill:Requirement,weapon:string|null|undefined):boolean {
 const kind=EQUIPMENT[weapon??'']?.kind;
 return skill.compatibleWeapons==='any'||skill.compatibleWeapons==='melee'&&kind==='sword'||skill.compatibleWeapons==='bow'&&kind==='bow'||skill.compatibleWeapons==='staff'&&kind==='staff';
}
export function skillWeaponRequirement(skill:Requirement):string {
 return skill.compatibleWeapons==='staff'?'需要装备法杖':skill.compatibleWeapons==='bow'?'需要装备弓箭':skill.compatibleWeapons==='melee'?'需要装备近战武器':'需要装备对应武器';
}
