"""Assemble authored CC0 Native65 motions; production actors are never written.

Run with Blender 4.5: blender -b --python this_file -- [--native-only]
Default builds all 11, requiring the official prop-stage bow.fbx first.
Native clips retain their original bone-local pose basis and target rest data.
The only custom work is library selection, temporal assembly, baking and QA.
"""
from pathlib import Path
import bpy, json, math, hashlib, sys, argparse
from mathutils import Vector,Matrix

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/.tmp/native-production/animation'
UAL1=ROOT/'src/.tools/universal-animation-library-standard/Universal Animation Library[Standard]/Unreal-Godot/UAL1_Standard.glb'
UAL2=ROOT/'src/.tools/quaternius-ready-kits/universal-animation-library-2-standard/Universal Animation Library 2[Standard]/Unreal-Godot/UAL2_Standard.glb'
KAY=ROOT/'src/.tools/research-animation-kaykit/free-1.1/KayKit_Character_Animations_1.1/Animations/gltf/Rig_Medium/Rig_Medium_CombatRanged.glb'
CANONICAL=['idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact']
FPS=30

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def assign(rig,action):
    rig.animation_data_create();rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    for track in list(rig.animation_data.nla_tracks):rig.animation_data.nla_tracks.remove(track)

def reset(rig):
    for p in rig.pose.bones:
        p.rotation_mode='QUATERNION';p.matrix_basis.identity()

def imported(path):
    old=set(bpy.data.objects);actions=set(bpy.data.actions)
    bpy.ops.import_scene.gltf(filepath=str(path))
    return list(set(bpy.data.objects)-old),list(set(bpy.data.actions)-actions)

def time(frame):bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame));bpy.context.view_layer.update()
def pose(rig):return {p.name:(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())for p in rig.pose.bones}

def native_sources():
    actions={};reference=None;meshes=[]
    for label,path in [('UAL1',UAL1),('UAL2',UAL2)]:
        objects,new=imported(path);rig=next(o for o in objects if o.type=='ARMATURE')
        for action in new:
            name=action.name.split('|')[-1]
            if name.endswith('.001'):name=name[:-4]
            action.name=label+'__'+name;action.use_fake_user=True;actions[(label,name)]=action
        if reference is None:
            reference=rig;reference.name='Native65_ActionRig'
            meshes=[o for o in objects if o.type=='MESH']
        else:
            assert list(reference.data.bones.keys())==list(rig.data.bones.keys())
            delta=max(abs(a-b)for p in reference.data.bones for r1,r2 in zip(p.matrix_local,rig.data.bones[p.name].matrix_local)for a,b in zip(r1,r2))
            assert delta<1e-6,('UAL rest mismatch',delta)
            for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    assert len(reference.data.bones)==65 and 'Head'in reference.data.bones
    return reference,meshes,actions

def full(actions,lib,name):
    a=actions[(lib,name)];return {'library':lib,'clip':name,'start':float(a.frame_range[0]),'end':float(a.frame_range[1])}

def segments_for(actions):
    # These are authored motion segments, not newly synthesized character poses.
    sword=[{'library':'UAL2','clip':'Sword_Regular_A','start':4.,'end':13.},
           {'library':'UAL2','clip':'Sword_Regular_A_Rec','start':0.,'end':4.2}]
    # Enter is a short anticipation, Shoot provides the cue and native follow-through.
    # Runtime .2s cue/.7s action is declared for data-driven sampling, not 3.5x speedup.
    spell=[full(actions,'UAL1','Spell_Simple_Enter'),full(actions,'UAL1','Spell_Simple_Shoot'),full(actions,'UAL1','Spell_Simple_Exit')]
    return {
      'idle':[full(actions,'UAL1','Idle_Loop')],
      'walk':[full(actions,'UAL1','Walk_Loop')],
      'run':[full(actions,'UAL1','Jog_Fwd_Loop')],
      'attack_sword':sword,
      'attack_staff':spell,
      'spell':spell,
      'dodge':[full(actions,'UAL1','Roll')],
      'hit':[full(actions,'UAL1','Hit_Chest')],
      'death':[full(actions,'UAL1','Death01')],
      'interact':[full(actions,'UAL1','Interact')],
    }

def sample_segments(rig,actions,segments):
    duration=sum((s['end']-s['start'])/FPS for s in segments)
    frames=[float(i)for i in range(math.floor(duration*FPS)+1)]
    if abs(frames[-1]-duration*FPS)>1e-5:frames.append(duration*FPS)
    samples=[]
    for frame in frames:
        remain=frame
        selected=segments[-1];source_frame=selected['end']
        for segment in segments:
            length=segment['end']-segment['start']
            if remain<=length+1e-6:
                selected=segment;source_frame=segment['start']+remain;break
            remain-=length
        reset(rig);assign(rig,actions[(selected['library'],selected['clip'])]);time(source_frame)
        samples.append((frame,pose(rig)))
    return samples,duration

def bake(rig,name,samples):
    previous=bpy.data.actions.get(name)
    if previous:bpy.data.actions.remove(previous)
    action=bpy.data.actions.new(name);action.use_fake_user=True;assign(rig,action)
    previous_rotations={}
    for frame,values in samples:
        for bn,(loc,rot,scale)in values.items():
            # q and -q represent the same authored pose. Keep each curve on one
            # quaternion hemisphere before component interpolation across joins.
            rot=rot.copy();rot.normalize()
            if bn in previous_rotations:rot.make_compatible(previous_rotations[bn])
            previous_rotations[bn]=rot.copy()
            p=rig.pose.bones[bn];p.rotation_mode='QUATERNION';p.location=loc;p.rotation_quaternion=rot;p.scale=scale
            for channel in ['location','rotation_quaternion','scale']:p.keyframe_insert(channel,frame=frame)
    for f in action.fcurves:
        for k in f.keyframe_points:k.interpolation='LINEAR'
    return action

