"""Export-only game LoD and compact PNGs; preserve editable high-detail sources."""
from pathlib import Path
import bpy,json,shutil,os,math,sys
import numpy as np
ROOT=Path(__file__).resolve().parents[2];SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'));OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
from blender_bootstrap import TargetService
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
def tris(obj):return sum(len(p.vertices)-2 for p in obj.data.polygons)
def decimate(obj,ratio):
    if ratio>=.99 or tris(obj)<200 or obj.data.shape_keys:return
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.select_all(action='DESELECT');obj.select_set(True)
    mod=obj.modifiers.new('GameLOD','DECIMATE');mod.ratio=max(.12,ratio);mod.use_collapse_triangulate=True
    while obj.modifiers.find(mod.name)>0:bpy.ops.object.modifier_move_up(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
reports={}
selected=sys.argv[sys.argv.index('--character')+1] if '--character' in sys.argv else None
for identity in (selected.split(',') if selected else IDS):
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['idle'];bpy.context.scene.frame_set(1)
    scene=bpy.context.scene;scene.view_settings.view_transform='Standard';scene.view_settings.look='None';scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.image_settings.color_depth='8';scene.render.image_settings.compression=100
    meshes=[o for o in rig.children_recursive if o.type=='MESH'];materials={m for o in meshes for m in o.data.materials}
    def bounds(objects):
        z=[]
        for obj in objects:
            ev=obj.evaluated_get(bpy.context.evaluated_depsgraph_get());mesh=ev.to_mesh()
            z.extend((ev.matrix_world@v.co).z for v in mesh.vertices);ev.to_mesh_clear()
        return min(z),max(z)
    idle_lo,idle_hi=bounds(meshes)
    rig.data.pose_position='REST';bpy.context.view_layer.update()
    rest_lo,rest_hi=bounds(meshes)
    skin_lo,skin_hi=bounds([o for o in meshes if '_skin_surface' in o.name])
    geometry={'idleHeightMetres':idle_hi-idle_lo,'restHeightMetres':rest_hi-rest_lo,'restBodyHeightMetres':skin_hi-rest_lo,'measurement':'Actual evaluated sole-to-top bounds; body excludes hair and held props. profile.height is the original concept envelope, not a post-haircut body scale command.'}
    rig.data.pose_position='POSE';bpy.context.view_layer.update()
    image_nodes=[n for mat in materials for n in mat.node_tree.nodes if n.type=='TEX_IMAGE' and n.image]
    folder=OUT/identity;authoring=SOURCE/'textures'/identity;authoring.mkdir(parents=True,exist_ok=True)
    before_bytes=sum(p.stat().st_size for p in (folder/'textures').glob('*.png'));source_images={}
    previous=json.loads((folder/'manifest.json').read_text()).get('lod',{})
    for node in image_nodes:
        image=node.image;source_path=Path(bpy.path.abspath(image.filepath));name=source_path.name;high=authoring/name
        if source_path.resolve()!=high.resolve():shutil.copy2(source_path,high)
        source_images[name]=high;image.filepath='//'+os.path.relpath(high,SOURCE).replace('\\','/')
    # This source save contains the full geometry and full-resolution texture
    # references. All operations below affect only the exported runtime copy.
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{identity}.blend'),relative_remap=False)
    # Keep the MPFB refinement editable in the source, but export its evaluated
    # geometry. Runtime Cocos actors must not depend on default morph weights.
    for obj in meshes:
        if obj.data.shape_keys and obj.get('mpfb_targets'):TargetService.bake_targets(obj)
    textures=[]
    for name,high in source_images.items():
        image=bpy.data.images.load(str(high),check_existing=False)
        principal=identity in ['raphael','mira']
        limit=(1024 if principal else 512) if name=='skin.png' else ((256 if principal else 128) if name in ['eyes.png','brows.png'] else 256)
        if name=='lashes.png' or (name=='haircards.png' and not principal):limit=128
        width,height=image.size
        if max(width,height)>limit:
            scale=limit/max(width,height);image.scale(max(1,round(width*scale)),max(1,round(height*scale)))
        pixels=np.array(image.pixels[:],dtype=np.float32).reshape(-1,4)
        linear=np.clip(pixels[:,:3],0,1)
        srgb=np.where(linear<=.0031308,linear*12.92,1.055*np.power(linear,1/2.4)-.055)
        # Keep 7 bits/channel on skin, 5 on maps whose original procedural grain
        # cost more bytes than visible detail. Alpha masks retain full precision.
        levels=127 if name=='skin.png' else 31
        srgb=np.round(srgb*levels)/levels
        pixels[:,:3]=np.where(srgb<=.04045,srgb/12.92,np.power((srgb+.055)/1.055,2.4))
        image.pixels.foreach_set(pixels.ravel())
        destination=folder/'textures'/name;image.save_render(str(destination),scene=scene);image.filepath=str(destination)
        for node in image_nodes:
            if Path(node.image.filepath).name==name:node.image=image
        textures.append('textures/'+name)
    for path in (folder/'textures').glob('*.png'):
        if path.name not in source_images:
            assert path.resolve().is_relative_to((folder/'textures').resolve());path.unlink()
    before_tris=sum(tris(o) for o in meshes);rig.data.pose_position='REST';bpy.context.view_layer.update();eligible=[]
    for obj in meshes:
        ratio=1
        if '_haircards_surface' in obj.name:ratio=min(1,(7000 if identity in ['raphael','mira'] else 3000)/max(1,tris(obj)))
        elif '_libraryboots_surface' in obj.name:ratio=.65 if identity in ['raphael','mira'] else .45
        elif '_librarycowl_surface' in obj.name:ratio=.70 if identity in ['raphael','mira'] else .50
        elif '_hair_surface' in obj.name:ratio=.45 if identity in ['raphael','mira'] else .30
        elif '_brass_surface' in obj.name:ratio=.55 if identity in ['raphael','mira'] else .38
        elif obj.name=='male_casualsuit01':ratio=.80 if identity in ['raphael','mira'] else .62
        elif '_linen_surface' in obj.name:ratio=.7 if identity in ['raphael','mira'] else .48
        elif '_vest_surface' in obj.name:ratio=.85 if identity in ['raphael','mira'] else .65
        elif '_belt_surface' in obj.name:ratio=.7
        elif '_steel_surface' in obj.name:ratio=.8 if identity in ['raphael','mira'] else .6
        if ratio<1:eligible.append(obj);decimate(obj,ratio)
    target=40000 if identity=='raphael' else (38000 if identity=='mira' else 30000)
    current=sum(tris(o) for o in meshes)
    if current>target:
        variable=sum(tris(o) for o in eligible);fixed=current-variable
        ratio=max(.15,(target-fixed)/max(1,variable))
        for obj in eligible:decimate(obj,ratio)
    bone_names={b.name for b in rig.data.bones};max_influences=0
    for obj in meshes:
        for vertex in obj.data.vertices:
            influences=sorted([(g.group,g.weight) for g in vertex.groups if obj.vertex_groups[g.group].name in bone_names and g.weight>1e-6],key=lambda p:-p[1])
            for index,weight in influences[4:]:obj.vertex_groups[index].remove([vertex.index])
            total=sum(w for _,w in influences[:4])
            for index,weight in influences[:4]:obj.vertex_groups[index].add([vertex.index],weight/total,'REPLACE')
            max_influences=max(max_influences,len(influences[:4]))
    rig.data.pose_position='POSE';bpy.context.view_layer.update();bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for obj in meshes:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    fbx=folder/f'{identity}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=.001,path_mode='RELATIVE',embed_textures=False)
    after_bytes=sum(p.stat().st_size for p in (folder/'textures').glob('*.png'));after_tris=sum(tris(o) for o in meshes)
    report={'sourceTriangles':before_tris,'runtimeTriangles':after_tris,'textureBytesBefore':previous.get('textureBytesBefore',before_bytes),'textureBytesAfter':after_bytes,'fbxBytes':fbx.stat().st_size,'sourceGeometryPreserved':True,'skinMaxSize':1024 if identity in ['raphael','mira'] else 512,'constantCurveThreshold':.001}
    reports[identity]=report
    manifest_path=folder/'manifest.json';manifest=json.loads(manifest_path.read_text());manifest['lod']=report;manifest['triangles']=after_tris;manifest['maxInfluences']=max_influences;manifest['textures']=textures;manifest['geometry']=geometry;manifest_path.write_text(json.dumps(manifest,indent=2))
    print('[OPTIMIZED]',identity,json.dumps(report),flush=True)
report_path=OUT/'optimization-report.json'
previous_reports=json.loads(report_path.read_text()) if selected and report_path.exists() else {}
previous_reports.update(reports);report_path.write_text(json.dumps(previous_reports,indent=2))
print('[TOTALS]',sum(v['textureBytesBefore'] for v in reports.values()),'->',sum(v['textureBytesAfter'] for v in reports.values()),'texture bytes;',sum(v['runtimeTriangles'] for v in reports.values()),'triangles',flush=True)
