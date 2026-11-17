import type {Node} from 'cc';
import {UiSkin} from '../../../shared/ui/UiSkin';

// Reuse the approved paintings. Color follows level, independently of the saved effect ID.
const LEVEL_ARTWORK=['','maxHp','armor','criticalDamage','criticalChance','power'] as const;
export const gemArtworkPath=(tier:number)=>'equipment/gem-orbs-v5/'+LEVEL_ARTWORK[tier];
export function mountGemArtwork(parent:Node,tier:number,size:number){
 const icon=UiSkin.sprite(parent,gemArtworkPath(tier),size,size);icon.node.name='GemCrystalArtwork';return icon.node;
}
