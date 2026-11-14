"""Correct only dodge/death ground contact on the editable shared-rig actions."""
from pathlib import Path
import bpy,math,json,os,sys
from mathutils import Vector,Quaternion
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'));OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer'];report={}
selected=sys.argv[sys.argv.index('--character')+1].split(',') if '--character' in sys.argv else IDS
for identity in selected:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');root=rig.pose.bones['Root'];boots=bpy.data.objects.get(identity+'_libraryboots_surface') or bpy.data.objects[identity+'_belt_surface']
    feet=[v.index for v in boots.data.vertices if v.co.z<.30]
    gain=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()@Vector((0,0,1))).z
    assert gain>.1
    def activate(action,frame):
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        bpy.context.scene.frame_set(math.floor(frame),subframe=frame%1);bpy.context.view_layer.update()
    def ground():
        ev=boots.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();value=min((boots.matrix_world@mesh.vertices[i].co).z for i in feet);ev.to_mesh_clear();return value
    result={}
    for name in ['dodge','death']:
        action=bpy.data.actions[name];start,end=map(float,action.frame_range)
        frames=sorted(set([start,end]+[float(f) for f in range(math.ceil(start),math.floor(end)+1)]))
        z_curve=next(fc for fc in action.fcurves if fc.data_path=='pose.bones["Root"].location' and fc.array_index==2)
        original_z={f:z_curve.evaluate(f) for f in frames}
        old_min=1e6
        for f in frames:activate(action,f);old_min=min(old_min,ground())
        if name=='death' and '--preserve-pose' not in sys.argv:
            for fc in list(action.fcurves):
                if any(fc.data_path==f'pose.bones["{bone}"].rotation_quaternion' for bone in ['thigh_l','thigh_r','calf_l','calf_r']):action.fcurves.remove(fc)
            for bone in ['thigh_l','thigh_r','calf_l','calf_r']:
                pb=rig.pose.bones[bone];pb.rotation_quaternion=Quaternion()
                for f in [start,end]:pb.keyframe_insert('rotation_quaternion',frame=f)
            rest=root.bone.matrix_local.to_quaternion()
            for f in frames:
                t=(f-start)/(end-start);fall=min(1,t/.72);ease=fall*fall*(3-2*fall)
                root.rotation_quaternion=rest.inverted()@Quaternion((1,0,0),math.pi/2*ease)@rest
                root.keyframe_insert('rotation_quaternion',frame=f)
        corrected={}
        for f in frames:
            activate(action,f);root.location.z=original_z[f];bpy.context.view_layer.update();lowest=ground()
            corrected[f]=original_z[f]+max(0,.004-lowest)/gain
        # Replace fractional authoring samples on Z, avoiding an old lower key
        # between the corrected 30fps samples. Keep the exact original range.
        action.fcurves.remove(z_curve)
        for f,z in corrected.items():root.location.z=z;root.keyframe_insert('location',index=2,frame=f)
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
        new_min=1e6
        for f in frames:activate(action,f);new_min=min(new_min,ground())
        activate(action,end);result[name]={'minimumBefore':old_min,'minimumAfter':new_min,'finalGround':ground(),'frames':len(frames),'durationPreserved':list(action.frame_range)==[start,end]}
        assert new_min>-.0001,(identity,name,new_min)
    activate(bpy.data.actions['idle'],1);bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{identity}.blend'),relative_remap=False)
    report[identity]=result;print('[GROUND_FIXED]',identity,json.dumps(result),flush=True)
(OUT/'foot-contact-report.json').write_text(json.dumps(report,indent=2))
