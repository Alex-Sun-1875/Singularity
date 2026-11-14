"""Refine the installed native short hairstyle; bake its own UV/PBR maps."""
from pathlib import Path
import bpy,sys,json,hashlib,math
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

BASE=Path(__file__).resolve().parent;ROOT=BASE.parents[2]
sys.path.insert(0,str(ROOT/'tools/model-pipeline'))
import cocos_v5_character_redesign as pipeline
import cocos_native_characters as native
SOURCE=ROOT/'source-art/characters/3d-appearance-v3'
KIT=ROOT/'src/.tools/quaternius-ready-kits/universal-base-characters-standard/Universal Base Characters[Standard]'
PATH=KIT/'Hairstyles/Rigged to Head Bone/glTF (Godot -Unreal)/Hair_SimpleParted.gltf'

def digest(o):
    return hashlib.sha256(repr(([tuple(v.co)for v in o.data.vertices],[tuple(p.vertices)for p in o.data.polygons],[[tuple(v.uv)for v in l.data]for l in o.data.uv_layers],[(g.name,g.index)for g in o.vertex_groups],[[tuple((g.group,g.weight))for g in v.groups]for v in o.data.vertices])).encode()).hexdigest()

bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'raphael.blend'))
rig=bpy.data.objects['raphael_Native65'];rig.data.pose_position='REST';bpy.context.scene.frame_set(0)
original=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
proof={'nonHairMeshHashes':{o.name:digest(o)for o in original if o.get('nativePart')!='hair'},'actionHash':pipeline.curves(),'bindHash':pipeline.skeleton(rig)}
source_rig,meshes=native.imported(PATH);assert len(meshes)==1
hair=meshes[0];correction=rig.data.bones['Head'].matrix_local@source_rig.data.bones['Head'].matrix_local.inverted()
head=next(o for o in original if o.get('nativePart')=='head');surface=BVHTree.FromObject(head,bpy.context.evaluated_depsgraph_get())
root_values=[];changed=[]
for v in hair.data.vertices:
    co=correction@v.co;before=co.copy()
    # Keep the author's short parted silhouette. Give temples a little body,
    # settle the tall crown and softly relax the front sweep.
    side=max(0,min(1,(abs(co.x)-.05)/.035))*max(0,min(1,(1.795-co.z)/.09))
    co.x+=math.copysign(.0035*side,co.x)
    co.z-=.003*max(0,min(1,(co.z-1.795)/.05))
    if co.y<-.025 and co.z>1.755:
        co.y-=.003*max(0,min(1,(co.z-1.755)/.07))
    near,n,_,distance=surface.find_nearest(co)
    gap=(co-near).dot(n) if near is not None else .02
    if near is not None and distance<.008 and co.z>1.755 and gap<.002:
        co+=n*min(.004,.002-gap)
    root_values.append(.86+.14*max(0,min(1,gap/.022)))
    v.co=co;changed.append((co-before).length)
native.transfer(hair,rig);hair.name='raphael_native_hair_Hair_SimpleParted';hair['nativePart']='hair';hair['defaultVisible']=True
bpy.data.objects.remove(source_rig,do_unlink=True)
for o in original:
    if o.get('nativePart')=='hair':bpy.data.objects.remove(o,do_unlink=True)

# Preserve the author's UV charts and flow; use Blender's packing rather than
# inventing a second hair texture layout by hand.
uv=hair.data.uv_layers[0];uv.name='Hair_Source_UV'
mat=hair.data.materials[0];mat.name='Native_Hair_Short_Detailed_Source';tree=mat.node_tree
bsdf=next(n for n in tree.nodes if n.type=='BSDF_PRINCIPLED')
coord=tree.nodes.new('ShaderNodeUVMap');coord.uv_map='Hair_Source_UV'
for node in tree.nodes:
    if node.type=='TEX_IMAGE' and node.image:
        tree.links.new(coord.outputs['UV'],node.inputs['Vector'])
        if 'basecolor' in (node.image.name+node.image.filepath).lower():node.image=bpy.data.images.load(str(BASE/'native-silver-source.png'),check_existing=True)
    if node.type=='NORMAL_MAP':node.uv_map='Hair_Source_UV'
attribute=hair.data.color_attributes.new(name='HairRootShade',type='FLOAT_COLOR',domain='POINT')
for c,value in zip(attribute.data,root_values):c.color=(value,value,value,1)
pipeline.select([hair]);smooth=hair.modifiers.new('Native lock surface refinement','SUBSURF');smooth.levels=1;smooth.render_levels=1
bpy.ops.object.modifier_apply(modifier=smooth.name)
for polygon in hair.data.polygons:polygon.use_smooth=True
for v in hair.data.vertices:
    if v.co.z<1.70:continue
    near,n,_,distance=surface.find_nearest(v.co)
    if near is not None and distance<.006:
        gap=(v.co-near).dot(n)
        if gap<.0015:v.co+=n*min(.0035,.0015-gap)
color_node=tree.nodes.new('ShaderNodeVertexColor');color_node.layer_name='HairRootShade'
base_socket=bsdf.inputs['Base Color'];old=base_socket.links[0].from_socket
mix=tree.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1
tree.links.new(old,mix.inputs[1]);tree.links.new(color_node.outputs['Color'],mix.inputs[2]);tree.links.new(mix.outputs[0],base_socket)
new=hair.data.uv_layers.new(name='Hair_Finish_UV',do_init=True);hair.data.uv_layers.active=new;new.active_render=True
pipeline.select([hair]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.uv.select_all(action='SELECT')
bpy.ops.uv.average_islands_scale();bpy.ops.uv.pack_islands(rotate=False,margin=.012)
bpy.ops.object.mode_set(mode='OBJECT')
maps=BASE/'textures';maps.mkdir(parents=True,exist_ok=True)
for channel,name in [('Color','hair-base.png'),('Normal','hair-normal-base.png')]:
    image=pipeline.bake([hair],'native-short-'+channel,1024,channel);pipeline.save_image(image,maps/name)

# Store the actual occupied UV faces for the later local protective composite.
uv=hair.data.uv_layers['Hair_Finish_UV'];faces=[[[float(x)for x in uv.data[li].uv]for li in p.loop_indices]for p in hair.data.polygons]
(BASE/'uv-faces.json').write_text(json.dumps(faces),encoding='utf-8')
objects=[o for o in bpy.data.objects if o.type=='MESH'and o.get('nativePart')]
assert {o.name:digest(o)for o in objects if o.get('nativePart')!='hair'}==proof['nonHairMeshHashes']
assert pipeline.curves()==proof['actionHash']and pipeline.skeleton(rig)==proof['bindHash']
proof.update(faceBodyUnchanged=True,all14ActionsUnchanged=True,bindPoseUnchanged=True,sourceAsset=PATH.relative_to(ROOT).as_posix(),sourceSHA256=pipeline.sha(PATH),hairTriangles=pipeline.triangles(hair),maximumControlCageAdjustmentMetres=max(changed),surfaceRefinement='One native Blender subdivision level on authored locks; restrained scalp clearance after smoothing',uvMethod='Original UV islands packed by native Blender tools; original PBR detail baked to dedicated 1024 atlas')
(BASE/'preservation.json').write_text(json.dumps(proof,indent=2)+'\n',encoding='utf-8')
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'hair-stage.blend'),relative_remap=False)
print('NATIVE_SHORT_HAIR_STAGED',json.dumps(proof),flush=True)
