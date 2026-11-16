import {AudioClip,AudioSource,Node} from 'cc';
import type {GameEvent} from '../../../core/Contracts';
import type {GameSession} from '../../../core/GameSession';
import {gameResources} from '../../../shared/assets/GameResources';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {COMBAT_SKILLS} from '../../combat/data/PureSkills';
import {weaponCombatFamily} from '../../progression/common/CombatLoadouts';
import {COMBAT_AUDIO_CUES,audioFamily,combatAudioPath,contactAudioRequest,eventAudioFamily,preparationCue,
 type AudioFamily,type CombatAudioCue,type CombatAudioRequest} from '../common/CombatAudioCues';

type Voice={source:AudioSource;until:number;key:string;priority:number};
type TimedFamily={family:AudioFamily;until:number};
type HitSegment={segment:number;until:number};

/** Six stoppable Cocos sources; shared engine adaptation owns platform playback.
 * Actual contacts are delivered only by the visible representative-hit callback.
 * Loading never replays a missed action after its clip finally arrives. */
export class CombatAudio {
 private readonly root:Node;
 private readonly voices:Voice[]=[];
 private readonly clips=new Map<string,AudioClip>();
 private readonly loads=new Map<AudioFamily,Promise<void>>();
 private readonly requested=new Set<AudioFamily>();
 private readonly failures=new Set<string>();
 private readonly lastVariant=new Map<CombatAudioCue,number>();
 private readonly remembered=new Map<string,TimedFamily>();
 private readonly segments=new Map<string,HitSegment>();
 private readonly heard=new Map<string,number>();
 private prep:{id:string;voice:Voice}|undefined;
 private game:GameSession|undefined;
 private family:AudioFamily|undefined;
 private clock=0;
 private nextImpact=0;
 private nextRelease=0;
 private suspended=false;
 private active=true;
 private disposed=false;
 private played=0;
 private dropped=0;
 private impactCount=0;
 private maximumVoices=0;

 constructor(parent:Node){
  this.root=new Node('CombatAudio');parent.addChild(this.root);
  for(let n=0;n<6;n++){
   const node=new Node('CombatAudioVoice'+n);this.root.addChild(node);
   const source=node.addComponent(AudioSource);source.playOnAwake=false;source.loop=false;
   this.voices.push({source,until:0,key:'',priority:0});
  }
 }

 /** Caller may explicitly retry a failed family after correcting a load error. */
 prepare(family:AudioFamily,retry=false):Promise<void>{
  if(this.disposed)return Promise.resolve();
  const loading=this.loads.get(family);if(loading)return loading;
  if(this.requested.has(family)&&!retry)return Promise.resolve();
  this.requested.add(family);
  const jobs:Promise<void>[]=[];
  for(const name of Object.keys(COMBAT_AUDIO_CUES) as CombatAudioCue[]){
   if(COMBAT_AUDIO_CUES[name].family!==family)continue;
   for(let variant=1;variant<=3;variant++){
    const path=combatAudioPath(name,variant);if(this.clips.has(path))continue;
    jobs.push(new Promise(resolve=>{
     let settled=false;
     const complete=(error:Error|null,clip?:AudioClip)=>{
      if(settled)return;settled=true;
      if(this.disposed){resolve();return;}
      try{
       if(error||!clip)throw error??new Error('no clip');
       clip.addRef();this.clips.set(path,clip);this.failures.delete(path);
      }catch(failure){
       if(!this.failures.has(path))console.warn('[CombatAudio] Sound unavailable; gameplay continues:',path,failure instanceof Error?failure.message:String(failure));
       this.failures.add(path);
      }finally{resolve();}
     };
     try{gameResources.load(path,AudioClip,complete);}
     catch(error){complete(error instanceof Error?error:new Error(String(error)));}
    }));
   }
  }
  const result=Promise.all(jobs).then(()=>{this.loads.delete(family);});
  this.loads.set(family,result);return result;
 }

