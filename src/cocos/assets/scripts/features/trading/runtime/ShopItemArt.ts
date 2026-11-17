import type {Node} from 'cc';
import type {Hud} from '../../../app/Hud';
import {UiSkin} from '../../../shared/ui/UiSkin';
import {CompactGraphics} from '../../../shared/ui/CompactGraphics';
import {FeedbackView as F} from '../../../shared/ui/FeedbackView';
import {EQUIPMENT} from '../../equipment/data/Equipment';
import {SUPPLIES} from '../../equipment/data/Supplies';
import {EquipmentArt} from '../../equipment/runtime/EquipmentArt';
import {mountGemArtwork} from '../../gems/runtime/GemArtwork';
import type {ShopProduct} from '../data/Shops';

export function shopItemArt(ui:{hud:Hud;scale:number},parent:Node,p:ShopProduct,size:number){
 const u=ui.scale;
 if(p.kind==='gem'){mountGemArtwork(parent,p.tier!,size*u);return;}
 if(p.kind==='equipment'){EquipmentArt.icon(parent,EQUIPMENT[p.id],size*u,size*u);return;}
 if(p.kind==='supply'){const icon=UiSkin.sprite(parent,SUPPLIES[p.supply!].groundArt,size*.72*u,size*.72*u);icon.node.setRotationFromEuler(0,0,45);icon.node.setPosition(0,3*u);return;}
 const g=ui.hud.node('DrillArtwork',parent,0,0,size*u,size*u).addComponent(CompactGraphics),s=size/42*u;g.strokeColor=F.color('text.preparationAccent');g.lineWidth=3*s;g.moveTo(-12*s,12*s);g.lineTo(10*s,-10*s);g.moveTo(-7*s,16*s);g.lineTo(15*s,-6*s);g.moveTo(7*s,-13*s);g.lineTo(13*s,-7*s);g.stroke();
}
