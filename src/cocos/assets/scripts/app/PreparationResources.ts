import {Node,Texture2D} from 'cc';
import type {GameSession} from '../core/GameSession';
import {gameResources} from '../shared/assets/GameResources';
import {PREPARATION_SKINS,PREPARATION_DESIGN as D} from '../shared/ui/PreparationTheme';
import {UI_FRAME_LAYOUT} from '../shared/ui/UiChrome';
import {UiSkin} from '../shared/ui/UiSkin';
import {COMBAT_SKILL_LIST} from '../features/combat/data/PureSkills';
import {preloadCombatSkillIcons} from '../features/progression/runtime/SkillBook';
import {EquipmentArt} from '../features/equipment/runtime/EquipmentArt';
import {EQUIPMENT} from '../features/equipment/data/Equipment';
import {shopProducts} from '../features/trading/data/Shops';
import {SUPPLIES} from '../features/equipment/data/Supplies';
import {gemArtworkPath} from '../features/gems/runtime/GemArtwork';
import {GEM_TIERS} from '../features/gems/data/Gems';

const ROOT='ui/quiet-bronze/';
const skins=(names:RegExp)=>Object.entries(PREPARATION_SKINS).filter(([name])=>names.test(name)).map(([,skin])=>skin.asset);
const chrome=[...skins(/^(header|surface|logo|rule|active|shell-rule|button-dark|button-gold|badge-gold|badge-teal)$/),D.frame.asset,
 ...[D.artwork.coin,D.artwork.campfire,D.artwork.footerRule],
 UI_FRAME_LAYOUT.panelSkin,UI_FRAME_LAYOUT.panelMaterial,UI_FRAME_LAYOUT.capsuleSkin,
 'menu-pill-inset-v5'];
const characterChrome=[...skins(/^(hero|plaque|attribute-row|attribute-.+)$/),
 ...['power','armor','criticalChance','speed'].map(id=>'rpg-stat-'+id+'-v3'),'ui/icons/attack','ui/icons/dash'];
const equipmentChrome=[...skins(/^(hero|identity|socket|socket-selected|scope|scope-active|categories|chip|card|card-selected|item-.+|inspect-.+|stat-.+|info|empty-offhand)$/),D.artwork.offhand,
 ...Object.values(D.artwork.mainWeaponIcons),D.artwork.familyPaintings.BOW,
 ...['sword','bow','staff','head','chest','hands','feet','necklace','ring','offhand'].map(k=>'rpg-equipment-'+k)];
const skillChrome=[...skins(/^(skill-row|selection-row|skill-selected|card|card-selected|stat-.+|info)$/),
 'rpg-skill-icon-frame-v6','rpg-skill-rank-on-v6','rpg-skill-rank-off-v6'];
const allocationChrome=skins(/^(hero-narrow|identity|side-tab|side-tab-selected|point-counter|skill-cost|step|smoke|crest-sword|info|stat-.+)$/);
const professionChrome=[...skins(/^(hero|identity|card|card-selected|info)$/),...Object.values(D.artwork.familyPaintings),...Object.values(D.artwork.mainWeaponIcons)];
// Workshop-only art is prepared at page entry, rather than increasing the
// whole journey's startup set. Its dark selected labels need the gold plate.
const workshopChrome=['rpg-anvil-v2','rpg-approved-sword-v3','rpg-stat-power-v3',
 ...['tab-gold','tab-dark','header-rule','confirm','list-rule','list-underline',
 'approved-room','anvil','name-rule','stamp','rule','heading-rule','arrow',
 'stage','limit','coin','iron'].map(id=>'rpg-forge-'+id+'-v7')];
const workshopPage=(menu:string)=>menu.startsWith('forge')||menu==='gems'||menu.startsWith('gems:');
type PreparedSkills={owner:Node;pending:Promise<void>;count:number;ready:boolean};

