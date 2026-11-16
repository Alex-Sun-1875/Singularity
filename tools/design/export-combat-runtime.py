"""Export approved design records into deterministic, filesystem-free Cocos data.

Run with Python's standard library; no runtime JSON importer or extra package is
needed by the minigame. Generated records retain their authored geometry and VFX
metadata. Historical ARC/FRO records are intentionally never exported as skills.
"""
from __future__ import annotations

import json
import copy
import argparse
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source-art/skills/pure-skills-v2"
TARGET = ROOT / "src/cocos/assets/scripts/features"
DESTINATIONS = {"PureSkills.ts":"combat/data", "Campaign.ts":"campaign/data", "CampaignGeography.ts":"world/data", "EquipmentCatalog.ts":"equipment/data"}


def literal(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def write(name: str, text: str) -> None:
    (TARGET / DESTINATIONS[name] / name).write_text(text, encoding="utf-8", newline="\n")


def apply_runtime_revision(skills: dict, filename: str) -> None:
    """Apply an explicit user revision without rewriting the historical catalog."""
    revision = json.loads(Path(__file__).with_name(filename).read_text(encoding="utf-8"))
    by_id = {skill["id"]: skill for skill in skills["skills"]}
    for skill_id, patch in revision["skills"].items():
        skill = by_id[skill_id]
        for key, value in patch.items():
            if key != "ranks":
                skill[key] = value
        if "ranks" in patch:
            for rank, update in zip(skill["ranks"], patch["ranks"], strict=True):
                assert rank["rank"] == update["rank"]
                rank.update(update)
    if "style" in revision:
        skills["styles"]["WAR"].update(revision["style"])
    for style, patch in revision.get("styles", {}).items():
        skills["styles"][style].update(patch)
    skills["rules"].update(revision.get("rules", {}))


def apply_runtime_revisions(skills: dict) -> None:
    apply_runtime_revision(skills, "melee-revision-v1.json")
    apply_runtime_revision(skills, "combat-connections-revision-v1.json")
    apply_runtime_revision(skills, "local-playtest-revision-v1.json")
    apply_runtime_revision(skills, "combat-tempo-revision-v1.json")
    apply_runtime_revision(skills, "skill-points-revision-v1.json")
    apply_runtime_revision(skills, "melee-reach-revision-v2.json")
    # The connection revision's historical timing text predates tempo tuning.
    chain_arrow = next(skill for skill in skills["skills"] if skill["id"] == "BOW_02")
    chain_arrow["mechanic"] = re.sub(r"^保留[^。]+。", "施放时序采用当前战斗节奏修订。", chain_arrow["mechanic"])


def export(skills_only: bool = False) -> None:
    skills = json.loads((SOURCE / "skill-catalog.json").read_text(encoding="utf-8"))
    apply_runtime_revisions(skills)
    campaign = json.loads((SOURCE / "campaign-v8.json").read_text(encoding="utf-8"))
    ids = [skill["id"] for skill in skills["skills"]]
    assert len(ids) == len(set(ids)) == 30
    assert sum(len(skill["ranks"]) for skill in skills["skills"]) == 150
    assert not any(id.startswith(("ARC_", "FRO_")) for id in ids)
    assert len(campaign["levels"]) == 97
    assert len(campaign["enemies"]) == 24 and len(campaign["bosses"]) == 12
    assert len(skills["equipmentEffects"]) == 74
    legacy = copy.deepcopy(skills["skills"])
    revision = json.loads(Path(__file__).with_name("four-skill-kit-revision-v1.json").read_text(encoding="utf-8"))
    skills["skills"] = [revision["skills"].get(s["id"], s) for s in skills["skills"] if s["id"] not in revision["retired"]] + revision["added"]
    order = "WAR_01 WAR_02 WAR_03 WAR_05 WAR_P1 WAR_P2 BOW_01 BOW_06 BOW_07 BOW_05 BOW_P1 BOW_P2 FIR_01 FIR_04 FIR_03 FIR_02 FIR_P1 FIR_P2 THU_01 THU_02 THU_03 THU_05 THU_P1 THU_P2 COM_01".split()
    skills["skills"].sort(key=lambda skill: order.index(skill["id"]))
    skills["rules"].update(revision["rules"])
    skills["loadout"].update(revision["loadout"])
    for style, patch in revision.get("styles", {}).items():
        skills["styles"][style].update(patch)
    for key, value in skills["equipmentEffects"].items():
        for old, new in revision["equipmentTextReplacements"].items():
            value = value.replace(old, new)
        skills["equipmentEffects"][key] = value
    skills["retiredSpellToSkill"] = {key: revision["legacyMapping"].get(value, value) for key, value in skills["retiredSpellToSkill"].items() if revision["legacyMapping"].get(value, value) in order}
    ids = [s["id"] for s in skills["skills"]]
    resources = json.loads(Path(__file__).with_name("class-resources-v1.json").read_text(encoding="utf-8"))
    skills["rules"].update(resources["rules"])
    apply_runtime_revision(skills, "mage-staff-requirement-v1.json")
    for skill in skills["skills"]:
        skill["resourceCost"] = resources["skillCosts"].get(skill["id"], 0)
        if skill["type"] == "ultimate":
            skill["ultimateCost"] = 0
    for key, value in skills["equipmentEffects"].items():
        for old, new in resources["equipmentTextReplacements"].items():
            value = value.replace(old, new)
        skills["equipmentEffects"][key] = value
    assert len(ids) == len(set(ids)) == 25
    for style in ["WAR", "BOW", "FIR", "THU"]:
        assert sum(s["style"] == style and s["type"] in ["active", "ultimate"] for s in skills["skills"]) == 4
    for skill in skills["skills"] + legacy:
        skill.setdefault("compatibleWeapons", "any")
        skill.setdefault("targetingMode", "self")
        skill.setdefault("offensive", False)
        for field in ["windupSeconds", "releaseCommitSeconds", "recoverySeconds", "ultimateCost", "sharedUltimateLockSeconds"]:
            skill.setdefault(field, 0)
        for rank in skill["ranks"]:
            for field in ["maxDamagePerTargetS", "authoredDamageHits", "radiusMetres", "rangeMetres", "castRangeMetres", "cooldownSeconds", "breakPower", "shieldMaxHpPercent", "healMaxHpPercent"]:
                rank.setdefault(field, 0)
    # V3 had the compact 25-skill catalog. Freeze it before restoring the pool,
    # so both V2 and V3 saves are validated against their own exact definitions.
    four = copy.deepcopy(skills["skills"])
    restored = json.loads(Path(__file__).with_name("restored-skill-library-v1.json").read_text(encoding="utf-8"))
    current = {s["id"]: s for s in skills["skills"]}
    current.update(restored["skills"])
    current.update({s["id"]: s for s in restored["added"]})
    order = "WAR_01 WAR_02 WAR_03 WAR_04 WAR_05 WAR_P1 WAR_P2 BOW_01 BOW_02 BOW_03 BOW_04 BOW_06 BOW_07 BOW_05 BOW_P1 BOW_P2 FIR_01 FIR_02 FIR_03 FIR_04 FIR_05 FIR_P1 FIR_P2 THU_01 THU_02 THU_03 THU_04 THU_06 THU_05 THU_P1 THU_P2 COM_01 COM_02".split()
    skills["skills"] = [current[id] for id in order]
    for skill in skills["skills"]:
        if skill["id"] in restored["resourceCosts"]:
            skill["resourceCost"] = restored["resourceCosts"][skill["id"]]
    skills["rules"].update(restored["rules"])
    skills["loadout"].update(restored["loadout"])
    # V4 saves retain the restored catalog's exact cast snapshots. Only the
    # playable V5 catalog receives the fixed-bar balance and activation rules.
    restored_skills = copy.deepcopy(skills["skills"])
    apply_runtime_revision(skills, "fixed-skill-kit-v1.json")
    by_id = {skill["id"]: skill for skill in skills["skills"]}
    for family in ["WAR", "BOW", "FIR", "THU"]:
        single, ultimate = by_id[family + "_01"], by_id[family + "_05"]
        assert single["maxTargets"] == 1
        for index, rank in enumerate(single["ranks"]):
            burst = ultimate["ranks"][index]
            assert rank["targetLimit"] == 1 and 2 <= rank["cooldownSeconds"] <= 5
            assert burst["cooldownSeconds"] == 12
            assert rank["maxDamagePerTargetS"] > burst["maxDamagePerTargetS"]
            for ordinary in skills["skills"]:
                if ordinary["style"] != family or ordinary.get("damageRole") not in ["area", "control"] or ordinary["type"] != "active":
                    continue
                assert burst["maxDamagePerTargetS"] > ordinary["ranks"][index]["maxDamagePerTargetS"]
    assert all(0 < rank["cooldownSeconds"] < 12 for skill in skills["skills"] if skill["type"] in ["active", "mobility"] for rank in skill["ranks"])
    original = json.loads((SOURCE / "skill-catalog.json").read_text(encoding="utf-8"))
    skills["retiredSpellToSkill"] = original["retiredSpellToSkill"]
    for key, value in original["equipmentEffects"].items():
        for old, new in resources["equipmentTextReplacements"].items():
            value = value.replace(old, new)
        skills["equipmentEffects"][key] = value
    # Current equipment follows the fixed skill identities; the historical
    # catalog and its original equipment descriptions remain untouched.
    fixed_equipment = json.loads(Path(__file__).with_name("fixed-skill-kit-v1.json").read_text(encoding="utf-8"))
    skills["equipmentEffects"].update(fixed_equipment.get("equipmentEffects", {}))
    assert len(current) == len(order) == 33
    header = "/** Generated by tools/design/export-combat-runtime.py; edit the design source, then regenerate. */\n"
    types = '''export type CombatStyle = 'WAR'|'BOW'|'FIR'|'THU'|'COM';
export type CombatSkillType = 'active'|'ultimate'|'passive'|'mobility';
export interface SkillGeometry {
  kind:string; origin:string; lengthMetres?:number; widthMetres?:number; depthMetres?:number;
  radiusMetres?:number; angleDegrees?:number; anglesDegrees?:number[];
  primaryProjectileCount?:number; childProjectileLimit?:number; totalTargetLimit?:number;
}
export interface CombatSkillRank {
  upgradeEffect?:string; upgradeEffects?:Record<string,number>;
  rank:number; requiredCharacterLevel:number; visualTier:number;
  maxDamagePerTargetS:number; authoredDamageHits:number; radiusMetres:number; rangeMetres:number;
  cooldownSeconds:number; breakPower:number; shieldMaxHpPercent:number; healMaxHpPercent:number;
  castRangeMetres:number; geometry?:SkillGeometry; targetLimit?:number|null; evolution?:string;
  vfxAnchor?:string; vfxDirection?:string; peakDurationSeconds?:number;
  visualEvolutionDoesNotChangeHitBudget?:boolean; vfxLayers?:Record<string,string>;
  primaryValue?:number; effect?:string; burnDurationBonusSeconds?:number; markedDirectSkillBonusPercent?:number;
  chainTargetLimit?:number; connectionRadiusMetres?:number; damagePerSecondaryTargetS?:number;
  totalCastDamageBudgetS?:number; followUpDamageFraction?:number;
  zoneDurationSeconds?:number; armSeconds?:number; slowPercent?:number; slowLingerSeconds?:number; rootSeconds?:number;
  moveMetres?:number; moveSeconds?:number; speedPercent?:number; reductionPercent?:number; interruptSeconds?:number;
}
export interface CombatSkillDef {
  unlockLevel:number;
  id:string; name:string; style:CombatStyle; type:CombatSkillType;
  activation?:'manual'|'automatic'; damageRole?:'single'|'area'|'control'|'support';
  compatibleWeapons:'melee'|'bow'|'staff'|'any'; targetingMode:string; offensive:boolean;
  windupSeconds:number; releaseCommitSeconds:number; recoverySeconds:number;
  resourceCost:number; consumableCost:number; enemyForcedDisplacement:number;
  ultimateCost:number; sharedUltimateLockSeconds:number; maxTargets?:number|null;
  targetShape?:string; mechanic?:string; effect?:string; visual?:string;
  ranks:CombatSkillRank[]; counterplay?:string; maxTargetsPerProjectile?:number;
  targetLimitScope?:string; procCounter?:string;
  graphPolicy?:Record<string,unknown>; projectilePolicy?:Record<string,unknown>; volleyPolicy?:Record<string,unknown>;
}
export type PureSkillDef = CombatSkillDef;
export type PureSkillRank = CombatSkillRank;
'''
    write("PureSkills.ts", header + types
          + "export const COMBAT_SKILL_LIST:CombatSkillDef[] = " + literal(skills["skills"]) + ";\n"
          + "export const COMBAT_SKILLS:Record<string,CombatSkillDef> = Object.fromEntries(COMBAT_SKILL_LIST.map(skill=>[skill.id,skill]));\n"
          + "export const PURE_SKILLS = COMBAT_SKILLS;\n"
          + "// Frozen V2 definitions are read only by save validation, never by the playable skill catalog.\n"
          + "const LEGACY_SKILL_OVERRIDES:Record<string,CombatSkillDef> = " + literal({s["id"]: s for s in legacy if s not in skills["skills"]}) + ";\n"
          + "export const LEGACY_COMBAT_SKILLS:Record<string,CombatSkillDef> = Object.fromEntries(" + literal([s["id"] for s in legacy]) + ".map(id=>[id,LEGACY_SKILL_OVERRIDES[id]??COMBAT_SKILLS[id]]));\n"
          + "const FOUR_SKILL_OVERRIDES:Record<string,CombatSkillDef> = " + literal({s["id"]: s for s in four if s not in skills["skills"]}) + ";\n"
          + "export const FOUR_SKILL_COMBAT_SKILLS:Record<string,CombatSkillDef> = Object.fromEntries(" + literal([s["id"] for s in four]) + ".map(id=>[id,FOUR_SKILL_OVERRIDES[id]??COMBAT_SKILLS[id]]));\n"
          + "const RESTORED_SKILL_OVERRIDES:Record<string,CombatSkillDef> = " + literal({s["id"]: s for s in restored_skills if s not in skills["skills"]}) + ";\n"
          + "export const RESTORED_COMBAT_SKILLS:Record<string,CombatSkillDef> = Object.fromEntries(" + literal([s["id"] for s in restored_skills]) + ".map(id=>[id,RESTORED_SKILL_OVERRIDES[id]??COMBAT_SKILLS[id]]));\n"
          + "export function combatSkillCatalog(version=5):Record<string,CombatSkillDef>{return version===2?LEGACY_COMBAT_SKILLS:version===3?FOUR_SKILL_COMBAT_SKILLS:version===4?RESTORED_COMBAT_SKILLS:COMBAT_SKILLS;}\n"
          + "export const PROGRESSION = " + literal(skills["progression"]) + ";\n"
          + "export const COMBAT_STYLES = " + literal(skills["styles"]) + ";\n"
          + "export const SKILL_LOADOUT = " + literal(skills["loadout"]) + ";\n"
          + "export const RETIRED_SPELL_TO_SKILL:Record<string,string> = " + literal(skills["retiredSpellToSkill"]) + ";\n"
          + "export const EQUIPMENT_EFFECTS:Record<string,string> = " + literal(skills["equipmentEffects"]) + ";\n"
          + "export const COMBAT_RULES = " + literal(skills["rules"]) + ";\n"
          )
    if skills_only:
        print(f"Exported {len(order)} playable skills / {len(order)*5} ranks; fixed active slots plus one ultimate; frozen V2/V3/V4 definitions retained")
        return
    campaign_types = '''export interface CampaignRegionDef {id:string; old:string; name:string; act:number; plate:string; theme:string; pool:string; recommendedLevels:number[]}
export interface CampaignLevelDef {id:string;region:string;name:string;kind:string;encounter:string;objective:string;reward:string;route:string;recommendedLevel:number[];encounterLevel:number;rangedLayoutReview?:string}
export interface CampaignEnemyDef {id:string; name:string; region:string; hp:number; damage?:number; baseHp?:number; baseDamage?:number; level?:number; windup?:number; lock?:number; recovery?:number; role?:string; counter?:string; arena?:string; moves?:string; fixedLoot?:string; rewardEvent?:string; firstClearExperience?:number; mandatory?:boolean; recommendedArenaClearMetres?:number[]; damageIsLevelOneBase?:boolean; enemyForcedDisplacement?:number; hitReactionDoesNotMoveEnemy?:boolean; damagedAwarenessRangeMetres?:number; recommendedCounterRangeMetres?:number[]; runtimeStatus?:string; art?:{file:string;position:string;spriteReady:boolean};rangedResponse?:string}
export interface CampaignEquipmentDef {id:string;name:string;effect:string;region?:string;slot?:string;grade?:string;weight?:number;visual?:string;tierAndSlot?:string;set?:string;source?:string;legacyName?:string;legacySource?:string;sourceDocument?:string;previousDesignEffect?:string;runtimeStatus?:string;art?:{file:string;position:string;spriteReady:boolean}}
export interface MainExperienceEvent {id:string;mainQuestId:string;trigger:string;experience:number;minimumMainOnlyLevel:number}
'''
    events = [dict(event, mainQuestId=reward["id"]) for reward in campaign["mainRewards"] for event in reward["experienceEvents"]]
    write("Campaign.ts", header + "import {MONSTER_ENEMIES} from '../../world/data/MonsterEcology';\n" + campaign_types
          + "export const CAMPAIGN_REGIONS:CampaignRegionDef[] = " + literal(campaign["regions"]) + ";\n"
          + "export const CAMPAIGN_LEVEL_LIST:CampaignLevelDef[] = " + literal(campaign["levels"]) + ";\n"
          + "export const CAMPAIGN_LEVELS:Record<string,CampaignLevelDef> = Object.fromEntries(CAMPAIGN_LEVEL_LIST.map(level=>[level.id,level]));\n"
          + "export const CAMPAIGN_COMMON_ENEMIES:CampaignEnemyDef[] = " + literal(campaign["enemies"]) + ";\n"
          + "export const CAMPAIGN_BOSSES:CampaignEnemyDef[] = " + literal(campaign["bosses"]) + ";\n"
          + "export const CAMPAIGN_ENEMY_TEMPLATES:Record<string,CampaignEnemyDef> = Object.fromEntries([...CAMPAIGN_COMMON_ENEMIES,...CAMPAIGN_BOSSES,...MONSTER_ENEMIES].map(enemy=>[enemy.id,enemy]));\n"
          + "export const CAMPAIGN_EQUIPMENT:CampaignEquipmentDef[] = " + literal(campaign["legacyEquipment"] + campaign["newEquipment"] + campaign["retainedLegendaries"]) + ";\n"
          + "export const MAIN_REWARDS = " + literal(campaign["mainRewards"]) + ";\n"
          + "export const SIDE_REWARDS = " + literal(campaign["sideRewards"]) + ";\n"
          + "export const MAIN_XP_EVENTS:MainExperienceEvent[] = " + literal(events) + ";\n"
          + "export const CAMPAIGN_RULES = " + literal(campaign["rules"]) + ";\n")
    # The SVGs contain stable node/edge metadata, including the conditional
    # bridge, harbour arm and inner fortress links. Do not invent a shortcut.
    coordinates, edges = {}, []
    for svg in sorted((ROOT / "source-art/maps/world-atlas-v3").glob("*geographic-plan.svg")):
        tree = ET.parse(svg)
        for element in tree.iter():
            attrs = element.attrib
            if "data-place" in attrs:
                marker = next((child for child in element if child.tag.endswith(("ellipse", "circle"))), None)
                if marker is not None:
                    coordinates[attrs["data-place"]] = {"x": round(float(marker.attrib["cx"]) / 24, 3), "z": round((1600 - float(marker.attrib["cy"])) / 16, 3)}
            if "data-a" in attrs and "data-b" in attrs:
                edges.append({"a": attrs["data-a"], "b": attrs["data-b"], "conditional": attrs.get("data-kind") != "walk-both"})
    assert len(coordinates) == 91
    write("CampaignGeography.ts", header
          + "import type {Point} from '../../../core/Contracts';\n"
          + "export const CAMPAIGN_ATLAS:Record<string,Point> = " + literal(coordinates) + ";\n"
          + "export const CAMPAIGN_ROADS:{a:string;b:string;conditional:boolean}[] = " + literal(edges) + ";\n")
    equipment = []
    set_ids = {"誓卫": "oath", "逐风": "wind", "寻宝客": "seeker", "灰烬": "ember", "沉钟": "bell", "缄印": "seal"}
    for source in campaign["legacyEquipment"] + campaign["newEquipment"] + campaign["retainedLegendaries"]:
        shape = source.get("slot", source.get("tierAndSlot", "")).split(" ")[0]
        slot = {"头": "head", "身": "chest", "手": "hands", "靴": "feet", "戒": "ringLeft", "项链": "necklace"}.get(shape, "offhand" if "盾" in shape or "法器" in shape else "weapon")
        kind = "armor" if slot in ["head", "chest", "hands", "feet", "offhand"] else "ring" if slot == "ringLeft" else "necklace" if slot == "necklace" else "bow" if "弓" in shape else "staff" if "杖" in shape else "sword"
        level_match = re.search(r"L(\d)", source.get("tierAndSlot", ""))
        quality_match = re.search(r"普通|精良|稀有|史诗|传奇", source.get("tierAndSlot", ""))
        record = {"id": source["id"], "name": source["name"], "kind": kind, "slot": slot,
                  "level": int(level_match[1]) if level_match else 3,
                  "quality": source.get("grade", quality_match[0] if quality_match else "传奇" if source["id"].startswith("L") else "稀有"),
                  "description": skills["equipmentEffects"][source["id"]], "weaponFamily": shape,
                  "source": source.get("source", "当地装备池" if not source["id"].startswith("DE") else "对应可选首领固定奖")}
        if "双手" in shape:
            record["twoHanded"] = True
        if source.get("set") in set_ids:
            record["set"] = set_ids[source["set"]]
        hp_match = re.search(r"最大生命\+(\d+)", record["description"])
        if hp_match:
            record["maxHp"] = int(hp_match[1])
        if slot in ["head", "chest", "hands", "feet"]:
            record["armor"] = {"head": 2, "chest": 6, "hands": 1, "feet": 1}[slot]
        equipment.append(record)
    assert len({item["id"] for item in equipment}) == 74
    write("EquipmentCatalog.ts", header
          + "import type {ItemDef} from './Equipment';\n"
          + "export const EQUIPMENT_CATALOG:ItemDef[] = " + literal(equipment) + ";\n")
    print(f"Exported {len(order)} skills / {len(order)*5} ranks, 74 equipment, 97 nodes, 24 archetypes and 12 bosses")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skills-only", action="store_true", help="Regenerate only PureSkills.ts")
    export(skills_only=parser.parse_args().skills_only)
