import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'event.captain':'灰披队长','event.defeatPrerequisite':'击败{name}','event.goPrerequisite':'前往前置任务（自动导航）','event.choosePrerequisite':'选择前置任务','event.navigate':'自动导航','event.navigationHint':'选择要先完成的任务。自动导航遵守道路与等级限制，遇敌暂停；抵达后按提示完成行动。',
 'event.confirm':'执行这项行动','event.ready':'条件已满足，确认后执行这项行动。','event.locked':'条件未满足','event.completed':'已完成','event.viewResult':'查看结果','event.viewRequirements':'查看条件','event.return':'返回旅途',
 'event.unavailable':'这项行动当前不可执行。','event.complete':'已完成：{label}',
 'event.requires':'现场前置行动','event.requiresAll':'请先完成：{requirements}','event.requiresAny':'还需完成其中一项：{requirements}','event.clearEncounter':'请先处理本地固定守军及其增援。','event.leaveCombat':'请先离开敌人的攻击范围。',
 'event.cancelHunt':'缴销猎契','event.huntPrerequisite':'前往湿林庄园，阅读“被转卖的猎径副图”，再返回岩林登记台。','event.huntComplete':'猎契已缴销，督猎封锁已解除。沿线藏身处不再列为追猎目标；野外游荡怪仍按狩猎周期出没。',
 'battle.complete':'{title} · 战线稳固',
 'battle.incoming':'{title} · 下一阵即将到来',
 'battle.progress':'{title} · 第{wave}/{total}阵 · 剩余{alive}',
 'wave.mill':'兽潮冲入 · 一鼓作气清开粮道',
 'wave.workshopMachine':'矿械压近 · 集中击破重型爬机',
 'wave.workshopBeasts':'兽潮最后一阵 · 工匠正在撤离',
 'wave.oath':'矿械与洞穴群 · 打穿最后防线',
};
const en:Record<keyof typeof zh,string>={
 'event.captain':'Greycloak Captain','event.defeatPrerequisite':'Defeat {name}','event.goPrerequisite':'Navigate to prerequisite','event.choosePrerequisite':'Choose a prerequisite','event.navigate':'Auto-navigate','event.navigationHint':'Choose a prerequisite. Navigation follows open roads and level requirements, and pauses for enemies. Follow the prompts on arrival.',
 'event.confirm':'Carry out action','event.ready':'Requirements met. Confirm to carry out this action.','event.locked':'Requirements not met','event.completed':'Completed','event.viewResult':'View result','event.viewRequirements':'View requirements','event.return':'Return to journey',
 'event.unavailable':'This action is currently unavailable.','event.complete':'Completed: {label}',
 'event.requires':'the prerequisite field action','event.requiresAll':'Complete first: {requirements}','event.requiresAny':'Also complete one of: {requirements}','event.clearEncounter':'Clear the local fixed guards and their reinforcements first.','event.leaveCombat':'Leave enemy attack range first.',
 'event.cancelHunt':'Cancel hunting contract','event.huntPrerequisite':'Read the resold hunting-route copy in the Wetwood Estate, then return to the rockwood registry.','event.huntComplete':'The contract is cancelled and the huntmaster blockade is lifted. The hideouts are no longer hunting targets. Roaming wildlife still respawns on its hunting cycle.',
 'battle.complete':'{title} · Battle won',
 'battle.incoming':'{title} · Next wave incoming',
 'battle.progress':'{title} · Wave {wave}/{total} · {alive} remaining',
 'wave.mill':'Beasts incoming · Clear the grain road',
 'wave.workshopMachine':'Machines approaching · Focus the heavy crawler',
 'wave.workshopBeasts':'Final beast wave · Workers evacuating',
 'wave.oath':'Machines and cave beasts · Break the final line',
};
const translate=registerMessages('campaign',zh,en);
export const campaignText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
