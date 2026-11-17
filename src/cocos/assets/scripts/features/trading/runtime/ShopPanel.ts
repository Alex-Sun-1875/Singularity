import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import {MERCHANTS} from '../../equipment/data/Equipment';
import {SHOP_SERVICES} from '../data/Shops';
import {tradingText as t} from '../locales/TradingText';
import {AREAS} from '../../world/data/WorldData';
import {playableArea} from '../../journey/data/ChapterJourney';
import {renderShopInventory} from './ShopInventoryPanel';

export function shopGreeting(game:GameSession):string {return t('greet')+(game.state.flags.workers_returned?'\n\n'+t('returned'):'');}
export function renderShopPanel(hud:Hud,game:GameSession,menu:string,merchant:string):boolean {
 if(menu==='services'||menu.startsWith('services:')){
  const filter=menu.split(':')[1],rows=Object.entries(SHOP_SERVICES).filter(([id,v])=>playableArea(v.area)&&(v.public||game.state.discoveredMerchants.includes(id)||game.state.flags['visited:'+v.area])&&(!filter||filter==='gem'?(!filter||v.gems):filter==='supply'?v.supplies:!!Object.keys(MERCHANTS[id].stock).length)).map(([id,v])=>({label:v.label+' · '+v.service,detail:t('known',{area:AREAS[v.area].name,service:v.service}),action:'service-go:'+id}));
  hud.showList(t('title'),t('hint'),rows,[{back:true,label:t('end'),action:'close'}],hud.touchTargetSize,{placement:'right',tabs:[{label:t('all'),action:'services',selected:!filter},...(['equipment','supply','gem'] as const).map(kind=>({label:t(kind),action:'services:'+kind,selected:filter===kind}))]});return true;
 }
 if(menu!=='shop'&&menu!=='shop-categories'&&!menu.startsWith('shop:')&&!menu.startsWith('shop-item:'))return false;
 const service=SHOP_SERVICES[merchant],definition=MERCHANTS[merchant];if(!service||!definition){hud.clearModal();return true;}
 renderShopInventory(hud,game,menu,merchant);return true;
}
