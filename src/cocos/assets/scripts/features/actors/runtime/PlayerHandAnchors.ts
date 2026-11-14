/** Visual calibration anchors for the approved flat Raphael drawings.
 *
 * Source: assets/resources/flat2d/characters/raphael/manifest.json and its
 * face-v1/hero-v6/{hero-v4-spell-interact-readable,
 * hero-v4-bow-spell-interact-readable,W11-attack-readable,
 * W07-attack-readable,hero-v4-w01-attack-readable}.png frames.
 *
 * Each crop was placed at its semantic foot origin using the manifest's actual
 * worldUnitsPerPixel and per-image frameScaleFactors, then inspected on a
 * 110 pixels/metre grid. Values are rounded visual calibration (roughly
 * +/-0.03-0.06m), not anatomical tracking or pixel-accurate bone sockets.
 * x is camera-right and y is camera-up, both measured from the ground foot.
 *
 * Spell anchors follow the visible gathering/released orb and finally the
 * lowered casting hand. Staff anchors follow the staff's head; bow anchors
 * follow its forward grip/arrow outlet. Sword anchors follow the sword hand,
 * and do not imply that the sword should emit an extra spell or projectile.
 * W08/L02 bow poses share the reviewed family calibration; their small shape
 * differences should be checked in-game. This file does not alter any art,
 * frame crop, body scale, equipped item, collision, or authoritative hit point.
 * Inspection sheets: temp/action-sequence-audit/*-sockets.jpg.
 */

type Anchor=readonly [x:number,y:number];
type Direction='down'|'right'|'up'|'left';
type Anchors=Record<Direction,readonly Anchor[]>;

const SPELL:Anchors={
 down:[[0,1.09],[-.25,1.18],[-.21,.77]],
 right:[[.27,1.18],[.45,1.25],[.08,.84]],
 up:[[-.12,1.04],[.38,1.25],[.29,.85]],
 left:[[-.24,1.14],[-.47,1.22],[-.09,.79]],
};

// The existing bow-casting drawings stow the bow and cast from a free hand.
// Their orb is a little lower than the unarmed family in front/side views.
const BOW_SPELL:Anchors={
 down:[[0,1.06],[-.27,1.15],[-.21,.78]],
 right:[[.27,1.13],[.41,1.22],[.08,.82]],
 up:[[-.10,1.02],[.38,1.25],[.28,.83]],
 left:[[-.24,1.15],[-.46,1.18],[-.09,.79]],
};

const STAFF:Anchors={
 down:[[-.24,1.24],[-.15,1.27],[-.23,1.35],[-.21,1.28]],
 right:[[.15,1.33],[.56,1.37],[.65,1.45],[.16,1.34]],
 up:[[.24,1.35],[.40,1.40],[.41,1.47],[.24,1.34]],
 left:[[-.20,1.32],[-.47,1.37],[-.58,1.42],[-.19,1.32]],
};

const BOW:Anchors={
 down:[[.25,.89],[.42,1.24],[.40,1.16],[.35,.88]],
 right:[[.34,.99],[.52,1.24],[.49,1.19],[.37,.96]],
 up:[[-.22,1.03],[-.42,1.22],[-.44,1.16],[-.29,.96]],
 left:[[-.34,.98],[-.50,1.24],[-.47,1.18],[-.34,.92]],
};

const SWORD:Anchors={
 down:[[-.18,1.07],[.04,1.01],[.25,1.27],[-.17,1.07]],
 right:[[.15,1.09],[.28,1.29],[.47,1.39],[.15,1.09]],
 up:[[.25,.99],[.32,1.25],[.36,1.39],[.24,.98]],
 left:[[-.15,1.08],[-.21,1.28],[-.39,1.39],[-.17,1.07]],
};

/** Resolve the actual sampled pose/ordinal, not the requested skill's name. */
export function playerHandOffset(pose:string,ordinal:number,direction:string):{x:number;y:number}{
 const name=pose.toLowerCase(),facing=direction.toLowerCase().replace(/[\s_-]/g,'');
 const cardinal:Direction=facing.includes('right')?'right':facing.includes('left')?'left':facing.startsWith('up')?'up':'down';
 const family=name.startsWith('attack_staff')||name==='spell_w11'?STAFF:
  name.startsWith('attack_bow')?BOW:name.startsWith('attack_sword')?SWORD:
  /^spell_(w07|w08|l02)$/.test(name)?BOW_SPELL:SPELL;
 const frames=family[cardinal],index=Math.max(0,Math.min(frames.length-1,Number.isFinite(ordinal)?Math.floor(ordinal):0));
 const [x,y]=frames[index];return{x,y};
}
