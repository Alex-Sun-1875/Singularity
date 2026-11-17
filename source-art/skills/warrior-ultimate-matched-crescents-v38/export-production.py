"""Export v38 assets, preserving contact helpers maintained in the production TS.

Only the profile/presentation prefix is generated. The protected contact suffix
must already exist in WarriorUltimate.ts; restore it from source control rather
than silently replacing its maintained collision logic with generated data.
"""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil


BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
COMMON = ROOT / "src/cocos/assets/scripts/features/combat/common"
PRODUCTION = ROOT / "src/cocos/assets/resources/vfx/production"
TS_UUID = "703ac2da-6ae9-4e9b-b31c-c4bd5ef57882"
FLOW_UUID = "e61389b7-e7c8-4863-9ec8-f7b597b28e81"
EFFECT_UUID = "c8ad752e-9373-4299-8edc-2a047adbe741"
PROTECTED_TS_MARKER = "/** Inverse of the shader"


def write_json(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


profile_path = BASE / "swoosh-profile.json"
profile = json.loads(profile_path.read_text(encoding="utf-8"))
outer, inner = profile["outerSamples"], profile["innerSamples"]
assert len(outer) == len(inner) == 129
assert outer[0] == inner[0] == [0, 0]
assert outer[-1] == inner[-1] == [3.6, 5.7866667]
assert profile["fixedScale"] == 1 and profile["fixedGeometry"] and profile["fixedWorldHeight"]
assert profile["rankWaveCounts"] == {"1": 1, "2": 2, "3": 2, "4": 3, "5": 3}


def points(name, values):
    rows = ["  " + json.dumps(p, separators=(", ", ": ")) + "," for p in values]
    return f"export const {name} = [\n" + "\n".join(rows) + "\n] as const satisfies readonly WarriorUltimatePoint[];\n"


ts_path = COMMON / "WarriorUltimate.ts"
if not ts_path.is_file():
    raise FileNotFoundError(f"Restore {ts_path} first: its protected contact helpers are maintained source.")
maintained_ts = ts_path.read_text(encoding="utf-8")
if maintained_ts.count(PROTECTED_TS_MARKER) != 1:
    raise ValueError("Expected exactly one protected contact-helper marker; refusing to overwrite WarriorUltimate.ts.")
protected_ts_tail = maintained_ts[maintained_ts.index(PROTECTED_TS_MARKER):]
ts_source = """/** Approved v38 contour, in local metres. Forward is +Z; the wave plane is Y/Z.
 * Exported from the user-traced source-art profile by export-production.py.
 * Every pulse uses these same points, height and scale throughout its lifetime.
 */
export type WarriorUltimatePoint = readonly [height: number, forward: number];

"""
ts_source += points("WARRIOR_ULTIMATE_OUTER", outer) + "\n"
ts_source += points("WARRIOR_ULTIMATE_INNER", inner) + "\n"
ts_source += """/** Shared visual/contact clock; damage budgets and actor clips are authored separately. */
export const WARRIOR_ULTIMATE = {
  outerSamples: WARRIOR_ULTIMATE_OUTER,
  innerSamples: WARRIOR_ULTIMATE_INNER,
  fixedScale: 1,
  fixedGeometry: true,
  fixedWorldHeight: true,
  planeLift: 0.12,
  pulseInterval: 0.22,
  waveLife: 1.02,
  visualDuration: 1.52,
  launchDelay: 0.018,
  appearSeconds: 0.025,
  dissolveStart: 0.40,
  dissolveDuration: 0.62,
  alphaReference: 245,
  silver: [0.79, 0.83, 0.86],
  rankWaveCounts: [1, 2, 2, 3, 3],
  mesh: {
    depthSegments: 16,
    bodyDepth: 0.66,
    wakeDepth: 0.34,
    wakeLength: 1.10,
    wakeHeightAmplitude: 0.015,
    wakeHeightFrequency: 23,
    wakeSideAmplitude: 0.012,
    wakeEnvelopeExponent: 1.2,
    boundingRadius: 8,
  },
  travel: {
    start: 0.15,
    contactAdvance: 5.255349567118673,
  },
} as const;

/** Pass the cast's captured skill rank, so later skill changes cannot alter a live cast. */
export function warriorUltimateWaveCount(rank: number): 1 | 2 | 3 {
  const index = Number.isFinite(rank) ? Math.max(0, Math.min(4, Math.floor(rank) - 1)) : 0;
  return WARRIOR_ULTIMATE.rankWaveCounts[index];
}

const clamp = (value: number): number => Math.max(0, Math.min(1, value));
const smooth = (value: number): number => { const q = clamp(value); return q * q * (3 - 2 * q); };

/** Constant forward speed through the entire fade. Preserve the authored
 * advance at the end of the damaging crest without a slow drifting phase. */
export function warriorUltimateDistance(age: number): number {
  const travel = WARRIOR_ULTIMATE.travel;
  return travel.start + travel.contactAdvance
    * Math.max(0, Math.min(WARRIOR_ULTIMATE.waveLife, age)) / WARRIOR_ULTIMATE_CONTACT.endAge;
}
"""
ts_source += "\n" + protected_ts_tail
ts_path.write_text(ts_source, encoding="utf-8")
ts_meta = deepcopy(json.loads((COMMON / "WhirlwindSkill.ts.meta").read_text(encoding="utf-8")))
ts_meta["uuid"] = TS_UUID
write_json(ts_path.with_suffix(".ts.meta"), ts_meta)

flow_path = PRODUCTION / "warrior-ultimate-flow-v38.png"
shutil.copyfile(BASE / "swoosh-flow.png", flow_path)
flow_meta = deepcopy(json.loads((PRODUCTION / "warrior-flow-v1.png.meta").read_text(encoding="utf-8")))
old_uuid = flow_meta["uuid"]
flow_meta = json.loads(json.dumps(flow_meta).replace(old_uuid, FLOW_UUID))
flow_meta["subMetas"]["6c48a"]["displayName"] = flow_path.stem
write_json(flow_path.with_suffix(".png.meta"), flow_meta)

fragment_path = BASE / "swoosh.frag"
fragment = fragment_path.read_text(encoding="utf-8").strip()
pressure_path = PRODUCTION / "warrior-pressure-wave-v2.effect"
pressure = pressure_path.read_text(encoding="utf-8")
technique = pressure.split("CCProgram pressure-wave-vs %{", 1)[0]
technique = technique.replace("pressure-wave-vs", "warrior-ultimate-v38-vs")
technique = technique.replace("pressure-wave-fs", "warrior-ultimate-v38-fs")
technique = technique.replace("[0.80, 0.82, 0.84, 1]", "[0.79, 0.83, 0.86, 1]")
effect_path = PRODUCTION / "warrior-ultimate-v38.effect"
vertex = """CCProgram warrior-ultimate-v38-vs %{
  precision highp float;
  #include <builtin/uniforms/cc-global>
  #include <builtin/uniforms/cc-local>
  in vec3 a_position;
  in vec2 a_texCoord;
  out vec2 v_uv;
  uniform PressureParams {
    vec4 mainColor;
    vec4 flowState;
  };
  vec4 vert () {
    v_uv = a_texCoord;
    return cc_matViewProj * cc_matWorld * vec4(a_position, 1.0);
  }
}%

CCProgram warrior-ultimate-v38-fs %{
  precision highp float;
  #include <legacy/output-standard>
  in vec2 v_uv;
  uniform sampler2D mainTexture;
  uniform sampler2D flowTexture;
  uniform PressureParams {
    vec4 mainColor;
    vec4 flowState;
  };
"""
effect_path.write_text(technique + vertex + fragment + "\n}%\n", encoding="utf-8")
effect_meta = deepcopy(json.loads(pressure_path.with_suffix(".effect.meta").read_text(encoding="utf-8")))
effect_meta["uuid"] = EFFECT_UUID
write_json(effect_path.with_suffix(".effect.meta"), effect_meta)

assert digest(flow_path) == digest(BASE / "swoosh-flow.png")
assert effect_path.read_text(encoding="utf-8").split("vec4 frag ()", 1)[1].rsplit("}%", 1)[0].strip() == fragment.split("vec4 frag ()", 1)[1].strip()
write_json(BASE / "production-export.json", {
    "design": "user-approved fixed v38 red-line crescent",
    "generatedBy": "export-production.py",
    "profileSha256": digest(profile_path),
    "fragmentSha256": digest(fragment_path),
    "flowSourceSha256": digest(BASE / "swoosh-flow.png"),
    "contourSamplesPerEdge": len(outer),
    "fragmentCopiedExactly": True,
    "vertexDisplacement": False,
    "rankWaveCounts": profile["rankWaveCounts"],
    "maintainedExtension": {
        "source": ts_path.relative_to(ROOT).as_posix(),
        "marker": PROTECTED_TS_MARKER,
        "sha256Utf8Lf": sha256(protected_ts_tail.encode("utf-8")).hexdigest(),
        "exportPolicy": "Regenerate only the readonly contour/presentation prefix; preserve the maintained contact-helper suffix verbatim. Missing or ambiguous suffix aborts before writes.",
        "behavior": "Each pulse sweeps its visible moving bright crest against standing targets in their launch-relative ground-height interval; contact-span projections cache both vertical bounds in at most 32 keys. No contour, material, animation timing or mesh size changes.",
    },
    "outputs": [
        {"path": p.relative_to(ROOT).as_posix(), "sha256": digest(p)}
        for p in [ts_path, ts_path.with_suffix(".ts.meta"), flow_path,
                  flow_path.with_suffix(".png.meta"), effect_path, effect_path.with_suffix(".effect.meta")]
    ],
    "status": "data and assets exported; runtime wiring, engine import, platform and device verification belong to the integration task",
})
print(f"Exported {len(outer)} exact points per edge, fixed mesh/timing, flow and effect; no build executed.")
