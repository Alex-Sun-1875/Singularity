"""Roundtrip actual FBX through Blender and render neutral authoring evidence."""
from pathlib import Path
import bpy,sys,json,math,hashlib,os
import numpy as np
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'));OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
CLIPS=['idle','walk','run','attack_sword','attack_bow','attack_staff','spell','dodge','hit','death','interact']
def actual_action(name):
    return next(a for a in bpy.data.actions if a.name==name or a.name.endswith('|'+name))
def sample(rig,action,frame):
    rig.animation_data_create();rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    bpy.context.scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
    points=[];deps=bpy.context.evaluated_depsgraph_get()
    for obj in sorted(rig.children_recursive,key=lambda o:o.name):
        if obj.type!='MESH' or obj.get('native_default_hidden',False):continue
        evaluated=obj.evaluated_get(deps);mesh=evaluated.to_mesh()
        points.extend(obj.matrix_world@v.co for v in mesh.vertices)
        evaluated.to_mesh_clear()
    return np.array(points,dtype=float)
def inspect(identity):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    folder=OUT/identity
    bpy.ops.import_scene.fbx(filepath=str(folder/f'{identity}.fbx'),use_anim=True,automatic_bone_orientation=False)
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    manifest=json.loads((folder/'manifest.json').read_text())
    native=manifest.get('runtimeProfile')=='native-kit-v1'
    if native:
        hidden={n for p in manifest['parts'].values() if not p['defaultVisible'] for n in p['nodes']}
        for obj in rig.children_recursive:obj['native_default_hidden']=obj.name in hidden
    normalized={a.name.split('|')[-1]:a for a in bpy.data.actions}
    missing=set(CLIPS)-set(normalized)
    if missing:
        assert '--allow-pending' in sys.argv and native and missing==set(manifest.get('pendingClips',[])),missing
    inspect_clips=[n for n in CLIPS if n in normalized]
    idle=sample(rig,normalized['idle'],normalized['idle'].frame_range[0]);motions={}
    for name in inspect_clips:
        action=normalized[name];start,end=action.frame_range
        p=sample(rig,action,start+(end-start)*.45)
        motions[name]=p
    death=normalized['death'];start,end=death.frame_range
    d1=sample(rig,death,start+(end-start)*.85);d2=sample(rig,death,end)
    boots=next((o for o in rig.children_recursive if native and o.name in manifest['parts']['feet']['nodes']),None)
    if boots is None:boots=next((o for o in rig.children_recursive if o.name==identity+'_libraryboots_surface'),None)
    if boots is None:boots=next(o for o in rig.children_recursive if o.name==identity+'_belt_surface')
    foot_indices=[v.index for v in boots.data.vertices if native or v.co.z<.30]
    def foot_ground(action,fraction):
        rig.animation_data.action=action
        if action.slots:rig.animation_data.action_slot=action.slots[0]
        first,last=action.frame_range;frame=first+(last-first)*fraction;bpy.context.scene.frame_set(int(frame),subframe=frame%1);bpy.context.view_layer.update()
        ev=boots.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh();minimum=min((boots.matrix_world@mesh.vertices[i].co).z for i in foot_indices);ev.to_mesh_clear();return minimum
    ground_samples={name:[foot_ground(normalized[name],i/20) for i in range(21)] for name in ['idle','walk','run','attack_sword','dodge','death']}
    motion_ground={name:min(values) for name,values in ground_samples.items()}
    distinct={tuple(np.round(v[::max(1,len(v)//60)].ravel(),2)) for v in motions.values()}
    missing=[];used_images=[]
    for material in bpy.data.materials:
        if material.use_nodes:
            for node in material.node_tree.nodes:
                if node.type=='TEX_IMAGE' and node.image:
                    path=Path(bpy.path.abspath(node.image.filepath));used_images.append(str(path))
                    if not path.is_file():missing.append(str(path))
    report={'boneCount':len(rig.data.bones),'actions':{k:{'importedName':a.name,'frames':list(a.frame_range)} for k,a in normalized.items()},'meshCount':sum(o.type=='MESH' for o in rig.children_recursive),'vertexCount':len(idle),'animatedVertexDelta':float(np.max(np.linalg.norm(motions['run']-idle,axis=1))),'deathFinalDelta':float(np.max(np.linalg.norm(d1-d2,axis=1))),'idleGround':float(idle[:,2].min()),'height':float(idle[:,2].max()-idle[:,2].min()),'distinctMotionSignatures':len(distinct),'allImagesResolved':len(used_images)>0 and not missing,'usedImages':used_images,'missingImages':missing,'boneNames':[b.name for b in rig.data.bones]}
    report['fbxSha256']=hashlib.sha256((folder/f'{identity}.fbx').read_bytes()).hexdigest()
    report['motionGroundMinimum']=motion_ground
    report['motionGroundMaximum']={name:max(values) for name,values in ground_samples.items()}
    if native:report['runtimeProfile']='native-kit-v1';report['skinJointCount']=manifest['skinJointCount'];report['pendingClips']=sorted(missing)
    (folder/'inspection.json').write_text(json.dumps(report,indent=2))
    assert report['allImagesResolved'],missing
    assert report['deathFinalDelta']<.001,report['deathFinalDelta']
    assert min(motion_ground.values())>-.008,motion_ground
    assert max(report['motionGroundMaximum'][name] for name in ['idle','walk'])<.015,report['motionGroundMaximum']
    print('[FBX_INSPECT]',identity,report['boneCount'],'bones',len(normalized),'actions','movement',round(report['animatedVertexDelta'],3),'ground',round(report['idleGround'],4),'height',round(report['height'],3),flush=True)
def aim(obj,point):obj.rotation_euler=(Vector(point)-obj.location).to_track_quat('-Z','Y').to_euler()
def compose(paths,out,columns):
    images=[bpy.data.images.load(str(p),check_existing=False) for p in paths];w,h=images[0].size;rows=math.ceil(len(images)/columns)
    arr=np.ones((rows*h,columns*w,4),dtype=np.float32);arr[:,:,:3]=.19
    for i,im in enumerate(images):
        pixels=np.asarray(im.pixels[:],dtype=np.float32).reshape(h,w,4);x=i%columns*w;y=(rows-1-i//columns)*h
        arr[y:y+h,x:x+w,:]=pixels
    image=bpy.data.images.new(out.stem,width=columns*w,height=rows*h);image.pixels.foreach_set(arr.ravel());image.filepath_raw=str(out);image.file_format='PNG';image.save()
    for im in images:bpy.data.images.remove(im)
def render(identity):
    runtime='--runtime' in sys.argv
    if runtime:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=str(OUT/identity/f'{identity}.fbx'),use_anim=True)
    else:bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');scene=bpy.context.scene
    manifest=json.loads((OUT/identity/'manifest.json').read_text())
    if manifest.get('runtimeProfile')=='native-kit-v1':
        hidden={n for p in manifest['parts'].values()if not p['defaultVisible']for n in p['nodes']}
        for obj in rig.children_recursive:obj.hide_render=obj.name in hidden
    for obj in rig.children_recursive:
        if obj.name.startswith('Equipped_'):obj.hide_render=True
    action=actual_action('idle');rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    scene.frame_set(1)
    scene.render.engine='CYCLES';scene.cycles.samples=16;scene.cycles.use_denoising=True
    if manifest.get('runtimeProfile')=='native-kit-v1':scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=384;scene.render.resolution_y=512;scene.render.resolution_percentage=100
    if scene.world is None:scene.world=bpy.data.worlds.new('PreviewWorld')
    scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.20,.20,.20,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.5
    scene.view_settings.view_transform='AgX'
    bpy.ops.object.camera_add(location=(0,-5,1.0));camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=2.15;aim(camera,(0,0,.96));scene.camera=camera
    for pos,energy,size in [((2,-3,4),450,3),((-3,-2,2.5),230,3),((1,2,3),450,2)]:
        bpy.ops.object.light_add(type='AREA',location=pos);light=bpy.context.object;light.data.energy=energy;light.data.shape='DISK';light.data.size=size;aim(light,(0,0,1))
    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.008));floor=bpy.context.object;floor.name='PreviewGround'
    material=bpy.data.materials.new('PreviewGround');material.diffuse_color=(.18,.17,.15,1);floor.data.materials.append(material)
    bpy.ops.object.text_add(location=(-.73,-.45,1.965),rotation=(math.pi/2,0,0));label=bpy.context.object;label.name='PreviewLabel';label.data.size=.055
    label_mat=bpy.data.materials.new('PreviewLabel');label_mat.use_nodes=True;label_bsdf=label_mat.node_tree.nodes.get('Principled BSDF');label_bsdf.inputs['Base Color'].default_value=(.8,.77,.69,1);label_bsdf.inputs['Emission Color'].default_value=(.8,.77,.69,1);label_bsdf.inputs['Emission Strength'].default_value=.3;label.data.materials.append(label_mat)
    preview=SOURCE/'previews'/('runtime' if runtime else '');preview.mkdir(parents=True,exist_ok=True)
    views=[]
    for view,angle in [('front',0),('back',math.pi),('side',math.pi/2)]:
        camera.location=(-5*math.sin(angle),-5*math.cos(angle),1.0);aim(camera,(0,0,.96));label.rotation_euler=camera.rotation_euler;label.location=Vector((0,0,.96))+camera.rotation_euler.to_quaternion()@Vector((-.73,1.005,.45));label.data.body=identity+' / '+view;path=preview/f'{identity}-{view}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);views.append(path)
    compose(views,preview/f'{identity}-turnaround.png',3);camera.location=(0,-5,1.0);aim(camera,(0,0,.96));label.rotation_euler=camera.rotation_euler;label.location=(-.73,-.45,1.965)
    if identity in ['raphael','mira']:
        height=1.85 if identity=='raphael' else 1.70;target=height-.18
        camera.location=(0,-5,target);aim(camera,(0,0,target));camera.data.ortho_scale=.72
        label.location=(-.25,-.45,target+.29);label.data.size=.022;label.data.body=identity+' / face and garment'
        path=preview/f'{identity}-closeup.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True)
        camera.location=(0,-5,1.0);aim(camera,(0,0,.96));camera.data.ortho_scale=2.15;label.location=(-.73,-.45,1.965);label.data.size=.055
    if identity=='raphael':
        for obj in rig.children_recursive:
            if obj.name.startswith('Equipped_'):obj.hide_render=False
        frames=[]
        for name in CLIPS:
            if name in manifest.get('pendingClips',[])and'--allow-pending'in sys.argv:continue
            action=actual_action(name);rig.animation_data.action=action;start,end=action.frame_range;frame=start+(end-start)*(.90 if name=='death' else .40)
            if action.slots:rig.animation_data.action_slot=action.slots[0]
            scene.frame_set(int(frame),subframe=frame%1);label.data.body=name;path=preview/f'motion-{name}.png';scene.render.filepath=str(path);bpy.ops.render.render(write_still=True);frames.append(path)
        compose(frames,preview/'raphael-motion-contact-sheet.png',5)
    print('[RENDERED]',identity,flush=True)
selected=sys.argv[sys.argv.index('--character')+1] if '--character' in sys.argv else None
for identity in (selected.split(',') if selected else IDS):
    if '--render' in sys.argv:render(identity)
    else:inspect(identity)
if '--render' in sys.argv and not selected:
    preview=SOURCE/'previews'/('runtime' if '--runtime' in sys.argv else '')
    compose([preview/f'{identity}-front.png' for identity in IDS],preview/'cast-front-contact-sheet.png',5)
