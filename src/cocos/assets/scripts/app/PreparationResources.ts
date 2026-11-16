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

const ROOT='ui/quiet-bronze/';
const chrome=[...Object.values(PREPARATION_SKINS).map(s=>s.asset),D.frame.asset,
 ...[D.artwork.coin,D.artwork.campfire,D.artwork.footerRule,D.artwork.offhand],
 ...Object.values(D.artwork.familyPaintings),...Object.values(D.artwork.mainWeaponIcons),
 UI_FRAME_LAYOUT.panelSkin,UI_FRAME_LAYOUT.panelMaterial,UI_FRAME_LAYOUT.capsuleSkin,
 'menu-pill-inset-v5','rpg-skill-icon-frame-v6','rpg-skill-rank-on-v6','rpg-skill-rank-off-v6',
 ...['sword','bow','staff','head','chest','hands','feet','necklace','ring','offhand'].map(k=>'rpg-equipment-'+k)];

/** Warm the actual UiSkin texture sources without leasing drawable frames. */
export class PreparationResources {
 private common:Promise<void>|undefined;private textures=new Set<Texture2D>();private destroyed=false;
 private skillOwner:Node|undefined;private skillKey='';private skillPending:Promise<void>|undefined;private skillReady=false;
 private itemOwner:Node|undefined;private itemKey='';private itemPending:Promise<void>|undefined;
 constructor(private root:Node){}
 private owner(name:string){const owner=new Node(name);this.root.addChild(owner);return owner;}
 preloadCommon(){
  return this.common??=Promise.all(Array.from(new Set(chrome.map(id=>UiSkin.texturePath(ROOT+id)))).map(path=>new Promise<void>((resolve,reject)=>gameResources.load(path,Texture2D,(error,texture)=>{
   if(error){reject(error);return;}if(!this.destroyed&&!this.textures.has(texture)){texture.addRef();this.textures.add(texture);}resolve();
  })))).then(()=>{}).catch(error=>{this.common=undefined;throw error;});
 }
 preloadSkills(game:GameSession){
  const c=game.state.combat,ids=Array.from(new Set([...COMBAT_SKILL_LIST.map(s=>s.id),...c.activeSlots,c.ultimate,...c.passiveSlots].filter((id):id is string=>!!id))).sort(),key=ids.join('|');
  if(key===this.skillKey)return this.skillPending!;
  const previous=this.skillOwner,owner=this.owner('PreparedSkillIcons');this.skillOwner=owner;this.skillKey=key;this.skillReady=false;
  return this.skillPending=preloadCombatSkillIcons(ids,owner).then(()=>{if(this.skillOwner===owner)this.skillReady=true;previous?.destroy();},error=>{previous?.destroy();if(this.skillOwner===owner){this.skillKey='';this.skillReady=false;}owner.destroy();throw error;});
 }
 async prepare(game:GameSession){await Promise.all([this.preloadCommon(),this.preloadSkills(game),this.preloadOwned(game)]);}
 /** A newly selected family is prepared before replacing the complete current page. */
 async family(game:GameSession,family:string){if(!['WAR','BOW','FIR','THU','COM'].includes(family))return;await this.preloadSkills(game);}
 needs(menu:string){return ['attributes','inventory','equipment','profession','checks'].includes(menu)||menu.startsWith('allocation:')||menu.startsWith('allocation-skill:')||menu.startsWith('forge');}
 async page(game:GameSession,menu:string){
  await this.preloadCommon();
  if(menu==='checks'||menu.startsWith('allocation:')||menu.startsWith('allocation-skill:')){
   if(!this.skillReady)await this.preloadSkills(game);
  }
  if(menu==='inventory'||menu==='equipment'||menu==='profession'||menu.startsWith('forge')){
   await this.preloadOwned(game);
  }
 }
 private async preloadOwned(game:GameSession){
   const ids=Array.from(new Set([...Object.keys(game.state.inventory).filter(id=>game.state.inventory[id]>0),...Object.values(game.state.equipment).flat().filter((id):id is string=>typeof id==='string')])).filter(id=>EQUIPMENT[id]).sort(),key=ids.join('|');
   if(this.itemKey!==key){const previous=this.itemOwner,owner=this.owner('PreparedOwnedEquipment');this.itemOwner=owner;this.itemKey=key;this.itemPending=EquipmentArt.preloadItems(ids.map(id=>EQUIPMENT[id]),owner).then(()=>{previous?.destroy();},error=>{previous?.destroy();if(this.itemOwner===owner)this.itemKey='';owner.destroy();throw error;});}
   await this.itemPending;
 }
 inspect(){return {commonTextures:this.textures.size,commonTextureBytes:Array.from(this.textures).reduce((n,t)=>n+(t.getGFXTexture()?.size??0),0),skillIcons:this.skillKey?this.skillKey.split('|').length:0,skillReady:this.skillReady,ownedEquipmentIcons:this.itemKey?this.itemKey.split('|').length:0};}
 destroy(){this.destroyed=true;this.skillOwner?.destroy();this.itemOwner?.destroy();for(const texture of this.textures)texture.decRef();this.textures.clear();}
}
