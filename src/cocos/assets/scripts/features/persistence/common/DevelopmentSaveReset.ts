import type {KeyValueStore} from './SaveStore';

export const SKILL_POINT_SAVE_PREFIX='sword-fire.skills-v1';
export const SKILL_POINT_RESET_MARKER='sword-fire.skills-v1-reset';
export interface ResettableGameStore extends KeyValueStore {keys():string[];removeItem(key:string):void;}

/** User-authorized development reset, 2026-11-10. Never runs twice on a store. */
export function resetSkillPointPreviewStore(storage:ResettableGameStore):number {
 if(storage.getItem(SKILL_POINT_RESET_MARKER)==='1')return 0;
 const keys=storage.keys().filter(key=>key.startsWith('sword-fire.ch01.')||key.startsWith(SKILL_POINT_SAVE_PREFIX+'.')||key.startsWith('sword-fire-chart:')||key==='sword-fire-chart-index');
 for(const key of keys){storage.removeItem(key);if(storage.getItem(key)!==null)throw new Error('清理测试存档失败，请重试');}
 storage.setItem(SKILL_POINT_RESET_MARKER,'1');if(storage.getItem(SKILL_POINT_RESET_MARKER)!=='1')throw new Error('测试存档清理标记未保存，请重试');
 return keys.length;
}
