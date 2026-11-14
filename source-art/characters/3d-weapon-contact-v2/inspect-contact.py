"""Mesh-level offline review using Blender evaluated skin and native BVH."""
from pathlib import Path
import bpy,json,math,sys
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[3];OUT=Path(__file__).resolve().parent
def tree(objects,region=None):
    vertices=[];polygons=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in objects:
        selected=None
        if region:
            names={region:'hand_r' if region=='right' else 'hand_l'}
            groups={g.index for g in obj.vertex_groups if g.name==names[region] or g.name.startswith(('index_','middle_','ring_','pinky_','thumb_')) and g.name.endswith('_r' if region=='right' else '_l')}
            selected={v.index for v in obj.data.vertices if sum(g.weight for g in v.groups if g.group in groups)>.65}
        ev=obj.evaluated_get(deps);mesh=ev.to_mesh();offset=len(vertices)
        vertices.extend(ev.matrix_world@v.co for v in mesh.vertices)
        polygons.extend(tuple(offset+i for i in p.vertices) for p in mesh.polygons if selected is None or all(i in selected for i in p.vertices))
        ev.to_mesh_clear()
    return BVHTree.FromPolygons(vertices,polygons) if polygons else None

rows=[]
for label,source in [('before',ROOT/'src/.tmp/native-production/source/raphael.blend'),('after',OUT/'authored-bow.blend')]:
    bpy.ops.wm.open_mainfile(filepath=str(source));rig=bpy.data.objects['raphael_Native65']
    objects=[o for o in bpy.data.objects if o.type=='MESH' and '_native_' in o.name and '_hood_' not in o.name]
    body=[o for o in objects if '_native_body_' in o.name]
    for clip in ['attack_bow','attack_sword','attack_staff']:
        action=bpy.data.actions[clip];rig.animation_data.action=action;rig.animation_data.action_slot=action.slots[0]
        contacts=[]
        frames=range(math.floor(action.frame_range[1])+1) if '--quick' not in sys.argv else sorted(set([0,10,20,30,min(40,math.floor(action.frame_range[1])),math.floor(action.frame_range[1])]))
        for f in frames:
            if f>action.frame_range[1]:continue
            bpy.context.scene.frame_set(f);bpy.context.view_layer.update();torso=tree(body)
            result={'frame':f}
            for side in ['right','left']:
                hand=tree(objects,side);pairs=torso.overlap(hand) if hand else []
                result[side+'HandIntersectingTriangles']=len({b for a,b in pairs})
            contacts.append(result)
        rows.append({'label':label,'clip':clip,'samples':contacts})
(OUT/'mesh-contact-review.json').write_text(json.dumps({'method':'Blender BVHTree.overlap on evaluated torso clothing and actual hand/finger triangles, all source frames; garment shoulder seams excluded','rows':rows},indent=2)+'\n')
print('MESH_REVIEW',json.dumps([{'label':x['label'],'clip':x['clip'],'maxRight':max(v['rightHandIntersectingTriangles'] for v in x['samples']),'maxLeft':max(v['leftHandIntersectingTriangles'] for v in x['samples'])} for x in rows]))
