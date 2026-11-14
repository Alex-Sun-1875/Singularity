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
                override='skin-head.png'if part=='head'else'skin-hands.png'if'Regular'in material.name else'cloth-burgundy.png'if part=='body'and'Ranger'in material.name else'cloth-charcoal.png'if part in ['arms','legs','hood']and'Ranger'in material.name else None
                if override:path=BASE/'textures'/override;record['maps']['albedo']='../appearance-v2/textures/'+override
            node.image=bpy.data.images.load(str(path),check_existing=True)
pipeline.prepare_sources(objects,manifest)

# Only replace the hairstyle. Head/eyes/brows are the original current mesh and UV.
old_hair=next(o for o in objects if o.get('nativePart')=='hair');head=next(o for o in objects if o.get('nativePart')=='head');low,high=hair_library._bounds(head)
meta=hair_library._asset('short02');hair=hair_library._import_hair(meta);hair_library._fit(hair,(.210,.214,.174),(0,.018),high[2]+.027)
hm=hair_library._hair_material('raphael','wavy',meta,(.42,.45,.49));hair_library._bind(hair,'raphael','short_wavy',rig,hm)
bs=next(n for n in hm.node_tree.nodes if n.type=='BSDF_PRINCIPLED');source=next(n for n in hm.node_tree.nodes if n.type=='TEX_IMAGE');source.image=bpy.data.images.load(str(BASE/'textures/silver-wavy-hair.png'));hm.node_tree.links.new(source.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.76
source_uv=hair.data.uv_layers.active.name
for node in hm.node_tree.nodes:
    if node.type=='TEX_IMAGE'and not node.inputs['Vector'].is_linked:uv=hm.node_tree.nodes.new('ShaderNodeUVMap');uv.uv_map=source_uv;hm.node_tree.links.new(uv.outputs[0],node.inputs['Vector'])
bpy.data.objects.remove(old_hair,do_unlink=True);objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
records.pop(next(k for k,r in records.items()if r['parts']==['hair']))
records[hm.name]={'runtimeName':hm.name,'parts':['hair'],'maps':{'albedo':'../appearance-v2/textures/silver-wavy-hair.png'},'sourcePBR':{'effectiveFactors':{'roughness':.76,'metallic':0}},'alphaClip':True,'doubleSided':True,'alphaThreshold':.28}

# Reuse the accepted 2D embroidery on the original jerkin UV, retaining its belts/forms.
body=next(o for o in objects if o.get('nativePart')=='body'and'belt'not in o.name.lower());old=body.data.materials[0];material=old.copy();material.name='Raphael_Refined_Native_Jerkin';body.data.materials[0]=material;record=copy.deepcopy(records[old.name]);record['runtimeName']=material.name;record['parts']=['body'];records[material.name]=record
tree=material.node_tree;bs=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED');base=bs.inputs['Base Color'].links[0].from_socket;native_uv=body.data.uv_layers.active.name
native=tree.nodes.new('ShaderNodeUVMap');native.uv_map=native_uv
for node in list(tree.nodes):
    if node.type=='TEX_IMAGE'and not node.inputs['Vector'].is_linked:tree.links.new(native.outputs[0],node.inputs['Vector'])
layer=body.data.uv_layers.new(name='EmbroideryProjection');sx=abs(rig.data.bones['upperarm_l'].head_local.x)/.1919;sz=rig.data.bones['neck_01'].head_local.z/1.5205
for polygon in body.data.polygons:
    for i in polygon.loop_indices:
        co=body.data.vertices[body.data.loops[i].vertex_index].co;layer.data[i].uv=(.25+co.x/(.84*sx)if polygon.normal.y<0 else .75-co.x/(.84*sx),(co.z/sz-.85)/.72)
projection=tree.nodes.new('ShaderNodeUVMap');projection.uv_map=layer.name;art=tree.nodes.new('ShaderNodeTexImage');art.image=bpy.data.images.load(str(ROOT/'source-art/characters/3d-appearance-v1/references/coat-design-atlas.png'));art.extension='EXTEND';tree.links.new(projection.outputs[0],art.inputs['Vector']);sep=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(art.outputs['Color'],sep.inputs[0]);mask=tree.nodes.new('ShaderNodeMapRange');mask.inputs['From Min'].default_value=.02;mask.inputs['From Max'].default_value=.30;mask.clamp=True;tree.links.new(sep.outputs['Green'],mask.inputs['Value'])
fabric=tree.nodes.new('ShaderNodeTexImage');fabric.image=bpy.data.images.load(str(BASE/'textures/fabric-mask.png'));fabric.image.colorspace_settings.name='Non-Color';tree.links.new(native.outputs[0],fabric.inputs['Vector']);mul=tree.nodes.new('ShaderNodeMath');mul.operation='MULTIPLY';tree.links.new(mask.outputs[0],mul.inputs[0]);tree.links.new(fabric.outputs['Color'],mul.inputs[1]);mix=tree.nodes.new('ShaderNodeMixRGB');mix.inputs[2].default_value=(.46,.29,.10,1);tree.links.new(mul.outputs[0],mix.inputs[0]);tree.links.new(base,mix.inputs[1]);tree.links.new(mix.outputs[0],bs.inputs['Base Color'])
body.data.uv_layers.active=body.data.uv_layers[native_uv];body.data.uv_layers[native_uv].active_render=True
image=pipeline.bake([body],'native-jerkin-embroidery',1024,'Color');pipeline.save_image(image,BASE/'textures/jerkin-embroidered.png');record['maps']['albedo']='../appearance-v2/textures/jerkin-embroidered.png'
# Restore the original UV topology after baking the projected pixels.
body.data.uv_layers.remove(body.data.uv_layers['EmbroideryProjection']);body.data.uv_layers.active=body.data.uv_layers[native_uv]
node=tree.nodes.new('ShaderNodeTexImage');node.image=image;tree.links.new(native.outputs[0],node.inputs['Vector']);tree.links.new(node.outputs['Color'],bs.inputs['Base Color'])
assert {o.name:mesh_digest(o)for o in face_objects}==face_before
assert {o.name:mesh_digest(o)for o in objects if o.get('nativePart')!='hair'}==body_before
assert pipeline.curves()==action_hash and pipeline.skeleton(rig)==bind_hash
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
scene.frame_set(0);scene.name='raphael-refined';pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-refined.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False)
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
parts={}
for obj in objects:parts.setdefault(obj['nativePart'],{'nodes':[],'defaultVisible':bool(obj.get('defaultVisible',True))})['nodes'].append(obj.name)
used={m.name for o in objects for m in o.data.materials};manifest.update(appearanceRevision='2d-design-v2',prefabRoot='raphael-refined',appearanceReview='source-art/characters/3d-appearance-v2/README.md',materials=[r for k,r in records.items()if k in used],parts=parts,triangles=sum(pipeline.triangles(o)for o in objects))
(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(BASE/'preservation.json').write_text(json.dumps({'faceHeadEyesBrowsGeometryUVWeightsUnchanged':True,'allBodyClothingGeometryUVWeightsUnchanged':True,'rigBindUnchanged':True,'all14MotionCurvesUnchanged':True,'faceMeshHashes':face_before,'bodyMeshHashes':body_before,'actionHash':action_hash,'bindHash':bind_hash,'hairstyle':meta,'meshes':len(objects),'triangles':manifest['triangles']},indent=2)+'\n',encoding='utf-8');print('REFINED_NATIVE_EXPORTED',len(objects),manifest['triangles'])
