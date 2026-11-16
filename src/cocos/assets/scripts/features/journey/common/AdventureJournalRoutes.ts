import {FIELD_QUESTS} from '../../campaign/data/FieldQuests';
import {CHAPTER_TWO_SIDE_QUESTS} from '../../campaign/data/ChapterTwoSideQuests';

/** Legacy shortcuts enter the same workspace without carrying gameplay state. */
export interface AdventureJournalRequest {
 mode?:'journal'|'map';entryId?:string;filter?:'current'|'completed'|'locations';area?:string;
}
export function adventureJournalRoute(route:string,currentChapter=1):AdventureJournalRequest|undefined {
 if(route==='map')return {mode:'map'};
 if(route==='journey'||route==='journey-tasks'||route==='journey-tasks:main'||route==='journey-tasks:side')return {mode:'journal',filter:'current'};
 if(route==='journey-chapters'||route==='journey-tasks:chapters')return {mode:'journal',entryId:`chapter:${currentChapter}`,filter:'current'};
 if(route==='journey-future'||route==='journey-locked')return {mode:'journal',entryId:'chapter:3',filter:'current'};
 if(route==='campaign-log')return {mode:'journal',filter:'completed'};
 const parts=route.split(':'),id=parts[1];if(!id)return;
 if(parts[0]==='journey-chapter'&&/^[1-8]$/.test(id))return {mode:'journal',entryId:`chapter:${id}`};
 if(parts[0]==='journey-task')return {mode:'journal',entryId:`main:${id}`};
 if(parts[0]==='journey-encounter-route'||parts[0]==='journey-encounter-clues')return {mode:'journal',entryId:`main:${id}`};
 if(parts[0]==='journey-side-task')return {mode:'journal',entryId:`side:${id}`};
 if(parts[0]==='journey-field-task'){
  const quest=[...FIELD_QUESTS,...CHAPTER_TWO_SIDE_QUESTS].find(quest=>quest.steps.some(step=>step===id));
  return quest?{mode:'journal',entryId:`side:${quest.id}`}:{mode:'journal'};
 }
 if(parts[0]==='journey-field'&&/^[1-8]$/.test(id))return {mode:'journal',entryId:`chapter:${id}`};
 if(parts[0]==='campaign-log')return {mode:'journal',entryId:`replay:${id}`,filter:'completed'};
 if(parts[0]==='journey-map'||parts[0]==='atlas')return {mode:'map',entryId:`area:${id}`,area:id};
 return;
}
