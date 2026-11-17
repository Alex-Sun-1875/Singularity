'use strict';

// Design arithmetic only. This file never loads or writes a player save,
// changes runtime configuration, builds the game, or allocates real rewards.
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const root = path.resolve(__dirname, '../..');
const cocos = path.join(root, 'src/cocos');
require(require.resolve('tsx/cjs', {paths: [cocos]}));
const {EQUIPMENT} = require(path.join(cocos, 'assets/scripts/features/equipment/data/Equipment.ts'));
const {forgingCost, forgingThreshold} = require(path.join(cocos, 'assets/scripts/features/crafting/data/EquipmentForging.ts'));
const runtimeEconomy = require(path.join(cocos, 'assets/scripts/features/economy/data/Economy.ts'));
const {gemAmount} = require(path.join(cocos, 'assets/scripts/features/gems/data/Gems.ts'));
const modelPath = path.join(root, 'docs/design/shop-economy-v1.json');
const model = JSON.parse(fs.readFileSync(modelPath, 'utf8'));
const sum = values => values.reduce((a, b) => a + b, 0);
const gemPrices = [model.gem.basePrice];
const gemFees = [];
for (let tier = 1; tier < 5; tier++) {
  const fee = model.gem.firstSynthesisFee * model.gem.synthesisFeeRatio ** (tier - 1);
  gemFees.push(fee);
  gemPrices.push(model.gem.synthesisRatio * gemPrices[tier - 1] + fee);
}
if (JSON.stringify(gemPrices)!==JSON.stringify(runtimeEconomy.GEM_PRICES.slice(1)) || JSON.stringify(gemFees)!==JSON.stringify(runtimeEconomy.GEM_SYNTHESIS_FEES.slice(1)) || runtimeEconomy.GOLD_CAPACITY!==model.goldCapacity) throw Error('Runtime prices/capacity drift from the design model');
const attributeKeys={power:'powerPercent',maxHp:'health',armor:'armorPoints',criticalChance:'criticalChancePoints',criticalDamage:'criticalDamagePoints'};
for (const [stat,key] of Object.entries(attributeKeys)) for (let tier=1;tier<=5;tier++) if (Math.abs(gemAmount(stat,tier)-model.gem.standardBaseEffect[key]*model.gem.effectScale[tier-1])>1e-6) throw Error('Runtime gem effects drift from the design model');
if (model.chapters.some((chapter,i)=>runtimeEconomy.CHAPTER_ECONOMY[i].total!==chapter.finiteGold || runtimeEconomy.CHAPTER_ECONOMY[i].ordinaryGold!==chapter.repeatGoldPerOrdinaryKill)) throw Error('Runtime chapter policy drifts from the design model');
const gemValue = counts => sum(counts.map((count, i) => count * gemPrices[i]));
const chapterRows = model.chapters.map(chapter => {
  const main = chapter.finiteGold * 2 / 5;
  const boss = chapter.finiteGold / 10;
  const fixedCombat = chapter.finiteGold / 6;
  const exploration = chapter.finiteGold / 3;
  const mandatory = main + boss + fixedCombat;
  if (![main, boss, fixedCombat, exploration, mandatory].every(Number.isSafeInteger) || mandatory + exploration !== chapter.finiteGold) throw Error('Non-integral chapter allocation');
  return {...chapter, main, boss, fixedCombat, exploration, mandatory};
});
const normalWeapon = EQUIPMENT.LC1_T_E_FIR;
const normalRing = EQUIPMENT.LC1_T_L;
if (!normalWeapon || !normalRing) throw Error('Current early equipment references changed');
const early = model.earlyScenario;
const firstForge = forgingCost(normalWeapon, 1).gold + forgingCost(normalRing, 1).gold;
const secondForge = forgingCost(normalWeapon, 2).gold + forgingCost(normalRing, 2).gold;
const earlyRows = [];
for (const route of ['main', 'exploration']) {
  const counts = route === 'main' ? early.chapter1MainGemCounts : early.chapter1ExplorationGemCounts;
  const income = route === 'main' ? chapterRows[0].mandatory : chapterRows[0].finiteGold;
  const costs = {equipment: early.chapter1Equipment, forging: firstForge, supplies: early.chapter1Supplies, gems: gemValue(counts), inlay: sum(counts) * model.gem.standardInlayFee};
  const totalSpent = sum(Object.values(costs));
  const firstBalance = income - totalSpent;
  earlyRows.push({chapter: 1, route, income, openingBalance: 0, availableGold: income, costs, totalSpent, closingBalance: firstBalance, finalGemCounts: counts});
  const second = route === 'main' ? early.chapter2Main : early.chapter2Exploration;
  const secondIncome = route === 'main' ? chapterRows[1].mandatory : chapterRows[1].finiteGold;
  const secondCosts = {equipment: second.equipment, forging: secondForge, supplies: second.supplies, gems: gemValue(second.finalGemCounts) - gemValue(counts), inlay: second.inlayOperations * model.gem.standardInlayFee, opening: second.openingAllowance, inheritance: second.inheritanceAllowance};
  const secondSpent = sum(Object.values(secondCosts));
  earlyRows.push({chapter: 2, route, income: secondIncome, openingBalance: firstBalance, availableGold: secondIncome + firstBalance, costs: secondCosts, totalSpent: secondSpent, closingBalance: secondIncome + firstBalance - secondSpent, finalGemCounts: second.finalGemCounts});
}
const end = model.endScenario;
const cultivation = forgingThreshold(EQUIPMENT[end.mainWeaponId], end.mainWeaponRank) + end.otherSlots * forgingThreshold(EQUIPMENT[end.otherSlotReferenceId], end.otherSlotRank);
const endCommonCosts = {forging: cultivation, equipment: end.equipmentAllowance, supplies: end.supplyAllowance, stoneSynthesis: end.stoneSynthesisAllowance, opening: end.drillUnitsForEightThreeSocketItems * model.supplies.drillUnitPrice + end.openingFeeForEightThreeSocketItems, inlay: end.standardSocketCount * model.gem.standardInlayFee, inheritance: end.inheritanceAllowance};
const endRows = [
  ['main', end.mainGemCounts, sum(chapterRows.map(c => c.mandatory))],
  ['exploration', end.explorationGemCounts, sum(chapterRows.map(c => c.finiteGold))],
  ['optionalTopGem', end.optionalTopGemCounts, sum(chapterRows.map(c => c.finiteGold))]
].map(([route, counts, income]) => {
  if (sum(counts) !== end.standardSocketCount) throw Error('Socket scenario does not match');
  const costs = {...endCommonCosts, gems: gemValue(counts)};
  const totalSpent = sum(Object.values(costs));
  return {route, income, gemCounts: counts, costs, totalSpent, closingBalance: income - totalSpent};
});
if ([...earlyRows, ...endRows].some(row => row.closingBalance < 0)) throw Error('Proposed budget overspent');
const sourcePaths = [
  'docs/design/shop-economy-v1.json',
  'tools/design/shop-economy-v1.cjs',
  'src/cocos/assets/scripts/features/economy/data/Economy.ts',
  'src/cocos/assets/scripts/features/equipment/data/Equipment.ts',
  'src/cocos/assets/scripts/features/crafting/data/EquipmentForging.ts',
  'src/cocos/assets/scripts/features/equipment/data/CampaignEquipmentGrowth.ts',
  'src/cocos/assets/scripts/features/gems/data/Gems.ts'
];
const report = {
  status: 'deterministic-design-arithmetic-only-not-natural-play-validation',
  runtimeConsistency: 'prices, capacity, gem effects and chapter policy match the implementation; future chapters remain unavailable',
  date: model.date,
  inputs: sourcePaths.map(file => ({path: file, sha256: crypto.createHash('sha256').update(fs.readFileSync(path.join(root, file))).digest('hex')})),
  gems: gemPrices.map((price, i) => ({tier: i + 1, level: model.gem.levels[i], chapter: model.gem.chapters[i], price, lowerTierSynthesisFee: i ? gemFees[i - 1] : null, baseGemCount: model.gem.synthesisRatio ** i, totalSynthesisFees: price - gemPrices[0] * model.gem.synthesisRatio ** i})),
  chapters: chapterRows,
  finiteGoldTotal: sum(chapterRows.map(c => c.finiteGold)),
  mandatoryGoldTotal: sum(chapterRows.map(c => c.mandatory)),
  earlyScenarios: earlyRows,
  endScenarios: endRows,
  repeatGoldSensitivity: chapterRows.map(chapter => ({chapter: chapter.chapter, released: chapter.released, goldPerKill: chapter.repeatGoldPerOrdinaryKill, cases: model.repeatKillsPerMinuteSensitivity.map(kills => ({killsPerMinute: kills, grossGoldPerMinute: kills * chapter.repeatGoldPerOrdinaryKill, tier1Minutes: Math.round(gemPrices[0] / kills / chapter.repeatGoldPerOrdinaryKill * 100) / 100}))})),
  wholeBodyGemOnly: [16, 24, 40].map(sockets => ({standardSockets: sockets, pricesByTier: gemPrices.map(price => price * sockets)}))
};
const result = JSON.stringify(report, null, 2) + '\n';
if (process.argv.includes('--write')) fs.writeFileSync(path.join(root, 'docs/design/shop-economy-v1-calculation.json'), result);
process.stdout.write(result);
