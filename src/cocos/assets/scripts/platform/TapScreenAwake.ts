import type {ScreenAwake} from './ScreenAwake';

/** Official API: https://developer.taptap.cn/minigameapidoc/dev/api/device/screen/tap.setKeepScreenOn/ */
export interface TapScreenAPI {
 setKeepScreenOn?(options:{keepScreenOn:boolean;success?:()=>void;fail?:(error:unknown)=>void}):void|Promise<unknown>;
}

/** Foreground ownership only; no per-frame polling or changes to system brightness. */
export class TapScreenAwake implements ScreenAwake {
 private wanted=false;
 private disposed=false;
 private warnedUnsupported=false;
 constructor(private readonly api:TapScreenAPI|undefined,private readonly warn:(message:string,error?:unknown)=>void=(message,error)=>console.warn('[ScreenAwake]',message,error)){}
 setForeground(foreground:boolean){if(this.disposed)return;this.wanted=foreground;this.apply(foreground);}
 dispose(){if(this.disposed)return;this.disposed=true;this.wanted=false;this.apply(false);}
 private apply(keepScreenOn:boolean){
  const api=this.api;
  if(!api?.setKeepScreenOn){
   if(api&&keepScreenOn&&!this.warnedUnsupported){this.warnedUnsupported=true;this.warn('This TapTap host does not expose setKeepScreenOn.');}
   return;
  }
  let settled=false;
  const success=()=>{
   if(settled)return;settled=true;
   // A late native completion must not restore an earlier foreground/background state.
   if(keepScreenOn!==this.wanted)this.apply(this.wanted);
  };
  const fail=(error:unknown)=>{if(settled)return;settled=true;this.warn('Could not '+(keepScreenOn?'enable':'release')+' screen-on protection.',error);};
  try{
   const pending=api.setKeepScreenOn({keepScreenOn,success,fail});
   if(pending&&typeof pending.then==='function')void pending.then(success,fail);
  }catch(error){fail(error);}
 }
}
