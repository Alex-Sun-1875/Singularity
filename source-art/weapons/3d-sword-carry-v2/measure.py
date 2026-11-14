"""Measure the current evaluated costume, reusing the existing Blender/BVH workflow."""
from pathlib import Path
import bpy, json
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[2]
manifest = json.loads((ROOT / 'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
bpy.ops.wm.open_mainfile(filepath=str(ROOT / manifest['source']))
rig = bpy.data.objects['raphael_Native65']
rig.data.pose_position = 'POSE'
action = bpy.data.actions['idle']
rig.animation_data.action = action
if action.slots:
    rig.animation_data.action_slot = action.slots[0]
bpy.context.scene.frame_set(0)
axis = Matrix(((1, 0, 0, 0), (0, 0, 1, 0), (0, -1, 0, 0), (0, 0, 0, 1)))
dg = bpy.context.evaluated_depsgraph_get()
verts, faces = [], []
for obj in bpy.data.objects:
    if obj.type != 'MESH' or obj.get('nativePart') != 'body':
        continue
    ev = obj.evaluated_get(dg)
    mesh = ev.to_mesh()
    offset = len(verts)
    verts.extend(tuple((axis @ obj.matrix_world) @ v.co) for v in mesh.vertices)
    faces.extend(tuple(offset + i for i in p.vertices) for p in mesh.polygons)
    ev.to_mesh_clear()
bvh = BVHTree.FromPolygons(verts, faces)
rows = []
for y in [1.05, 1.15, 1.25, 1.35, 1.45, 1.55, 1.6]:
    for x in [-.2, -.15, -.1, -.05, 0, .05, .1, .15, .2]:
        p, n, _, d = bvh.ray_cast(Vector((x, y, -1)), Vector((0, 0, 1)), 2)
        if p:
            rows.append({'x': x, 'y': y, 'surface': list(p), 'normal': list(n)})
(BASE / 'back-surface.json').write_text(json.dumps({'source': manifest['source'], 'samples': rows}, indent=2) + '\n', encoding='utf-8')
print('Measured', len(rows), 'idle costume points', flush=True)

# Compare the same rigid sheath against the evaluated animated costume.
def pose(name, fraction):
    action = bpy.data.actions[name]
    rig.animation_data.action = action
    if action.slots:
        rig.animation_data.action_slot = action.slots[0]
    frame = action.frame_range[0] + (action.frame_range[1] - action.frame_range[0]) * fraction
    bpy.context.scene.frame_set(int(frame), subframe=frame-int(frame))
    bpy.context.view_layer.update()

def surface():
    verts, faces = [], []
    dg = bpy.context.evaluated_depsgraph_get()
    for obj in bpy.data.objects:
        if obj.type != 'MESH' or obj.get('nativePart') != 'body':
            continue
        ev = obj.evaluated_get(dg)
        mesh = ev.to_mesh()
        offset = len(verts)
        verts.extend(tuple((axis @ obj.matrix_world) @ v.co) for v in mesh.vertices)
        faces.extend(tuple(offset + i for i in p.vertices) for p in mesh.polygons)
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(verts, faces)

recipes = json.loads((BASE / 'candidate-placements.json').read_text(encoding='utf-8'))
old = json.loads((BASE / 'before-bindings.json').read_text(encoding='utf-8'))['bindings'] if (BASE / 'before-bindings.json').exists() else manifest['cocosBinding']
recipes.append({'name': 'before', **old['swordBackCarry']['items']['W01']})
bones = ['spine_01', 'spine_02', 'spine_03']
frames = []
pose('idle', 0)
references = {bone: (axis @ rig.matrix_world @ rig.pose.bones[bone].matrix).inverted() for bone in bones}
for clip, fraction in [('idle', 0)] + [(name, f) for name in ['walk', 'run', 'dodge'] for f in [.0, .25, .5, .75]]:
    pose(clip, fraction)
    bvh = surface()
    for recipe in recipes:
        p, d = Vector(recipe['position']), Vector(recipe['blade']).normalized()
        for bone in bones:
            motion = (axis @ rig.matrix_world @ rig.pose.bones[bone].matrix) @ references[bone]
            outward = (motion.to_3x3() @ Vector((0, 0, -1))).normalized()
            samples = []
            for t in [.16, .24, .32, .4, .48]:
                point = motion @ (p + d*t)
                q, n, _, distance = bvh.find_nearest(point)
                # Decorative costume faces include inward normals. Classify the
                # back side in the animated torso frame instead of using them.
                samples.append({'t': t, 'point': list(point), 'surface': list(q), 'signedCenterGap': distance * (1 if (point-q).dot(outward)>0 else -1)})
            frames.append({'recipe': recipe['name'], 'bone': bone, 'clip': clip, 'fraction': fraction, 'samples': samples})
(BASE / 'anchor-measurements.json').write_text(json.dumps(frames, indent=2)+'\n', encoding='utf-8')
print('Measured', len(frames), 'sheath frames', flush=True)
