import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'mode.task':'自动','mode.hunt':'挂机','mode.operations':'自动操作','action.resume':'继续','action.stop':'停止','action.navigate':'寻路',
 'daily.header':'战斗{earned}/{cap}','daily.loading':'战斗—/—','daily.maxLevel':'已满级',
 'task.select':'自动 · 选择下一目标','task.travel':'自动 · 前往{target}','task.fight':'自动 · 处理敌人','task.interact':'自动 · 调查目标','task.settle':'自动 · 等待任务结算',
 'hunt.search':'挂机 · 寻找猎物','hunt.fight':'挂机 · 正在战斗','hunt.wait':'挂机 · 等待猎物刷新','hunt.empty':'本场景没有循环猎物','hunt.unreachable':'挂机 · 寻找可达猎物','hunt.capped':'挂机 · 今日经验额度已满',
 'loot.collect':'{mode} · 拾取掉落','loot.approach':'{mode} · 前往拾取','target.blocked':'{mode} · 暂时跳过受阻目标',
 'pause.manual':'已手动接管 · 点击继续','pause.menu':'自动操作暂挂 · 菜单关闭后继续','pause.story':'自动操作暂挂 · 剧情结束后继续','pause.dialogue':'自动操作暂挂 · 完成交互后继续','pause.dice':'自动操作暂挂 · 完成检定后继续',
 'pause.background':'已暂停 · 返回游戏后点击继续','pause.auth':'已暂停 · 登录完成后点击继续','pause.portrait':'已暂停 · 横屏后点击继续','pause.failure':'已暂停 · 资源恢复后点击继续','pause.blocked':'道路受阻 · 点击继续重试',
 'navigation.paused':'寻路已暂停 · 点击继续','navigation.threat':'前方有敌人 · 处理后继续寻路','navigation.travel':'寻路 · {target}','navigation.arrived':'已抵达{target}。',
 'interaction.confirm':'确认交互','interaction.investigate':'调查','interaction.cancel':'稍后','interaction.unavailable':'目标暂不可交互',
 'route.locked':'目标路线尚未开放，请先解锁道路或提升等级。','task.missing':'没有可执行的任务或可达猎区。','task.failed':'目标暂时无法执行 · 点击继续重试',
 'health.low':'生命过低且无可用恢复路线 · 点击继续','health.return':'自动 · 前往检查点恢复','health.retreat':'自动 · 脱离危险','health.rest':'自动 · 检查点休整','health.failed':'无法安全抵达检查点 · 点击继续',
 'dead':'自动操作已停止，请手动返回检查点。','daily.summary':'刷怪经验 {earned}/{cap} · {rate}%','daily.limit':'今日刷怪经验已满 · 仍可拾取','daily.label':'刷怪经验','daily.value':'{earned}/{cap}','daily.rate':'{rate}%收益','daily.capped':'已达上限',
 'started.task':'自动任务已开启，赶路、战斗和任务阶段将连续执行。','started.hunt':'本场景挂机已开启。','stopped':'自动操作已停止。',
};
const en:Record<keyof typeof zh,string>={
 'mode.task':'Auto','mode.hunt':'Hunt','mode.operations':'Automation','action.resume':'Resume','action.stop':'Stop','action.navigate':'Travel',
 'daily.header':'XP {earned}/{cap}','daily.loading':'XP —/—','daily.maxLevel':'Max level',
 'task.select':'Auto · Finding objective','task.travel':'Auto · Going to {target}','task.fight':'Auto · Fighting','task.interact':'Auto · Investigating','task.settle':'Auto · Awaiting completion',
 'hunt.search':'Hunt · Finding prey','hunt.fight':'Hunt · Fighting','hunt.wait':'Hunt · Awaiting respawn','hunt.empty':'No repeatable enemies here','hunt.unreachable':'Hunt · Finding reachable prey','hunt.capped':'Hunt · Daily XP capped',
 'loot.collect':'{mode} · Collecting loot','loot.approach':'{mode} · Approaching loot','target.blocked':'{mode} · Skipping blocked target',
 'pause.manual':'Manual control · Tap resume','pause.menu':'Paused · Resumes after menu','pause.story':'Paused · Resumes after story','pause.dialogue':'Paused · Resumes after dialogue','pause.dice':'Paused · Resumes after check',
 'pause.background':'Paused · Tap resume after returning','pause.auth':'Paused · Tap resume after login','pause.portrait':'Paused · Resume in landscape','pause.failure':'Paused · Resume after recovery','pause.blocked':'Route blocked · Tap resume',
 'navigation.paused':'Travel paused · Tap resume','navigation.threat':'Enemy ahead · Clear it then resume','navigation.travel':'Travel · {target}','navigation.arrived':'Arrived at {target}.',
 'interaction.confirm':'Interact','interaction.investigate':'Investigate','interaction.cancel':'Later','interaction.unavailable':'Target unavailable',
 'route.locked':'Route unavailable. Unlock it or level up first.','task.missing':'No available quest or reachable hunting ground.','task.failed':'Objective unavailable · Tap resume',
 'health.low':'Low health and no recovery route · Tap resume','health.return':'Auto · Returning to checkpoint','health.retreat':'Auto · Retreating','health.rest':'Auto · Resting','health.failed':'Cannot safely reach checkpoint · Tap resume',
 'dead':'Automation stopped. Return to the checkpoint manually.','daily.summary':'Hunt XP {earned}/{cap} · {rate}%','daily.limit':'Daily hunt XP capped · Loot still available','daily.label':'Hunt XP','daily.value':'{earned}/{cap}','daily.rate':'{rate}% XP','daily.capped':'Capped',
 'started.task':'Auto quests enabled: travel, combat and quest stages continue automatically.','started.hunt':'Hunting enabled in this area.','stopped':'Automation stopped.',
};
const translate=registerMessages('automation',zh,en);
// The existing language preference still covers story only.
export const automationText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
