import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'title':'首领与精英','entry':'首领与精英','count':'{count} 个目标','range':'Lv{min}–{max}',
 'empty':'暂无已击败的 Lv{min}–{max} 首领或精英','explore':'前往探索','alive':'已出现','ready':'可再战','waiting':'等待刷新','after':'后可再战','wildAfter':'后尝试刷新',
 'boss':'章节首领','optional':'可选首领','elite':'精英','wild':'野外精英',
 'follow':'关注提醒','followed':'已关注','go':'自动前往','early':'提前前往','travel':'前往',
 'entrance':'{place} · 抵达入口后发起再战','approach':'{place} · 抵达后手动接近挑战','waitDetail':'{place} · 远离出生点20米，满足条件后刷新',
 'cooldown':'{place} · {time} 后可再战','blocked':'路线未开放或道路受阻','outOfRange':'目标尚未击败或已超出当前等级范围',
};
const en:Record<keyof typeof zh,string>={
 'title':'Bosses & elites','entry':'Bosses & elites','count':'{count} targets','range':'Lv{min}–{max}',
 'empty':'No defeated bosses or elites at Lv{min}–{max}','explore':'Explore','alive':'Appeared','ready':'Rematch ready','waiting':'Awaiting spawn','after':'until rematch','wildAfter':'until spawn check',
 'boss':'Chapter boss','optional':'Optional boss','elite':'Elite','wild':'Wild elite',
 'follow':'Follow','followed':'Following','go':'Travel','early':'Travel early','travel':'Go',
 'entrance':'{place} · Start the rematch at the entrance','approach':'{place} · Approach manually after arrival','waitDetail':'{place} · Leave 20m clearance and wait for spawn conditions',
 'cooldown':'{place} · Rematch in {time}','blocked':'Route locked or blocked','outOfRange':'Target not defeated yet or outside your current level range',
};
const tr=registerMessages('bosses',zh,en);
export const bossText=(key:keyof typeof zh,values:Record<string,string|number>={})=>tr(key,values,'zh-CN');
