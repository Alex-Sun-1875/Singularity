"""Render existing licensed Native65/v6 actors to transparent 2D sprite sheets.

Run with the repository's Blender 4.5.15, for example:
blender -b -t 2 --python src/prototype-2d/tools/render-sprites.py -- 
  --characters raphael,raider --actions idle,walk,attack_sword,dodge,death --directions 8

No FBX, production actors, rigs, action curves or source .blend files are saved.
Sheets have one direction per row, one animation frame per column.
Runtime sheets are finalized at half size; full-resolution PNG frames remain
in each actor's frames/ directory. --finalize-existing performs only that
conversion on existing sheets, without re-rendering.
"""
from pathlib import Path
import argparse,hashlib,json,math,sys,time

import bpy
import numpy as np
from mathutils import Matrix,Vector
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'src/prototype-2d/assets/characters'
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import v5_face_hair_adapter as faces
import v5_wardrobe_adapter as wardrobe
import cocos_v5_character_redesign as exporter

WIDTH,HEIGHT=192,320
ORIGIN=(96,216)
DIRECTIONS=[('down',0),('downRight',45),('right',90),('upRight',135),
            ('up',180),('upLeft',225),('left',270),('downLeft',315)]
CLIPS={'idle':(4,6,True),'walk':(6,9,True),'attack_sword':(6,14,False),
       'dodge':(6,16,False),'death':(4,7,False),
       'idle_bow':(1,1,True),'walk_bow':(6,9,True),'attack_bow':(6,6,False),
       'idle_staff':(1,1,True),'walk_staff':(6,9,True),'attack_staff':(6,7,False)}


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def assign(rig,name):
    action=bpy.data.actions[name]
    if not rig.animation_data:rig.animation_data_create()
    rig.animation_data.action=action
    if action.slots:rig.animation_data.action_slot=action.slots[0]
    return action


def set_time(frame):
    bpy.context.scene.frame_set(math.floor(frame),subframe=frame-math.floor(frame))


def load_actor(identity):
    source=ROOT/'src/.tmp/native-production/source'/(identity+'.blend')
    before=sha(source)
    bpy.ops.wm.open_mainfile(filepath=str(source),load_ui=False,use_scripts=False)
    scene=bpy.context.scene
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE')
    original=json.loads((ROOT/'src/cocos/assets/resources/actors'/identity/'manifest.json').read_text(encoding='utf-8-sig'))
    meshes=[o for o in bpy.data.objects if o.type=='MESH' and o.get('nativePart')]
    exporter.prepare_sources(meshes,original);exporter.skin_detail(meshes)
    face_record=faces.apply(identity,rig,original)
    wardrobe_record=wardrobe.apply(identity,rig,original)
    for obj in list(scene.objects):
        if obj.type in ['CAMERA','LIGHT']:bpy.data.objects.remove(obj,do_unlink=True)
        elif obj.type=='MESH' and not obj.get('nativePart'):obj.hide_render=True
        elif obj.type=='MESH' and obj.get('nativePart'):
            obj.hide_render=not bool(obj.get('defaultVisible',True))
            if 'opaque_roots' in obj.name:obj.hide_render=True
    # The authored CC0 KayKit sword is already in the native helper's local
    # frame. Append its editable mesh/materials; retain the source transforms.
    props={}
    for kind in ['sword','bow','arrow','staff']:
        prop_source=ROOT/'source-art/characters/redesign-v6/props'/(kind+'.blend')
        with bpy.data.libraries.load(str(prop_source),link=False)as(src,dst):
            dst.objects=[n for n in src.objects if n.startswith('V5_'+kind+'_')]
        props[kind]=[]
        bone='attach_bow_l'if kind=='bow'else'attach_arrow_r'
        for obj in dst.objects:
            if obj.type!='MESH':continue
            scene.collection.objects.link(obj);basis=obj.matrix_world.copy()
            obj.parent=rig;obj.parent_type='BONE';obj.parent_bone=bone
            obj.matrix_parent_inverse=Matrix.Translation((0,-rig.data.bones[bone].length,0))
            if kind=='bow':basis=Matrix.Rotation(math.pi,4,'Z')@basis
            elif kind=='arrow':basis=Matrix.Translation((0,.35595446825,0))@Matrix.Rotation(-math.pi/2,4,'X')@basis
            obj.matrix_basis=basis
            obj.hide_render=kind!='sword';obj['spriteProp']=kind;props[kind].append(obj)
        assert props[kind],'Missing authored prop source meshes: '+kind
    rig.data.pose_position='POSE'
    assign(rig,'idle');set_time(0)
    visible=[o for o in scene.objects if o.type=='MESH' and not o.hide_render]
    pivot=bpy.data.objects.new('Sprite_ActorYaw',None);scene.collection.objects.link(pivot)
    # Native rigs use quaternion rotation and object-level animation channels.
    # A separate empty rotates the whole fitted actor without touching either.
    matrix=rig.matrix_world.copy();rig.parent=pivot;rig.matrix_world=matrix
    bpy.context.view_layer.update()
    sole=min((o.matrix_world@Vector(c)).z for o in visible if o.get('nativePart')for c in o.evaluated_get(bpy.context.evaluated_depsgraph_get()).bound_box)
    pivot.location.z=-sole
    print('[SPRITE_FLOOR]',identity,sole,flush=True)
    assert sha(source)==before
    return rig,pivot,props,{'nativeSource':str(source.relative_to(ROOT)).replace('\\','/'),
        'nativeSourceSHA256':before,'faceHairRevision':face_record['version'],
        'wardrobeRevision':'existing v5_wardrobe_adapter','rigBones':len(rig.data.bones),
        'actionSource':'Existing Native65 canonical actions; Quaternius CC0',
        'propSourceFolder':'source-art/characters/redesign-v6/props',
        'rootLayerOmitted':'Opaque scalp underlayer is excluded because its copied deform data leaves a static fragment in large native poses.',
        'sourceRigAndActionsEdited':False,
        'hairSources':[{'asset':m['asset'],'author':m.get('author'),'license':m.get('license'),'source':m.get('source')}for m in face_record['sources']]}


