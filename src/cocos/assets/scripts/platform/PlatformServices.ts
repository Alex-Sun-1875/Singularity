import {game, Game, sys} from 'cc';
import {MINIGAME} from 'cc/env';
import type {KeyValueStore} from '../features/persistence/common/SaveStore';
import {TapLogin,type TapLoginAPI} from './TapLogin';
import {TAP_AUTH_CONFIG} from './TapAuthConfig';
import {TapUpdates,type TapUpdateManager} from './TapUpdates';
import {BUILD_PROFILE} from '../shared/BuildProfile';

export type MemoryWarning={level?:number};
type TapAPI=TapLoginAPI&{getStorageSync(key:string):unknown;setStorageSync(key:string,value:string):void;removeStorageSync(key:string):void;getStorageInfoSync():{keys:string[]};getUpdateManager?():TapUpdateManager;onMemoryWarning?(listener:(warning?:MemoryWarning)=>void):void;offMemoryWarning?(listener:(warning?:MemoryWarning)=>void):void};
/** Both platforms run identical rules; only persistence/lifecycle cross this boundary. */
export class PlatformServices implements KeyValueStore {
 readonly tap:TapAPI|undefined=(globalThis as any).tap;
 readonly auth:TapLogin;
 readonly updates:TapUpdates;
 constructor(changed:()=>void=()=>{}){const guestTest=BUILD_PROFILE.name==='test'&&(globalThis as any).__SINGULARITY_GUEST_TEST__===true;this.auth=new TapLogin(this.tap,(MINIGAME||!!this.tap)&&!guestTest,{...TAP_AUTH_CONFIG,guestTest},changed);this.updates=new TapUpdates(this.tap,changed);}
 private storageKey(key:string){return BUILD_PROFILE.storagePrefix+key;}
 getItem(key:string):string|null {
   key=this.storageKey(key);
   if(this.tap){const v=this.tap.getStorageSync(key);return typeof v==='string'&&v.length?v:null;}
   return sys.localStorage.getItem(key);
 }
 setItem(key:string,value:string):void {
   key=this.storageKey(key);
   if(this.tap)this.tap.setStorageSync(key,value);else sys.localStorage.setItem(key,value);
 }
 removeItem(key:string):void {
   key=this.storageKey(key);
   if(this.tap)this.tap.removeStorageSync(key);else sys.localStorage.removeItem(key);
 }
 keys():string[]{
   if(this.tap)return this.logicalKeys(this.tap.getStorageInfoSync().keys);
   const keys:string[]=[];for(let i=0;i<sys.localStorage.length;i++){const key=sys.localStorage.key(i);if(key!==null)keys.push(key);}return this.logicalKeys(keys);
 }
 private logicalKeys(keys:string[]){const prefix=BUILD_PROFILE.storagePrefix;return prefix?keys.filter(key=>key.startsWith(prefix)).map(key=>key.slice(prefix.length)):keys.filter(key=>!key.startsWith('singularity.dev.'));}
 lifecycle(hide:()=>void,show:()=>void):()=>void {
   game.on(Game.EVENT_HIDE,hide);game.on(Game.EVENT_SHOW,show);
   return ()=>{game.off(Game.EVENT_HIDE,hide);game.off(Game.EVENT_SHOW,show);};
 }
 /** iOS does not supply Android's numeric warning level. Keep the exact
  * listener for official unsubscription and tolerate older host libraries. */
 memoryPressure(listener:(warning?:MemoryWarning)=>void):()=>void {
  const tap=this.tap;if(!tap?.onMemoryWarning||!tap.offMemoryWarning)return ()=>{};
  try{tap.onMemoryWarning(listener);}catch{return ()=>{};}
  return ()=>{try{tap.offMemoryWarning(listener);}catch{/* Host teardown must remain safe. */}};
 }
}
