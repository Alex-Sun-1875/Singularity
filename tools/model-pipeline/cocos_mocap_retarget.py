"""CMU BVH -> existing Unreal-compatible MPFB rig through BVH Retargeter 4.4.

Adaptation uses the upstream solver unchanged. Root travel is removed only
after retargeting, retaining captured pelvis lift, weight transfer and rotation.
"""
from pathlib import Path
import bpy,sys,importlib.util,json,addon_utils,os
from types import SimpleNamespace
from mathutils import Quaternion,Vector
import math

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'))
OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))
DATA=ROOT/'source-art/characters/mocap/cmu'
TOOL=ROOT/'src/.tools/retarget_bvh-version_4_4_0'
SELECTIONS={
    'run':('16_36',2,26,.641806,True),
    'walk':('16_15',34,68,.779143,True),
    'idle':('111_28',5,77,2.4,True),
    'attack_sword':('02_07',30,66,.9,False),
    'attack_bow':('79_86',70,148,1.25,False),
}
UAL={'idle':('Idle_Loop',True),'walk':('Walk_Loop',True),'run':('Jog_Fwd_Loop',True),
     'attack_sword':('Sword_Attack',False)}


def prepare_library(identity,production=False):
    """Use the maintained retarget operator, then adapt timing and floor only."""
    path=SOURCE/(identity+'.blend') if production else ROOT/'src/.tmp/character-fidelity'/('draft-'+identity+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(path));scene=bpy.context.scene;scene.render.fps=30
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    rig.pose.bones['Root'].rotation_quaternion=Quaternion()
    rig.pose.bones['Root'].location=(0,0,0);rig.pose.bones['Root'].scale=(1,1,1)
    grip={p.name:p.rotation_quaternion.copy() for p in rig.pose.bones if any(n in p.name for n in ['index_','middle_','ring_','pinky_','thumb_'])}
    old_objects=set(bpy.data.objects);old_actions=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(ROOT/'src/.tools/universal-animation-library-standard/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb'))
    source=next(o for o in bpy.data.objects if o.type=='ARMATURE' and o!=rig)
    source.data.bones['Head'].name='head';register();reports={}
    target_scale=rig.scale.copy()
    stride_scale=rig.data.bones['thigh_l'].length/source.data.bones['thigh_l'].length*target_scale.z
    boots=bpy.data.objects.get(identity+'_libraryboots_surface') or bpy.data.objects.get(identity+'_belt_surface')
    feet=[v.index for v in boots.data.vertices if v.co.z<.30]
    for name,(library,loop) in UAL.items():
        raw=bpy.data.actions[library];first,last=raw.frame_range;duration=(last-first)/30
        # The upstream solver writes its calibration T-pose at frame zero.
        # Reserve that frame instead of shifting the calibration into the clip.
        for fc in raw.fcurves:
            for key in fc.keyframe_points:
                key.co.x+=1-first;key.handle_left.x+=1-first;key.handle_right.x+=1-first
        count=round(last-first)
        source.animation_data.action=raw
        if raw.slots:source.animation_data.action_slot=raw.slots[0]
        bpy.ops.object.select_all(action='DESELECT');source.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
        # The authoring rigs use a uniform identity-height scale. The solver
        # requires unit object scale; restore it before evaluating skinned boots.
        rig.scale=(1,1,1)
        rig.pose.bones['Root'].rotation_quaternion=Quaternion()
        rig.pose.bones['Root'].location=(0,0,0);rig.pose.bones['Root'].scale=(1,1,1)
        result=bpy.ops.mcp.retarget_selected_to_active(useAutoSource=True,useAutoTarget=True,useAutoScale=True,useCenterAnimation=False,useAllFrames=False,startFrame=1,endFrame=count+1)
        rig.scale=target_scale;bpy.context.view_layer.update()
        assert result=={'FINISHED'},(identity,name,result)
        action=rig.animation_data.action
        previous=bpy.data.actions.get(name)
        if previous and previous!=action:bpy.data.actions.remove(previous)
        action.name=name;action.use_fake_user=True
        for fc in action.fcurves:
            for key in list(fc.keyframe_points):
                if key.co.x<1:fc.keyframe_points.remove(key)
        # Root is deliberately unmapped by the upstream solver. Explicit keys
        # prevent the previous death clip's fall transform leaking into idle.
        root=rig.pose.bones['Root'];root.rotation_mode='QUATERNION'
        root.rotation_quaternion=Quaternion();root.location=(0,0,0);root.scale=(1,1,1)
        for frame in [1,count+1]:
            for channel in ['rotation_quaternion','location','scale']:
                root.keyframe_insert(channel,frame=frame)
        if name not in ['spell','interact','death']:
            for frame in range(1,count+2):
                scene.frame_set(frame)
                for bn,q in grip.items():
                    rig.pose.bones[bn].rotation_quaternion=q
                    rig.pose.bones[bn].keyframe_insert('rotation_quaternion',frame=frame)
        minimum=1e10;tail_minimum=1e10;floor_samples=[]
        if boots:
            for i in range(count+1):
                scene.frame_set(1+i);ev=boots.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
                z=min((ev.matrix_world@mesh.vertices[i].co).z for i in feet);minimum=min(minimum,z)
                floor_samples.append(z)
                if i>count*.9:tail_minimum=min(tail_minimum,z)
                ev.to_mesh_clear()
            # Contact is measured from the actual skinned sole, after omitting
            # calibration. Walk/idle/attacks keep one foot on the ground; jogging
            # retains its captured flight above the lowest contact pose.
            root=rig.pose.bones['Root']
            gain=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()@Vector((0,0,1))).z
            zcurve=next((fc for fc in action.fcurves if fc.data_path=='pose.bones["Root"].location' and fc.array_index==2),None)
            original=[zcurve.evaluate(f) if zcurve else 0 for f in range(1,count+2)]
            if zcurve:action.fcurves.remove(zcurve)
            for frame in range(1,count+2):
                scene.frame_set(frame)
                ground=floor_samples[frame-1]
                desired=.003+(ground-minimum if name=='run' else 0)
                root.location.z=original[frame-1]+(desired-ground)/gain
                root.keyframe_insert('location',index=2,frame=frame)
        if name=='death':
            # Hold the final collapsed pose; core death is not an animation loop.
            scene.frame_set(count+1)
            hold=count+1+math.ceil(count*.3)
            for p in rig.pose.bones:
                p.keyframe_insert('location',frame=hold);p.keyframe_insert('rotation_quaternion',frame=hold)
            duration=(hold-1)/30
        for fc in action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
        reports[name]={'source':library,'duration':duration,'loop':loop,'calibrationFrameExcluded':True,'minimumBootHeightBeforeGrounding':minimum,'holdFinalPose':False,'nominalSpeedMetresPerSecond':(.975 if name=='walk' else 5.357142857142857 if name=='run' else 0)*stride_scale,'strideSource':'UAL1_Standard_RM root displacement / source duration, scaled by the retarget thigh ratio and target object scale'}
        print('[LIBRARY_MOTION]',identity,name,reports[name],flush=True)
    for obj in set(bpy.data.objects)-old_objects:bpy.data.objects.remove(obj,do_unlink=True)
    for action in list(bpy.data.actions):
        if action not in old_actions and action.name not in UAL:bpy.data.actions.remove(action)
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(path),relative_remap=False)
    if production:
        mp=OUT/identity/'manifest.json';manifest=json.loads(mp.read_text())
        manifest['libraryMotion']={'tool':'BVH Retargeter 4.4.0','toolLicense':'GPL-2.0-or-later','dataset':'Quaternius Universal Animation Library Standard 2026-06-16','assetLicense':'CC0-1.0','clips':reports}
        for name,record in reports.items():manifest['clips'][name]={'name':name,**record}
        mp.write_text(json.dumps(manifest,indent=2))