def studio():
    scene=bpy.context.scene
    scene.render.engine='BLENDER_EEVEE_NEXT'
    if hasattr(scene.eevee,'taa_render_samples'):scene.eevee.taa_render_samples=16
    scene.render.threads_mode='FIXED';scene.render.threads=2
    scene.render.resolution_x=WIDTH;scene.render.resolution_y=HEIGHT
    scene.render.resolution_percentage=100
    scene.render.film_transparent=True
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA'
    scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=35
    scene.view_settings.view_transform='AgX'
    scene.world=bpy.data.worlds.new('Sprite_NeutralWorld');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.28,.30,.34,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.45
    for name,location,energy,size,color in [
        ('Sprite_WarmKey',(-3,-4,6),700,4.0,(1,.88,.73)),
        ('Sprite_NeutralFill',(3,-1,4),480,4.0,(.84,.91,1)),
        ('Sprite_Rim',(0,3,5),650,3.0,(1,.94,.83))]:
        data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.shape='DISK';data.size=size;data.color=color
        obj=bpy.data.objects.new(name,data);scene.collection.objects.link(obj);obj.location=location
        obj.rotation_euler=(Vector((0,0,.9))-obj.location).to_track_quat('-Z','Y').to_euler()
    data=bpy.data.cameras.new('Sprite_Camera');camera=bpy.data.objects.new('Sprite_Camera',data)
    scene.collection.objects.link(camera);data.type='ORTHO';data.ortho_scale=3.5*max(WIDTH,HEIGHT)/256
    camera.location=(0,-6,4.5)
    camera.rotation_euler=(-camera.location).to_track_quat('-Z','Y').to_euler()
    scene.camera=camera
    # Translation in the camera's own image-up vector gives one exact ground
    # anchor in every frame, including rolls and deaths; never recenter poses.
    up=camera.rotation_euler.to_matrix()@Vector((0,1,0))
    camera.location+=up*((ORIGIN[1]-HEIGHT*.5)*(3.5/256))
    bpy.context.view_layer.update()
    projected=world_to_camera_view(scene,camera,Vector((0,0,0)))
    assert abs(projected.x*WIDTH-ORIGIN[0])<.05
    assert abs((1-projected.y)*HEIGHT-ORIGIN[1])<.05
    return camera


