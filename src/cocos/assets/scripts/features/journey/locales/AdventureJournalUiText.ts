import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 title:'冒险日志',journal:'日志',tasks:'任务',taskLog:'任务日志',map:'地图',current:'当前',completed:'已完成',locations:'地点',hideCompleted:'隐藏已完成',
 main:'主线',side:'支线',replay:'回看',chapter:'章节',place:'地点',later:'后续章节',
 emptyCurrent:'这一章暂无正在进行的任务。',emptyCompleted:'这一章还没有已完成的记录。',
 emptyLocations:'探索新地点后，会在这里留下记录。',timeline:'行动记录',choice:'你的选择',
 mapDetail:'日志详情',viewMap:'在地图查看',viewSite:'查看地点',actions:'可采取的行动',travel:'传送',go:'前往目标',
 selectedPlace:'选中地点：{name}',unknownPlace:'{name} · 尚未抵达，显示区域概略',
 mapHint:'选择地点或任务标记可查看记录。',emptyEntry:'选择左侧章节、任务或地点，展开旅程记录。',
 readOnly:'敬请期待',currentStep:'当前目标',doneStep:'已完成',lockedStep:'待进行',walkMark:'前往标记',travelBusy:'正在准备传送…',
};
const en:Record<keyof typeof zh,string>={
 title:'Adventure journal',journal:'Journal',tasks:'Tasks',taskLog:'Quest log',map:'Map',current:'Current',completed:'Completed',locations:'Places',hideCompleted:'Hide completed',
 main:'Main',side:'Side',replay:'Replay',chapter:'Chapter',place:'Place',later:'Later chapters',
 emptyCurrent:'There are no active quests in this chapter.',emptyCompleted:'No completed records in this chapter yet.',
 emptyLocations:'Explored places will appear here.',timeline:'Journey record',choice:'Your choice',
 mapDetail:'Journal details',viewMap:'View on map',viewSite:'View place',actions:'Available actions',travel:'Travel',go:'Go',
 selectedPlace:'Selected place: {name}',unknownPlace:'{name} · Not visited, regional outline only',
 mapHint:'Select a place or quest marker to read its record.',emptyEntry:'Select a chapter, quest or place to read its record.',
 readOnly:'Coming soon',currentStep:'Current objective',doneStep:'Completed',lockedStep:'Pending',walkMark:'Go to marker',travelBusy:'Preparing travel…',
};
const translate=registerMessages('adventure-journal-ui',zh,en);
export const journalUiText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
