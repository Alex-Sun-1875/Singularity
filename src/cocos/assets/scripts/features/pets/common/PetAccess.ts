import type {GameState} from '../../../core/GameSession';
import {JOURNEY_CHAPTERS,chapterForArea,playableArea} from '../../journey/data/ChapterJourney';
import {PET_POLICY} from '../data/Pets';

export const PET_CHAPTER_ENTRY_RECEIPT='pet:chapter-entry';
interface ChapterEntry {v:1;chapter:number;area:string;at:number}
export interface PetAccess {available:boolean;released:boolean;unlocked:boolean;requiredChapter:number;reason:string}
const CLOSED_ACCESS:Readonly<PetAccess>=Object.freeze({available:false,released:false,unlocked:false,requiredChapter:PET_POLICY.unlockChapter,reason:'宠物系统从第三章开放，当前尚未开放，敬请期待。'});
const LOCKED_ACCESS:Readonly<PetAccess>=Object.freeze({available:false,released:true,unlocked:false,requiredChapter:PET_POLICY.unlockChapter,reason:'请实际进入第三章后解锁宠物系统。'});
const OPEN_ACCESS:Readonly<PetAccess>=Object.freeze({available:true,released:true,unlocked:true,requiredChapter:PET_POLICY.unlockChapter,reason:''});
const object=(value:unknown):value is Record<string,unknown>=>!!value&&typeof value==='object'&&!Array.isArray(value)&&Object.getPrototypeOf(value)===Object.prototype;

/** Content publication and a real released chapter are independent requirements. */
export function petReleaseReady():boolean {return PET_POLICY.enabled&&JOURNEY_CHAPTERS.some(chapter=>chapter.id===PET_POLICY.unlockChapter&&chapter.available);}
function chapterEntry(s:GameState):ChapterEntry|null {
 const raw=s.receipts[PET_CHAPTER_ENTRY_RECEIPT];if(typeof raw!=='string')return null;let entry:unknown;try{entry=JSON.parse(raw);}catch{return null;}
 if(!object(entry)||Object.keys(entry).sort().join()!=='area,at,chapter,v'||entry.v!==1||typeof entry.chapter!=='number'||!Number.isSafeInteger(entry.chapter)||entry.chapter<PET_POLICY.unlockChapter||typeof entry.area!=='string'||entry.area.length>100||typeof entry.at!=='number'||!Number.isFinite(entry.at)||entry.at<0||entry.at>s.time)return null;
 // Availability is deliberately omitted here: a later chapter/content closure
 // must retain a legitimate earlier visit. Unknown areas still map to chapter 1.
 if(!JOURNEY_CHAPTERS.some(chapter=>chapter.id===entry.chapter)||chapterForArea(entry.area)!==entry.chapter||s.flags['visited:'+entry.area]!==true)return null;
 const current=entry.area===s.area&&Array.isArray(s.enemies),saved=Object.prototype.hasOwnProperty.call(s.encounters,entry.area)&&Array.isArray(s.encounters[entry.area]);
 return current||saved?entry as unknown as ChapterEntry:null;
}
export function petAccess(s:GameState):Readonly<PetAccess> {
 const unlocked=chapterEntry(s)!==null;if(!petReleaseReady())return unlocked?{...CLOSED_ACCESS,unlocked:true}:CLOSED_ACCESS;return unlocked?OPEN_ACCESS:LOCKED_ACCESS;
}
/** Frequent simulation queries remain allocation-free on the closed path. */
export function petAvailable(s:GameState):boolean {return petReleaseReady()&&chapterEntry(s)!==null;}
/** Called only after GameSession.enter has committed the actual map. The
 * caller cannot supply a level, chapter number, area or completion flag. */
export function recordPetChapterEntry(s:GameState):boolean {
 if(s.receipts[PET_CHAPTER_ENTRY_RECEIPT]!==undefined)return false;
 const chapter=chapterForArea(s.area);if(chapter<PET_POLICY.unlockChapter||!playableArea(s.area)||!JOURNEY_CHAPTERS.some(definition=>definition.id===chapter&&definition.available)||s.flags['visited:'+s.area]!==true||!Object.prototype.hasOwnProperty.call(s.encounters,s.area)||!Array.isArray(s.encounters[s.area])||!Number.isFinite(s.time)||s.time<0)return false;
 const entry:ChapterEntry={v:1,chapter,area:s.area,at:s.time};s.receipts[PET_CHAPTER_ENTRY_RECEIPT]=JSON.stringify(entry);return true;
}
/** The entry is a cross-checked receipt, never an independent unlock boolean. */
export function validatePetAccess(s:GameState):void {if(s.receipts[PET_CHAPTER_ENTRY_RECEIPT]!==undefined&&!chapterEntry(s))throw new Error('无效的宠物章节进入凭证');}