def frames_for(action,count,loop):
    start,end=map(float,action.frame_range)
    if count==1:return[start]
    # Avoid duplicate endpoint for loops. Keep exact final fallen pose for death.
    return [start+(end-start)*i/(count if loop else count-1)for i in range(count)]


def clip(rig,name,still=False):
    count,fps,loop=CLIPS[name]
    if still:count=1;fps=1
    source_name=('attack_bow'if name=='idle_bow'else'attack_staff'if name=='idle_staff'
                 else'walk'if name.startswith('walk_')else name)
    action=assign(rig,source_name)
    frames=frames_for(action,count,loop)
    if name=='attack_bow'and not still:frames=[0,16,30,40,43,49]
    weapon='bow'if name.endswith('_bow')else'staff'if name.endswith('_staff')else'sword'
    return action,frames,fps,loop,weapon


def props_pose(props,identity,name,frame,weapon):
    for kind,objects in props.items():
        for obj in objects:obj.hide_render=identity=='mira'or kind not in (['bow','arrow']if weapon=='bow'else[weapon])
    for obj in props['bow']:
        if obj.data.shape_keys:
            for key in obj.data.shape_keys.key_blocks:
                if key.name!='Basis':key.value=(min(1,frame/40)if frame<=40 else max(0,1-(frame-40)/3))if name=='attack_bow'else 0
    for obj in props['arrow']:obj.hide_render=identity=='mira'or weapon!='bow'or(name=='attack_bow'and frame>43)