 private remember(id:unknown,family:AudioFamily):void {
  if(typeof id==='string'&&id){this.remembered.set(id,{family,until:this.clock+18});if(this.remembered.size>160)this.remembered.delete(this.remembered.keys().next().value!);}
 }
 private currentFamily(game:GameSession):AudioFamily{return weaponCombatFamily(game.state.equipment.weapon,game.state.combat);}
 private resolveFamily(event:GameEvent,game:GameSession):AudioFamily {
  const old=this.remembered.get(String(event.action??event.castId??event.id));
  const weapon=typeof event.weapon==='string'?EQUIPMENT[event.weapon]?.kind:undefined;
  const fromWeapon=weapon==='sword'?'WAR':weapon==='bow'?'BOW':undefined;
  return eventAudioFamily(event,fromWeapon??old?.family??this.currentFamily(game));
 }
 private stop(voice:Voice):void {
  voice.source.stop();voice.source.clip=null;voice.until=0;voice.key='';voice.priority=0;
  if(this.prep?.voice===voice)this.prep=undefined;
 }
 private stopPreparation():void {if(this.prep)this.stop(this.prep.voice);}
 /** Input cancellation stops only windup, preserving genuine released tails. */
 cancelPreparation():void {this.stopPreparation();}
 private play(request:CombatAudioRequest,key:string):Voice|undefined {
  if(this.disposed||this.suspended||!this.active)return;
  let variation=(this.lastVariant.get(request.cue)??0)%3+1;
  let clip:AudioClip|undefined;
  // Never repeat the previous variant when another loaded one is available.
  for(let n=0;n<3;n++){
   const candidate=this.clips.get(combatAudioPath(request.cue,variation));
   if(candidate){clip=candidate;break;}variation=variation%3+1;
  }
  if(!clip){this.dropped++;return;}
  let voice=this.voices.find(item=>item.until<=this.clock);
  if(!voice){
   const weakest=this.voices.reduce((a,b)=>a.priority<b.priority||a.priority===b.priority&&a.until<b.until?a:b);
   if(weakest.priority>=request.priority){this.dropped++;return;}
   voice=weakest;
  }
  this.stop(voice);
  voice.source.clip=clip;voice.source.volume=Math.max(0,Math.min(1,request.volume));
  voice.key=key;voice.priority=request.priority;
  voice.until=this.clock+Math.min(COMBAT_AUDIO_CUES[request.cue].duration,request.limit??99);
  voice.source.play();this.lastVariant.set(request.cue,variation);this.played++;
  this.maximumVoices=Math.max(this.maximumVoices,this.voices.filter(v=>v.until>this.clock).length);
  return voice;
 }
 private preparation(id:string,family:AudioFamily,duration?:number):void {
  this.stopPreparation();const cue=preparationCue(family);if(!cue)return;
  const voice=this.play({cue,volume:family==='BOW' ? .22 : .20,priority:0,limit:duration},'prepare:'+id);
  if(voice)this.prep={id,voice};
 }
 private once(key:string,request:CombatAudioRequest,seconds=.12):boolean {
  if((this.heard.get(key)??0)>this.clock)return false;
  const voice=this.play(request,key);if(!voice)return false;
  this.heard.set(key,this.clock+seconds);return true;
 }
 private launch(family:AudioFamily,key:string):void {
  if(this.clock<this.nextRelease)return;
  const cue:CombatAudioCue=family==='WAR'?'war_swing':family==='BOW'?'bow_release':family==='FIR'?'fir_charge':'thu_charge';
  const elemental=family==='FIR'||family==='THU';
  if(this.once('release:'+key,{cue,volume:family==='WAR' ? .31 : family==='BOW' ? .46 : .18,priority:1,limit:elemental ? .15 : undefined},5))this.nextRelease=this.clock+.075;
 }