def floor_report(rig,meshes,action):
    assign(rig,action);rows=[]
    groups={}
    for o in meshes:
        indices={g.index for g in o.vertex_groups if g.name in ['foot_l','ball_l','ball_leaf_l','foot_r','ball_r','ball_leaf_r']}
        groups[o.name]=[v.index for v in o.data.vertices if sum(g.weight for g in v.groups if g.group in indices)>.35]
    start,end=action.frame_range
    for f in range(math.ceil(start),math.floor(end)+1):
        time(f);body=[];feet=[]
        for o in meshes:
            ev=o.evaluated_get(bpy.context.evaluated_depsgraph_get());m=ev.to_mesh()
            used={i for poly in m.polygons for i in poly.vertices}
            body.extend((ev.matrix_world@m.vertices[i].co).z for i in used)
            feet.extend((ev.matrix_world@m.vertices[i].co).z for i in groups[o.name]);ev.to_mesh_clear()
        rows.append({'frame':f,'bodyMinZ':min(body),'footMinZ':min(feet)if feet else None})
    return {'referenceOnly':True,'perCharacterSoleAdjustmentRequired':True,'minBodyZ':min(x['bodyMinZ']for x in rows),'minFootZ':min(x['footMinZ']for x in rows if x['footMinZ']is not None),'maxFootMinZ':max(x['footMinZ']for x in rows if x['footMinZ']is not None),'samples':rows}

def retarget_setup():
    """Register the already vendored upstream solver; only rig maps are adapted."""
    import importlib.util
    spec=importlib.util.spec_from_file_location('_native_bvh_bridge',ROOT/'tools/model-pipeline/cocos_mocap_retarget.py')
    bridge=importlib.util.module_from_spec(spec);spec.loader.exec_module(bridge);bridge.register()
    from retarget_bvh.utils import BD
    from retarget_bvh.source import CSourceInfo
    from retarget_bvh.target import CTargetInfo
    from bpy.props import EnumProperty
    source={'name':'KayKit Medium Original','fingerprint':['handslot.l','wrist.r'],'bones':{'hips':'hips','spine':'spine','chest':'chest','head':'head'}}
    for side,cap in [('l','L'),('r','R')]:
        for src,dst in [('upperarm','upper_arm'),('lowerarm','forearm'),('hand','hand'),('upperleg','thigh'),('lowerleg','shin'),('foot','foot'),('toes','toe')]:source['bones'][src+'.'+side]=dst+'.'+cap
    source_path=OUT/'kaykit-source-rig-map.json';source_path.write_text(json.dumps(source,indent=2))
    target=json.loads((ROOT/'src/.tools/retarget_bvh-version_4_4_0/known_rigs/unreal.json').read_text())
    target['name']='Native65 Original';target['bones']['Head']=target['bones'].pop('head')
    target_path=OUT/'native65-target-rig-map.json';target_path.write_text(json.dumps(target,indent=2))
    scn=bpy.context.scene;s=CSourceInfo(scn,'');s.readFile(str(source_path));BD.sourceInfos[s.name]=s
    t=CTargetInfo(scn,'');t.readFile(str(target_path));BD.targetInfos[t.name]=t
    bpy.types.Scene.McpSourceRig=EnumProperty(items=[(k,k,k)for k in BD.sourceInfos],name='Source rig')
    bpy.types.Scene.McpTargetRig=EnumProperty(items=[(k,k,k)for k in BD.targetInfos],name='Target rig')
    scn.McpSourceRig=s.name;scn.McpTargetRig=t.name;scn.McpSourceTPose='Default';scn.McpTargetTPose='Default'
    return BD,s,t

def bow_probe():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'native65-actions.blend'))
    rig=bpy.data.objects['Native65_ActionRig'];original={b.name:b.matrix_local.copy()for b in rig.data.bones}
    meshes=[o for o in bpy.data.objects if o.type=='MESH'and any(m.type=='ARMATURE'and m.object==rig for m in o.modifiers)]
    BD,s,t=retarget_setup();objects,actions=imported(KAY)
    source=next(o for o in objects if o.type=='ARMATURE');source.name='KayKit_OriginalSource'
    for o in objects:
        if o.type=='MESH':o.hide_render=True
    action=next(a for a in actions if a.name.split('|')[-1].split('.')[0]=='Ranged_Bow_Draw')
    source.animation_data.action=action.copy()
    if source.animation_data.action.slots:source.animation_data.action_slot=source.animation_data.action.slots[0]
    first,last=source.animation_data.action.frame_range
    # The solver owns calibration frame zero. Shift all original keys by one;
    # this retains the author's real frame-zero pose instead of deleting it.
    for fc in source.animation_data.action.fcurves:
        for k in fc.keyframe_points:k.co.x+=1;k.handle_left.x+=1;k.handle_right.x+=1
    reset(rig);bpy.ops.object.select_all(action='DESELECT');source.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
    result=bpy.ops.mcp.retarget_selected_to_active(useAutoSource=False,useAutoTarget=False,useAutoScale=True,useCenterAnimation=False,useAllFrames=False,startFrame=1,endFrame=round(last+1))
    assert result=={'FINISHED'},result
    action=rig.animation_data.action;action.name='BOW_PROBE__Draw';action.use_fake_user=True
    delta=max(abs(a-b)for name,m in original.items()for x,y in zip(m,rig.data.bones[name].matrix_local)for a,b in zip(x,y))
    report={'solver':'Unmodified vendored BVH Retargeter 4.4.0','retargetResult':list(result),'targetRestMaxDelta':delta,'sourceOriginalFrames':[first,last],'outputFrames':list(action.frame_range),'sourceFirstFrameRetainedAt':1,'floor':floor_report(rig,meshes,action)}
    (OUT/'bow-probe-report.json').write_text(json.dumps(report,indent=2))
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'bow-probe.blend'),relative_remap=False)
    print('[BOW_PROBE]',json.dumps({k:v for k,v in report.items()if k!='floor'}),flush=True)

