import {game, Game} from 'cc';
import type {KeyValueStore} from '../features/persistence/common/SaveStore';
import {TapLogin,type TapLoginAPI} from './TapLogin';
import {TAP_AUTH_CONFIG} from './TapAuthConfig';
import {TapUpdates,type TapUpdateManager} from './TapUpdates';
import {BUILD_PROFILE} from '../shared/BuildProfile';
import {TapScreenAwake,type TapScreenAPI} from './TapScreenAwake';
import {HtmlScreenAwake} from './HtmlScreenAwake';
import type {ScreenAwake} from './ScreenAwake';
import {isTapMinigame,isHtmlRuntime,readTapAPI} from './RuntimePlatform';
import {platformStorage} from './PlatformStorage';

export type MemoryWarning={level?:number};
type TapAPI=TapLoginAPI&TapScreenAPI&{getUpdateManager?():TapUpdateManager;onMemoryWarning?(listener:(warning?:MemoryWarning)=>void):void;offMemoryWarning?(listener:(warning?:MemoryWarning)=>void):void};
/** Both platforms run identical rules; only persistence/lifecycle cross this boundary. */
export class PlatformServices implements KeyValueStore {
 readonly tap=readTapAPI<TapAPI>();
 readonly auth:TapLogin;
 readonly updates:TapUpdates;
 constructor(changed:()=>void=()=>{}){const guestTest=isTapMinigame&&BUILD_PROFILE.name==='test'&&(globalThis as any).__SINGULARITY_GUEST_TEST__===true;this.auth=new TapLogin(this.tap,isTapMinigame&&!guestTest,{...TAP_AUTH_CONFIG,guestTest},changed);this.updates=new TapUpdates(this.tap,changed);}
 getItem(key:string):string|null{return platformStorage.getItem(key);}
 setItem(key:string,value:string):void{platformStorage.setItem(key,value);}
 removeItem(key:string):void{platformStorage.removeItem(key);}
 keys():string[]{return platformStorage.keys();}
 lifecycle(hide:()=>void,show:()=>void):()=>void {
   // Build/runtime selection is explicit: a browser never invokes TapTap screen APIs.
   const screen:ScreenAwake=isTapMinigame?new TapScreenAwake(this.tap):isHtmlRuntime?new HtmlScreenAwake():{setForeground:()=>{},dispose:()=>{}};
   let listening=true;
   const onHide=()=>{if(!listening)return;screen.setForeground(false);hide();};
   const onShow=()=>{if(!listening)return;screen.setForeground(true);show();};
   game.on(Game.EVENT_HIDE,onHide);game.on(Game.EVENT_SHOW,onShow);
   screen.setForeground(true);
   return ()=>{if(!listening)return;listening=false;game.off(Game.EVENT_HIDE,onHide);game.off(Game.EVENT_SHOW,onShow);screen.dispose();};
 }
 /** iOS does not supply Android's numeric warning level. Keep the exact
  * listener for official unsubscription and tolerate older host libraries. */
 memoryPressure(listener:(warning?:MemoryWarning)=>void):()=>void {
  const tap=this.tap;if(!tap?.onMemoryWarning||!tap.offMemoryWarning)return ()=>{};
  try{tap.onMemoryWarning(listener);}catch{return ()=>{};}
  return ()=>{try{tap.offMemoryWarning(listener);}catch{/* Host teardown must remain safe. */}};
 }
}
