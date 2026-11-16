import {sys} from 'cc';
import type {KeyValueStore} from '../features/persistence/common/SaveStore';
import {BUILD_PROFILE} from '../shared/BuildProfile';
import {isTapMinigame,isHtmlRuntime,readTapAPI} from './RuntimePlatform';

export interface PlatformKeyValueStore extends KeyValueStore {removeItem(key:string):void;keys():string[];}
interface TapStorageAPI {
 getStorageSync(key:string):unknown;
 setStorageSync(key:string,value:string):void;
 removeStorageSync(key:string):void;
 getStorageInfoSync():{keys:string[]};
}
function requireTapStorage(method:keyof TapStorageAPI):TapStorageAPI{
 const api=readTapAPI<TapStorageAPI>();
 if(typeof api?.[method]!=='function')throw new Error('TapTap storage API unavailable: '+method);
 return api;
}
const tapStorage:PlatformKeyValueStore={
 getItem(key){const value=requireTapStorage('getStorageSync').getStorageSync(key);return typeof value==='string'&&value.length?value:null;},
 setItem(key,value){requireTapStorage('setStorageSync').setStorageSync(key,value);},
 removeItem(key){requireTapStorage('removeStorageSync').removeStorageSync(key);},
 keys(){return requireTapStorage('getStorageInfoSync').getStorageInfoSync().keys;},
};
function requireHtmlStorage(){
 if(!isHtmlRuntime)throw new Error('HTML storage is unavailable on this runtime');
 return sys.localStorage;
}
const htmlStorage:PlatformKeyValueStore={
 getItem(key){return requireHtmlStorage().getItem(key);},
 setItem(key,value){requireHtmlStorage().setItem(key,value);},
 removeItem(key){requireHtmlStorage().removeItem(key);},
 keys(){const storage=requireHtmlStorage(),keys:string[]=[];for(let i=0;i<storage.length;i++){const key=storage.key(i);if(key!==null)keys.push(key);}return keys;},
};
const storage=isTapMinigame?tapStorage:htmlStorage;
/** One namespace for journey saves, preferences, charts and diagnostics alike.
 * A missing TapTap API must fail visibly to SaveStore instead of changing stores. */
export const platformStorage:PlatformKeyValueStore={
 getItem(key){return storage.getItem(BUILD_PROFILE.storagePrefix+key);},
 setItem(key,value){storage.setItem(BUILD_PROFILE.storagePrefix+key,value);},
 removeItem(key){storage.removeItem(BUILD_PROFILE.storagePrefix+key);},
 keys(){const prefix=BUILD_PROFILE.storagePrefix,keys=storage.keys();return prefix?keys.filter(key=>key.startsWith(prefix)).map(key=>key.slice(prefix.length)):keys.filter(key=>!key.startsWith('singularity.dev.'));},
};
