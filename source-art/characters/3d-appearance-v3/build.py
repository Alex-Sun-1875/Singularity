"""Keep the current native face/body/rig; refine only skin, hair and clothing maps."""
from pathlib import Path
import bpy,json,sys,hashlib,copy
from mathutils import Vector
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import v5_face_hair_adapter as hair_library
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-motion-tempo-v1/compact-jog.blend'))
rig=bpy.data.objects['raphael_Native65'];scene=bpy.context.scene;scene.render.fps=30;scene.render.fps_base=1;rig.data.pose_position='REST'
manifest=json.loads((ROOT/'source-art/characters/3d-appearance-v1/before/manifest.json').read_text(encoding='utf-8'));records={r['runtimeName']:r for r in manifest['materials']};original_records=copy.deepcopy(records);action_hash=pipeline.curves();bind_hash=pipeline.skeleton(rig)
def mesh_digest(o):return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in layer.data]for layer in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];face_objects=[o for o in objects if o.get('nativePart')in ['head','eyes','brows']];face_before={o.name:mesh_digest(o)for o in face_objects};body_before={o.name:mesh_digest(o)for o in objects if o.get('nativePart')!='hair'}
for obj in objects:
    part=obj['nativePart']
    for index,original in enumerate(list(obj.data.materials)):
        material=original
        if not material:continue
        original_name=material.name;source_record=original_records[original_name];material=material.copy();material.name=original_name+'_'+part+'_'+hashlib.sha256(obj.name.encode()).hexdigest()[:5];obj.data.materials[index]=material;record=copy.deepcopy(source_record);record['runtimeName']=material.name;record['parts']=[part];records[material.name]=record
        for node in material.node_tree.nodes:
            if node.type!='TEX_IMAGE'or not node.image:continue
            filename=node.image.filepath.lower();kind='normal'if'normal'in filename else'orm'if'orm'in filename else'roughness'if'rough'in filename else'albedo'
            if kind not in record['maps']:continue
            path=(ROOT/'src/cocos/assets/resources/actors/raphael'/source_record['maps'][kind]).resolve()
            if kind=='albedo':
                override='skin-head.png'if part=='head'else'skin-hands.png'if'Regular'in material.name else'cloth-burgundy.png'if part=='body'and'Ranger'in material.name else'hair-silver.png'if part=='hair' else'cloth-charcoal.png'if part in ['arms','legs','hood']and'Ranger'in material.name else None
                if override:path=BASE/'textures'/override;record['maps']['albedo']='../appearance-v3/textures/'+override
            node.image=bpy.data.images.load(str(path),check_existing=True)
pipeline.prepare_sources(objects,manifest)

# Smooth and tailor the ORIGINAL hairstyle; the original face is untouched.
hair=next(o for o in objects if o.get('nativePart')=='hair');z0=min(v.co.z for v in hair.data.vertices);z1=max(v.co.z for v in hair.data.vertices);center=Vector((0,.012,(z0+z1)*.5))
for vertex in hair.data.vertices:
    co=vertex.co;t=max(0,min(1,(co.z-z0)/(z1-z0)));co.x*=1+.075*t;co.y=center.y+(co.y-center.y)*(1+.035*t);co.z+=.006*t*(1-t)*4
    if co.y<-.025 and t>.30:co.y-=.006*(t-.30)/.70;co.x+=.003*t
pipeline.select([hair]);modifier=hair.modifiers.new('Smooth native short waves','SUBSURF');modifier.levels=1;modifier.render_levels=1;bpy.ops.object.modifier_apply(modifier=modifier.name)
for polygon in hair.data.polygons:polygon.use_smooth=True
for material in hair.data.materials:
    bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');image=next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE'and n.image.colorspace_settings.name=='sRGB');material.node_tree.links.new(image.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.72
    records[material.name]['sourcePBR']['effectiveFactors']['roughness']=.72
assert {o.name:mesh_digest(o)for o in face_objects}==face_before
assert {o.name:mesh_digest(o)for o in objects if o.get('nativePart')!='hair'}==body_before
assert pipeline.curves()==action_hash and pipeline.skeleton(rig)==bind_hash
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
scene.frame_set(0);scene.name='raphael-polish';pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
parts={}
for obj in objects:parts.setdefault(obj['nativePart'],{'nodes':[],'defaultVisible':bool(obj.get('defaultVisible',True))})['nodes'].append(obj.name)
used={m.name for o in objects for m in o.data.materials};manifest.update(appearanceRevision='2d-design-v3',prefabRoot='raphael-polish',appearanceReview='source-art/characters/3d-appearance-v3/README.md',materials=[r for k,r in records.items()if k in used],parts=parts,triangles=sum(pipeline.triangles(o)for o in objects))
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(BASE/'preservation.json').write_text(json.dumps({'faceHeadEyesBrowsGeometryUVWeightsUnchanged':True,'allBodyClothingGeometryUVWeightsUnchanged':True,'rigBindUnchanged':True,'all14MotionCurvesUnchanged':True,'faceMeshHashes':face_before,'bodyMeshHashes':body_before,'actionHash':action_hash,'bindHash':bind_hash,'hairstyle':{'method':'Original native hair; smooth subdivision and restrained silhouette/forelock adjustment','source':'Quaternius CC0'},'meshes':len(objects),'triangles':manifest['triangles']},indent=2)+'\n',encoding='utf-8');print('REFINED_NATIVE_EXPORTED',len(objects),manifest['triangles'])
