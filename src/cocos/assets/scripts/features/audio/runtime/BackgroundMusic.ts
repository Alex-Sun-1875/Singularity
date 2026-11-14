import {AudioClip,AudioSource,Node} from 'cc';
import {gameResources} from '../../../shared/assets/GameResources';
import type {KeyValueStore} from '../../persistence/common/SaveStore';

const TRACK='audio/music/dawn-embers';
const PREFERENCE='sword-and-fire.music.v1';

/** One persistent source across area rebuilds; Cocos owns platform audio playback. */
export class BackgroundMusic {
 private readonly root:Node;
 private readonly source:AudioSource;
 private clip:AudioClip|undefined;
 private requested=false;
 private loading=false;
 private disposed=false;
 private suspended=false;
 private allowed=false;
 private playing=false;
 private level=0;
 enabled=true;
 failed=false;

 constructor(parent:Node,private readonly store:KeyValueStore,private readonly changed:()=>void){
  this.root=new Node('BackgroundMusic');parent.addChild(this.root);
  this.source=this.root.addComponent(AudioSource);
  this.source.playOnAwake=false;this.source.loop=true;this.source.volume=0;
  try{this.enabled=this.store.getItem(PREFERENCE)!=='off';}catch{ /* Storage failure must not block play. */ }
 }

 start():void{this.requested=true;this.gesture();}

 /** Called by real input as well as start, allowing the engine to unlock mobile audio. */
 gesture():void{
  if(this.disposed||!this.requested||!this.enabled||this.suspended)return;
  if(!this.clip&&!this.loading&&!this.failed)this.load();
  else if(this.clip&&this.allowed&&!this.playing){this.source.play();this.playing=true;}
 }

 toggle():void{
  // A failed download gets an explicit retry rather than automatic network polling.
  if(this.failed){this.failed=false;this.enabled=true;this.gesture();}
  else{this.enabled=!this.enabled;if(this.enabled)this.gesture();}
  try{this.store.setItem(PREFERENCE,this.enabled?'on':'off');}catch{ /* Keep this session's choice. */ }
  this.changed();
 }

 get label():string{return this.failed?'背景音乐：载入失败，点击重试':`背景音乐：${this.enabled?'开':'关'}`;}

 setSuspended(value:boolean):void{
  this.suspended=value;
  if(value){this.allowed=false;this.pause();}
  else this.gesture();
 }

 update(dt:number,allowed:boolean,quiet:boolean):void{
  if(this.disposed)return;
  this.allowed=allowed;
  if(!allowed||this.suspended){this.pause();return;}
  const target=this.enabled&&this.requested&&this.clip?(quiet ? .13 : .28):0;
  this.level+=(target-this.level)*(1-Math.exp(-Math.min(dt,.5)*2.8));
  this.source.volume=this.level;
  if(target>0&&this.clip&&!this.playing){this.source.play();this.playing=true;}
  if(target===0&&this.level<.001)this.pause();
 }

 private pause():void{
  if(this.playing)this.source.pause();
  this.playing=false;this.level=0;this.source.volume=0;
 }

 private load():void{
  this.loading=true;
  gameResources.load(TRACK,AudioClip,(error,clip)=>{
   this.loading=false;
   if(this.disposed)return;
   if(error||!clip){this.failed=true;console.warn('[Music] Background track unavailable; gameplay continues.');this.changed();return;}
   clip.addRef();this.clip=clip;this.source.clip=clip;this.gesture();
  });
 }

 dispose():void{
  this.disposed=true;this.source.stop();this.source.clip=null;
  this.clip?.decRef();this.clip=undefined;this.root.destroy();
 }
}