/** Warm the actual UiSkin texture sources without leasing drawable frames. */
export class PreparationResources {
 private gemArt:Promise<void>|undefined;
 private common:Promise<void>|undefined;private textures=new Set<Texture2D>();private destroyed=false;
 private textureLoads=new Map<string,Promise<void>>();
 private workshop:Promise<void>|undefined;private workshopReady=false;
 private skills=new Map<string,PreparedSkills>();
 private itemOwner:Node|undefined;private itemKey='';private itemPending:Promise<void>|undefined;
 private shopOwner:Node|undefined;private shopKey='';private shopPending:Promise<void>|undefined;
 constructor(private root:Node){}
 private owner(name:string){const owner=new Node(name);this.root.addChild(owner);return owner;}
 private preloadTextures(ids:readonly string[],priority?:number){
  return Promise.all(Array.from(new Set(ids.map(id=>UiSkin.texturePath(id.startsWith('ui/')?id:ROOT+id)))).map(path=>{
   const existing=this.textureLoads.get(path);if(existing)return existing;
   const pending=new Promise<void>((resolve,reject)=>gameResources.load(path,Texture2D,(error,texture)=>{
   if(error){reject(error);return;}if(!this.destroyed&&!this.textures.has(texture)){texture.addRef();this.textures.add(texture);}resolve();
   },priority));this.textureLoads.set(path,pending);void pending.catch(()=>{if(this.textureLoads.get(path)===pending)this.textureLoads.delete(path);});return pending;
  })).then(()=>{});
 }
 preloadCommon(priority?:number){return this.common??=this.preloadTextures(chrome,priority).catch(error=>{this.common=undefined;throw error;});}
 private preloadWorkshop(){return this.workshop??=this.preloadTextures(workshopChrome).then(()=>{if(!this.destroyed)this.workshopReady=true;}).catch(error=>{this.workshop=undefined;throw error;});}
 preloadSkills(game:GameSession,family:string=game.state.combat.family){
  const existing=this.skills.get(family);if(existing)return existing.pending;
  const ids=COMBAT_SKILL_LIST.filter(s=>s.style===family).map(s=>s.id),owner=this.owner('PreparedSkillIcons:'+family);
  const entry:PreparedSkills={owner,pending:Promise.resolve(),count:ids.length,ready:false};
  entry.pending=preloadCombatSkillIcons(ids,owner).then(()=>{entry.ready=true;},error=>{if(this.skills.get(family)===entry)this.skills.delete(family);owner.destroy();throw error;});
  this.skills.set(family,entry);return entry.pending;
 }
 async prepare(game:GameSession){await Promise.all([this.preloadCommon(),this.preloadTextures(characterChrome),this.preloadTextures(equipmentChrome,-1),this.preloadSkills(game),this.preloadOwned(game)]);}
 /** A newly selected family is prepared before replacing the complete current page. */
 async family(game:GameSession,family:string){if(!['WAR','BOW','FIR','THU','COM'].includes(family))return;await Promise.all([this.preloadSkills(game,family),this.preloadTextures(['rpg-profession-'+(family==='COM'?'war':family.toLowerCase())+'-v1'])]);}
 needs(menu:string){return ['attributes','inventory','equipment','profession','checks','shop','shop-categories'].includes(menu)||menu.startsWith('shop:')||menu.startsWith('shop-item:')||menu.startsWith('allocation:')||menu.startsWith('allocation-skill:')||workshopPage(menu);}
 async page(game:GameSession,menu:string,merchant=''){
  const art=menu==='attributes'?characterChrome:menu==='profession'?professionChrome:menu==='checks'?skillChrome:menu.startsWith('allocation:')?[...allocationChrome,...(menu==='allocation:skills'?skillChrome:characterChrome)]:equipmentChrome;
  await Promise.all([this.preloadCommon(),this.preloadTextures(art),...(workshopPage(menu)?[this.preloadWorkshop()]:[]),
   ...(menu.startsWith('shop')?[this.preloadShop(merchant)]:[]),
   ...(menu==='gems'||menu.startsWith('gems:')?[this.preloadGemArtwork()]:[]),
   ...(menu==='checks'?[this.family(game,game.state.combat.family)]:[]),
   ...(menu==='checks'||menu==='allocation:skills'||menu.startsWith('allocation-skill:')?[this.preloadSkills(game)]:[]),
   ...(menu==='inventory'||menu==='equipment'||menu==='profession'||workshopPage(menu)?[this.preloadOwned(game)]:[])]);
 }
 private preloadGemArtwork(){return this.gemArt??=Promise.all(GEM_TIERS.map(tier=>UiSkin.frame(gemArtworkPath(tier),0,this.root))).then(()=>{}).catch(error=>{this.gemArt=undefined;throw error;});}
 private async preloadShop(merchant:string){
  const products=shopProducts(merchant),key=merchant;
  if(key!==this.shopKey){const previous=this.shopOwner,owner=this.owner('PreparedShopGoods');this.shopOwner=owner;this.shopKey=key;
   this.shopPending=Promise.all([EquipmentArt.preloadItems(products.filter(p=>p.item).map(p=>EQUIPMENT[p.item!]),owner),...products.filter(p=>p.supply).map(p=>UiSkin.frame(SUPPLIES[p.supply!].groundArt,0,owner)),...Array.from(new Set(products.filter(p=>p.kind==='gem').map(p=>gemArtworkPath(p.tier!)))).map(path=>UiSkin.frame(path,0,owner))]).then(()=>{previous?.destroy();},error=>{previous?.destroy();if(this.shopOwner===owner)this.shopKey='';owner.destroy();throw error;});
  }
  await this.shopPending;
 }
 private async preloadOwned(game:GameSession){
   const ids=Array.from(new Set([...Object.keys(game.state.inventory).filter(id=>game.state.inventory[id]>0),...Object.values(game.state.equipment).flat().filter((id):id is string=>typeof id==='string')])).filter(id=>EQUIPMENT[id]).sort(),key=ids.join('|');
   if(this.itemKey!==key){const previous=this.itemOwner,owner=this.owner('PreparedOwnedEquipment');this.itemOwner=owner;this.itemKey=key;this.itemPending=EquipmentArt.preloadItems(ids.map(id=>EQUIPMENT[id]),owner).then(()=>{previous?.destroy();},error=>{previous?.destroy();if(this.itemOwner===owner)this.itemKey='';owner.destroy();throw error;});}
   await this.itemPending;
 }
 inspect(){return {commonTextures:this.textures.size,commonTextureBytes:Array.from(this.textures).reduce((n,t)=>n+(t.getGFXTexture()?.size??0),0),workshopReady:this.workshopReady,skillIcons:Array.from(this.skills.values()).reduce((n,s)=>n+s.count,0),skillReady:Array.from(this.skills.values()).some(s=>s.ready),ownedEquipmentIcons:this.itemKey?this.itemKey.split('|').length:0};}
 destroy(){this.destroyed=true;this.workshopReady=false;for(const entry of this.skills.values())entry.owner.destroy();this.skills.clear();this.itemOwner?.destroy();this.shopOwner?.destroy();for(const texture of this.textures)texture.decRef();this.textures.clear();this.textureLoads.clear();}
}
