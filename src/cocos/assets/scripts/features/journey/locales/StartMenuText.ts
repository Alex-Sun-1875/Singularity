import {registerMessages} from '../../../shared/i18n/Localization';
const zh={
 'continue':'继续游戏','start':'开始游戏','restart':'重新开始','settings':'设置',
 'loading':'正在准备…','reload':'重新载入','unavailable':'存档不可用',
 'recovery':'存档异常，继续将载入最近完整进度',
 'restartRequired':'存档不兼容或损坏，请重新开始',
 'restart.title':'重新开始？',
 'restart.body':'这会重置当前旅程的角色、等级、装备、任务与地图探索，从开场重新开始。音画与操作设置会保留。\n\n旧档会先备份，再替换为全新进度；确认后无法在游戏中返回旧旅程。',
 'restart.confirm':'确认重新开始','restart.cancel':'取消',
 'menu':'返回主菜单','menu.detail':'保存并保留当前旅程',
 'restart.detail':'重置当前旅程，需确认',
};
const en:Record<keyof typeof zh,string>={
 'continue':'Continue','start':'Start game','restart':'New game','settings':'Settings',
 'loading':'Preparing…','reload':'Reload','unavailable':'Save unavailable',
 'recovery':'Save issue: continue from the last intact progress',
 'restartRequired':'Incompatible or damaged save. Start a new game.',
 'restart.title':'Start a new game?',
 'restart.body':'This resets your character, level, equipment, quests and map exploration, starting again from the opening. Audio, visual and control settings are kept.\n\nThe old save is backed up before it is replaced. You cannot return to the old journey in game after confirming.',
 'restart.confirm':'Start new game','restart.cancel':'Cancel',
 'menu':'Main menu','menu.detail':'Save and keep this journey',
 'restart.detail':'Reset this journey after confirmation',
};
const translate=registerMessages('start-menu',zh,en);
export const startMenuText=(key:keyof typeof zh)=>translate(key,{},'zh-CN');