def complete_bow():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'native65-actions.blend'))
    rig=bpy.data.objects['Native65_ActionRig'];rest={b.name:b.matrix_local.copy()for b in rig.data.bones}
    meshes=[o for o in bpy.data.objects if o.type=='MESH'and any(m.type=='ARMATURE'and m.object==rig for m in o.modifiers)]
    # Reuse the authored Native65 finger pose; KayKit has no finger joints.
    reset(rig);assign(rig,bpy.data.actions['UAL1__Sword_Idle']);time(0)
    fingers={p.name:p.rotation_quaternion.copy()for p in rig.pose.bones if any(x in p.name for x in ['index_','middle_','ring_','pinky_','thumb_'])}
    BD,source_info,target_info=retarget_setup();objects,new=imported(KAY);source=next(o for o in objects if o.type=='ARMATURE');source.name='KayKit_AuthorReference'
    raw={a.name.split('|')[-1].removesuffix('.001'):a for a in new}
    for o in objects:
        if o.type=='MESH':o.hide_render=True;o.hide_viewport=True
    source.animation_data.action=None;reset(source);source_info.addManualBones(source)
    from retarget_bvh.t_pose import autoTPose
    autoTPose(bpy.context,source);bpy.context.view_layer.update()
    source_tp={s:source.pose.bones['hand.'+s].matrix.to_quaternion()for s in ['l','r']}
    source_slot_rest={s:source.data.bones['hand.'+s].matrix_local.inverted()@source.data.bones['handslot.'+s].matrix_local for s in ['l','r']}
    output={};calibration={};ground=[]
    for raw_name in ['Ranged_Bow_Draw','Ranged_Bow_Release','Ranged_Bow_Aiming_Idle']:
        original=raw[raw_name];working=source.copy();working.data=source.data.copy();bpy.context.collection.objects.link(working);working.name='KayKit_SolverWork'
        work_action=original.copy();assign(working,work_action)
        for fc in work_action.fcurves:
            for k in fc.keyframe_points:k.co.x+=1;k.handle_left.x+=1;k.handle_right.x+=1
        reset(rig);bpy.ops.object.select_all(action='DESELECT');working.select_set(True);rig.select_set(True);bpy.context.view_layer.objects.active=rig
        last=round(original.frame_range[1])
        result=bpy.ops.mcp.retarget_selected_to_active(useAutoSource=False,useAutoTarget=False,useAutoScale=True,useCenterAnimation=False,useAllFrames=False,startFrame=1,endFrame=last+1)
        assert result=={'FINISHED'},(raw_name,result)
        retargeted=rig.animation_data.action;retargeted.name='RETARGET__'+raw_name;retargeted.use_fake_user=True
        assign(rig,retargeted);time(0)
        corr={s:rig.pose.bones['hand_'+s].matrix.to_quaternion().inverted()@source_tp[s]for s in ['l','r']}
        calibration[raw_name]={s:list(corr[s])for s in corr}
        frames=[]
        for frame in range(last+1):
            assign(rig,retargeted);time(frame+1)
            values=pose(rig)
            for bn,q in fingers.items():values[bn]=(values[bn][0],q.copy(),values[bn][2])
            assign(source,original);time(frame)
            slots={s:source.pose.bones['hand.'+s].matrix.inverted()@source.pose.bones['handslot.'+s].matrix for s in ['l','r']}
            frames.append({'body':values,'slots':slots,'correction':corr})
        output[raw_name]=frames
        bpy.data.objects.remove(working,do_unlink=True)
        print('[BOW_RETARGET_READY]',raw_name,last+1,flush=True)
    # Helpers are rigid attachment adapters, not new skin/IK bones. Parent-relative
    # rest positions use actual original Native65 knuckles, then preserve every
    # authored socket rotation/translation delta in that calibrated frame.
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    helper_records={}
    for side,name in [('l','attach_bow_l'),('r','attach_arrow_r')]:
        hand=rig.data.edit_bones['hand_'+side];grip=(rig.data.edit_bones['index_01_'+side].head+rig.data.edit_bones['pinky_01_'+side].head)*.5
        c=output['Ranged_Bow_Draw'][0]['correction'][side]
        local=Matrix.LocRotScale(hand.matrix.inverted()@grip,c@source_slot_rest[side].to_quaternion(),Vector((1,1,1)))
        e=rig.data.edit_bones.get(name)or rig.data.edit_bones.new(name);e.parent=hand;e.use_deform=False;e.matrix=hand.matrix@local;e.length=.055
        helper_records[side]={'bone':name,'parent':'hand_'+side,'referenceParentRelativeRest':[list(row)for row in local],'referenceHandRest':[list(row)for row in rest['hand_'+side]],'sourceSlotRest':[list(row)for row in source_slot_rest[side]],'sourceLocalTranslationScale':rig.data.edit_bones['hand_'+side].length/source.data.bones['hand.'+side].length,'geometryAnchor':'Original index_01/pinky_01 head midpoint; no new finger pose or solver'}
    bpy.ops.object.mode_set(mode='OBJECT')
    # EditBone.matrix assignment can normalize its bone frame. Publish the
    # actual object-mode rest, which is what appended Actions are relative to.
    for side,record in helper_records.items():
        hand=rig.data.bones[record['parent']];helper=rig.data.bones[record['bone']]
        record['referenceParentRelativeRest']=[list(row)for row in hand.matrix_local.inverted()@helper.matrix_local]
        record['referenceHelperRest']=[list(row)for row in helper.matrix_local]
        record['restContract']='Actual object-mode Bone.matrix_local read-back; never a pre-normalization prediction'
    timeline=[('Ranged_Bow_Draw',f)for f in range(41)]+[('Ranged_Bow_Release',f)for f in range(1,10)]
    samples=[];slot_records=[]
    for frame,(clip,sf)in enumerate(timeline):
        row=output[clip][sf];values=row['body']
        # Set a temporary pose on the target with no action evaluation before
        # asking Blender to convert rigid helper matrices into local basis.
        rig.animation_data.action=None
        for bn,(loc,rot,scale)in values.items():
            if bn not in rig.pose.bones:continue
            p=rig.pose.bones[bn];p.location=loc;p.rotation_quaternion=rot;p.scale=scale
        bpy.context.view_layer.update()
        for side in ['l','r']:
            record=helper_records[side];raw_slot=row['slots'][side];sr=source_slot_rest[side];c=row['correction'][side]
            anchor=Vector([r[3]for r in record['referenceParentRelativeRest'][:3]])
            local=Matrix.LocRotScale(anchor+c@(raw_slot.translation-sr.translation)*record['sourceLocalTranslationScale'],c@raw_slot.to_quaternion(),Vector((1,1,1)))
            helper=rig.pose.bones[record['bone']];helper.rotation_mode='QUATERNION';helper.matrix=rig.pose.bones[record['parent']].matrix@local
            bpy.context.view_layer.update();values[helper.name]=(helper.location.copy(),helper.rotation_quaternion.copy(),helper.scale.copy())
        samples.append((float(frame),values));slot_records.append({'frame':frame,'source':clip,'sourceFrame':sf})
    action=bake(rig,'attack_bow',samples)
    # A thigh-scaled short source torso can lower the transferred pelvis. A
    # single vertical root translation removes the measured penetration only.
    before=floor_report(rig,meshes,action);root=rig.pose.bones['root'];up=(rig.matrix_world.to_3x3()@root.bone.matrix_local.to_3x3()).inverted()@Vector((0,0,.003-before['minFootZ']))
    for frame,values in samples:
        loc,rot,scale=values['root'];values['root']=(loc+up,rot,scale)
    action=bake(rig,'attack_bow',samples)
    after=floor_report(rig,meshes,action)
    delta=max(abs(a-b)for name,m in rest.items()for x,y in zip(m,rig.data.bones[name].matrix_local)for a,b in zip(x,y));assert delta<1e-6
    manifest=json.loads((OUT/'manifest.json').read_text());manifest['status']='CANONICAL_11_READY_FOR_POSE_REVIEW';manifest['availableActions']=CANONICAL
    manifest['clips']['attack_bow']={'name':'attack_bow','fps':30,'duration':49/30,'startFrame':0,'endFrame':49,'loop':False,'holdFrame':40,'holdFraction':40/49,'releaseSourceFrames':[0,9],'sourceSegments':[{'library':'KayKitFree1.1','clip':'Ranged_Bow_Draw','start':0,'end':40},{'library':'KayKitFree1.1','clip':'Ranged_Bow_Release','start':0,'end':9}],'sourceFirstFramePreserved':True,'solver':'BVH Retargeter 4.4.0, unchanged; source/target mapping configs alongside output','targetRestMaxDelta':delta,'referenceFloorCorrectionWorldZ':float(.003-before['minFootZ']),'floor':after,'fingerPose':'Original UAL1 Sword_Idle frame 0; KayKit has no finger joints','actionSlots':[{'identifier':s.identifier,'type':s.target_id_type,'handle':s.handle}for s in action.slots]}
    manifest['attachments']={'status':'AUTHORED_DYNAMIC_SLOT_BAKED','skinBones':65,'totalBonesIncludingNondeformHelpers':len(rig.data.bones),'left':helper_records['l'],'right':helper_records['r'],'installPolicy':'Create nondeform helper with target hand rest @ referenceParentRelativeRest; recompute anchor from original target knuckles if body proportions differ. Preserve parent-relative animation deltas. Do not copy reference world positions.','weaponFramePolicy':'Helpers retain authored KayKit socket axes. Apply prop authorToExport rotation inverse only; do not cancel its baked physical length.','timeline':slot_records}
    (OUT/'bow-author-socket-calibration.json').write_text(json.dumps(calibration,indent=2))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');assign(rig,bpy.data.actions['attack_bow']);time(40)
    for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native65-actions.blend'),relative_remap=False)
    print('[BOW_CANONICAL_READY]',49/30,40/49,delta,after['minFootZ'],after['maxFootMinZ'],flush=True)

