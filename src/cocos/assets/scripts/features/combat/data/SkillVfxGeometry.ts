import type {CombatSkillEvent} from '../../../core/Contracts';
import {COMBAT_SKILLS,type SkillGeometry} from './PureSkills';

/** Accepted cast dimensions win over catalog data, including authored zeroes. */
export function skillVfxGeometry(e:Pick<CombatSkillEvent,'skillId'|'rank'|'shape'|'radius'|'width'|'length'|'depth'|'angleDegrees'|'anglesDegrees'|'geometry'>):SkillGeometry {
 const r=COMBAT_SKILLS[e.skillId]?.ranks[Math.max(0,Math.min(4,(e.rank??1)-1))],g=e.geometry??r?.geometry;
 return {...g,kind:e.shape??g?.kind??'self',origin:g?.origin??'caster',
  radiusMetres:e.radius??g?.radiusMetres??0,widthMetres:e.width??g?.widthMetres??0,
  lengthMetres:e.length??g?.lengthMetres??0,depthMetres:e.depth??g?.depthMetres??0,
  angleDegrees:e.angleDegrees??g?.angleDegrees??0,anglesDegrees:e.anglesDegrees??g?.anglesDegrees};
}
/** Pure local-to-world convention also used by the combat rectangle predicates. */
export function skillLocalPoint(p:{x:number;z:number},angle:number,side:number,forward:number){return{x:p.x+Math.cos(angle)*side+Math.sin(angle)*forward,z:p.z-Math.sin(angle)*side+Math.cos(angle)*forward};}
