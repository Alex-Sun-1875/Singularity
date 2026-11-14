import {NavigationWasmBackend} from '../common/NavigationWasmBackend';
import {loadPackagedWasm} from '../../../platform/WasmModule';
import {Navigation} from './Navigation';
import {NAVIGATION_WASM} from './NavigationWasmConfig';

let pending:Promise<void>|undefined;
let enabled:boolean=NAVIGATION_WASM.enabled;
let state:'idle'|'disabled'|'loading'|'ready'|'fallback'=enabled?'idle':'disabled';
let backend:NavigationWasmBackend|undefined;
/** One test switch controls every migrated CPU operation. Loading can finish
 * after a disable, but must never reinstall the backend against that choice. */
export function setComputationWasmEnabled(value:boolean):Promise<void>{
 enabled=value&&NAVIGATION_WASM.available;
 if(!enabled){Navigation.useSearchBackend(undefined);state='disabled';return Promise.resolve();}
 return prepareNavigationWasm();
}
/** Optional acceleration never gates login, scene startup or normal rules. */
export function prepareNavigationWasm():Promise<void>{
 if(!enabled||!NAVIGATION_WASM.available){state='disabled';return Promise.resolve();}
 if(backend){Navigation.useSearchBackend(backend);state='ready';return Promise.resolve();}
 if(pending)return pending;
 state='loading';
 pending=(async()=>{
  try{
   const instance=await loadPackagedWasm(NAVIGATION_WASM.path,NAVIGATION_WASM.subpackage,{navigation:{hypot:Math.hypot}});
   backend=new NavigationWasmBackend(instance.exports,error=>{Navigation.useSearchBackend(undefined);backend=undefined;state=enabled?'fallback':'disabled';console.warn('[NavigationWasm] JavaScript fallback',String(error));});
   if(enabled){Navigation.useSearchBackend(backend);state='ready';}else state='disabled';
  }catch(error){state=enabled?'fallback':'disabled';console.warn('[NavigationWasm] JavaScript fallback',String(error));}
  finally{pending=undefined;}
 })();return pending;
}
export function navigationWasmState(){return{enabled,available:NAVIGATION_WASM.available,state,activeBackend:state==='ready',abi:NAVIGATION_WASM.abi,bytes:NAVIGATION_WASM.bytes,...backend?.inspect()};}
