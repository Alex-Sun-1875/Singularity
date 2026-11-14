import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'marker.task':'任务目标','marker.travel':'任务去向','marker.hunt':'狩猎','marker.boss':'任务首领',
 'radar.exit':'任务出口','radar.hunt':'狩猎目标','radar.blocked':'目标受阻','status.blocked':'受阻',
 'action.investigate':'调查','action.interact':'交互','action.defeat':'击败','action.hunt':'狩猎','action.travel':'前往','action.rest':'休整',
 'detail.blocked':'路线受阻','detail.distance':'{distance}米',
 'growth.boss':'关底 Lv{level} · 当前 Lv{current}，先在附近狩猎成长',
 'growth.bossRoute':'Lv{level} · 无任务前置，实际击败后通关',
 'growth.summary':'前两章约10天 · Lv1—20。今日战斗经验 {earned}/{cap}，手动、自动与挂机共享；挂机另限1000。任务与首通经验另计。',
 'growth.hunt':'建议选择接近自身等级的猎区；低于角色4级起，重复击杀经验逐步减少。',
 'life.rewardUnlocked':'任务装备已解锁，可在旅程中领取；战斗装备仍由随机掉落获得。','life.chapterCleared':'第{chapter}章通关 · 可继续挑战Boss随机战利品',
 'life.weaponChoice':'Lv{level} · {family} · 武器强度 {power}',
 'life.title':'第{chapter}章 · 任务装备与随机战利品','life.task':'任务固定 · {quality} · {name}','life.claimed':'已领取 · {name}','life.ready':'可领取','life.locked':'完成 {task} 后可领取','life.choose':'{name} · 领取装备','life.choice':'选择一件；取消会保留资格。武器四流派各有对应形态。',
 'life.random':'战斗随机 · {quality} · {name}','life.randomDetail':'Lv{level} · 奖池中可获得，未保证掉出或集齐。','life.rules':'击败Boss有机会获得珍稀装备；首杀与再战均可获得战利品，固定任务装备另计。','life.preference':'武器掉落偏好 · {style}','life.preferenceHint':'默认跟随当前流派；选择后仅影响新掉落，不重抽已生成物品。','life.sources':'查看战斗奖池与Boss冷却','life.taskReward':'任务装备','life.legacy':'旧版已解锁奖励 · {route}',
 'life.cooldown':'再战剩余 {time} · 到时前往入口主动挑战','life.bossAlive':'Boss尚未击败 · 首杀也参与随机掉落','life.bossReady':'可前往本地再战入口挑战 · 10分钟冷却','life.claimOk':'任务装备已领取，可在行囊装备。','life.claimFailed':'请先完成对应任务，并在脱战后领取。','life.styleSet':'武器掉落偏好已设为{style}。','life.styleAuto':'跟随当前流派',
 'life.daily':'战斗 {earned}/{cap} · 挂机 {idle}/{idleCap} · 今日初始 Lv{level}','life.legacyHint':'更新前已经获得的领取资格继续保留。','life.artifact':'共享成长神器 · {name}','life.artifactDetail':'挑战各地Boss有机会获得，可随角色成长。','life.bossFighting':'本轮Boss存活 · 击败后开始10分钟冷却','life.styleWar':'破军','life.styleBow':'弓术','life.styleFire':'火术','life.styleThunder':'雷术','life.selected':'已选',
};
const en:Record<keyof typeof zh,string>={
 'marker.task':'Quest target','marker.travel':'Quest route','marker.hunt':'Hunt','marker.boss':'Quest boss',
 'radar.exit':'Quest exit','radar.hunt':'Hunt target','radar.blocked':'Route blocked','status.blocked':'Blocked',
 'action.investigate':'Investigate','action.interact':'Interact','action.defeat':'Defeat','action.hunt':'Hunt','action.travel':'Travel','action.rest':'Rest',
 'detail.blocked':'Route blocked','detail.distance':'{distance}m',
 'growth.boss':'Boss Lv{level} · Currently Lv{current}. Hunt nearby to prepare.',
 'growth.bossRoute':'Lv{level} · No quest prerequisite. Defeat the boss to clear.',
 'growth.summary':'Chapters 1–2: about 10 days, Lv1–20. Combat XP {earned}/{cap}, shared by manual, auto and idle. Idle also has a 1000 limit. Quest and first-clear XP are separate.',
 'growth.hunt':'Hunt near your level. Repeat kills start granting less XP when enemies are four or more levels below you.',
 'life.rewardUnlocked':'Quest equipment unlocked. Claim it from Journey; combat equipment remains random.','life.chapterCleared':'Chapter {chapter} cleared · Challenge Bosses for random loot.',
 'life.weaponChoice':'Lv{level} · {family} · Weapon strength {power}',
 'life.title':'Chapter {chapter} · Quest equipment and random loot','life.task':'Quest reward · {quality} · {name}','life.claimed':'Claimed · {name}','life.ready':'Ready to claim','life.locked':'Complete {task} to claim','life.choose':'{name} · Choose equipment','life.choice':'Choose one. Cancelling keeps the reward. Weapon forms cover all four styles.',
 'life.random':'Random loot · {quality} · {name}','life.randomDetail':'Lv{level} · Available in the pool, not guaranteed to drop.','life.rules':'Defeat Bosses for a chance at rare equipment. First clears and rematches both grant loot; quest equipment is separate.','life.preference':'Weapon loot preference · {style}','life.preferenceHint':'Defaults to your current style. Changes apply to future drops only.','life.sources':'View loot pools and Boss cooldowns','life.taskReward':'Quest equipment','life.legacy':'Previously earned reward · {route}',
 'life.cooldown':'Rematch in {time} · Return to the entrance when ready','life.bossAlive':'Boss undefeated · First clear also rolls loot','life.bossReady':'Ready at the local rematch entrance · 10 minute cooldown','life.claimOk':'Quest equipment claimed. Equip it from inventory.','life.claimFailed':'Complete the quest and leave combat before claiming.','life.styleSet':'Weapon loot preference set to {style}.','life.styleAuto':'Follow current style',
 'life.daily':'Combat {earned}/{cap} · Idle {idle}/{idleCap} · Starting Lv{level}','life.legacyHint':'Reward eligibility earned before the update is retained.','life.artifact':'Shared growing artifact · {name}','life.artifactDetail':'A possible reward from Bosses across the world that grows with your character.','life.bossFighting':'Boss alive · 10 minute cooldown starts after defeat','life.styleWar':'Melee','life.styleBow':'Bow','life.styleFire':'Fire','life.styleThunder':'Thunder','life.selected':'Selected',
};
const translate=registerMessages('journey',zh,en);
// The current language preference still covers story only, like the automation UI.
export const journeyText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
