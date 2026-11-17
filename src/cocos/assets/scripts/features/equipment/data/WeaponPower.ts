/** Native weapon strength has useful early gains and a bounded late-game curve.
 * All weapon descriptions and combat paths use the same diminishing return.
 */
export function weaponPowerMultiplier(power:number):number {
 const strength=Number.isFinite(power)?Math.max(0,power):0;
 return 1+strength/(100+strength/3);
}
export const weaponPowerBonusPercent=(power:number)=>(weaponPowerMultiplier(power)-1)*100;

type NativeWeapon={id:string;slot:string;level:number;quality:string;power?:number};
const LEGACY_STRENGTH=[10,18,30,45,63] as const;
const QUALITY_STRENGTH:Readonly<Record<string,number>>={'普通':.85,'精良':.9,'稀有':1,'史诗':1.1,'传奇':1.18,'神器':1.25};
/** Fixed legacy tier/quality, never the wearer's level. Explicit strength and
 * zero-strength starter weapons retain their authored identity. Growing
 * weapons are resolved separately by their existing level curve.
 */
export function nativeWeaponStrength(item:NativeWeapon):number {
 if(item.power!==undefined)return Number.isFinite(item.power)?Math.max(0,item.power):0;
 if(item.slot!=='weapon'||['W01','W07','W11'].includes(item.id))return 0;
 const tier=Math.max(1,Math.min(5,Math.floor(item.level)||1));
 return Math.round(LEGACY_STRENGTH[tier-1]*(QUALITY_STRENGTH[item.quality]??1));
}