def register():
    if 'retarget_bvh' in sys.modules:
        from retarget_bvh.utils import BD
        BD.ensureInited(bpy.context.scene)
        return
    spec=importlib.util.spec_from_file_location('retarget_bvh',TOOL/'__init__.py',submodule_search_locations=[str(TOOL)])
    addon=importlib.util.module_from_spec(spec);sys.modules['retarget_bvh']=addon;spec.loader.exec_module(addon)
    addon.register()
    from retarget_bvh.utils import BD
    BD.prefs=SimpleNamespace(verbose=False,useLimits=True,useUnlock=False,useBlenderBvh=False,useNativeFbx=False)
    BD.ensureInited(bpy.context.scene)


def retarget(identity,clip,file):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'src/.tmp/character-fidelity'/('draft-'+identity+'.blend')))
    register()
    scene=bpy.context.scene;scene.render.fps=30
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig
    old=set(bpy.data.actions)
    # This rig's 53 names match BVH Retargeter's maintained Unreal preset.
    bpy.ops.mcp.load_and_retarget(filepath=str(DATA/(file+'.bvh')),useAutoTarget=True,useAutoSource=True,useAutoScale=True,useSimplify=False,useBendPositive=False,useCenterAnimation=False)
    action=rig.animation_data.action
    action.name='CMU_'+file;action.use_fake_user=True
    print('[MOCAP_RAW]',clip,file,action.name,list(action.frame_range),flush=True)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'src/.tmp/character-fidelity'/('mocap-'+file+'.blend')),relative_remap=False)


