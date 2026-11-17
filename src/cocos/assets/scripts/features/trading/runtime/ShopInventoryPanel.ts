import {ButtonComponent as Button,Label,Node,ScrollView,UITransform,Vec2} from 'cc';
import type {Hud} from '../../../app/Hud';
import type {GameSession} from '../../../core/GameSession';
import {ButtonSurface} from '../../../shared/ui/ButtonSurface';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {UI_COLORS as C} from '../../../shared/ui/UiTheme';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {MERCHANTS} from '../../equipment/data/Equipment';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {GEM_STAT_NAMES,gemLevelName,gemBankKey,gemValueText} from '../../gems/data/Gems';
import {gemPurchasePreview} from '../../gems/common/GemPreview';
import {CHAPTER_ECONOMY} from '../../economy/data/Economy';
import {SHOP_SERVICES,shopProducts,shopProduct,type ShopProduct} from '../data/Shops';
import {tradingText as t} from '../locales/TradingText';
import {TradeWindow} from './TradeWindow';
import {shopItemArt} from './ShopItemArt';
import {PREPARATION_DESIGN as D,preparationSkinAsset} from '../../../shared/ui/PreparationTheme';

interface View {merchant:string;filter:string;selected:string;quantity:number;descending:boolean;scroll:number}
const views=new WeakMap<GameSession,View>();
function owned(game:GameSession,p:ShopProduct){const s=game.state;return p.kind==='gem'?(s.gems.bank[gemBankKey(p.stat!,p.tier!)]??0)/5:p.kind==='drills'?s.gems.drills:p.kind==='supply'?s.player[SUPPLIES[p.supply!].stock]:s.inventory[p.id]??0;}
const category=(p:ShopProduct)=>p.kind==='drills'?'materials':p.kind;
const matches=(p:ShopProduct,filter:string)=>filter==='all'||filter==='gem'?filter==='all'||p.kind==='gem':filter.startsWith('gem:')?p.kind==='gem'&&p.tier===Number(filter.slice(4)):category(p)===filter;