def fit_canvas(identity,rig,pivot,props,still):
    """Fit every native clip before rendering; preserve scale and ground anchor.

    Sampling all clips makes later incremental bow/staff runs use the exact
    same cell contract as the initial sword batch. This only changes framing.
    """
    global WIDTH,HEIGHT,ORIGIN
    upp=3.5/256
    low_x=low_up=0.;high_x=high_up=0.
    scene=bpy.context.scene
    for name in (['idle']if still else CLIPS):
        action,frames,fps,loop,weapon=clip(rig,name,still)
        for direction,yaw in DIRECTIONS:
            pivot.rotation_euler.z=math.radians(yaw)
            for frame in frames:
                props_pose(props,identity,name,frame,weapon);set_time(frame)
                graph=bpy.context.evaluated_depsgraph_get()
                for obj in scene.objects:
                    if obj.type!='MESH'or obj.hide_render:continue
                    evaluated=obj.evaluated_get(graph)
                    for corner in evaluated.bound_box:
                        co=evaluated.matrix_world@Vector(corner)
                        up=co.y*.6+co.z*.8
                        low_x=min(low_x,co.x);high_x=max(high_x,co.x)
                        low_up=min(low_up,up);high_up=max(high_up,up)
    half=math.ceil((max(abs(low_x),abs(high_x))/upp+8)/16)*16
    WIDTH=max(192,half*2)
    origin_y=max(216,math.ceil(high_up/upp+8))
    HEIGHT=max(320,math.ceil((origin_y-low_up/upp+8)/32)*32)
    ORIGIN=(WIDTH//2,origin_y)
    pivot.rotation_euler.z=0;assign(rig,'idle');set_time(0)
    report={'worldBoundsProjected':[low_x,low_up,high_x,high_up],
            'frameWidth':WIDTH,'frameHeight':HEIGHT,'origin':list(ORIGIN),'marginPixels':8,
            'sampling':'All requested actor native motion samples and all 8 directions; evaluated mesh bounds'}
    print('[SPRITE_CANVAS]',identity,report,flush=True)
    return report


def pack_sheet(paths,output,columns,rows):
    pixels=np.zeros((HEIGHT*rows,WIDTH*columns,4),dtype=np.float32)
    bounds=[]
    for row in range(rows):
        for column in range(columns):
            image=bpy.data.images.load(str(paths[row*columns+column]),check_existing=False)
            data=np.empty(WIDTH*HEIGHT*4,dtype=np.float32);image.pixels.foreach_get(data)
            data=data.reshape(HEIGHT,WIDTH,4)
            # Blender pixels start at bottom-left, while row zero in the
            # runtime manifest starts at the sheet's top-left.
            bottom=(rows-1-row)*HEIGHT
            pixels[bottom:bottom+HEIGHT,column*WIDTH:(column+1)*WIDTH]=data
            ys,xs=np.nonzero(data[:,:,3]>.02)
            assert len(xs),'Empty sprite: '+str(paths[row*columns+column])
            bbox=[int(xs.min()),int(HEIGHT-1-ys.max()),int(xs.max()+1),int(HEIGHT-ys.min())]
            bounds.append(bbox)
            bpy.data.images.remove(image)
    image=bpy.data.images.new(output.stem,width=WIDTH*columns,height=HEIGHT*rows,alpha=True)
    image.colorspace_settings.name='sRGB';image.alpha_mode='STRAIGHT'
    image.pixels.foreach_set(pixels.ravel());image.update()
    image.filepath_raw=str(output);image.file_format='PNG';image.save()
    bpy.data.images.remove(image)
    return bounds


def render(identity,actions,directions,still=False):
    rig,pivot,props,source=load_actor(identity)
    canvas=fit_canvas(identity,rig,pivot,props,still)
    camera=studio();scene=bpy.context.scene
    folder=OUT/identity;folder.mkdir(parents=True,exist_ok=True)
    raw=folder/'frames';raw.mkdir(exist_ok=True)
    path=folder/'manifest.json'
    manifest=json.loads(path.read_text())if path.exists()else{}
    if manifest.get('runtimeSheetScale')==.5:
        # Restore untouched actions from their full-resolution source frames
        # before a partial rebuild. Never mix half-size and full-size atlases
        # under one actor contract, or skip finalization on a subsequent run.
        for old_name,record in manifest.get('actions',{}).items():
            if old_name in actions:continue
            old_directions=record.get('directions',manifest['directions'])
            assert old_directions==[d for d,y in directions], 'Direction count changed: rebuild every existing actor action together'
            assert record['width']*2==WIDTH*record['frames'] and record['height']*2==HEIGHT*len(directions), 'Framing changed: rebuild every existing actor action together'
            files=[raw/(old_name+'-'+direction+'-'+str(i)+'.png')for direction in old_directions for i in range(record['frames'])]
            record['alphaBoundsPerFrame']=pack_sheet(files,folder/record['image'],record['frames'],len(directions))
            record['width']*=2;record['height']*=2
        for key in ['runtimeSheetScale','runtimeScaleMethod','sourceRender']:manifest.pop(key,None)
    manifest.update({'version':'native65-v6-prerender-v1','id':identity,
        'frameWidth':WIDTH,'frameHeight':HEIGHT,'origin':list(ORIGIN),
        'directions':[name for name,yaw in directions],
        'directionYawDegrees':[yaw for name,yaw in directions],
        'layout':'one direction per row, chronological frames in columns; top-left coordinates',
        'camera':{'projection':'orthographic','elevationDegrees':math.degrees(math.atan2(4.5,6)),
                  'orthoScale':camera.data.ortho_scale,'worldUnitsPerPixel':3.5/256},
        'canvasFit':canvas,
        'background':'transparent RGBA; no ground geometry or baked floor shadow',
        'source':source,'actions':manifest.get('actions',{})})
    for name in actions:
        started=time.time();action,frames,fps,loop,weapon=clip(rig,name,still)
        count=len(frames);paths=[]
        for row,(direction,yaw)in enumerate(directions):
            pivot.rotation_euler.z=math.radians(yaw)
            for column,frame in enumerate(frames):
                props_pose(props,identity,name,frame,weapon);set_time(frame)
                output=raw/(name+'-'+direction+'-'+str(column)+'.png')
                scene.render.filepath=str(output);bpy.ops.render.render(write_still=True);paths.append(output)
        sheet=folder/(name+'.png');bounds=pack_sheet(paths,sheet,count,len(directions))
        assert all(b[0]>0 and b[1]>0 and b[2]<WIDTH and b[3]<HEIGHT for b in bounds),('Cropped sprite',identity,name,bounds)
        manifest['actions'][name]={'image':sheet.name,'frames':count,'fps':fps,'loop':loop,
            'holdLastFrame':name=='death','width':WIDTH*count,'height':HEIGHT*len(directions),
            'weapon':'none'if identity=='mira'else weapon,'directions':[d for d,y in directions],
            'sourceAction':action.name,'sourceFrames':frames,'sourceFrameRange':list(action.frame_range),
            'alphaBoundsPerFrame':bounds,'seconds':count/fps}
        path.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8')
        print('[SPRITE_SHEET_READY]',identity,name,sheet,time.time()-started,flush=True)
    return manifest


def finalize_characters(identities):
    """Use Blender's image scaler once; keep source renders for future quality."""
    for identity in identities:
        folder=OUT/identity;path=folder/'manifest.json'
        manifest=json.loads(path.read_text())
        if manifest.get('runtimeSheetScale')==.5:continue
        manifest['sourceRender']={key:manifest[key]for key in ['frameWidth','frameHeight','origin']}
        manifest['sourceRender'].update({'worldUnitsPerPixel':manifest['camera']['worldUnitsPerPixel'],
                                        'rawFramesFolder':'frames','preservedAtFullResolution':True})
        for name,record in manifest['actions'].items():
            target=folder/record['image']
            image=bpy.data.images.load(str(target),check_existing=False)
            expected=(record['width'],record['height'])
            assert tuple(image.size)==expected,(identity,name,'Unexpected atlas dimensions',tuple(image.size),expected)
            image.scale(expected[0]//2,expected[1]//2)
            image.filepath_raw=str(target);image.file_format='PNG';image.save()
            bpy.data.images.remove(image)
            record['width']//=2;record['height']//=2
            record['alphaBoundsPerFrame']=[[math.floor(b[0]/2),math.floor(b[1]/2),math.ceil(b[2]/2),math.ceil(b[3]/2)]for b in record['alphaBoundsPerFrame']]
        manifest['frameWidth']//=2;manifest['frameHeight']//=2
        manifest['origin']=[v/2 for v in manifest['origin']]
        manifest['camera']['worldUnitsPerPixel']*=2
        manifest['runtimeSheetScale']=.5
        manifest['runtimeScaleMethod']='Blender Image.scale 50%; full-resolution transparent source frames retained'
        temp=path.with_suffix('.json.tmp');temp.write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf8');temp.replace(path)
        print('[SPRITE_RUNTIME_HALF]',identity,manifest['frameWidth'],manifest['frameHeight'],flush=True)
    budget={}
    for path in OUT.glob('*/manifest.json'):
        manifest=json.loads(path.read_text());records=manifest['actions']
        png=sum((path.parent/record['image']).stat().st_size for record in records.values())
        rgba=sum(record['width']*record['height']*4 for record in records.values())
        budget[manifest['id']]={'actions':len(records),'directions':len(manifest['directions']),
            'pngBytes':png,'estimatedRGBABytes':rgba,'estimatedRGBAMiB':round(rgba/1024**2,2),
            'runtimeSheetScale':manifest.get('runtimeSheetScale',1)}
    report={'scope':'Runtime sprite PNG sheets listed in actor manifests; raw frames excluded',
            'rgbaEstimate':'width * height * 4 bytes; base texture level, excluding renderer bookkeeping',
            'characters':budget,'totalPNGBytes':sum(r['pngBytes']for r in budget.values()),
            'totalEstimatedRGBABytes':sum(r['estimatedRGBABytes']for r in budget.values())}
    report['totalEstimatedRGBAMiB']=round(report['totalEstimatedRGBABytes']/1024**2,2)
    (OUT/'runtime-budget.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf8')
    print('[SPRITE_RUNTIME_BUDGET]',report,flush=True)


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--characters',default='raphael,raider')
    parser.add_argument('--actions',default=','.join(CLIPS))
    parser.add_argument('--directions',type=int,choices=[4,8],default=8)
    parser.add_argument('--still',action='store_true',help='One source frame per direction, useful for an NPC idle')
    parser.add_argument('--finalize-existing',action='store_true',help='Only half-size existing runtime atlases; never renders')
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[])
    directions=DIRECTIONS if args.directions==8 else DIRECTIONS[::2]
    identities=args.characters.split(',')
    if args.finalize_existing:finalize_characters(identities);return
    for identity in identities:
        render(identity,args.actions.split(','),directions,args.still)
        finalize_characters([identity])


if __name__=='__main__':main()
