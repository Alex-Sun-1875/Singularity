import {DEV} from 'cc/env';
import {isHtmlRuntime} from './RuntimePlatform';

/** URL and history belong to HTML preview, never to minigame startup or saves. */
export function htmlPreviewOption(name:string):string|null{
 if(!isHtmlRuntime)return null;
 try{return new URLSearchParams(globalThis.location.search).get(name);}catch{return null;}
}
export function rememberHtmlPreviewOption(name:string,value:string):void{
 if(!isHtmlRuntime)return;
 try{const url=new URL(globalThis.location.href);url.searchParams.set(name,value);globalThis.history.replaceState(null,'',url);}catch{/* Cosmetic preview navigation is optional. */}
}
export function isLocalHtmlDevelopment():boolean{
 if(!DEV||!isHtmlRuntime)return false;
 try{return ['127.0.0.1','localhost','[::1]'].includes(globalThis.location.hostname);}catch{return false;}
}
/** Resource graph selection is not a platform, login or release-build flag. */
export function htmlBundlePreview():boolean{return isHtmlRuntime&&(globalThis as {__SINGULARITY_BUNDLE_PREVIEW__?:boolean}).__SINGULARITY_BUNDLE_PREVIEW__===true;}
