"""Adapt UAL's authored two-hand grip through the installed BVH Retargeter.

Only Raphael's finger quaternion tracks are replaced. Body motion, meshes,
weights, materials and clip ranges remain unchanged. Use --production to save
the existing authoring source; otherwise write an isolated draft.
"""
from pathlib import Path
import hashlib
import json
import shutil
import sys

import bpy

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from cocos_mocap_retarget import register

SOURCE = ROOT / 'source-art/characters/cocos'
STAGE = ROOT / 'src/.tmp/actor-hand-review'
LIBRARY = ROOT / 'src/.tools/universal-animation-library-standard/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb'
FINGERS = ('index_', 'middle_', 'ring_', 'pinky_', 'thumb_')


def is_finger(path):
    return any(f'pose.bones["{prefix}' in path for prefix in FINGERS)


def body_fingerprint(action):
    curves = []
    for fc in action.fcurves:
        if is_finger(fc.data_path):
            continue
        curves.append((fc.data_path, fc.array_index, [
            (list(k.co), list(k.handle_left), list(k.handle_right), k.interpolation)
            for k in fc.keyframe_points
        ]))
    return hashlib.sha256(json.dumps(sorted(curves)).encode()).hexdigest()


def adapt(production=False):
    STAGE.mkdir(parents=True, exist_ok=True)
    source_path = SOURCE / 'raphael.blend'
    backup = STAGE / 'before'
    backup.mkdir(exist_ok=True)
    if production and not (backup / 'raphael.blend').exists():
        shutil.copy2(source_path, backup / 'raphael.blend')
        for name in ['raphael.fbx', 'manifest.json']:
            shutil.copy2(ROOT / 'src/cocos/assets/resources/actors/raphael' / name, backup / name)

    bpy.ops.wm.open_mainfile(filepath=str(source_path))
    scene = bpy.context.scene
    rig = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
    originals = list(bpy.data.actions)
    ranges = {a.name: list(a.frame_range) for a in originals}
    before = {a.name: body_fingerprint(a) for a in originals}
    finger_names = [p.name for p in rig.pose.bones if p.name.startswith(FINGERS)]
    old_objects = set(bpy.data.objects)
    rig.animation_data.action = bpy.data.actions['idle']
    scene.frame_set(1)
    scale = rig.scale.copy()

    bpy.ops.import_scene.gltf(filepath=str(LIBRARY))
    source = next(o for o in bpy.data.objects if o.type == 'ARMATURE' and o != rig)
    source.data.bones['Head'].name = 'head'
    register()
    raw = bpy.data.actions['Driving_Loop']
    first, last = raw.frame_range
    for fc in raw.fcurves:
        for key in fc.keyframe_points:
            key.co.x += 1 - first
            key.handle_left.x += 1 - first
            key.handle_right.x += 1 - first
    count = round(last - first)
    source.animation_data.action = raw
    if raw.slots:
        source.animation_data.action_slot = raw.slots[0]
    bpy.ops.object.select_all(action='DESELECT')
    source.select_set(True)
    rig.select_set(True)
    bpy.context.view_layer.objects.active = rig
    rig.scale = (1, 1, 1)
    result = bpy.ops.mcp.retarget_selected_to_active(
        useAutoSource=True, useAutoTarget=True, useAutoScale=True,
        useCenterAnimation=False, useAllFrames=False, startFrame=1, endFrame=count + 1,
    )
    if result != {'FINISHED'}:
        raise RuntimeError(f'Upstream retarget operator failed: {result}')
    rig.scale = scale
    scene.frame_set(max(1, count // 2))
    bpy.context.view_layer.update()
    pose = {name: rig.pose.bones[name].rotation_quaternion.copy() for name in finger_names}

    for obj in set(bpy.data.objects) - old_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    rig.animation_data.action = None
    for action in list(bpy.data.actions):
        if action not in originals:
            bpy.data.actions.remove(action)
    for action in originals:
        rig.animation_data.action = action
        if action.slots:
            rig.animation_data.action_slot = action.slots[0]
        for fc in list(action.fcurves):
            if is_finger(fc.data_path):
                action.fcurves.remove(fc)
        start, end = ranges[action.name]
        for frame in [start, end]:
            for name, quat in pose.items():
                bone = rig.pose.bones[name]
                bone.rotation_mode = 'QUATERNION'
                bone.rotation_quaternion = quat
                bone.keyframe_insert('rotation_quaternion', frame=frame)
        if body_fingerprint(action) != before[action.name]:
            raise RuntimeError(f'Non-finger curve changed: {action.name}')
        if list(action.frame_range) != ranges[action.name]:
            raise RuntimeError(f'Clip range changed: {action.name}')

    rig.animation_data.action = bpy.data.actions['idle']
    if rig.animation_data.action.slots:
        rig.animation_data.action_slot = rig.animation_data.action.slots[0]
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    destination = source_path if production else STAGE / 'raphael.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(destination), relative_remap=False)
    report = {
        'identity': 'raphael', 'upstream': 'Quaternius UAL1 Standard / Driving_Loop',
        'assetLicense': 'CC0-1.0', 'solver': 'Installed BVH Retargeter 4.4.0, unchanged',
        'scope': 'Two closed grip finger poses; no body retarget, mesh, wardrobe or material edits.',
        'reason': 'The old procedural hand pose curled around the global armature axis and left the weapon hand visibly open.',
        'fingerBones': len(pose), 'clips': ranges,
        'nonFingerCurveHashes': before, 'nonFingerCurvesUnchanged': True,
        'poseWXYZ': {name: list(quat) for name, quat in pose.items()},
        'sourceSaved': str(destination),
        'limits': 'Generic authored power grip, not a bespoke archery three-finger release or individual finger contact solver.',
    }
    report_path = SOURCE / 'hero-hand-grip-v2.json' if production else STAGE / 'hero-hand-grip-v2.json'
    report_path.write_text(json.dumps(report, indent=2), encoding='utf8')
    print('[HERO_GRIP]', destination, len(pose), 'finger bones;', len(originals), 'existing clips; body curves unchanged')


if __name__ == '__main__':
    adapt('--production' in sys.argv)
