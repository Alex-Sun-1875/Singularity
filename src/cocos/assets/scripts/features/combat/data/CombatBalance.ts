/** Normal-play economy. Content difficulty is authored independently of player gear. */
export const COMBAT_BALANCE={
 skillPowerBase:18,skillPowerPerLevel:1.05,
 basicAttackInterval:.5,
 bowTapDamage:18,bowChargedDamage:48,
 combatResourceRegen:4,restResourceRegen:16,
 potionHealthFraction:.3,potionMinimumHealth:30,potionCooldown:8,
 equipmentReductionCap:.55,statusReductionCap:.5,totalReductionCap:.7,
 elementalArmorFraction:.5,
} as const;

/** Equipment and temporary protection occupy separate, bounded multipliers.
 * Armor keeps its percentage-point meaning; it also gives half protection
 * against elemental attacks, so a defensive item is useful in mixed encounters.
 */
export function incomingDamageReduction(armorPercent:number,status:number,ward:number,physical:boolean){
 const armor=Math.max(0,Math.min(COMBAT_BALANCE.equipmentReductionCap,armorPercent/100))*(physical?1:COMBAT_BALANCE.elementalArmorFraction);
 const protection=Math.max(-.25,Math.min(COMBAT_BALANCE.statusReductionCap,status));
 return Math.min(COMBAT_BALANCE.totalReductionCap,1-(1-armor)*(1-protection)*(1-Math.max(0,Math.min(.5,ward))));
}
