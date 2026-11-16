import {AudioClip,AudioSource,Node} from 'cc';
import {gameResources} from '../../../shared/assets/GameResources';
import type {KeyValueStore} from '../../persistence/common/SaveStore';

const PREFERENCE='sword-and-fire.music.v1';
const TRACKS={explore:'audio/music/embers-oaths-explore',combat:'audio/music/embers-oaths-combat',aftermath:'audio/music/embers-oaths-aftermath'} as const;
const MODES=['explore','combat','aftermath'] as const;
const COMBAT_ENTRY_SECONDS=.7;
const COMBAT_EXIT_SECONDS=4;
const CROSSFADE_SECONDS=1.5;

type MusicMode=keyof typeof TRACKS;
export interface MusicContext {combat:boolean;boss:boolean;areaKind?:string;areaId?:string;interrupted?:boolean;settled?:boolean}
interface MusicSlot {
 source:AudioSource;
 clip:AudioClip|undefined;
 loading:boolean;
 failed:boolean;
 playing:boolean;
 level:number;
 submittedVolume:number;
}
interface MusicTransition {
 sequence:number;
 from:MusicMode|undefined;
 to:MusicMode;
 phaseSeek:boolean;
 outgoingTime:number|undefined;
 outgoingDuration:number|undefined;
 incomingDuration:number|undefined;
 targetTime:number|undefined;
 reason:'initial'|'outgoing-not-playing'|'phase-seek-requested'|'aftermath-from-start'|'theme-return'|'combat-resume';
}

/** Two loops and one non-looping musical release; Cocos owns platform audio. */
export class BackgroundMusic {
 private readonly root:Node;
 private readonly slots:Record<MusicMode,MusicSlot>;
 private requested=false;
 private disposed=false;
 private suspended=false;
 private allowed=false;
 private desired:MusicMode='explore';
 private active:MusicMode|undefined;
 private pendingMode:MusicMode|undefined;
 private transitionCount=0;
 private phaseSeekCount=0;
 private lastTransition:MusicTransition|undefined;
 private engagedFor=0;
 private peacefulFor=0;
 private battleQualified=false;
 private contextArea:string|undefined;
 private aftermathCount=0;
 private aftermathCompleted=0;
 private aftermathFinishReason:'tail'|'ended'|'unavailable'|undefined;
 private readonly aftermathEnded=()=>{if(!this.disposed)this.finishAftermath('ended');};
 enabled=true;
 failed=false;

 constructor(parent:Node,private readonly store:KeyValueStore,private readonly changed:()=>void){
  this.root=new Node('BackgroundMusic');parent.addChild(this.root);
  this.slots={explore:this.createSlot('Exploration'),combat:this.createSlot('Combat'),aftermath:this.createSlot('Aftermath',false)};
  this.slots.aftermath.source.node.on(AudioSource.EventType.ENDED,this.aftermathEnded);
  try{this.enabled=this.store.getItem(PREFERENCE)!=='off';}catch{ /* Keep audio optional if preference storage fails. */ }
 }

 private createSlot(name:string,loop=true):MusicSlot {
  const node=new Node(name);this.root.addChild(node);
  const source=node.addComponent(AudioSource);
  source.playOnAwake=false;source.loop=loop;source.volume=0;
  return {source,clip:undefined,loading:false,failed:false,playing:false,level:0,submittedVolume:0};
 }

 start():void{this.requested=true;this.gesture();}

 /** Real input lets Cocos unlock mobile audio; requests never restart a playing loop. */
 gesture():void{
  if(this.disposed||!this.requested||!this.enabled||this.suspended)return;
  this.ensureAssets();
  if(this.allowed){const mode=this.activate(this.availableMode());if(mode)this.play(this.slots[mode]);}
 }

 toggle():void{
  if(this.failed){
   // Retry failed assets only on this explicit action; there is no network polling.
   for(const mode of MODES)this.slots[mode].failed=false;
   this.failed=false;this.enabled=true;this.gesture();
  }else{
   this.enabled=!this.enabled;
   if(this.enabled)this.gesture();else this.pauseAll();
  }
  try{this.store.setItem(PREFERENCE,this.enabled?'on':'off');}catch{ /* The current session's choice still applies. */ }
  this.changed();
 }

 get label():string{return this.failed?'背景音乐：载入失败，点击重试':`背景音乐：${this.enabled?'开':'关'}`;}

