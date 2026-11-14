"""Reuse the project's native65 natural-head/library-hair adapter for a probe."""
from pathlib import Path
import bpy,json,sys,bmesh
ROOT=Path(__file__).resolve().parents[3];BASE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'tools/model-pipeline'));import v5_face_hair_adapter as adapter
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters/3d-motion-tempo-v1/compact-jog.blend'))
rig=bpy.data.objects['raphael_Native65'];manifest=json.loads((ROOT/'src/cocos/assets/resources/actors/raphael/manifest.json').read_text(encoding='utf-8'))
curly='--curly'in sys.argv
adapter.STYLE['raphael'].update(size=(.218,.211,.190),offset=(0,.012,.034),tint=(.36,.38,.42),smile=.0003,brow=.0003,asym=.0002,jaw=-.0018,cheek=.0034)
if curly:
    adapter.STYLE['raphael']['asset']='o4saken_curly01';original_import=adapter._import_hair
    def cropped_import(meta):
        obj=original_import(meta);low,high=adapter._bounds(obj)
        bm=bmesh.new();bm.from_mesh(obj.data)
        bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,low[2]+(high[2]-low[2])*.43),plane_no=(0,0,1),clear_inner=True,clear_outer=False,dist=1e-6)
        bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS');bm.to_mesh(obj.data);bm.free()
        bpy.context.view_layer.objects.active=obj
        count=sum(len(p.vertices)-2 for p in obj.data.polygons)
        if count>18000:
            mod=obj.modifiers.new('NativeHairBudget','DECIMATE');mod.ratio=18000/count;mod.use_collapse_triangulate=True;bpy.ops.object.modifier_apply(modifier=mod.name)
        return obj
    adapter._import_hair=cropped_import
record=adapter.apply('raphael',rig,manifest)
# Keep dark ash-brown eyebrows, as in the silver-haired 2D face.
obj=next(o for o in bpy.data.objects if o.get('nativePart')=='brows');material=obj.data.materials[0]
for n in material.node_tree.nodes:
    if n.type=='MIX_RGB'and n.blend_type=='MULTIPLY':n.inputs[2].default_value=(.045,.034,.027,1)
material['v6Tint']=[.045,.034,.027]
(BASE/'face-hair-source.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')
suffix='curly-pilot'if curly else'head-pilot'
bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(BASE/(suffix+'.blend')),relative_remap=False)
adapter._render('raphael',rig,BASE/(suffix+'.png'))
