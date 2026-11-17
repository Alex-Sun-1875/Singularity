import {GameSession,validateSnapshot,type GameState} from '../../../core/GameSession';
import type {WorldQuery} from '../../../core/Contracts';

/** New campaign rules use their own slots; historical saves are not migrated. */
export const CAMPAIGN_SAVE_PREFIX='sword-fire.campaign90-v1';

export interface KeyValueStore {getItem(key:string):string|null;setItem(key:string,value:string):void}
export interface SaveResult {ok:boolean;error?:string;warning?:string}
export interface LoadResult {session:GameSession|null;warning?:string}
interface Envelope {version:1;revision:number;payload:string;hash:string}
/** Detect incomplete/corrupt storage writes; this is an integrity check, not encryption. */
export function checksum(payload:string):string {let h=2166136261;for(let i=0;i<payload.length;i++){h^=payload.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0).toString(16).padStart(8,'0');}

/** Alternating verified whole-state commits. No pointer file can invalidate both slots. */
export class SaveStore {
 private loaded=false;
 private blocked=false;
 private revision=0;
 private backupSequence=0;
 private pending:{text:string;slot:string;revision:number;stateRevision:number}|null=null;
 private lastWarning:string|undefined;
 constructor(private storage:KeyValueStore,private prefix=CAMPAIGN_SAVE_PREFIX){}
 private key(slot:string){return `${this.prefix}.${slot}`;}
 private inspect():{snapshot:GameState|null;warning?:string}{
  let best:GameState|null=null,revision=0;const problems:string[]=[];
  for(const slot of ['a','b']){
   let raw:string|null;
   try{raw=this.storage.getItem(this.key(slot));}catch{problems.push(slot);continue;}
   if(raw===null)continue;
   try{
    if(typeof raw!=='string'||raw.length>2_000_000)throw new Error('size');
    const e:Envelope=JSON.parse(raw);
    if(!e||Object.keys(e).sort().join(',')!=='hash,payload,revision,version'||e.version!==1||!Number.isSafeInteger(e.revision)||e.revision<1||typeof e.payload!=='string'||typeof e.hash!=='string'||checksum(e.payload)!==e.hash)throw new Error('envelope');
    const snapshot:unknown=JSON.parse(e.payload);validateSnapshot(snapshot);
    if(e.revision>revision){best=snapshot;revision=e.revision;}
   }catch{problems.push(slot);}
  }
  this.revision=revision;this.blocked=problems.length>0;this.loaded=true;
  const warning=this.blocked?'存档损坏、版本未知或无法读取：原始内容已保留，自动保存暂停。可继续最近完整进度；明确新建旅程会先备份旧档。':undefined;
  this.lastWarning=warning;return {snapshot:best,warning};
 }
 load(world:WorldQuery):LoadResult{const found=this.inspect();return {session:found.snapshot?GameSession.restore(found.snapshot,world):null,warning:found.warning};}
 write(session:GameSession):SaveResult{
  if(!this.loaded)this.inspect();
  if(this.blocked)return {ok:false,error:this.lastWarning??'原始存档已保留，请明确选择新建旅程。'};
  try{
   // A failed attempt never advances revision. Replace that alternate slot's
   // pending bytes with the latest whole snapshot; the last verified slot stays intact.
   const payload=session.serializeSnapshot(),snapshot:unknown=JSON.parse(payload);validateSnapshot(snapshot);const revision=this.revision+1;const envelope:Envelope={version:1,revision,payload,hash:checksum(payload)};this.pending={text:JSON.stringify(envelope),slot:revision%2?'a':'b',revision,stateRevision:snapshot.revision};
   const pending=this.pending;
   this.storage.setItem(this.key(pending.slot),pending.text);
   if(this.storage.getItem(this.key(pending.slot))!==pending.text)return {ok:false,error:'保存未通过写后校验；进度仍在当前会话，正在等待重试。'};
   this.revision=pending.revision;this.pending=null;
   if(session.state.revision===pending.stateRevision)session.dirty=false;
   return {ok:true};
  }catch{return {ok:false,error:'本地保存失败；进度仍在当前会话，请重试保存。'};}
 }
 /** Only call after the player's explicit New Journey action. Every original is backed up first. */
 startFresh(session:GameSession):SaveResult{
  if(!this.loaded)this.inspect();
  try{
   const snapshot=session.snapshot();validateSnapshot(snapshot);
   const originals:{slot:string;raw:string}[]=[];
   for(const slot of ['a','b']){const raw=this.storage.getItem(this.key(slot));if(raw!==null)originals.push({slot,raw});}
   let batch:string;
   do{batch=`backup-${Date.now()}-${++this.backupSequence}`;}while(originals.some(o=>this.storage.getItem(this.key(`${batch}-${o.slot}`))!==null));
   for(const o of originals){const key=this.key(`${batch}-${o.slot}`);this.storage.setItem(key,o.raw);if(this.storage.getItem(key)!==o.raw)return {ok:false,error:'旧档备份未通过校验，原始存档未改动。'};}
   this.blocked=false;this.pending=null;this.lastWarning=undefined;
   // Commit both slots so the preceding journey cannot return as a fallback.
   const first=this.write(session);if(!first.ok)return first;
   const mirror=this.write(session);
   return mirror.ok?mirror:{ok:true,warning:'新旅程已安全保存；第二份镜像写入失败，将在下一次保存重试。旧档备份仍保留。'};
  }catch{return {ok:false,error:'旧档备份失败，未覆盖原始存档。'};}
 }
 get recoveryRequired(){return this.blocked;}
}
