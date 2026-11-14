from pathlib import Path
import bpy,json,hashlib,sys
BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2];sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline

def digest(o):
    return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(BASE/'hair-stage.blend'));rig=bpy.data.objects['raphael_Native65']
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')];hair=next(o for o in objects if o.get('nativePart')=='hair')
hair.name='raphael_native_hair_Hair_SimpleParted'
proof=json.loads((BASE/'preservation.json').read_text())
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
for attribute in list(hair.data.color_attributes):hair.data.color_attributes.remove(attribute)
for name in [layer.name for layer in hair.data.uv_layers if layer.name!='Hair_Finish_UV']:
    hair.data.uv_layers.remove(hair.data.uv_layers[name])
hair.data.uv_layers[0].name='UVMap';hair.data.uv_layers[0].active_render=True
mat=bpy.data.materials.new('Native_Hair_Short_Fine_v4');mat.use_nodes=True;tree=mat.node_tree;bsdf=tree.nodes.get('Principled BSDF');bsdf.inputs['Metallic'].default_value=1;bsdf.inputs['Roughness'].default_value=1
coord=tree.nodes.new('ShaderNodeUVMap');coord.uv_map='UVMap'
def texture(name,data=False):
    n=tree.nodes.new('ShaderNodeTexImage');n.image=bpy.data.images.load(str(BASE/'textures'/name),check_existing=True);n.image.colorspace_settings.name='Non-Color'if data else'sRGB';tree.links.new(coord.outputs['UV'],n.inputs['Vector']);return n
color=texture('hair-detail-color.png');tree.links.new(color.outputs['Color'],bsdf.inputs['Base Color'])
normal=texture('hair-detail-normal.png',True);n=tree.nodes.new('ShaderNodeNormalMap');n.uv_map='UVMap';tree.links.new(normal.outputs['Color'],n.inputs['Color']);tree.links.new(n.outputs[0],bsdf.inputs['Normal'])
orm=texture('hair-detail-orm.png',True);sep=tree.nodes.new('ShaderNodeSeparateColor');tree.links.new(orm.outputs['Color'],sep.inputs[0]);tree.links.new(sep.outputs['Green'],bsdf.inputs['Roughness']);tree.links.new(sep.outputs['Blue'],bsdf.inputs['Metallic'])
hair.data.materials.clear();hair.data.materials.append(mat)
for p in hair.data.polygons:p.material_index=0
manifest=json.loads((BASE.parent/'3d-appearance-v3/manifest.json').read_text(encoding='utf-8'))
manifest['materials']=[r for r in manifest['materials']if 'hair'not in r.get('parts',[])]+[{
 'runtimeName':mat.name,'parts':['hair'],
 'maps':{'albedo':'../native-hair-v4/textures/hair-detail-color.png','normal':'../native-hair-v4/textures/hair-detail-normal.png','orm':'../native-hair-v4/textures/hair-detail-orm.png'},
 'sourcePBR':{'effectiveFactors':{'roughness':1,'metallic':1}},'ormChannels':{'occlusion':'r','roughness':'g','metallic':'b'},'doubleSided':True}]
manifest.update(appearanceRevision='native-short-fine-v4',prefabRoot='raphael-polish',appearanceReview='source-art/characters/3d-native-hair-v4/README.md',source=(BASE/'raphael.blend').relative_to(ROOT).as_posix(),triangles=sum(pipeline.triangles(o)for o in objects))
manifest['hairstyle']={'asset':'Original Quaternius Hair_SimpleParted','license':'CC0-1.0','source':'Official free Standard already installed','geometry':'Original authored short-hair topology and lock flow; restrained temple/crown fit up to 4.1 mm','texture':'Dedicated packed UV atlas; native broad shading with cloud fine strand detail guided by project 2D hair','physics':'Original Head binding; no simulated hair physics','rejectedLongHairSelected':False}
rig.data.pose_position='POSE';idle=bpy.data.actions['idle'];rig.animation_data.action=idle
if idle.slots:rig.animation_data.action_slot=idle.slots[0]
bpy.context.scene.frame_set(0);bpy.context.scene.name='raphael-polish';pipeline.select([rig]+objects);bpy.context.view_layer.objects.active=rig
bpy.ops.export_scene.gltf(filepath=str(BASE/'raphael-polish.glb'),export_format='GLB',use_selection=True,export_yup=True,export_animations=True,export_animation_mode='ACTIONS',export_force_sampling=True,export_frame_step=1,export_def_bones=False,export_skins=True,export_all_influences=False,export_vertex_color='NONE',export_all_vertex_colors=False,export_active_vertex_color_when_no_material=False)
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'raphael.blend'),relative_remap=False)
proof.update(renderers=len(objects),triangles=manifest['triangles'],finishedHairMeshHash=digest(hair),verifiedAfterExport=True)
(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8');(BASE/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print('NATIVE_SHORT_FINE_EXPORTED',manifest['triangles'],len(bpy.data.actions),flush=True)
