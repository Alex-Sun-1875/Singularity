"""Compare the authored character source with its prior accepted source."""
from pathlib import Path
import bpy,json,hashlib
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
def geometry():
    rows={}
    for o in bpy.data.objects:
        if o.type!='MESH'or '_native_'not in o.name:continue
        rows[o.name]={'vertices':[list(v.co)for v in o.data.vertices],'faces':[list(p.vertices)for p in o.data.polygons],'uv':[[list(p.uv)for p in layer.data]for layer in o.data.uv_layers],'weights':[[[g.group,g.weight]for g in v.groups]for v in o.data.vertices]}
    return hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
def curves(action):return {(c.data_path,c.array_index):[c.evaluate(i*.5)for i in range(2*int(action.frame_range[1])+1)]for c in action.fcurves}
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-weapon-contact-v2/authored-bow.blend'))
before_geo=geometry();before_actions={a.name:curves(a)for a in bpy.data.actions};rig=bpy.data.objects['raphael_Native65'];before_rest={b.name:[list(row)for row in b.matrix_local]for b in rig.data.bones}
bpy.ops.wm.open_mainfile(filepath=str(BASE/'compact-jog.blend'))
after_geo=geometry();rig=bpy.data.objects['raphael_Native65'];after_rest={b.name:[list(row)for row in b.matrix_local]for b in rig.data.bones}
assert before_geo==after_geo and before_rest==after_rest
assert set(before_actions)==set(a.name for a in bpy.data.actions)
max_unchanged=0;max_arm=0;legs=['thigh_l','calf_l','foot_l','thigh_r','calf_r','foot_r','root'];unchanged=[]
for action in bpy.data.actions:
    previous=before_actions[action.name];current=curves(action)
    if action.name not in ['run','run_staff']:
        assert previous==current,action.name;unchanged.append(action.name)
    else:
        for (path,component),values in current.items():
            if any(('"'+n+'"')in path for n in legs):continue
            old=previous[(path,component)];max_arm=max(max_arm,max(abs(a-b)for a,b in zip(values,old)))
assert max_arm<1e-6
old=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(BASE/'raphael.fbx'))
imported=[o for o in bpy.data.objects if o not in old];meshes=[o for o in imported if o.type=='MESH'];armature=next(o for o in imported if o.type=='ARMATURE')
assert len(meshes)==13 and len(armature.data.bones)==67
result={'meshUVWeightsSHA256':after_geo,'meshUVWeightsUnchanged':True,'bindPoseUnchanged':True,'unchangedActions':sorted(unchanged),'maxRunArmSpineHelperLocalChannelError':max_arm,'exportedMeshes':len(meshes),'exportedHierarchyBones':len(armature.data.bones),'sourceActionCount':len(before_actions)}
(BASE/'source-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('SOURCE_VERIFIED',json.dumps(result))
