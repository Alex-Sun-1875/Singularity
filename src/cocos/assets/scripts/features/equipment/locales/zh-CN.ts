export const zh={
 'combat.ready':'已脱战 · 可随时换装或切换职业',
 'combat.blocked':'仍有追击、攻击或持续伤害，请先脱战',
 'combat.wait':'脱战还需 {seconds} 秒 · 返回旅途继续',
 'combat.settling':'威胁已解除，安全等待 {seconds} 秒后可换装',
 'loot.pickup':'拾取','loot.supplyFull':'携带已满 · {count}/{capacity}',
 'loot.dropTitle':'{quality}装备掉落','loot.autoPickup':'靠近自动拾取','loot.dropFull':'携带已满 · 装备保留在原地','loot.groundName':'{quality} · {name}',
 'loot.bossResources':'Boss战利品 · 金币 +{gold} · 废铁 +2',
 'loot.rematchFirst':'先击败此地Boss，再来开启挑战',
 'loot.rematchSafe':'先离开附近敌人的攻击范围',
 'loot.rematchWait':'再战冷却 {time}，到时间后可主动挑战',
 'loot.rematchStarted':'Boss再战已开启 · 击败后有机会获得珍稀战利品',
 'loot.huntHeal':'猎归：生命 +{amount}',

 'action.equip':'穿戴','action.leftRing':'穿戴到左戒','action.rightRing':'穿戴到右戒',
 'action.equipped':'已穿戴','action.select':'选择装备','action.level':'等级不足','action.offhand':'需单手武器','action.blocked':'暂不可换','action.preparing':'准备中…',
 'reason.missing':'请选择已获得的装备','reason.unowned':'尚未获得这件装备','reason.level':'需要达到 Lv.{level} 才能穿戴',
 'reason.slot':'这件装备不适合所选部位','reason.twoHanded':'双手武器占用副手，请先换用单手武器','reason.equipped':'这件装备已穿戴',
 'notice.equipped':'已穿戴：{name}','notice.choose':'选择装备，再点击穿戴','notice.twoHanded':'穿戴双手武器将收起副手装备',
 'notice.loading':'正在准备装备资源…','notice.loadFailed':'装备资源载入失败，请重试',
 'slot.target':'正在选择：{slot}','slot.empty':'尚未获得适合{slot}的装备','filter.empty':'此分类暂无装备','empty.detail':'切换分类或部位，查看已获得的装备',
 'badge.equipped':'已穿戴','compare.equipped':'当前穿戴属性','compare.target':'与当前{slot}比较',
} as const;
export type EquipmentMessageKey=keyof typeof zh;
