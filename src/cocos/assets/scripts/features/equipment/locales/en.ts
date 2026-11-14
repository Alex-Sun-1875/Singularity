import type {EquipmentMessageKey} from './zh-CN';
export const en:Record<EquipmentMessageKey,string>={
 'combat.ready':'Out of combat · Gear and profession changes available',
 'combat.blocked':'Pursuit, attacks or ongoing damage still prevent gear changes',
 'combat.wait':'Safe in {seconds}s · Resume the journey to continue',
 'combat.settling':'Threats cleared · Gear changes available after {seconds}s of safety',
 'loot.pickup':'Pick up','loot.supplyFull':'At capacity · {count}/{capacity}',
 'loot.bossResources':'Boss loot · Gold +{gold} · Iron +2',
 'loot.rematchFirst':'Defeat this Boss before starting a rematch.',
 'loot.rematchSafe':'Leave nearby enemies’ attack range first.',
 'loot.rematchWait':'Rematch in {time}; return to challenge when ready.',
 'loot.rematchStarted':'Boss rematch started · Defeat it for a chance at rare loot',
 'loot.huntHeal':'Hunter’s return: Health +{amount}',

 'action.equip':'Equip','action.leftRing':'Equip left ring','action.rightRing':'Equip right ring',
 'action.equipped':'Equipped','action.select':'Select gear','action.level':'Level required','action.offhand':'One hand needed','action.blocked':'Unavailable','action.preparing':'Preparing…',
 'reason.missing':'Select an acquired item','reason.unowned':'You do not own this item','reason.level':'Reach Lv.{level} to equip this item',
 'reason.slot':'This item does not fit the selected slot','reason.twoHanded':'Your two-handed weapon occupies the off hand. Equip a one-handed weapon first.','reason.equipped':'This item is already equipped',
 'notice.equipped':'Equipped: {name}','notice.choose':'Select an item, then choose Equip','notice.twoHanded':'Equipping this two-handed weapon will stow your off-hand item',
 'notice.loading':'Preparing equipment assets…','notice.loadFailed':'Equipment assets failed to load. Try again.',
 'slot.target':'Selecting: {slot}','slot.empty':'No acquired gear fits {slot}','filter.empty':'No gear in this category','empty.detail':'Choose another category or slot to view your acquired gear',
 'badge.equipped':'Equipped','compare.equipped':'Equipped attributes','compare.target':'Compared with {slot}',
};
