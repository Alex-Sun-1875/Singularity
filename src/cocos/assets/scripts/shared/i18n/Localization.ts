import {createInstance} from 'i18next';

export type GameLocale='zh-CN'|'en';
export const LOCALE_PREFERENCE='sword-fire-story-locale';
const engine=createInstance();
// All catalogs are packaged modules: no browser detector, backend, HTTP or DOM.
void engine.init({lng:'zh-CN',fallbackLng:'zh-CN',supportedLngs:['zh-CN','en'],
 resources:{'zh-CN':{},en:{}},initAsync:false,keySeparator:false,
 interpolation:{escapeValue:false,prefix:'{',suffix:'}'},returnEmptyString:false});
const listeners=new Set<()=>void>();
let catalogRevision=0;
export function currentLocale():GameLocale{return engine.language==='en'?'en':'zh-CN';}
export function setLocale(value:unknown):void {
 const locale:GameLocale=value==='en'?'en':'zh-CN';
 if(locale===currentLocale())return;
 void engine.changeLanguage(locale,()=>{for(const listener of listeners)listener();});
}
export function onLocaleChanged(listener:()=>void):()=>void{listeners.add(listener);return ()=>{listeners.delete(listener);};}
/** Feature-owned catalogs share a small adapter; English must cover every Chinese key. */
export function registerMessages<Z extends Record<string,string>>(namespace:string,zh:Z,en:Record<keyof Z,string>){
 engine.addResourceBundle('zh-CN',namespace,zh,true,true);engine.addResourceBundle('en',namespace,en,true,true);
 catalogRevision++;
 // Keep only the latest arguments per message; changing counters stay bounded.
 const recent=new Map<keyof Z,{locale:string;revision:number;keys:number;values:Record<string,string|number>;text:string}>();
 return (key:keyof Z,values:Record<string,string|number>={},locale?:GameLocale):string=>{
  const language=locale??engine.language,keys=Object.keys(values),cached=recent.get(key);
  if(cached&&cached.revision===catalogRevision&&cached.locale===language&&cached.keys===keys.length&&keys.every(name=>Object.prototype.hasOwnProperty.call(cached.values,name)&&cached.values[name]===values[name]))return cached.text;
  const text=String(engine.t(String(key),{ns:namespace,...values,...(locale?{lng:locale}:{})}));
  if(Object.prototype.hasOwnProperty.call(zh,key)||Object.prototype.hasOwnProperty.call(en,key))recent.set(key,{locale:language,revision:catalogRevision,keys:keys.length,values:{...values},text});return text;
 };
}
