/** Uses the platform's automatic update check/download; never downloads code itself. */
export interface TapUpdateManager {
 onCheckForUpdate(listener:(result:{hasUpdate:boolean})=>void):void;
 onUpdateReady(listener:()=>void):void;
 onUpdateFailed(listener:()=>void):void;
 applyUpdate():void;
}
export class TapUpdates {
 status:'unsupported'|'idle'|'available'|'ready'|'failed'|'applying'='unsupported';
 promptPending=false;message='';private disposed=false;private manager:TapUpdateManager|undefined;
 constructor(api:{getUpdateManager?():TapUpdateManager}|undefined,private readonly changed:()=>void=()=>{}){
  try{
   this.manager=api?.getUpdateManager?.();if(!this.manager)return;this.status='idle';
   this.manager.onCheckForUpdate(result=>{if(!this.disposed&&this.status!=='ready'&&this.status!=='applying'){this.status=result.hasUpdate?'available':'idle';this.changed();}});
   this.manager.onUpdateReady(()=>{if(!this.disposed){this.status='ready';this.message='新版本已下载，保存旅途后重启即可更新。';this.promptPending=true;this.changed();}});
   this.manager.onUpdateFailed(()=>{if(!this.disposed){this.status='failed';this.promptPending=false;this.message='新版本下载未完成，可继续当前旅途，稍后重新打开游戏再试。';this.changed();}});
  }catch{this.status='unsupported';this.manager=undefined;}
 }
 get ready(){return this.status==='ready';}
 defer(){this.promptPending=false;this.changed();}
 requestPrompt(){if(this.ready){this.promptPending=true;this.changed();}}
 apply(save:()=>boolean):boolean {
  if(this.disposed||!this.ready||!this.manager)return false;
  try{
   if(!save()){this.message='进度保存失败，请重试或稍后更新。';this.promptPending=true;this.changed();return false;}
   this.status='applying';this.message='进度已保存，正在重启更新…';this.changed();this.manager.applyUpdate();return true;
  }catch{this.status='ready';this.message='更新未能启动，请重试或稍后重新打开游戏。';this.promptPending=true;this.changed();return false;}
 }
 dispose(){this.disposed=true;this.promptPending=false;}
}
