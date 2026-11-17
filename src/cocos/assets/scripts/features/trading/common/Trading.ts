import type {GameState} from '../../../core/GameSession';
import {EQUIPMENT,MERCHANTS} from '../../equipment/data/Equipment';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {GEM_POLICY,gemBankKey} from '../../gems/data/Gems';
import {shopProduct,shopChapter,type ShopProduct} from '../data/Shops';

export interface ShopQuote {allowed:boolean;reason:string;token:string;product?:ShopProduct;quantity:number;total:number;balance:number;remaining:number;stock?:number}
interface Host {state():GameState;access(merchant:string):{available:boolean;reason:string};equipment(merchant:string,item:string):boolean;gems(merchant:string,product:string,quantity:number):boolean;id(prefix:string):string;changed():void}
export class Trading {
 constructor(private host:Host){}
 quote(merchant:string,id:string,quantity=1):ShopQuote {
  const s=this.host.state(),p=shopProduct(merchant,id),total=(p?.price??0)*quantity;
  const q:ShopQuote={allowed:false,reason:'',token:JSON.stringify([s.sequence,s.revision,s.gems.revision,s.player.gold,s.progression.level,shopChapter(s),merchant,id,quantity]),product:p,quantity,total,balance:s.player.gold,remaining:s.player.gold-total};
  const access=this.host.access(merchant);
  if(!p||!Number.isSafeInteger(quantity)||quantity<1||quantity>10||p.kind==='equipment'&&quantity!==1)q.reason='请选择有效的商品与数量';
  else if(!access.available)q.reason=access.reason;
  else if(shopChapter(s)<p.chapter)q.reason=`进入真实开放的第${p.chapter}章后供货`;
  else if(s.progression.level<p.level)q.reason=`角色 Lv${p.level} 开放`;
  else if(p.kind==='equipment'&&(!(s.merchantStock[merchant]?.[id]>0)||!!s.inventory[id]))q.reason=s.inventory[id]?'已经持有这件装备':'本旅程已售罄';
  else if(p.kind==='supply'&&s.player[SUPPLIES[p.supply!].stock]+quantity>SUPPLIES[p.supply!].capacity)q.reason='药剂携带容量不足';
  else if(p.kind==='gem'&&(s.gems.bank[gemBankKey(p.stat!,p.tier!)]??0)+quantity*5>GEM_POLICY.capacity||p.kind==='drills'&&s.gems.drills+quantity>GEM_POLICY.capacity)q.reason='材料库存容量不足';
  else if(s.player.gold<total)q.reason=`金币不足，还差 ${total-s.player.gold}`;
  else q.allowed=true;
  if(p?.kind==='equipment')q.stock=s.merchantStock[merchant]?.[id]??MERCHANTS[merchant]?.stock[id]??0;
  return q;
 }
 buy(merchant:string,id:string,quantity:number,token:string):boolean {
  const q=this.quote(merchant,id,quantity);if(!q.allowed||q.token!==token||!q.product)return false;
  const s=this.host.state(),p=q.product;
  if(p.kind==='equipment')return this.host.equipment(merchant,id);
  if(p.kind==='gem'||p.kind==='drills')return this.host.gems(merchant,id,quantity);
  const request=this.host.id('shop');s.player.gold-=q.total;s.player[SUPPLIES[p.supply!].stock]+=quantity;
  s.receipts[request]=JSON.stringify([1,merchant,id,quantity,q.total]);this.host.changed();return true;
 }
}
export function validateShopReceipts(s:GameState):void {
 for(const [key,value]of Object.entries(s.receipts)){
  if(!key.startsWith('shop:'))continue;
  try{
   const [version,merchant,id,quantity,total]=JSON.parse(String(value)),product=shopProduct(merchant,id),sequence=Number(key.slice(5));
   if(!Number.isSafeInteger(sequence)||sequence<1||sequence>s.sequence||version!==1||product?.kind!=='supply'||!s.discoveredMerchants.includes(merchant)||!Number.isSafeInteger(quantity)||quantity<1||quantity>10||total!==product.price*quantity)throw new Error();
  }catch{throw new Error('无效的商店购买凭证');}
 }
}