def prepare(identity,draft=True):
    destination=ROOT/'src/.tmp/character-fidelity'/('draft-'+identity+'.blend') if draft else SOURCE/(identity+'.blend')
    bpy.ops.wm.open_mainfile(filepath=str(destination))
    scene=bpy.context.scene;scene.render.fps=30
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    grip={pb.name:pb.rotation_quaternion.copy() for pb in rig.pose.bones if any(n in pb.name for n in ['index_','middle_','ring_','pinky_','thumb_'])}
    sources={}
    for clip,(file,start,end,duration,loop) in SELECTIONS.items():
        rawpath=ROOT/'src/.tmp/character-fidelity'/('mocap-'+file+'.blend')
        with bpy.data.libraries.load(str(rawpath)) as (available,loaded):loaded.actions=['CMU_'+file]
        sources[clip]=loaded.actions[0]
    reports={}
    for clip,(file,start,end,duration,loop) in SELECTIONS.items():
        raw=sources[clip];rig.animation_data.action=raw
        count=round(duration*30)
        samples=[]
        rest=rig.data.bones['pelvis'].matrix_local.to_3x3()
        for i in range(count+1):
            time=start+(end-start)*i/count;scene.frame_set(int(time),subframe=time%1)
            values={pb.name:[pb.rotation_quaternion.copy(),pb.location.copy()] for pb in rig.pose.bones}
            # Horizontal root travel lives in a tilted pelvis rest basis.
            offset=rest@values['pelvis'][1]
            values['pelvis'][1]=rest.inverted()@Vector((0,0,offset.z))
            values['Root'][1]=Vector((0,0,0))
            values['Root'][0]=Quaternion()
            for name,q in grip.items():values[name][0]=q.copy()
            samples.append(values)
        rest_q=rig.data.bones['pelvis'].matrix_local.to_quaternion()
        source_forward=(rest_q@samples[0]['pelvis'][0]@rest_q.inverted())@Vector((0,-1,0))
        heading=math.atan2(source_forward.x,-source_forward.y)
        if clip=='attack_bow':
            # Shooting direction comes from the captured extended bow arm,
            # while the pelvis keeps its natural open archer stance.
            frame=108;scene.frame_set(frame)
            source_forward=rig.pose.bones['hand_l'].head-rig.pose.bones['upperarm_l'].head
            heading=math.atan2(source_forward.x,-source_forward.y)
        correction=rest_q.inverted()@Quaternion((0,0,1),-heading)@rest_q
        for values in samples:values['pelvis'][0]=correction@values['pelvis'][0]
        if loop:
            # Close a captured stride by distributing the small endpoint error;
            # the captured foot timing and interjoint motion remain intact.
            for name in samples[0]:
                q0,l0=samples[0][name];ql,ll=samples[-1][name]
                delta=ql.inverted()@q0
                if delta.w<0:delta.negate()
                drift=ll-l0
                for i,values in enumerate(samples):
                    t=i/count;values[name][0]=values[name][0]@Quaternion().slerp(delta,t)
                    values[name][1]-=drift*t
        previous=bpy.data.actions.get(clip)
        if previous:bpy.data.actions.remove(previous)
        action=bpy.data.actions.new(clip);action.use_fake_user=True;rig.animation_data.action=action
        for i,values in enumerate(samples):
            for name,(q,loc) in values.items():
                pb=rig.pose.bones[name];pb.rotation_mode='QUATERNION';pb.rotation_quaternion=q;pb.location=loc;pb.scale=(1,1,1)
                frame=1+duration*30*i/count
                pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
        # Use the actual skinned library boot, keeping the running flight phase.
        boots=bpy.data.objects.get(identity+'_libraryboots_surface')
        floor=1e10
        if boots:
            for i in range(count+1):
                frame=1+duration*30*i/count;scene.frame_set(int(frame),subframe=frame%1);deps=bpy.context.evaluated_depsgraph_get();obj=boots.evaluated_get(deps);mesh=obj.to_mesh()
                floor=min(floor,min((obj.matrix_world@v.co).z for v in mesh.vertices));obj.to_mesh_clear()
            shift=(.003-floor)/rig.scale.z
            for fc in action.fcurves:
                if fc.data_path=='pose.bones["Root"].location' and fc.array_index==2:
                    for key in fc.keyframe_points:key.co.y+=shift
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        reports[clip]={'source':'CMU '+file,'sourceFrames':[start,end],'duration':duration,'loop':loop,'rootMotion':'Horizontal travel removed in pelvis rest basis','headingCorrectionRadians':-heading,'minimumBootHeightBeforeGrounding':floor}
        print('[MOCAP_CLIP]',identity,clip,json.dumps(reports[clip]),flush=True)
    for raw in sources.values():bpy.data.actions.remove(raw)
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(destination),relative_remap=False)
    if not draft:
        path=ROOT/'src/cocos/assets/resources/actors'/identity/'manifest.json';manifest=json.loads(path.read_text())
        manifest['motionCapture']={'tool':'BVH Retargeter 4.4.0','toolLicense':'GPL-2.0-or-later','dataset':'CMU Graphics Lab / cgspeed MotionBuilder BVH','clips':reports}
        for clip,info in reports.items():manifest['clips'][clip]={'name':clip,'duration':info['duration'],'loop':info['loop'],'holdFinalPose':False}
        path.write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':
    if '--ual' in sys.argv:
        names=sys.argv[sys.argv.index('--character')+1].split(',') if '--character' in sys.argv else ['raphael']
        for name in names:prepare_library(name,'--production' in sys.argv)
    elif '--prepare' in sys.argv:
        names=sys.argv[sys.argv.index('--character')+1].split(',') if '--character' in sys.argv else ['raphael']
        for name in names:prepare(name,'--production' not in sys.argv)
    else:
        names=sys.argv[sys.argv.index('--files')+1].split(',') if '--files' in sys.argv else ['16_36']
        for name in names:retarget('raphael',name,name)