 onEvents(events:readonly GameEvent[],game:GameSession):void {
  this.game=game;
  const family=this.currentFamily(game);
  if(family!==this.family){this.family=family;this.stopPreparation();void this.prepare(family);}
  if(events.some(e=>['area','travel','retry','death'].includes(e.type))){this.clear();return;}
  if(this.disposed||this.suspended||!this.active||game.state.player.hp<=0)return;
  for(const event of events){
   const kind=String(event.kind??''),castId=String(event.castId??''),id=String(event.id??''),skillId=String(event.skillId??'');
   const eventFamily=this.resolveFamily(event,game);
   if(event.type==='skill_hit'){
    const target=String(event.targetId??'');
    this.segments.set(castId+':'+target,{segment:Number(event.segment)||0,until:this.clock+1});
    continue;
   }
   if(event.type==='action'){
    this.remember(id,eventFamily);
    if(kind==='sword')this.launch('WAR',id);
    else if(kind==='bowAim')this.preparation(id,'BOW');
    else if(kind==='staff')this.preparation(id,eventFamily,.22);
   }else if(event.type==='projectile'&&!event.skillId){
    const projectile=game.state.projectiles.find(q=>q.id===id);
    const launchedFamily=audioFamily(event.family)??(kind==='arrow'?'BOW':eventFamily);
    this.remember(id,launchedFamily);this.remember(event.action??projectile?.feedbackActionId,launchedFamily);
    this.stopPreparation();this.launch(launchedFamily,id);
   }else if(event.type==='skill_cast'){
    this.remember(castId,eventFamily);void this.prepare(eventFamily);
    if(!skillId.startsWith('COM_'))this.preparation(castId,eventFamily,Number(event.duration)||undefined);
   }else if(event.type==='skill_release'){
    this.remember(castId,eventFamily);this.stopPreparation();
    const def=COMBAT_SKILLS[skillId];
    if(!def||skillId.startsWith('COM_'))continue;
    if(eventFamily==='FIR'&&skillId!=='FIR_04'||eventFamily==='THU')this.launch(eventFamily,castId+':0');
    else if(!def.offensive){
     const cue=preparationCue(eventFamily)??'war_swing';
     this.once('utility:'+castId,{cue,volume:.19,priority:1,limit:.18},5);
    }
   }else if(event.type==='skill_segment'){
    this.remember(event.projectileId,eventFamily);
    const phase=String(event.phase??''),segment=Number(event.segment)||0;
    if(skillId.startsWith('COM_')||event.child===true||phase==='network'||phase==='redirect'||phase==='impact'||skillId==='BOW_06')continue;
    if(eventFamily==='WAR'||eventFamily==='BOW')this.launch(eventFamily,castId+':'+segment);
   }else if(event.type==='skill_zone'&&skillId==='FIR_04'){
    this.once('wall:'+castId,{cue:'fir_wall',volume:.19,priority:0,limit:Math.min(3,Number(event.duration)||3)},6);
   }else if(event.type==='skill_end'){
    for(const voice of this.voices)if(voice.key==='wall:'+castId)this.stop(voice);
   }
  }
  this.cancelStalePreparation();
 }

 /** Only call for the visible representative chosen by CombatImpactFeedback.
  * No hit is synthesized for an empty swing, expired arrow or a burn tick. */
 impact(event:GameEvent,game:GameSession,blocked=false):boolean {
  if(this.disposed||game.state.player.hp<=0||game.state.status==='dead')return false;
  const family=this.resolveFamily(event,game),request=contactAudioRequest(event,family,blocked);
  if(!request||this.clock<this.nextImpact||this.suspended||!this.active)return false;
  void this.prepare(family);
  const action=String(event.action??event.castId??''),segment=this.segments.get(action+':'+String(event.id))?.segment??0;
  const network=request.cue==='thu_network';
  const key='impact:'+family+':'+action+':'+(network?'network':segment);
  if(this.once(key,request,network?6:1.5)){
   this.nextImpact=this.clock+.075;this.impactCount++;return true;
  }
  return false;
 }

 private cancelStalePreparation():void {
  if(this.prep&&this.game?.state.action?.id!==this.prep.id)this.stopPreparation();
 }
 update(dt:number,active:boolean):void {
  if(this.disposed)return;
  this.clock+=Math.min(.25,Math.max(0,dt));
  if(!active||this.suspended){if(this.active||this.voices.some(v=>v.until>0))this.clear();this.active=active;return;}
  this.active=true;
  for(const voice of this.voices)if(voice.until>0&&voice.until<=this.clock)this.stop(voice);
  this.cancelStalePreparation();
  for(const [key,value]of this.heard)if(value<=this.clock)this.heard.delete(key);
  for(const [key,value]of this.remembered)if(value.until<=this.clock)this.remembered.delete(key);
  for(const [key,value]of this.segments)if(value.until<=this.clock)this.segments.delete(key);
 }
 setSuspended(value:boolean):void {this.suspended=value;if(value)this.clear();}
 clear():void {
  for(const voice of this.voices)this.stop(voice);
  this.prep=undefined;this.heard.clear();this.remembered.clear();this.segments.clear();
  this.nextImpact=this.clock;this.nextRelease=this.clock;
 }
 inspect(){return {version:'fusion-v9',family:this.family,loadedClips:this.clips.size,loadingFamilies:Array.from(this.loads.keys()),failedPaths:Array.from(this.failures),activeVoices:this.voices.filter(v=>v.until>this.clock).map(v=>({key:v.key,remaining:v.until-this.clock,priority:v.priority})),voiceLimit:6,maximumVoices:this.maximumVoices,played:this.played,dropped:this.dropped,impacts:this.impactCount,preparing:this.prep?.id,suspended:this.suspended};}
 dispose():void {
  if(this.disposed)return;this.clear();this.disposed=true;
  for(const clip of this.clips.values())clip.decRef();this.clips.clear();this.root.destroy();
 }
}
