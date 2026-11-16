import type {CombatSkillDef,CombatSkillRank} from '../data/PureSkills';

/** Shared facts for the skill page, growth preview and HUD long press. */
export function skillRoleLabel(skill:CombatSkillDef):string {
 if(skill.activation==='automatic')return '自动强化';
 if(skill.type==='passive')return '职业被动';
 if(skill.type==='mobility')return '辅助 · 闪避';
 const role=skill.damageRole==='single'?'单体':skill.damageRole==='area'?'群攻':skill.damageRole==='control'?'群攻 · 控制':skill.damageRole==='support'?'辅助':'主动';
 return skill.type==='ultimate'?'终极 · '+role:role;
}

export function skillRankFacts(skill:CombatSkillDef,rank:CombatSkillRank):string[] {
 const facts:string[]=[];
 if(rank.maxDamagePerTargetS>0){
  facts.push(`${skill.activation==='automatic'?'强化额外伤害合计':'单敌直接伤害合计'} ${Number((rank.maxDamagePerTargetS*100).toFixed(1))}% 技能威力`+(rank.authoredDamageHits>1?` · 全${rank.authoredDamageHits}段`:''));
  if(rank.damagePerSecondaryTargetS!==undefined)facts.push(`连锁次目标 ${Number((rank.damagePerSecondaryTargetS*100).toFixed(1))}% 技能威力`);
  else if(skill.id==='BOW_02'&&rank.followUpDamageFraction!==undefined)facts.push(`后续目标为首目标伤害的 ${Math.round(rank.followUpDamageFraction*100)}%`);
 }
 if(skill.damageRole==='single')facts.push('每次施放仅命中同一个敌人');
 else if(skill.offensive&&rank.targetLimit)facts.push(`最多 ${rank.targetLimit} 个目标`);
 if(skill.id==='FIR_01')facts.push('燃烧伤害另计，不重复计算直接伤害段数');
 if(rank.shieldMaxHpPercent>0)facts.push(`护盾 ${rank.shieldMaxHpPercent}% 最大生命`);
 if(rank.healMaxHpPercent>0)facts.push(`治疗合计 ${rank.healMaxHpPercent}% 最大生命`);
 if(skill.id==='COM_02')facts.push('从补给栏第三格施放');
 if(skill.activation==='automatic')facts.push(`触发间隔 ${rank.cooldownSeconds}秒`,'满足条件自动触发，不占战斗按钮');
 return facts;
}