 /** Read-only diagnostics for actual Web/device verification, with no UI dependency. */
 inspect(){
  const tracks=MODES.map(mode=>{
   const slot=this.slots[mode];
   return {mode,path:TRACKS[mode],loaded:!!slot.clip,loading:slot.loading,failed:slot.failed,
    requestedPlayback:slot.playing,playing:slot.source.playing,volume:slot.source.volume,
    currentTime:slot.source.currentTime,duration:slot.source.duration,loop:slot.source.loop};
  });
  return {enabled:this.enabled,failed:this.failed,requested:this.requested,suspended:this.suspended,
   disposed:this.disposed,allowed:this.allowed,desired:this.desired,active:this.active,
   available:this.availableMode(),pendingMode:this.pendingMode,transitionCount:this.transitionCount,
   phaseSeekCount:this.phaseSeekCount,lastTransition:this.lastTransition?{...this.lastTransition}:undefined,
   engagedFor:this.engagedFor,peacefulFor:this.peacefulFor,battleQualified:this.battleQualified,
   contextArea:this.contextArea,aftermathCount:this.aftermathCount,aftermathCompleted:this.aftermathCompleted,
   aftermathFinishReason:this.aftermathFinishReason,sourceCount:tracks.length,
   playingSourceCount:tracks.filter(track=>track.playing).length,tracks};
 }

 setSuspended(value:boolean):void{
  this.suspended=value;
  if(value){this.allowed=false;this.pauseAll();}
  else this.gesture();
 }

 /** Loading, a new journey/area or death is an interruption, not a battle ending. */
 resetEncounter():void{
  this.battleQualified=false;this.engagedFor=0;this.peacefulFor=0;this.desired='explore';
  if(this.active==='aftermath'){
   const slot=this.slots.aftermath;this.pause(slot);slot.source.stop();this.active=undefined;
  }
 }

 update(dt:number,allowed:boolean,quiet:boolean,context?:MusicContext):void{
  if(this.disposed)return;
  if(context?.areaId!==undefined){
   if(this.contextArea!==undefined&&this.contextArea!==context.areaId)this.resetEncounter();
   this.contextArea=context.areaId;
  }
  if(context?.interrupted)this.resetEncounter();
  this.allowed=allowed;
  if(!allowed||this.suspended||!this.requested){this.pauseAll();return;}
  if(!this.enabled){
   // A fight that ended while muted must not produce a delayed release on unmute.
   // Muting an already playing aftermath, however, preserves its position.
   const engaged=!!context?.combat||!!context?.boss;
   if(!engaged&&this.desired==='combat')this.resetEncounter();
   else if(engaged&&this.desired==='aftermath'){this.desired='combat';this.battleQualified=true;}
   this.pauseAll();return;
  }
  const step=Math.max(0,Math.min(Number.isFinite(dt)?dt:0,.25));
  this.updateContext(step,context?.interrupted?undefined:context);
  if(this.desired==='aftermath'){
   const slot=this.slots.aftermath;
   if(slot.failed)this.finishAftermath('unavailable');
   else if(this.active==='aftermath'&&slot.source.playing&&slot.source.duration>CROSSFADE_SECONDS&&
    slot.source.currentTime>=slot.source.duration-CROSSFADE_SECONDS)this.finishAftermath('tail');
  }
  this.ensureAssets();
  const active=this.activate(this.availableMode());
  const volume=quiet?.13:.28;
  const fadeStep=step*.28/CROSSFADE_SECONDS;
  for(const mode of MODES){
   const slot=this.slots[mode],target=mode===active?volume:0;
   if(target>0)this.play(slot);
   if(slot.level!==target){
    const difference=target-slot.level;
    slot.level=Math.abs(difference)<=fadeStep?target:slot.level+Math.sign(difference)*fadeStep;
    this.submitVolume(slot,slot.level);
   }
   // An inaudible source is paused instead of silently decoding another 96s loop.
   if(target===0&&slot.level===0)this.pause(slot);
  }
 }

 private updateContext(dt:number,context?:MusicContext):void{
  const engaged=!!context?.combat||!!context?.boss;
  if(engaged){
   this.peacefulFor=0;this.engagedFor=Math.min(COMBAT_ENTRY_SECONDS,this.engagedFor+dt);
   // Boss uses this same combat score; no separate Boss arrangement is claimed.
   if(context?.boss||this.battleQualified||this.desired==='aftermath'||this.engagedFor>=COMBAT_ENTRY_SECONDS){
    this.desired='combat';this.battleQualified=true;
   }
  }else{
   this.engagedFor=0;
   if(this.battleQualified){
    this.peacefulFor=Math.min(COMBAT_EXIT_SECONDS,this.peacefulFor+dt);
    if(this.peacefulFor>=COMBAT_EXIT_SECONDS&&context?.settled!==false){
     this.battleQualified=false;this.desired='aftermath';this.aftermathCount++;this.aftermathFinishReason=undefined;
    }
   }
  }
 }

 private finishAftermath(reason:'tail'|'ended'|'unavailable'):void {
  if(this.desired!=='aftermath')return;
  this.desired='explore';this.peacefulFor=0;this.aftermathCompleted++;this.aftermathFinishReason=reason;
 }

 private availableMode():MusicMode|undefined {
  if(this.slots[this.desired].clip)return this.desired;
  if(this.desired==='aftermath'){
   // Hold an available loop while the short release loads; never loop the release
   // as a fallback for a missing exploration/combat score.
   if(this.active&&this.active!=='aftermath'&&this.slots[this.active].clip)return this.active;
   return this.slots.explore.clip?'explore':this.slots.combat.clip?'combat':undefined;
  }
  const other=this.desired==='combat'?'explore':'combat';
  return this.slots[other].clip?other:undefined;
 }

