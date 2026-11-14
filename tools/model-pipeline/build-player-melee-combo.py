"""Reuse installed CC0 UAL2 B/C sword motions; export a small animation-only carrier.

blender -b --python tools/model-pipeline/build-player-melee-combo.py
The production hero model, mesh, face and existing clips are never rewritten.
"""
from pathlib import Path
import sys,json,hashlib,math
import bpy
sys.path.insert(0,str(Path(__file__).resolve().parent))
import cocos_native_motions as native

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'src/cocos/assets/resources/actors/player-melee-combo'
ART=ROOT/'source-art/characters/player-melee-combo-v1'
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.scene.render.fps=30
rig,meshes,actions=native.native_sources()
rig.name='raphael_Native65'
clips={
 'attack_sword_2':('Sword_Regular_B',.38,[0,.12,.26,.38],[0,7,13,16]),
 'attack_sword_3':('Sword_Regular_C',.56,[0,.22,.36,.56],[0,15,28,60]),
}
sampled={};metadata={}
for name,(source,duration,times,frames) in clips.items():
    # Bake a short native-pose handoff into the clip itself so baked skinning
    # does not briefly snap through the idle pose between combo stages.
    entry_source,entry_frame=('Sword_Regular_A_Rec',4.2) if name.endswith('_2') else ('Sword_Regular_B',16)
    native.reset(rig);native.assign(rig,actions[('UAL2',entry_source)]);native.time(entry_frame)
    entry=native.pose(rig)
    samples=[]
    timeline=[i/30 for i in range(math.floor(duration*30)+1)]+[duration]
    root_position=None
    for t in timeline:
        index=next((i for i in range(1,len(times)) if t<=times[i]),len(times)-1)
        a,b=times[index-1:index+1]
        frame=frames[index-1]+(frames[index]-frames[index-1])*(t-a)/(b-a)
        native.reset(rig);native.assign(rig,actions[('UAL2',source)]);native.time(frame)
        values=native.pose(rig)
        weight=min(1,t/.08);weight=weight*weight*(3-2*weight)
        if weight<1:
            values={bn:(entry[bn][0].lerp(loc,weight),entry[bn][1].slerp(rot,weight),entry[bn][2].lerp(scale,weight)) for bn,(loc,rot,scale) in values.items()}
        if root_position is None:root_position=values['root'][0].copy()
        loc,rot,scale=values['root'];loc.x=root_position.x;loc.y=root_position.y
        samples.append((t*30,values))
    sampled[name]=samples
    metadata[name]={'source':source,'durationSeconds':duration,'gameplayTimes':times,'sourceFrames':frames,'entryPose':{'source':entry_source,'frame':entry_frame,'blendSeconds':.08},'rootMotion':'in-place; source root XY removed, original pose joints retained'}
# Export against the actual hero, not the library mannequin. Bone names alone
# do not imply the same bind: Raphael has different leg lengths, foot axes and
# object scale. Imported animation bakes those offsets into transform channels.
hero_manifest=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
hero_source=ROOT/hero_manifest['source']
bpy.ops.wm.open_mainfile(filepath=str(hero_source))
bpy.context.scene.render.fps=30
rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
rig.animation_data_clear();rig.data.pose_position='POSE'
for action in list(bpy.data.actions):bpy.data.actions.remove(action)
meshes=[o for o in bpy.data.objects if o.type=='MESH']
feet=[o for o in meshes if o.get('nativePart')=='feet']
assert feet,'Hero source must retain its actual boot geometry for sole alignment'
bind_hash=hashlib.sha256(repr([(b.name,b.parent.name if b.parent else None,[tuple(r)for r in b.matrix_local],b.use_deform)for b in rig.data.bones]).encode()).hexdigest()
retained=[]
for name,samples in sampled.items():
    action=native.bake(rig,name,samples)
    # Use the same evaluated-sole root offset as the production hero pipeline;
    # preserve the authored hip, knee, ankle and toe rotations throughout.
    corrected=[];offsets=[]
    root_bone=rig.pose.bones['root']
    up=(rig.matrix_world.to_3x3()@root_bone.bone.matrix_local.to_3x3()).inverted()@native.Vector((0,0,1))
    for frame,values in samples:
        native.time(frame)
        deps=bpy.context.evaluated_depsgraph_get();sole=min((o.matrix_world@v.co).z for obj in feet for o in [obj.evaluated_get(deps)] for v in o.data.vertices)
        offset=.003-sole
        loc,rot,scale=values['root'];values=dict(values);values['root']=(loc+up*offset,rot,scale)
        corrected.append((frame,values));offsets.append(offset)
    retained.append(native.bake(rig,name,corrected))
    metadata[name]['floorAlignment']={'method':'Actual hero boot geometry; vertical root offset only','soleMetres':.003,'offsetRangeMetres':[min(offsets),max(offsets)]}
for mesh in meshes:bpy.data.objects.remove(mesh,do_unlink=True)
# A three-vertex skin ensures Creator imports the normal skeletal-animation
# resource graph. This carrier is never added to the game scene.
mesh=bpy.data.meshes.new('MotionCarrier');mesh.from_pydata([(0,0,0),(.001,0,0),(0,.001,0)],[],[(0,1,2)]);mesh.update()
carrier=bpy.data.objects.new('MotionCarrier',mesh);bpy.context.collection.objects.link(carrier)
group=carrier.vertex_groups.new(name='root');group.add([0,1,2],1,'REPLACE')
modifier=carrier.modifiers.new('Native65','ARMATURE');modifier.object=rig
carrier.parent=rig
native.assign(rig,retained[0]);native.time(0)
bpy.ops.object.select_all(action='DESELECT');rig.select_set(True);carrier.select_set(True);bpy.context.view_layer.objects.active=rig
OUT.mkdir(parents=True,exist_ok=True);ART.mkdir(parents=True,exist_ok=True)
# Match the production GLB's Y-up conversion and joint hierarchy as well as its
# bind. FBX distributes the axis correction over different parent/root nodes;
# interpolating those channels with the GLB's clips can twist the whole body.
target=OUT/'combos-native.glb'
bpy.ops.export_scene.gltf(filepath=str(target),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
report={'generator':'tools/model-pipeline/build-player-melee-combo.py','source':str(native.UAL2.relative_to(ROOT)),'sourceSha256':native.sha(native.UAL2),'heroSource':str(hero_source.relative_to(ROOT)),'heroSourceSha256':native.sha(hero_source),'heroBindSha256':bind_hash,'license':'CC0-1.0','localMotionAssembly':True,'imageGenerationUsed':False,'clips':metadata,'bones':list(rig.data.bones.keys()),'output':str(target.relative_to(ROOT)),'bytes':target.stat().st_size,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'acceptance':'Native library motions assembled on the current hero bind; runtime and visual acceptance recorded separately.'}
(ART/'provenance.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('[MELEE_COMBO_EXPORTED]',target.stat().st_size,json.dumps(metadata),flush=True)
