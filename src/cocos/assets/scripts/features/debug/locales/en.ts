import type {zhCN} from './zh-CN';
export const en:Record<keyof typeof zhCN,string>={
 moveToSlot:'Slot {slot}',slotMoved:'Moved {skill} to slot {slot}; the previous skill swaps places.',
 'formation.horde':'Monster group',groupDetail:'Melee, shields and ranged · Enemies chase, attack and can die',monsterCount:'Monster count',monsterCountValue:'{count} enemies · Cycle 5 / 10 / 20',newWave:'New wave',newWaveDetail:'Respawn the whole group, refill and clear results',groupStats:'Alive {remaining}/{total} · Defeated {defeated}',hudGroupArea:'Monster group · Alive {count}/{total}', 'monster.raider':'Melee fighter','monster.shield':'Shield fighter','monster.archer':'Ranged fighter',
 hudGroupProgress:'Defeated {kills}/{total}',
 entryDetail:'Dedicated targets · Skill practice · Not saved',skillNotice:'Skills equip when selected. Choose a rank and close to practice.',mobilityReady:'Dodge is ready on its dedicated button',equipped:'Equipped {skill} and its weapon',debugTitle:'Skill range · Not saved',equip:'Equip selected skill and weapon',passiveInstruction:'Selecting a passive equips it in a passive slot.',activeInstruction:'Q/E/R/T or 1–4: active skills; G: ultimate. Selection equips the skill.',target:'Practice target',
 skillsSummary:'Lv40 · All styles · Ranks 1–5 · Not saved',resetDetail:'Reset targets, state and results',retaliate:'Sparring',retaliateOn:'On · Targets chase and attack for defensive practice',retaliateOff:'Off · Targets do not attack',injure:'Halve health',injureDetail:'Try healing with your current skill setup',
 title:'Skill range',description:'Temporary Lv40 character · 2m grid · Targets do not attack\nReturn to your journey on exit. Practice is never saved.',
 skills:'Skills and ranks',skillsDetail:'All styles · Active, ultimate, passive · Ranks 1–5',
 'formation.single':'Single target','formation.cluster':'Five clustered targets','formation.line':'Five targets in a line',selected:'Selected',
 distance:'Starting distance',distanceValue:'{metres}m · Cycle 1.5 / 4 / 8 / 12m',resource:'Class resource',unlimited:'Unlimited · Refilled every frame; cooldowns apply',normal:'Normal costs and regeneration',
 report:'Session results',stats:'Damage {damage} · Hits {hits} · Misses {misses} · Criticals {criticals}\nDPS {dps} · {seconds}s since first hit',
 reset:'Reset',exit:'Leave range',resume:'Resume',reportDescription:'Measures actual HP lost, including repeated, periodic and secondary damage. Hits count damage events. DPS includes idle time since the first hit and uses at least one second. Resetting or changing skill configuration clears the results.',
 toolbar:'Range settings',hudArea:'Skill range · {count} targets · {distance}m',hudDamage:'Damage {damage} · Hits {hits}',hudDps:'DPS {dps} · Tap for results',resetNotice:'Targets, health, resource, cooldowns and results reset',saved:'Temporary practice · Not saved',
};