def render_review(blend_path=None,rig_name='Native65_ActionRig',action_override=None,prefix='qa'):
    bpy.ops.wm.open_mainfile(filepath=str(blend_path or OUT/'native65-actions.blend'))
    rig=bpy.data.objects[rig_name];scene=bpy.context.scene
    props={}
    for name in ['bow','arrow','sword','staff']:
        previous=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(ROOT/'src/.tmp/native-production/props'/(name+'.fbx')))
        added=list(set(bpy.data.objects)-previous);meshes=[o for o in added if o.type=='MESH']
        for o in added:o.hide_render=True
        props[name]=meshes
        for o in meshes:print('[PROP_IMPORTED]',name,o.name,list(o.rotation_euler),list(o.scale),list(o.dimensions),flush=True)
    def parent_prop(obj,bone,rotation=None):
        imported_matrix=obj.matrix_world.copy()
        obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone
        obj.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones[bone].length,0))
        # FBX round-trip objects carry the standard .01 unit conversion and
        # axis basis. Keep it; replacing this by a unit rotation makes 100m props.
        obj.matrix_basis=(rotation or Matrix.Identity(4))@imported_matrix
    for name,bone in [('bow','attach_bow_l'),('arrow','attach_arrow_r')]:
        # FBX->Blender already restores bow +Z; only the held arrow needs its
        # authored +Z axis turned into the slot's forward +Y axis.
        for o in props[name]:parent_prop(o,bone,Matrix.Rotation(-math.pi/2,4,'X')if name=='arrow'else Matrix.Rotation(math.pi,4,'Z'))
    for name in ['sword','staff']:
        for o in props[name]:parent_prop(o,'attach_arrow_r')
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.015));plane=bpy.context.object;plane.name='QA_StudioFloor'
    mat=bpy.data.materials.new('QA_NeutralFloor');mat.diffuse_color=(.16,.17,.18,1);plane.data.materials.append(mat)
    world=scene.world or bpy.data.worlds.new('QA_World');scene.world=world;world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.22,.23,.25,1);world.node_tree.nodes['Background'].inputs[1].default_value=.45
    for name,location,power,size in [('QA_Key',(3,-4,6),800,5),('QA_Fill',(-3,-2,3),550,4)]:
        data=bpy.data.lights.new(name,'AREA');data.energy=power;data.shape='DISK';data.size=size;n=bpy.data.objects.new(name,data);scene.collection.objects.link(n);n.location=location;n.rotation_euler=(Vector((0,0,.9))-n.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('QA_Camera');camera=bpy.data.objects.new('QA_Camera',data);scene.collection.objects.link(camera);camera.location=(3,-5,2.8);camera.rotation_euler=(Vector((0,-.1,1.0))-camera.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=3.4;scene.camera=camera
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.render.resolution_x=700;scene.render.resolution_y=700;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX'
    records=[]
    cases=[('attack_bow',[20,40,43])]if action_override else [('attack_bow',[0,20,40,43,49]),('attack_sword',[0,3.6,13.2]),('attack_staff',[0,16,22,31,44])]
    if action_override:camera.location=(4,1,2.7);camera.rotation_euler=(Vector((0,-.1,1.0))-camera.location).to_track_quat('-Z','Y').to_euler()
    for name,frames in cases:
        for key,objects in props.items():
            for o in objects:o.hide_render=key not in (['bow','arrow']if name=='attack_bow'else ['sword']if name=='attack_sword'else ['staff'])
        assign(rig,bpy.data.actions[action_override or name])
        for frame in frames:
            time(frame)
            if name=='attack_bow':
                for o in props['bow']:
                    if o.data.shape_keys:
                        for key in o.data.shape_keys.key_blocks:
                            if key.name!='Basis':key.value=min(1,frame/40)if frame<=40 else max(0,1-(frame-40)/3)
            file=prefix+'-'+name+'-'+str(frame).replace('.','_')+'.png';scene.render.filepath=str(OUT/file);bpy.ops.render.render(write_still=True)
            rec={'clip':name,'frame':frame,'image':file,'hands':{s:list((rig.matrix_world@rig.pose.bones['hand_'+s].matrix).translation)for s in ['l','r']}}
            if name=='attack_bow':rec['attachments']={s:list((rig.matrix_world@rig.pose.bones['attach_'+('bow_l'if s=='l'else 'arrow_r')].matrix).translation)for s in ['l','r']}
            records.append(rec)
    (OUT/(prefix+'-pose-review.json'if prefix!='qa'else'pose-review.json')).write_text(json.dumps({'scope':'Offline authored motion + actual exported FBX props; neutral studio QA, not gameplay proof','records':records},indent=2))

def bake_bow_contact_for_rig(rig,action,bow_fbx=None,output_name=None):
    """Reusable character-stage adapter. It preserves rest/weights and uses
    Blender's official IK/CopyRotation solver for original-body proportions.
    Install the two nondeform helpers first; returns (bakedAction, metrics).
    """
    # The canonical helper rest must be the read-back Bone.matrix_local, not
    # an edit-mode construction guess. Preserve each target's knuckle anchor.
    contract=json.loads((OUT/'manifest.json').read_text())['attachments'];original={b.name:b.matrix_local.copy()for b in rig.data.bones if b.name not in ['attach_bow_l','attach_arrow_r']}
    wanted={}
    for side in ['left','right']:
        record=contract[side];hand=rig.data.bones[record['parent']];helper=rig.data.bones[record['bone']]
        matrix=hand.matrix_local@Matrix(record['referenceParentRelativeRest']);matrix.translation=helper.head_local.copy();wanted[record['bone']]=matrix
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);bpy.context.view_layer.objects.active=rig;bpy.ops.object.mode_set(mode='EDIT')
    for name,matrix in wanted.items():
        e=rig.data.edit_bones[name];length=e.length;e.matrix=matrix;e.length=length
    bpy.ops.object.mode_set(mode='OBJECT')
    assert max(abs(a-b)for n,m in original.items()for x,y in zip(m,rig.data.bones[n].matrix_local)for a,b in zip(x,y))<1e-6
    # The original native Sword_Idle off hand is relaxed. Reuse the authored
    # gripping hand with Blender's own mirrored-pose operation for the bow hand.
    left_grip={};auto_key=bpy.context.scene.tool_settings.use_keyframe_insert_auto
    bpy.context.scene.tool_settings.use_keyframe_insert_auto=False
    grip_source=bpy.data.actions.get('idle')
    if grip_source:
        reset(rig);assign(rig,grip_source);time(0);bpy.ops.object.mode_set(mode='POSE');bpy.ops.pose.select_all(action='DESELECT')
        for p in rig.pose.bones:
            if p.name.endswith('_r')and any(t in p.name for t in ['index_','middle_','ring_','pinky_','thumb_']):p.bone.select=True
        bpy.ops.pose.copy();bpy.ops.pose.paste(flipped=True)
        left_grip={p.name:p.rotation_quaternion.copy()for p in rig.pose.bones if p.name.endswith('_l')and any(t in p.name for t in ['index_','middle_','ring_','pinky_','thumb_'])}
        bpy.ops.object.mode_set(mode='OBJECT')
    bpy.context.scene.tool_settings.use_keyframe_insert_auto=auto_key
    bow_fbx=Path(bow_fbx or ROOT/'src/.tmp/native-production/props/bow.fbx')
    output_name=output_name or action.name
    old=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(bow_fbx))
    added=list(set(bpy.data.objects)-old);bow=next(o for o in added if o.type=='MESH');matrix=bow.matrix_world.copy()
    bow.parent=rig;bow.parent_type='BONE';bow.parent_bone='attach_bow_l';bow.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['attach_bow_l'].length,0));bow.matrix_basis=Matrix.Rotation(math.pi,4,'Z')@matrix
    basis=bow.data.shape_keys.key_blocks[0];draw=next(k for k in bow.data.shape_keys.key_blocks if k.name!='Basis')
    delta=[(a.co-b.co).length for a,b in zip(draw.data,basis.data)];largest=max(delta);indices=[i for i,v in enumerate(delta)if v>=largest*.999]
    goal=bpy.data.objects.new('TEMP_NativeBowWristGoal',None);orient=bpy.data.objects.new('TEMP_NativeBowHandOrientation',None)
    for o in [goal,orient]:bpy.context.collection.objects.link(o)
    ik=rig.pose.bones['lowerarm_r'].constraints.new('IK');ik.name='NativeBlenderBowContact';ik.target=goal;ik.chain_count=3;ik.use_stretch=False
    copy=rig.pose.bones['hand_r'].constraints.new('COPY_ROTATION');copy.target=orient;copy.owner_space='WORLD';copy.target_space='WORLD';copy.mix_mode='REPLACE'
    samples=[];contacts=[]
    for frame in range(50):
        ik.influence=0;copy.influence=0;assign(rig,action);time(frame)
        for name,q in left_grip.items():rig.pose.bones[name].rotation_quaternion=q
        draw.value=min(1,frame/40)if frame<=40 else max(0,1-(frame-40)/3);bpy.context.view_layer.update()
        nock=bow.matrix_world@(sum((basis.data[i].co.lerp(draw.data[i].co,draw.value)for i in indices),Vector())/len(indices))
        hand=rig.matrix_world@rig.pose.bones['hand_r'].matrix;slot=rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix
        orient.matrix_world=Matrix.LocRotScale(hand.translation,hand.to_quaternion(),Vector((1,1,1)));goal.location=nock-(slot.translation-hand.translation)
        weight=min(1,max(0,(frame-10)/10))if frame<=40 else max(0,1-(frame-40)/3);ik.influence=weight;copy.influence=weight;bpy.context.view_layer.update()
        values=pose(rig);solved={n:rig.pose.bones[n].matrix.copy()for n in ['clavicle_r','upperarm_r','lowerarm_r','hand_r']}
        constrained_hand=(rig.matrix_world@rig.pose.bones['hand_r'].matrix).translation.copy();constrained_grip=(rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix).translation.copy()
        ik.influence=0;copy.influence=0;bpy.context.view_layer.update()
        for name,m in solved.items():
            rig.pose.bones[name].matrix=m;bpy.context.view_layer.update();p=rig.pose.bones[name];values[name]=(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())
        grip=(rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix).translation
        contacts.append({'frame':frame,'ikInfluence':weight,'draw':draw.value,'gripToNockMetres':(grip-nock).length,'nock':list(nock),'wristGoal':list(goal.location),'constrainedHand':list(constrained_hand),'constrainedGrip':list(constrained_grip),'bakedGrip':list(grip)})
        samples.append((float(frame),values))
    rig.pose.bones['lowerarm_r'].constraints.remove(ik);rig.pose.bones['hand_r'].constraints.remove(copy)
    result=bake(rig,output_name,samples)
    for o in added+[goal,orient]:bpy.data.objects.remove(o,do_unlink=True)
    return result,{'solver':'Blender native IK 3 bones including clavicle, no stretch; CopyRotation; no custom solver','leftGripPoseSource':'Original native idle/Sword_Idle right fingers mirrored by Blender pose.copy/pose.paste(flipped=True)','leftGripBoneCount':len(left_grip),'holdFrame':40,'holdContactMetres':contacts[40]['gripToNockMetres'],'fullContactWindow':[20,40],'fullContactMaxMetres':max(c['gripToNockMetres']for c in contacts if 20<=c['frame']<=40),'contacts':contacts}