export function renderShopInventory(hud:Hud,game:GameSession,menu:string,merchant:string):void {
 let v=views.get(game);if(!v||v.merchant!==merchant){v={merchant,filter:'all',selected:'',quantity:1,descending:false,scroll:0};views.set(game,v);}
 if(menu==='shop:sort'){v.descending=!v.descending;v.scroll=0;}
 else if(menu.startsWith('shop:')){v.filter=menu.slice(5).replace('gem:materials','materials');v.quantity=1;v.scroll=0;}
 else if(menu.startsWith('shop-item:')){const [,id,raw]=menu.split(':'),p=shopProduct(merchant,id);if(p){v.selected=id;v.quantity=p.kind==='equipment'?1:[1,5,10].includes(Number(raw))?Number(raw):1;if(!matches(p,v.filter)){v.filter='all';v.scroll=0;}}}
 const ui=new TradeWindow(hud),u=ui.scale,w=ui.width,h=ui.height,released=Math.max(...CHAPTER_ECONOMY.filter(c=>c.released).map(c=>c.chapter));
 const catalog=shopProducts(merchant).filter(p=>p.chapter<=released),products=catalog.filter(p=>matches(p,v!.filter)).sort((a,b)=>(a.price-b.price)*(v!.descending?-1:1)||a.id.localeCompare(b.id));
 if(!products.some(p=>p.id===v!.selected))v.selected=(products.find(p=>p.id==='GEM_power_1')??products[0])?.id??'';
 const gemOnly=catalog.every(p=>p.kind==='gem'||p.kind==='drills'),filters=gemOnly?[{id:'all',label:t('all')},...Array.from(new Set(catalog.filter(p=>p.kind==='gem').map(p=>p.tier!))).map(tier=>({id:'gem:'+tier,label:gemLevelName(tier)+'级'})),{id:'materials',label:t('materials')}]:[{id:'all',label:t('all')},...Array.from(new Set(catalog.map(category))).map(id=>({id,label:t(id as 'equipment'|'supply'|'gem'|'materials')}))];
 const top=120,bottom=h-64,gridH=bottom-top,columns=4,visibleRows=gridH>=240?3:2;
 const cell=Math.min(96,(gridH-(visibleRows-1)*ui.gap)/visibleRows,(w*.57-24-(columns-1)*ui.gap)/columns),gridW=columns*cell+(columns-1)*ui.gap,left=18,detailLeft=left+gridW+20,detailW=w-detailLeft-18;
 const format=(n:number)=>String(n).replace(/\B(?=(\d{3})+(?!\d))/g,','),wallet=format(game.state.player.gold),walletW=Math.max(42,wallet.length*9);
 ui.label(MERCHANTS[merchant].name,64+(w-340)/2,27,w-340,30,22,C.ink);
 ui.label(SHOP_SERVICES[merchant].service,64+(w-340)/2,48,w-340,19,11.5,C.muted);
 const coin=UiSkin.asset(ui.panel,D.artwork.coin,19*u,19*u,false);coin.node.setPosition(ui.x(w-94-walletW),ui.y(32));
 const balance=ui.label(wallet,w-76-walletW/2,32,walletW,28,16,C.gold);balance.horizontalAlign=Label.HorizontalAlign.RIGHT;balance.enableWrapText=false;
 const tabsW=gridW-56,tabW=(tabsW-(filters.length-1)*ui.gap)/filters.length;
 filters.forEach((filter,i)=>ui.tab(filter.label,left+tabW/2+i*(tabW+ui.gap),88,tabW,'shop:'+filter.id,filter.id===v!.filter));
 ui.tab(v.descending?t('priceDescending'):t('priceAscending'),left+gridW-24,88,48,'shop:sort');
 ui.divider(detailLeft-10,78,bottom-78);
 const slotCount=Math.max(columns*visibleRows,Math.ceil(products.length/columns)*columns),contentH=Math.ceil(slotCount/columns)*(cell+ui.gap)-ui.gap;
 const {content,view}=ui.scroll(left,top,gridW,gridH,contentH,'ShopInventoryGridContent');
 view.node.on(ScrollView.EventType.SCROLLING,()=>{v!.scroll=view.getScrollOffset().y/u;});view.scrollToOffset(new Vec2(0,Math.max(0,Math.min(v.scroll,contentH-gridH))*u),0);
 for(let i=0;i<slotCount;i++){
  const p=products[i],selected=p?.id===v.selected,x=-gridW/2+cell/2+i%columns*(cell+ui.gap),y=-cell/2-Math.floor(i/columns)*(cell+ui.gap);
  const n=hud.node(p?`shop-item:${p.id}:1`:'EmptyShopInventorySlot',content,x*u,y*u,cell*u,cell*u),g=n.addComponent(CompactGraphics);
  g.fillColor=C.inset;g.rect((-cell/2-4)*u,(-cell/2-4)*u,(cell+8)*u,(cell+8)*u);g.fill();
  const texture=UiSkin.asset(n,preparationSkinAsset('surface'),(cell+8)*u,(cell+8)*u,false);texture.color=F.color('icon.normal',32);
  if(!p)continue;
  if(selected){UiSkin.asset(n,preparationSkinAsset('selection-inlay'),cell*u,cell*u,false);const edge=hud.node('SelectedInventoryEdge',n,0,0,cell*u,cell*u).addComponent(CompactGraphics);edge.strokeColor=F.color('selection.edge',170);edge.lineWidth=u;edge.rect((-cell/2+1)*u,(-cell/2+1)*u,(cell-2)*u,(cell-2)*u);edge.stroke();}
  const b=n.addComponent(Button);b.transition=Button.Transition.NONE;n.on(Button.EventType.CLICK,()=>hud.actions.click(`shop-item:${p.id}:1`));ButtonSurface.attach(n,{width:cell*u,height:cell*u,radius:2*u,overlay:true,after:n.children[n.children.length-1]});
  const artSize=p.kind==='gem'?40:48,icon=hud.node('ShopItemIcon',n,0,(p.kind==='gem'?12:6)*u,artSize*u,artSize*u);shopItemArt(ui,icon,p,artSize);
  const name=ui.text(n,p.kind==='drills'?t('materials'):p.name,0,-cell/2+(p.kind==='gem'?22:10.5),cell-6,p.kind==='gem'?16:20,11.5);name.horizontalAlign=Label.HorizontalAlign.CENTER;name.enableWrapText=false;
  const stock=Number(owned(game,p).toFixed(1));
  if(stock){const count=ui.text(n,'×'+stock,12,cell/2-9,cell-28,18,11.5);count.horizontalAlign=Label.HorizontalAlign.RIGHT;count.enableWrapText=false;count.enableOutline=true;count.outlineColor=C.dark;count.outlineWidth=2;}
  if(p.kind==='gem'){const effect=ui.text(n,GEM_STAT_NAMES[p.stat!],0,-cell/2+7,cell-6,14,11,C.muted);effect.horizontalAlign=Label.HorizontalAlign.CENTER;effect.enableWrapText=false;}
 }
 const lines=hud.node('InventoryGridLines',content,0,0,gridW*u,contentH*u).addComponent(CompactGraphics);lines.strokeColor=F.color('text.secondary',55);lines.lineWidth=.7*u;
 for(let c=1;c<columns;c++){const x=(-gridW/2-ui.gap/2+c*(cell+ui.gap))*u;lines.moveTo(x,0);lines.lineTo(x,-contentH*u);}
 for(let row=1;row<slotCount/columns;row++){const y=(ui.gap/2-row*(cell+ui.gap))*u;lines.moveTo(-gridW*u/2,y);lines.lineTo(gridW*u/2,y);}lines.stroke();
 const product=products.find(p=>p.id===v!.selected)??products[0];
 if(!product){ui.label(t('empty'),detailLeft+detailW/2,160,detailW,40);return;}
 v.selected=product.id;const q=game.trading.quote(merchant,product.id,v.quantity),cx=detailLeft+detailW/2;
 const hero=hud.node('SelectedShopItemArt',ui.panel,ui.x(detailLeft+32),ui.y(109),64*u,64*u);shopItemArt(ui,hero,product,64);
 const heading=ui.label(product.name,detailLeft+78+(detailW-78)/2,98,detailW-78,42,17,C.ink);heading.verticalAlign=Label.VerticalAlign.CENTER;
 const metadata=(product.stat?GEM_STAT_NAMES[product.stat]+' · ':'')+t('ownedCompact',{count:Number(owned(game,product).toFixed(1))});
 ui.label(metadata,detailLeft+78+(detailW-78)/2,129,detailW-78,20,11.5,C.muted);
 const blocks:{value:string;color:typeof C.ink;size:number}[]=[];
 if(q.reason)blocks.push({value:q.reason,color:F.color('state.failure'),size:13});
 if(product.kind==='gem'){
  blocks.push({value:gemValueText(product.stat!,product.tier!),color:C.ink,size:16});
  blocks.push({value:product.description.split('\n').slice(2).join('\n'),color:C.muted,size:13});
  blocks.push({value:gemPurchasePreview(game.state,product.stat!,product.tier!),color:C.muted,size:11.5});
 }else blocks.push({value:product.description+(product.kind==='equipment'?'\n'+t('remaining',{count:q.stock??0}):''),color:C.ink,size:14});
 const infoTop=149,infoH=Math.max(28,h-148-infoTop);let contentHeight=0;
 const measured=blocks.map(block=>{const label=ui.text(ui.panel,block.value,0,0,detailW,24,block.size,block.color);label.overflow=Label.Overflow.RESIZE_HEIGHT;label.updateRenderData(true);const height=label.node.getComponent(UITransform)!.height/u;label.node.destroy();contentHeight+=height+6;return {...block,height};});
 const info=ui.scroll(detailLeft,infoTop,detailW,infoH,Math.max(infoH,contentHeight),'ShopItemDetails').content;let offset=0;
 measured.forEach(block=>{const label=ui.text(info,block.value,0,-offset-block.height/2,detailW,block.height,block.size,block.color);label.verticalAlign=Label.VerticalAlign.TOP;offset+=block.height+6;});
 const after=q.remaining>=0?t('afterCompact',{gold:format(q.remaining)}):t('shortfall',{gold:format(-q.remaining)});
 ui.label(t('unitPrice',{gold:format(product.price)})+'  ·  '+after,cx,h-132,detailW,20,11.5,q.remaining>=0?C.muted:F.color('state.failure'));
 const quantityW=(detailW-2*ui.gap)/3;
 [1,5,10].forEach((count,i)=>ui.action('×'+count,detailLeft+quantityW/2+i*(quantityW+ui.gap),h-92,quantityW,`shop-item:${product.id}:${count}`,product.kind!=='equipment'||count===1,count===v!.quantity));
 const hasGems=catalog.some(p=>p.kind==='gem'),service=hasGems?{label:t('cultivate'),action:'gems'}:merchant==='lorn'?{label:t('forge'),action:'forge'}:undefined;
 if(service)ui.link(service.label+' ›',left+58,h-32,116,service.action);
 const pending=game.pendingGold();if(pending)ui.link(t('pendingShort',{gold:pending}),left+gridW-75,h-32,150,'wallet-claim');
 else ui.label(t('itemCount',{count:products.length}),service?left+124+(gridW-124)/2:left+gridW/2,h-32,service?gridW-124:gridW,24,11.5,C.muted);
 const buyW=144,priceW=detailW-buyW-12;
 ui.label(t('total'),detailLeft+priceW/2,h-49,priceW,14,11,C.muted);
 const totalCoin=UiSkin.asset(ui.panel,D.artwork.coin,16*u,16*u,false);totalCoin.node.setPosition(ui.x(detailLeft+8),ui.y(h-27));
 ui.label(format(q.total),detailLeft+24+(priceW-24)/2,h-27,priceW-24,32,24,C.gold);
 ui.action(t('buy'),w-18-buyW/2,h-32,buyW,`shop-buy:${product.id}:${v.quantity}:${q.token}`,q.allowed,false,true);
}
