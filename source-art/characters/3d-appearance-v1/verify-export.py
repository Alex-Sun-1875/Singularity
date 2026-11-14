"""Reuse native rig/action digests, FBX roundtrip and actual mesh-contact review."""
from pathlib import Path
import bpy,sys,json,importlib.util,math
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import cocos_v5_weapon_redesign as props
spec=importlib.util.spec_from_file_location('contact',ROOT/'source-art/characters/3d-weapon-contact-v2/inspect-contact.py')
# Import only the existing tree function; its original top-level legacy run stays untouched.
scope={'bpy':bpy,'BVHTree':__import__('mathutils.bvhtree',fromlist=['BVHTree']).BVHTree};script=(ROOT/'source-art/characters/3d-weapon-contact-v2/inspect-contact.py').read_text(encoding='utf-8');exec(script[script.index('def tree('):script.index('\nrows=[]')],scope);tree=scope['tree']
bpy.ops.wm.open_mainfile(filepath=str(BASE/'raphael.blend'));rig=bpy.data.objects['raphael_Native65'];review=json.loads((BASE/'authoring-review.json').read_text(encoding='utf-8'))
assert pipeline.curves()==review['preservedActionsSHA256']and pipeline.skeleton(rig)==review['preservedBindSHA256']
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];assert len(objects)==13
rig.data.pose_position='REST';bpy.context.view_layer.update();before=props.mesh_state(objects);previous=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(BASE/'raphael.fbx'));imported=[o for o in bpy.data.objects if o not in previous];after=props.mesh_state([o for o in imported if o.type=='MESH']);check=props.verify_roundtrip(before,after)
for obj in imported:bpy.data.objects.remove(obj,do_unlink=True)
rig.data.pose_position='POSE';body=[o for o in objects if o.get('nativePart')=='body'];rows=[]
for name in ['attack_bow','attack_sword','attack_staff']:
    action=bpy.data.actions[name];rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    frames=[]
    for frame in range(math.floor(action.frame_range[1])+1):
        bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();torso=tree(body);r={'frame':frame}
        for side in ['right','left']:
            hand=tree(objects,side);pairs=torso.overlap(hand)if hand else[];r[side]=len({b for a,b in pairs})
        frames.append(r)
    rows.append({'clip':name,'frames':frames,'maxRight':max(r['right']for r in frames),'maxLeft':max(r['left']for r in frames)})
result={'roundtrip':check,'rigBindUnchanged':True,'all14ActionCurvesUnchanged':True,'renderers':13,'meshContact':rows,'contactScope':'Evaluated garment body and actual hand/finger triangles; not shoulder seams or exhaustive all-skill collision acceptance'}
(BASE/'export-verification.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');print('APPEARANCE_VERIFIED',json.dumps({'roundtrip':check,'contact':[{k:r[k]for k in ['clip','maxLeft','maxRight']}for r in rows]}),flush=True)
