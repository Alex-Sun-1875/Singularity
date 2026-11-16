import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'title':'任务与章节','tab.chapters':'章节','tab.main':'主线','tab.side':'支线',
 'overview':'章节故事与任务进度，都随当前旅程保存。',
 'mainHelp':'查看当前目标、后续阶段与已完成的主线记录。',
 'progress':'主线 {done}/{total} · 关底 {boss}',
 'boss.done':'已通关','boss.pending':'未通关',
 'current':'当前目标：{name}','chapterFinished':'本章主线与关底已完成。',
 'bossGoal':'挑战{boss}','levelGate':'Lv{level}后开放本章行动，可先阅读故事与任务记录。',
 'future.title':'后续章节','future.description':'后续章节尚未开放，可查看筹备状态。',
 'comingSoon':'敬请期待','preview':'章节预告','backChapters':'返回章节','backTasks':'返回任务',
 'return':'返回旅途','hunt':'出发狩猎','campaignLog':'战役回看',
 'status.done':'已完成','status.current':'进行中','status.pending':'待进行','status.locked':'尚未解锁',
 'taskTitle':'第{chapter}章 · {name}','future.summary':'第4—8章 · 敬请期待',
};
const en:Record<keyof typeof zh,string>={
 'title':'Quests and chapters','tab.chapters':'Chapters','tab.main':'Main','tab.side':'Side',
 'overview':'Chapter stories and quest progress are saved with this journey.',
 'mainHelp':'View your current objective, later stages and completed main quests.',
 'progress':'Main {done}/{total} · Boss {boss}',
 'boss.done':'Cleared','boss.pending':'Not cleared',
 'current':'Current objective: {name}','chapterFinished':'The main quests and chapter boss are complete.',
 'bossGoal':'Challenge {boss}','levelGate':'Chapter actions unlock at Lv{level}. Stories and quest records remain readable.',
 'future.title':'Later chapters','future.description':'Later chapters are not open. View their preparation status.',
 'comingSoon':'Coming soon','preview':'Chapter preview','backChapters':'Back to chapters','backTasks':'Back to quests',
 'return':'Return to journey','hunt':'Go hunting','campaignLog':'Campaign replay',
 'status.done':'Complete','status.current':'In progress','status.pending':'Pending','status.locked':'Locked',
 'taskTitle':'Chapter {chapter} · {name}','future.summary':'Chapters 4–8 · Coming soon',
};
const translate=registerMessages('task-panel',zh,en);
export const taskPanelText=(key:keyof typeof zh,values:Record<string,string|number>={})=>translate(key,values,'zh-CN');
