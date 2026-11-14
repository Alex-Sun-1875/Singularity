import type {AreaDef} from '../../../core/Contracts';

export const JOURNEY_CHAPTERS=[
 {id:1,name:'兽潮之夜',available:true,boss:'BOSS_R1',arena:'S10',bossName:'灰披队长',level:1,endLevel:10,story:'兽群离开巢穴，旧哨塔在白昼里自行亮起。追踪兽潮、夺回据点，打破裂隘关的封锁。'},
 {id:2,name:'群山战火',available:true,boss:'BOSS_R2',arena:'H08',bossName:'守桥铠卫',level:11,endLevel:20,story:'军队争夺矿镇与天火，古代炉卫开始响应陌生的号令。深入工位和矿区，突破断岳前堡。'},
 {id:3,name:'沉钟回响',available:false},
 {id:4,name:'沉没王座',available:false},
 {id:5,name:'诸城烽火',available:false},
 {id:6,name:'黑冠围城',available:false},
 {id:7,name:'永夜降临',available:false},
 {id:8,name:'破晓之战',available:false},
] as const;
export const PLAYABLE_CHAPTERS=JOURNEY_CHAPTERS.filter((c):c is Extract<typeof JOURNEY_CHAPTERS[number],{available:true}>=>c.available);
export function playableArea(id:string){return /^(S\d\d(?:-T[1-6])?|T[1-6]|H\d\d|U1-\d\d)$/.test(id);}
/** Keep the full planning graph; only these exits participate in live play. */
export function playableExits(area:AreaDef){return playableArea(area.id)?area.exits.filter(exit=>playableArea(exit.to)):[];}
export const chapterForArea=(id:string)=>id.startsWith('H')||/^U1-(06|07|08|09|10)$/.test(id)?2:1;
export interface JourneyTask {id:string;chapter:number;area:string;name:string;story:string;goal:'observe'|'clear'|'hunt';kills?:number;experience:number;gold:number;iron:number}
export const JOURNEY_TASKS:JourneyTask[]=[
 {id:'border-traces',chapter:1,area:'S02',name:'暮色下的足迹',story:'兽群正朝石桥镇迁徙。观察渡口留下的爪痕与带有冠、龙纹样的古代矛尖，确认来自山林的共同威胁。',goal:'observe',experience:150,gold:20,iron:5},
 {id:'border-mill',chapter:1,area:'S07',name:'夺回断轮磨坊',story:'清除磨坊的固定守军，恢复居民可以使用的外围据点。地下传来的脚步声不属于这支驻军。',goal:'clear',experience:280,gold:40,iron:7},
 {id:'border-hunt',chapter:1,area:'S08',name:'猎场反击',story:'击败此地6只游荡怪，压住向镇外道路涌来的兽群。之前已经完成的真实狩猎同样计入。',goal:'hunt',kills:6,experience:400,gold:45,iron:7},
 {id:'border-camp',chapter:1,area:'S09',name:'灰披营地攻坚',story:'击败营地固定守军，夺下前往裂隘关的接近面。无需替军队运送物资换取参战资格。',goal:'clear',experience:600,gold:55,iron:8},
 {id:'border-watch',chapter:1,area:'U1-03',name:'初醒的旧军',story:'清除采掘廊的固定警戒组，查明自行苏醒的遗卫。完成后可领取本章任务传奇戒指，再去挑战灰披队长。',goal:'clear',experience:950,gold:65,iron:8},
 {id:'highland-front',chapter:2,area:'H01',name:'战火中的山驿',story:'在山驿了解交战方向。阿德里安的军队正在集中工匠与矿械，深城的炉光越来越亮。',goal:'observe',experience:600,gold:40,iron:5},
 {id:'highland-workers',chapter:2,area:'H03',name:'熔镜工位保卫战',story:'击败工匠院的固定敌阵，保住撤离通道。救援之后的征用令揭示了军队的另一面。',goal:'clear',experience:1500,gold:65,iron:7},
 {id:'highland-hunt',chapter:2,area:'H04',name:'矿区清剿',story:'击败采坑9只游荡怪，清开被凶兽与采掘机占据的矿区。清剿也是一场真实的狩猎。',goal:'hunt',kills:9,experience:2400,gold:85,iron:8},
 {id:'highland-ridge',chapter:2,area:'H07',name:'夺取石梁前哨',story:'击败前哨的固定警戒组，为山桥攻坚取得接近阵地；旧军用图记记载着巨大翼骨。各流派都可从自己的攻击距离突破。',goal:'clear',experience:3600,gold:110,iron:8},
 {id:'highland-oath',chapter:2,area:'U1-06',name:'三誓阵中的号令',story:'实际击败三誓军械廊的固定守军与三誓守卫。遗卫正在响应一个古老君主的号令；领取任务传奇武器后，前往断岳前堡。',goal:'clear',experience:5100,gold:150,iron:10},
];
export const journeyTaskKey=(id:string)=>`journey:task:${id}`;
export const journeyBossKey=(chapter:number)=>`journey:boss:${chapter}`;
export function installJourney(areas:Record<string,AreaDef>){
 for(const area of Object.values(areas)){
  if(!playableArea(area.id))continue;
  const chapter=PLAYABLE_CHAPTERS.find(c=>c.id===chapterForArea(area.id))!;
  area.objects.push({id:`journey-board:${area.id}`,action:'journey_board',label:'旅程 · 任务与狩猎',description:`第${chapter.id}章 ${chapter.name}。任务与狩猎均可成长，实际击败${chapter.bossName}完成本章。`,x:area.spawn.x-3,z:area.spawn.z,radius:1.35});
  for(const exit of area.exits)if(!playableArea(exit.to))exit.label+=' · 后续章节尚未开放';
 }
 for(const task of JOURNEY_TASKS){
  // The chapter's first observation belongs beside its arrival encounter,
  // rather than sending a new player across the entire scene to a generic slot.
  const at=task.id==='border-traces'?{x:-8,z:24}:task.id==='highland-front'?{x:48,z:-14}:{x:-7,z:-30};
  areas[task.area].objects.push({id:`journey-task:${task.id}`,eventId:task.id,action:'journey_task',label:task.name,description:task.story,...at,radius:1.35});
 }
}