def finalize_contact():
    """Use Blender's maintained IK/CopyRotation constraints, then bake once.

    This is an authored upper/lower-body mask plus rigid weapon-contact adapter;
    no custom limb solver or new character pose is implemented here.
    """
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'native65-actions.blend'))
    rig=bpy.data.objects['Native65_ActionRig'];manifest=json.loads((OUT/'manifest.json').read_text())
    sources={(lib,name):bpy.data.actions[lib+'__'+name]for lib,path in [('UAL1',UAL1),('UAL2',UAL2)]for name in [a.name[len(lib)+2:]for a in bpy.data.actions if a.name.startswith(lib+'__')]}
    meshes=[o for o in bpy.data.objects if o.type=='MESH'and any(m.type=='ARMATURE'and m.object==rig for m in o.modifiers)]
    for name,segments in segments_for(sources).items():
        samples,duration=sample_segments(rig,sources,segments);action=bake(rig,name,samples)
        manifest['clips'][name]['quaternionHemisphereContinuous']=True;manifest['clips'][name]['floor']=floor_report(rig,meshes,action)
        manifest['clips'][name]['actionSlots']=[{'identifier':s.identifier,'type':s.target_id_type,'handle':s.handle}for s in action.slots]
    reset(rig);assign(rig,sources[('UAL1','Idle_Loop')]);time(0);base=pose(rig)
    lower={'root','pelvis'}|{b for b in base if b.startswith(('thigh_','calf_','foot_','ball_'))}
    old=bpy.data.actions['attack_bow'];samples=[]
    for frame in range(50):
        reset(rig);assign(rig,old);time(frame);values=pose(rig)
        for bn in lower:values[bn]=tuple(v.copy()for v in base[bn])
        samples.append((float(frame),values))
    action=bake(rig,'attack_bow',samples)
    measured=floor_report(rig,meshes,action)
    up=(rig.matrix_world.to_3x3()@rig.data.bones['root'].matrix_local.to_3x3()).inverted()@Vector((0,0,.003-measured['minFootZ']))
    for frame,values in samples:
        loc,rot,scale=values['root'];values['root']=(loc+up,rot,scale)
    action=bake(rig,'attack_bow',samples)
    # Import the actual final FBX; its standard unit/axis conversion is retained.
    old_objects=set(bpy.data.objects);bpy.ops.import_scene.fbx(filepath=str(ROOT/'src/.tmp/native-production/props/bow.fbx'))
    prop_objects=list(set(bpy.data.objects)-old_objects);bow=next(o for o in prop_objects if o.type=='MESH');imported_matrix=bow.matrix_world.copy()
    bow.parent=rig;bow.parent_type='BONE';bow.parent_bone='attach_bow_l';bow.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones['attach_bow_l'].length,0));bow.matrix_basis=Matrix.Rotation(math.pi,4,'Z')@imported_matrix
    basis=bow.data.shape_keys.key_blocks[0];draw=next(k for k in bow.data.shape_keys.key_blocks if k.name!='Basis')
    lengths=[(d.co-b.co).length for d,b in zip(draw.data,basis.data)];maximum=max(lengths);nock_indices=[i for i,v in enumerate(lengths)if v>=maximum*.999]
    wrist=bpy.data.objects.new('QA_NativeIK_WristGoal',None);bpy.context.collection.objects.link(wrist)
    orientation=bpy.data.objects.new('QA_NativeIK_HandOrientation',None);bpy.context.collection.objects.link(orientation)
    constraint=rig.pose.bones['lowerarm_r'].constraints.new('IK');constraint.name='Blender_Native_BowContact_IK';constraint.target=wrist;constraint.chain_count=3;constraint.use_stretch=False
    copy=rig.pose.bones['hand_r'].constraints.new('COPY_ROTATION');copy.name='Blender_Native_AuthoredHandRotation';copy.target=orientation;copy.target_space='WORLD';copy.owner_space='WORLD';copy.mix_mode='REPLACE'
    baked=[];contacts=[]
    for frame in range(50):
        constraint.influence=0;copy.influence=0;assign(rig,action);time(frame)
        draw.value=min(1,frame/40)if frame<=40 else max(0,1-(frame-40)/3)
        bpy.context.view_layer.update()
        local=sum((basis.data[i].co.lerp(draw.data[i].co,draw.value)for i in nock_indices),Vector())/len(nock_indices)
        nock=bow.matrix_world@local
        hand=rig.matrix_world@rig.pose.bones['hand_r'].matrix;slot=rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix
        orientation.matrix_world=Matrix.LocRotScale(hand.translation,hand.to_quaternion(),Vector((1,1,1)))
        wrist.location=nock-(slot.translation-hand.translation)
        influence=min(1,max(0,(frame-10)/10))if frame<=40 else max(0,1-(frame-40)/3)
        constraint.influence=influence;copy.influence=influence;bpy.context.view_layer.update()
        values=pose(rig)
        # Evaluated native constraints are baked via Blender's matrix_basis
        # conversion, not by reconstructing any limb rotations ourselves.
        solved={n:p.matrix.copy()for n,p in rig.pose.bones.items()}
        constraint.influence=0;copy.influence=0;bpy.context.view_layer.update()
        for name in ['clavicle_r','upperarm_r','lowerarm_r','hand_r']:
            rig.pose.bones[name].matrix=solved[name];bpy.context.view_layer.update();p=rig.pose.bones[name];values[name]=(p.location.copy(),p.rotation_quaternion.copy(),p.scale.copy())
        error=(rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix).translation-nock
        contacts.append({'frame':frame,'draw':draw.value,'ikInfluence':influence,'gripToNockMetres':error.length,'nock':list(nock),'arrowSocket':list((rig.matrix_world@rig.pose.bones['attach_arrow_r'].matrix).translation)})
        baked.append((float(frame),values))
    rig.pose.bones['lowerarm_r'].constraints.remove(constraint);rig.pose.bones['hand_r'].constraints.remove(copy)
    action=bake(rig,'attack_bow',baked)
    for o in prop_objects+[wrist,orientation]:bpy.data.objects.remove(o,do_unlink=True)
    manifest['clips']['attack_bow'].update(quaternionHemisphereContinuous=True,lowerBodySource='Original UAL1 Idle_Loop frame0 lower-body mask; authored KayKit upper body retained',contactTool='Blender native IK chain3 including existing clavicle/use_stretch=False + world CopyRotation; gradual nock contact frames10..20, full contact20..40, authored release resumes40..43; baked',contactMaxMetres=max(c['gripToNockMetres']for c in contacts if 20<=c['frame']<=40),contactHoldMetres=contacts[40]['gripToNockMetres'],floor=floor_report(rig,meshes,action))
    manifest['clips']['attack_staff']['phaseSampling']={'gameplayFractions':[0,.2/.7,1],'sourceFractions':[10/44,16/44,1]}
    manifest['clips']['spell']['phaseSampling']={'gameplayFractions':[0,.25/.45,1],'sourceFractions':[8.5/44,16/44,22/44]}
    manifest['clips']['spell']['gameActionSeconds']=.45;manifest['clips']['spell']['gameCueSeconds']=.25
    manifest['clips']['dodge']['phaseSampling']={'gameplayFractions':[0,.04/.34,.22/.34,1],'sourceFractions':[6/44,10/44,28/44,36/44]}
    manifest['clips']['death']['holdFinalPoseMode']='Runtime holds original final collapsed pose; export-specific extra hold belongs to character manifest'
    manifest['attachments']['skinBones']=65;manifest['attachments']['propLocalRotationDegreesCocos']={'bow':[90,0,0],'arrow':[0,0,0],'sword':[0,0,0],'staff':[0,0,0]}
    manifest['status']='CANONICAL_11_CONTACT_BAKED_PENDING_FINAL_PICTURE'
    (OUT/'bow-contact-review.json').write_text(json.dumps({'solver':'Official Blender IK and CopyRotation only; no custom IK algorithm','contacts':contacts},indent=2))
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');assign(rig,action);time(40)
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native65-actions.blend'),relative_remap=False)
    print('[BOW_CONTACT_READY]',contacts[40]['gripToNockMetres'],max(c['gripToNockMetres']for c in contacts),flush=True)