 private activate(mode:MusicMode|undefined):MusicMode|undefined {
  if(!mode)return undefined;
  if(mode===this.active){this.pendingMode=undefined;return mode;}
  const from=this.active,outgoing=from?this.slots[from]:undefined,incoming=this.slots[mode];
  let outgoingTime:number|undefined,outgoingDuration:number|undefined;
  let incomingDuration:number|undefined,targetTime:number|undefined;
  let phaseSeek=false;
  let reason:MusicTransition['reason']=from?'outgoing-not-playing':'initial';
  if(mode==='aftermath'){
   incoming.source.stop();incoming.playing=false;incoming.source.currentTime=0;
   incoming.level=0;this.submitVolume(incoming,0);targetTime=0;reason='aftermath-from-start';
  }else if(from==='aftermath'){
   if(mode==='explore'){incoming.source.currentTime=0;targetTime=0;reason='theme-return';}
   else reason='combat-resume';
  }else if(outgoing?.clip&&outgoing.source.playing){
   outgoingTime=outgoing.source.currentTime;outgoingDuration=outgoing.source.duration;
   incomingDuration=incoming.source.duration;
   if(!Number.isFinite(outgoingTime)||outgoingTime<0||!Number.isFinite(outgoingDuration)||
    !Number.isFinite(incomingDuration)||!(outgoingDuration>0)||!(incomingDuration>0)){
    // Keep the current track while metadata becomes available. Never queue a
    // clamped-to-zero seek; Cocos bounds currentTime using clip.getDuration().
    this.pendingMode=mode;return from;
   }
   targetTime=(outgoingTime%outgoingDuration)/outgoingDuration*incomingDuration;
   // Both scores use the same 32-bar grid. This is a one-time approximate
   // position match, not a sample-synchronous transport. Cocos queues SEEK
   // before PLAY if its AudioPlayer is still loading; paused players cache it.
   incoming.source.currentTime=targetTime;
   phaseSeek=true;this.phaseSeekCount++;reason='phase-seek-requested';
  }
  // Rapid interruptions may revisit a third mode before the previous fade ends.
  // Keep at most the outgoing and incoming source audible.
  for(const other of MODES)if(other!==mode&&other!==from)this.pause(this.slots[other]);
  this.active=mode;this.pendingMode=undefined;this.transitionCount++;
  this.lastTransition={sequence:this.transitionCount,from,to:mode,phaseSeek,outgoingTime,
   outgoingDuration,incomingDuration,targetTime,
   reason};
  return mode;
 }

 private ensureAssets():void{
  this.load('explore');
  // Fetch the combat premix after the theme, keeping first music startup light.
  if(this.slots.explore.clip||this.slots.explore.failed)this.load('combat');
  if(this.slots.combat.clip||this.slots.combat.failed)this.load('aftermath');
 }

 private play(slot:MusicSlot):void{
  if(!slot.clip||slot.playing)return;
  // Cocos 3.8.8 play() resumes PAUSED but restarts PLAYING. An engine lifecycle
  // resume may precede our update, so check the real source before calling play.
  if(!slot.source.playing)slot.source.play();
  slot.playing=true;
 }

 private submitVolume(slot:MusicSlot,value:number):void{
  if(value===slot.submittedVolume)return;
  slot.source.volume=value;slot.submittedVolume=value;
 }

 private pause(slot:MusicSlot):void{
  if(slot.playing||slot.source.playing)slot.source.pause();
  slot.playing=false;slot.level=0;this.submitVolume(slot,0);
 }

 private pauseAll():void{for(const mode of MODES)this.pause(this.slots[mode]);}

 private load(mode:MusicMode):void{
  const slot=this.slots[mode];
  if(slot.clip||slot.loading||slot.failed||this.disposed)return;
  slot.loading=true;
  gameResources.load(TRACKS[mode],AudioClip,(error,clip)=>{
   slot.loading=false;
   if(this.disposed)return;
   if(error||!clip){
    slot.failed=true;this.failed=true;
    console.warn('[Music] Loop unavailable; a loaded track can continue.',mode);
    this.changed();return;
   }
   clip.addRef();slot.clip=clip;slot.source.clip=clip;
   this.failed=MODES.some(mode=>this.slots[mode].failed);
   this.gesture();
  });
 }

 dispose():void{
  if(this.disposed)return;this.disposed=true;
  this.slots.aftermath.source.node.off(AudioSource.EventType.ENDED,this.aftermathEnded);
  for(const mode of MODES){
   const slot=this.slots[mode];slot.source.stop();slot.source.clip=null;
   slot.clip?.decRef();slot.clip=undefined;slot.playing=false;
  }
  this.root.destroy();
 }
}
