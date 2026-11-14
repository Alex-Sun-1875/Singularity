import {Label,TTFFont} from 'cc';
import {gameResources} from '../assets/GameResources';
let cached:TTFFont|undefined;
let loading:Promise<TTFFont>|undefined;
/** Keep compact HUD lines at their chosen size; full details remain in their panel. */
export function fitRpgLine(value:string,width:number,size:number):string {
 const length=(s:string)=>Array.from(s).reduce((n,c)=>n+(c==='·'?.4:c==='…'?.85:c.charCodeAt(0)<128?.56:1),0)*size;
 if(length(value)<=width)return value;
 const chars=Array.from(value);while(chars.length&&length(chars.join('')+'…')>width)chars.pop();
 return chars.join('')+'…';
}
/** One bundled OFL subset keeps the approved serif face consistent across phones. */
export function applyRpgFont(label:Label){
 const apply=(font:TTFFont)=>{if(label.isValid){label.font=font;label.useSystemFont=false;}};
 if(cached){apply(cached);return;}
 loading??=new Promise<TTFFont>((resolve,reject)=>gameResources.load('ui/quiet-bronze/rpg-serif-v2',TTFFont,(error,font)=>{if(error){loading=undefined;reject(error);}else{cached=font;resolve(font);}}));
 void loading.then(apply).catch(()=>{if(label.isValid)label.fontFamily='serif';});
}
