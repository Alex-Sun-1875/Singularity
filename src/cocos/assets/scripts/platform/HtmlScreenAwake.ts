import type {ScreenAwake} from './ScreenAwake';

type HtmlScreenHost={
 isSecureContext?:boolean;
 document?:Pick<Document,'visibilityState'|'addEventListener'|'removeEventListener'>;
 navigator?:{wakeLock?:Pick<WakeLock,'request'>};
};

/** Browser-only Screen Wake Lock API: https://www.w3.org/TR/screen-wake-lock/
 * No DOM or navigator access occurs until this browser adapter is constructed. */
export class HtmlScreenAwake implements ScreenAwake {
 private foreground=false;
 private disposed=false;
 private pending=false;
 private retryPending=false;
 private warnedUnsupported=false;
 private lock:WakeLockSentinel|undefined;
 private releaseListener:(()=>void)|undefined;
 private readonly onVisibility=()=>this.synchronize();
 private readonly onInteraction=()=>this.synchronize();
 constructor(private readonly host:HtmlScreenHost=globalThis,private readonly warn:(message:string,error?:unknown)=>void=(message,error)=>console.warn('[HtmlScreenAwake]',message,error)){
  host.document?.addEventListener('visibilitychange',this.onVisibility);
  host.document?.addEventListener('pointerdown',this.onInteraction,{passive:true});
 }
 setForeground(foreground:boolean){if(this.disposed)return;this.foreground=foreground;this.synchronize();}
 dispose(){
  if(this.disposed)return;this.disposed=true;this.foreground=false;
  this.host.document?.removeEventListener('visibilitychange',this.onVisibility);
  this.host.document?.removeEventListener('pointerdown',this.onInteraction);
  this.synchronize();
 }
 private eligible(){return !this.disposed&&this.foreground&&this.host.document?.visibilityState==='visible';}
 private synchronize(){
  if(!this.eligible()){this.releaseCurrent();return;}
  if(this.lock&&!this.lock.released)return;
  if(this.pending){this.retryPending=true;return;}
  const api=this.host.navigator?.wakeLock;
  if(!this.host.isSecureContext||!api?.request){
   if(!this.warnedUnsupported){this.warnedUnsupported=true;this.warn('Screen Wake Lock requires a supported browser in a secure context.');}
   return;
  }
  this.pending=true;this.retryPending=false;void this.acquire(api);
 }
 private async acquire(api:Pick<WakeLock,'request'>){
  let retry=false;
  try{
   const lock=await api.request('screen');
   if(!this.eligible()){this.releaseLock(lock);return;}
   if(lock.released){retry=true;return;}
   this.lock=lock;
   this.releaseListener=()=>{
    if(this.lock!==lock)return;
    this.lock=undefined;this.releaseListener=undefined;
    // Respect system revocation; retry only on foreground/visibility/interaction.
   };
   lock.addEventListener('release',this.releaseListener,{once:true});
  }catch(error){retry=true;this.warn('Could not acquire screen wake lock.',error);}
  finally{
   this.pending=false;const retryPending=this.retryPending;this.retryPending=false;
   if(retry&&retryPending&&this.eligible())this.synchronize();
  }
 }
 private releaseCurrent(){
  const lock=this.lock;if(!lock)return;
  if(this.releaseListener)lock.removeEventListener('release',this.releaseListener);
  this.lock=undefined;this.releaseListener=undefined;this.releaseLock(lock);
 }
 private releaseLock(lock:WakeLockSentinel){
  if(lock.released)return;
  try{void lock.release().catch(error=>this.warn('Could not release screen wake lock.',error));}
  catch(error){this.warn('Could not release screen wake lock.',error);}
 }
}
