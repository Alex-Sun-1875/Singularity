import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'evade':'精准闪避','evadeReady':'精准闪避 · 可反击','counterReady':'反击就绪','counter':'反击','guard':'盾挡','magicGuard':'法术偏折','guardBreak':'破防','interrupt':'打断','stagger':'失衡',
 'dodgeHelp':'0.06–0.20秒内闪开直接攻击可精准闪避：恢复6点职业资源，2.5秒内下一次攻击或技能伤害提高20%；持续地面伤害仍须离开。',
 'combatHelp':'敌人不显示地面技能范围，观察蓄势动作、连招和收招停顿，侧移避开后反击。破阵技与近战第三段能削韧，普通怪可被打断，首领须积满100点韧性破坏且招式可打断时才失衡。盾兵正面减伤，绕侧或破盾再出手。',
} as const;
const en:Record<keyof typeof zh,string>={
 'evade':'Perfect dodge','evadeReady':'Dodge · Counter','counterReady':'Counter ready','counter':'Counter','guard':'Guard','magicGuard':'Deflected','guardBreak':'Guard broken','interrupt':'Interrupted','stagger':'Staggered',
 'dodgeHelp':'Dodge a direct hit during 0.06–0.20s to restore 6 class resource and empower your next attack or skill by 20% within 2.5s. Move out of persistent ground hazards.',
 'combatHelp':'Enemies show no ground range overlays: watch their anticipation, combos and recovery pauses, sidestep attacks, then counter. Break skills and third melee strikes damage poise. Bosses require 100 poise damage during an interruptible move or opening to stagger. Flank or break frontal guards.',
};
const tr=registerMessages('combat-tactics',zh,en);
export const tacticsText=(key:keyof typeof zh)=>tr(key,{},'zh-CN');
