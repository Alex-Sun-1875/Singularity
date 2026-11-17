import type {CombatSkillDef,CombatSkillRank} from '../data/PureSkills';

type HitCount=Pick<CombatSkillRank,'authoredDamageHits'> & Pick<Partial<CombatSkillRank>,'upgradeEffects'|'geometry'>;
type BeatSource={id?:string;skillId?:string;rank?:HitCount;ranks?:readonly HitCount[]};

// These beats are performed by the actor. Placed fire, a meteor's secondary
// ignition, ground aftershocks and healing/buff ticks remain world effects.
const ACTOR_BEATS=new Set(['WAR_01','WAR_02','WAR_04','WAR_05','BOW_03','BOW_05','THU_04','THU_05']);

/** Shared authoritative spacing. The optional argument is a hit payload (or
 * the authored hit count), not a character/skill level. */
export function combatSegmentInterval(skillId:string,rank?:HitCount|number):number {
 const hits=typeof rank==='number'?rank:rank?.authoredDamageHits??1;
 switch(skillId){
  case 'WAR_04':return typeof rank==='object'&&rank.geometry&&rank.geometry.kind!=='meleeWhirlwind'?.45:.48;
  case 'WAR_05':return .18;
  case 'BOW_03':return typeof rank==='object'?rank.upgradeEffects?.segmentSeconds??.10:.10;
  case 'FIR_02':return .30;
  case 'FIR_04':return 4/Math.max(1,hits);
  case 'FIR_05':return .75;
  case 'THU_04':case 'THU_05':return .25;
  default:return .16;
 }
}

/** Accepts an actual CombatCast, or a skill definition plus its accepted rank.
 * A definition without a rank describes its first tier only. */
export function combatActionBeatCount(source:BeatSource,rank?:HitCount):number {
 const id=source.skillId??source.id??'';
 if(!ACTOR_BEATS.has(id))return 1;
 const payload=rank??source.rank??source.ranks?.[0];
 if(id==='WAR_04'&&payload?.geometry&&payload.geometry.kind!=='meleeWhirlwind')return 1;
 const hits=(rank??source.rank??source.ranks?.[0])?.authoredDamageHits??1;
 return Math.max(1,Math.floor(hits));
}

/** Keep the actor through its final performed beat and full recovery. */
export function combatActionDuration(def:CombatSkillDef,rank:CombatSkillRank,windup:number,rushDuration=0):number {
 if(def.id==='COM_01')return .34;
 return Math.max(windup,def.releaseCommitSeconds)
  +(combatActionBeatCount(def,rank)-1)*combatSegmentInterval(def.id,rank)
  +def.recoverySeconds+rushDuration+(def.id==='BOW_07'?(rank as CombatSkillRank).moveSeconds??.2:0);
}
