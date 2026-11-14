/** Shared visual semantics. Pure data: no engine, storage, or gameplay rules. */
const P={ivory:'#EDE4CB',muted:'#AF9D85',red:'#F18E9F',enemy:'#C4332F',loss:'#DE9352',green:'#7BDEB4',cyan:'#83CDE6',amber:'#F0B666',gold:'#F7DA9D',fire:'#F7A765',lightning:'#A9B4FF',purple:'#C4A5ED',orange:'#F5A45D',dark:'#150F10'} as const;
export const FEEDBACK_PALETTE={
 'text.normal':P.ivory,'text.preparation':'#FFF0C9','text.preparationAccent':'#F2CB82','text.secondary':P.muted,'text.disabled':P.muted,'text.outline':P.dark,'icon.normal':'#FFFFFF',
 'control.disabled':'#120D0A',
 'state.selected':'#75C5B9','state.idle':P.ivory,'state.running':P.cyan,'state.paused':P.amber,'state.ready':P.gold,'state.success':P.green,'state.failure':P.red,'state.blocked':P.muted,
 'impact.core':'#FFF5DC','impact.metal':'#E4D3B0',
 'aim.range':'#E4D3B0','aim.edge':P.ivory,'aim.gold':'#C2AA79','aim.shadow':'#241C11','aim.highlight':'#FFF5DC',
 'resource.stamina':P.amber,'resource.focus':P.green,'resource.mana':P.cyan,
 'health.player':'#C35D75','health.text':P.green,'health.enemy':P.enemy,'health.loss':P.loss,'health.low':P.amber,'health.critical':P.red,'health.shield':P.cyan,
 'damage.physical':P.ivory,'damage.fire':P.fire,'damage.lightning':P.lightning,'damage.arcane':P.purple,'damage.taken':P.red,'damage.heal':P.green,'damage.absorbed':P.cyan,'damage.miss':P.muted,'damage.critical':P.gold,
 'identity.enemy':P.red,'identity.ally':P.green,'identity.neutral':P.ivory,'identity.elite':P.amber,'identity.boss':P.gold,
 'telegraph.windup':P.amber,'telegraph.active':P.red,'telegraph.friendly':P.cyan,
 'status.burn':P.fire,'status.slow':P.cyan,'status.control':P.purple,'status.buff':P.green,
 'skill.WAR':P.ivory,'skill.BOW':P.green,'skill.FIR':P.fire,'skill.THU':P.lightning,'skill.COM':P.gold,
 'quality.common':P.muted,'quality.fine':P.green,'quality.rare':P.cyan,'quality.epic':P.purple,'quality.legendary':P.orange,'quality.artifact':P.orange,
 'map.player':P.cyan,'map.ally':P.green,'map.enemy':P.red,'map.task':P.gold,'map.exit':P.cyan,'map.unknown':P.muted,
 'reward.gold':P.gold,'reward.experience':P.purple,'reward.skillPoint':P.green,
} as const;
export type FeedbackRole=keyof typeof FEEDBACK_PALETTE;
export interface NavigationFeedbackState {navigating:boolean;paused:boolean;arrived:boolean;blocked:boolean}
export function navigationFeedbackRole(s:NavigationFeedbackState):FeedbackRole {
 return s.navigating?'state.running':s.arrived?'state.ready':s.paused?'state.paused':s.blocked?'state.blocked':'state.idle';
}
const NAVIGATION_LABELS={
 'state.running':{button:'停止寻路',status:'自动寻路中'},'state.ready':{button:'已抵达目标',status:'等待现场操作'},
 'state.paused':{button:'继续寻路',status:'寻路已暂停'},'state.blocked':{button:'暂不可达',status:'路线受阻'},'state.idle':{button:'自动寻路',status:''},
} as const;
export function navigationFeedback(s:NavigationFeedbackState){const role=navigationFeedbackRole(s) as keyof typeof NAVIGATION_LABELS;return {role,...NAVIGATION_LABELS[role]};}
export function playerHealthFeedbackRole(hp:number,maxHp:number):FeedbackRole {
 const fraction=maxHp>0?hp/maxHp:0;return fraction<=.15?'health.critical':fraction<=.3?'health.low':'health.player';
}
/** Sources are the actual combat event element/family, never inferred from damage size. */
export function damageFeedbackRole(source?:string):FeedbackRole {
 if(source==='FIR'||['fire','burn','environment'].includes(source??''))return 'damage.fire';
 if(source==='THU'||source==='lightning')return 'damage.lightning';
 if(source==='arcane')return 'damage.arcane';return 'damage.physical';
}
const QUALITY_ROLES:Readonly<Record<string,FeedbackRole>>={'普通':'quality.common','精良':'quality.fine','稀有':'quality.rare','史诗':'quality.epic','传奇':'quality.legendary','神器':'quality.artifact'};
export function qualityFeedbackRole(quality:string):FeedbackRole{return QUALITY_ROLES[quality]??'quality.common';}
export function eventFeedbackRole(event:{type:string;success?:unknown}):FeedbackRole {
 if(['hurt','dead'].includes(event.type))return 'state.failure';
 if(event.type==='check_result')return event.success?'state.success':'state.paused';
 if(['journey_complete','quest','rest','supply_pickup'].includes(event.type))return 'state.success';
 if(event.type==='level_up'||event.type==='experience')return 'reward.experience';
 if(event.type==='reward')return 'reward.gold';
 if(event.type==='notice')return 'state.paused';return 'text.normal';
}
