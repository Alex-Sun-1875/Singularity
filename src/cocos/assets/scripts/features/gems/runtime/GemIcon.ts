import type {Node} from 'cc';
import type {Hud} from '../../../app/Hud';
import {mountGemArtwork} from './GemArtwork';

/** Shared socket/shop crystal. Tier is a numeral, separate from equipment quality. */
export function drawGemIcon(ui:{scale:number;hud:Hud},parent:Node,tier:number):void {
 mountGemArtwork(parent,tier,40*ui.scale);
}
