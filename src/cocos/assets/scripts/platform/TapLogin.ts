/** Callback-only TapTap APIs. No Cocos/browser dependencies in this boundary. */
export interface TapLoginAPI {
 login?(options:{timeout:number;success:(res:{code?:string})=>void;fail:(error:unknown)=>void}):void;
 checkSession?(options:{success:()=>void;fail:(error:unknown)=>void}):void;
}
export type LoginStatus='preview'|'guest'|'idle'|'checking'|'logging-in'|'platform-ready'|'failed';
export interface LoginState {status:LoginStatus;message:string;error?:string}
export interface LoginConfig {timeoutMs:number;guestTest?:boolean}
class LoginError extends Error {constructor(readonly code:string,message:string){super(message);}}
export class TapLogin {
 state:LoginState;
 private platformReady=false;
 private pending:Promise<boolean>|undefined;
 private disposed=false;
 private readonly cancellations=new Set<()=>void>();
 constructor(private readonly api:TapLoginAPI|undefined,readonly required:boolean,private readonly config:LoginConfig,private readonly changed:()=>void=()=>{}){this.state={status:required?'idle':config.guestTest?'guest':'preview',message:required?'等待登录':config.guestTest?'游客测试 · 仅本机存档（未登录）':'浏览器预览（不代表正式登录）'};}
 get ready():boolean{return !this.disposed&&(!this.required||this.state.status==='platform-ready'&&this.platformReady);}
 ensure(resume=false):Promise<boolean>{
  if(this.disposed)return Promise.resolve(false);
  if(!this.required)return Promise.resolve(true);
  if(this.pending)return this.pending;
  if(!resume&&this.ready)return Promise.resolve(true);
  this.pending=this.authenticate().finally(()=>{this.pending=undefined;});return this.pending;
 }
 private set(status:LoginStatus,message:string,error?:string){if(!this.disposed){this.state={status,message,...(error?{error}:{})};this.changed();}}
 private async authenticate():Promise<boolean>{
  try{
   if(!this.api?.login||!this.api.checkSession)throw new LoginError('PLATFORM_UNAVAILABLE','登录暂不可用，请关闭游戏后重新打开。');
   // The host can retain a valid session even after recreating the game.
   // Check it on cold starts too; never persist a code as proof of login.
   this.set('checking','正在检查登录状态…');
   const valid=await this.call<void>((success,fail)=>this.api!.checkSession!({success,fail})).then(()=>true,error=>{
    // A local timeout or cancellation does not prove the host session expired.
    if(error instanceof LoginError)throw error;
    return false;
   });
   if(this.disposed)return false;
   if(valid){this.platformReady=true;this.set('platform-ready','登录已就绪');return true;}
   this.platformReady=false;this.set('logging-in','正在登录…');
   const result=await this.call<{code?:string}>((success,fail)=>this.api!.login!({timeout:this.config.timeoutMs,success,fail}));
   if(typeof result?.code!=='string'||!result.code.trim())throw new LoginError('EMPTY_CODE','登录未完成，请重试。');
   if(this.disposed)return false;
   // This is platform login readiness, not an openid or a game-server session.
   // Never persist/log the one-time code or manufacture a token from it.
   this.platformReady=true;this.set('platform-ready','登录已就绪');return true;
  }catch(error){
   this.platformReady=false;const known=error instanceof LoginError?error:new LoginError('PLATFORM_FAILED','暂时无法连接，请检查网络后重试。');
   this.set('failed',known.message,known.code);return false;
  }
 }
 private call<T>(start:(success:(value:T)=>void,fail:(error:unknown)=>void)=>void):Promise<T>{
  return new Promise((resolve,reject)=>{
   let done=false;
   const finish=(error:unknown,value?:T)=>{if(done)return;done=true;clearTimeout(timer);this.cancellations.delete(cancel);if(error)reject(error);else resolve(value as T);};
   const cancel=()=>finish(new LoginError('CANCELLED','登录已中断，请重试。'));
   const timer=setTimeout(()=>finish(new LoginError('TIMEOUT','登录超时，请检查网络后重试。')),this.config.timeoutMs);
   this.cancellations.add(cancel);
   try{start(value=>finish(null,value),error=>finish(error||new Error('platform failed')));}catch(error){finish(error);}
  });
 }
 dispose(){this.disposed=true;this.platformReady=false;for(const cancel of Array.from(this.cancellations))cancel();}
}
