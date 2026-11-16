import {assetManager} from 'cc';
import {isTapMinigame,isHtmlRuntime,readTapAPI} from './RuntimePlatform';

type WasmRuntime={instantiate(source:ArrayBuffer|string,imports:WebAssembly.Imports):Promise<WebAssembly.WebAssemblyInstantiatedSource>};
type TapWasmAPI={loadSubpackage(options:{name:string;success:()=>void;fail:(error:unknown)=>void}):unknown};
/** TapTap's official runtime consumes package paths, while Web preview consumes
 * Cocos-downloaded bytes. Browser loading stays isolated at this platform edge. */
export async function loadPackagedWasm(path:string,subpackage:string,imports:WebAssembly.Imports):Promise<WebAssembly.Instance>{
 const runtime=(globalThis as unknown as {WebAssembly?:WasmRuntime}).WebAssembly;
 if(!runtime?.instantiate)throw new Error('WebAssembly is unavailable');
 if(isTapMinigame){
  const tap=readTapAPI<TapWasmAPI>();
  if(!tap?.loadSubpackage)throw new Error('TapTap WASM subpackage loading is unavailable');
  await new Promise<void>((resolve,reject)=>tap.loadSubpackage({name:subpackage,success:resolve,fail:reject}));
  return(await runtime.instantiate(path,imports)).instance;
 }
 if(!isHtmlRuntime)throw new Error('Custom WASM loading is unavailable on this runtime');
 const bytes=await new Promise<ArrayBuffer>((resolve,reject)=>assetManager.downloader.download(path,path,'.bin',{maxRetryCount:1},(error,data:ArrayBuffer)=>error?reject(error):resolve(data)));
 return(await runtime.instantiate(bytes,imports)).instance;
}