def main():
    argv=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else []
    parser=argparse.ArgumentParser();parser.add_argument('--native-only',action='store_true');parser.add_argument('--inspect',action='store_true');parser.add_argument('--bow-probe',action='store_true');parser.add_argument('--complete-bow',action='store_true');parser.add_argument('--render-review',action='store_true');parser.add_argument('--finalize-contact',action='store_true');args=parser.parse_args(argv)
    if args.bow_probe:bow_probe();return
    if args.complete_bow:complete_bow();return
    if args.render_review:render_review();return
    if args.finalize_contact:finalize_contact();return
    OUT.mkdir(parents=True,exist_ok=True);bpy.ops.wm.read_factory_settings(use_empty=True);bpy.context.scene.render.fps=FPS
    rig,meshes,actions=native_sources()
    raw={lib+'__'+name:{'frames':list(a.frame_range),'seconds':(a.frame_range[1]-a.frame_range[0])/FPS,'slots':[{'identifier':s.identifier,'type':s.target_id_type}for s in a.slots]}for(lib,name),a in actions.items()}
    (OUT/'raw-source-actions.json').write_text(json.dumps(raw,indent=2))
    if args.inspect:
        print(json.dumps(raw,indent=2));return
    selections=segments_for(actions);manifest={'status':'NATIVE_ACTIONS_READY_BOW_PENDING','fps':FPS,'canonicalActions':CANONICAL,'availableActions':list(selections),'referenceRig':'Native65_ActionRig','referenceSkinBones':65,'headBone':'Head','targetRestPolicy':'Keep original target rest/bind; assign these native pose-basis actions, never raw glTF absolute TRS.','actionSlotPolicy':'Assign action then action.slots[0], an OBJECT slot; slot identifiers are in clips[].','referenceThighLength':rig.data.bones['thigh_l'].length,'sources':[],'clips':{},'attachments':{'status':'BOW_PENDING','rightHand':'hand_r','leftHand':'hand_l'},'productionModified':False}
    for label,path in [('UAL1',UAL1),('UAL2',UAL2),('KayKitBow',KAY)]:manifest['sources'].append({'id':label,'file':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':sha(path),'license':'CC0-1.0'})
    for name,segments in selections.items():
        samples,duration=sample_segments(rig,actions,segments);action=bake(rig,name,samples)
        rec={'name':name,'duration':duration,'startFrame':0,'endFrame':duration*FPS,'fps':FPS,'loop':name in ['idle','walk','run'],'sourceSegments':segments,'holdFinalPose':name=='death','actionSlots':[{'identifier':s.identifier,'type':s.target_id_type,'handle':s.handle}for s in action.slots],'rootMotion':'Original in-place native clip; root/pelvis fully keyed to avoid previous action leakage','floor':floor_report(rig,meshes,action)}
        if name in ['walk','run']:rec.update(nominalSpeedMetresPerSecond=.975 if name=='walk'else 5.357142857142857,strideSource='Original UAL1 RM root displacement divided by source duration; target must scale by thigh ratio and object scale')
        if name=='attack_sword':rec.update(cueSeconds=.12,cueFraction=.12/.44,gameActionSeconds=.44,naturalPlayback=True)
        if name in ['spell','attack_staff']:rec.update(gameCueSeconds=.2,gameActionSeconds=.7,phaseSamplingRequired=True,nativeShootStartsAtSeconds=(segments[0]['end']-segments[0]['start'])/FPS,phaseNote='Use data-driven native enter/hold/shoot/exit phases; do not uniformly compress complete motion to .7 seconds')
        manifest['clips'][name]=rec;print('[NATIVE_READY]',name,duration,flush=True)
    assign(rig,bpy.data.actions['idle']);time(0);bpy.context.scene.frame_start=0;bpy.context.scene.frame_end=90
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'native65-actions.blend'),relative_remap=False)
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print('[NATIVE_MANIFEST]',str(OUT/'manifest.json'),flush=True)
    if not args.native_only:
        complete_bow()
        finalize_contact()

if __name__=='__main__':main()
