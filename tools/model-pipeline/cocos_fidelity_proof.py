"""Reproducible geometry proofs and transparent portraits, rendered by Blender."""
from pathlib import Path
import bpy, sys, math, os
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'))

def aim(obj,target):obj.rotation_euler=(Vector(target)-obj.location).to_track_quat('-Z','Y').to_euler()

def render(identity,draft=False):
    path=Path(sys.argv[sys.argv.index('--input')+1]) if '--input' in sys.argv else (ROOT/'src/.tmp/character-fidelity'/('draft-'+identity+'.blend') if draft else SOURCE/(identity+'.blend'))
    bpy.ops.wm.open_mainfile(filepath=str(path))
    for im in bpy.data.images:
        if not im.filepath or im.filepath.startswith('<'):continue
        candidate=SOURCE/'textures'/identity/Path(im.filepath).name
        if candidate.exists():im.filepath=str(candidate);im.reload()
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    clip=sys.argv[sys.argv.index('--clip')+1] if '--clip' in sys.argv else 'idle'
    rig.animation_data.action=bpy.data.actions[clip]
    if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
    scene=bpy.context.scene;scene.frame_set(1)
    if '--in-place' in sys.argv:
        action=rig.animation_data.action
        for fc in action.fcurves:
            if fc.data_path=='pose.bones["pelvis"].location' and fc.array_index in [0,1]:
                for key in fc.keyframe_points:key.co.y=0
        scene.frame_set(1)
    for obj in list(bpy.data.objects):
        if obj.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(obj,do_unlink=True)
    for obj in rig.children_recursive:
        if obj.name.startswith('Equipped_'):obj.hide_render=True
    scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.use_denoising=True
    scene.render.resolution_x=384;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    if scene.world is None:scene.world=bpy.data.worlds.new('ProofWorld')
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    scene.view_settings.view_transform='AgX'
    bpy.ops.object.camera_add(location=(0,-5,1))
    camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=2.15;aim(camera,(0,0,.96));scene.camera=camera
    for pos,energy,size in [((2,-3,4),450,3),((-3,-2,2.5),230,3),((1,2,3),450,2)]:
        bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;aim(light,(0,0,1))
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object
    material=bpy.data.materials.new('ProofGround');material.diffuse_color=(.18,.17,.15,1);floor.data.materials.append(material)
    folder=ROOT/'src/.tmp/character-fidelity/proofs' if draft else SOURCE/'previews/library-fidelity'
    folder.mkdir(parents=True,exist_ok=True)
    if '--actions' in sys.argv:
        camera.location=(-2.5,-5,1.3);aim(camera,(0,0,.95));camera.data.ortho_scale=2.3
        for name in ['idle','walk','run','attack_sword','attack_bow','spell']:
            rig.animation_data.action=bpy.data.actions[name];first,last=rig.animation_data.action.frame_range
            if rig.animation_data.action.slots:rig.animation_data.action_slot=rig.animation_data.action.slots[0]
            for i,t in enumerate([.1,.4,.7,.95]):
                frame=first+(last-first)*t;scene.frame_set(int(frame),subframe=frame%1)
                scene.render.filepath=str(folder/('action-'+name+'-'+str(i)+'.png'));bpy.ops.render.render(write_still=True)
        return
    if '--motion' in sys.argv:
        camera.location=(-3,-5,1.2);aim(camera,(0,0,.95));camera.data.ortho_scale=2.25
        first,last=rig.animation_data.action.frame_range
        for frame in range(int(first),int(last)+1,3):
            scene.frame_set(frame);scene.render.filepath=str(folder/('motion-'+clip+'-'+str(frame).zfill(3)+'.png'));bpy.ops.render.render(write_still=True)
        return
    for view,angle in ([] if '--face-only' in sys.argv else [('front',0),('side',math.pi/2),('back',math.pi)]):
        camera.location=(-5*math.sin(angle),-5*math.cos(angle),1);aim(camera,(0,0,.96));scene.render.filepath=str(folder/(identity+'-'+view+'.png'));bpy.ops.render.render(write_still=True)
    crown=[]
    for obj in rig.children_recursive:
        if obj.type!='MESH' or not any(part in obj.name for part in ['haircards_surface','skin_surface']):continue
        ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
        crown.extend((ev.matrix_world@vertex.co).z for vertex in mesh.vertices);ev.to_mesh_clear()
    target=max(crown)-.19
    camera.location=(0,-5,target);aim(camera,(0,0,target));camera.data.ortho_scale=.72
    scene.render.filepath=str(folder/(identity+'-closeup.png'));bpy.ops.render.render(write_still=True)
    if '--portrait' in sys.argv:
        scene.render.resolution_x=256;scene.render.resolution_y=320;scene.render.film_transparent=True;floor.hide_render=True
        camera.location=(.22,-5,target);aim(camera,(0,0,target));camera.data.ortho_scale=.56
        dest=Path(os.environ.get('SINGULARITY_CHARACTER_PORTRAITS',ROOT/'src/cocos/assets/resources/portraits'));dest.mkdir(parents=True,exist_ok=True)
        scene.render.filepath=str(dest/(identity+'.png'));bpy.ops.render.render(write_still=True)
    print('[FIDELITY_PROOF]',identity,folder,flush=True)

if __name__=='__main__':
    ids=sys.argv[sys.argv.index('--character')+1].split(',') if '--character' in sys.argv else ['raphael','mira']
    for identity in ids:render(identity,'--draft' in sys.argv)
