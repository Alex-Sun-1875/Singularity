from pathlib import Path
import bpy,json,math
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'assets/studies/hero-g1-motion-study';REV=OUT/'revision-local-01';REV.mkdir(exist_ok=True)
bpy.ops.wm.open_mainfile(filepath=str(Path(__file__).with_name('hero_g1_motion_study.blend')))
s=bpy.context.scene;cam=s.camera;rig=bpy.data.objects['HeroStudy_RIG'];s.frame_set(1)
scale=2.35;target=176/(512/scale*math.cos(math.radians(32)))
image=json.loads((OUT/'image-validation.json').read_text())
def px(v):
 a=world_to_camera_view(s,cam,v);return [float(a.x*512),float((1-a.y)*512)]
results={}
for a,d in zip([45,135,225,315],['front_right','back_right','back_left','front_left']):
 az=math.radians(a);cam.location=(5*math.sin(az),-5*math.cos(az),target+5*math.tan(math.radians(32)));cam.rotation_euler=(Vector((0,0,target))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.ortho_scale=scale;bpy.context.view_layer.update()
 dg=bpy.context.evaluated_depsgraph_get();groups={}
 for group,prefixes in [('head_and_hair',('continuous sculpted adult head','continuous swept brown hair sculpt','short broad swept hair relief')),('feet',('shaped leather boot last','hard leather sole','stitched boot welt'))]:
  ys=[]
  for o in rig.children:
   if o.type=='MESH' and o.name.startswith(prefixes):
    ev=o.evaluated_get(dg);me=ev.to_mesh();ys.extend(px(o.matrix_world@v.co)[1] for v in me.vertices);ev.to_mesh_clear()
  groups[group]={'top_y':min(ys),'bottom_y':max(ys)}
 bb=image['directions'][d]['bbox'];root=px(Vector((0,0,0)))
 results[d]={'root_px':root,'canonical_axis_head_marker_px':px(Vector((0,0,1.84))),'posed_head_bone_tip_px':px(rig.matrix_world@rig.pose.bones['head'].tail),'render_alpha_bbox':bb,'alpha_height':bb[3]-bb[1],'root_to_alpha_top_height':root[1]-bb[1],'alpha_below_root':bb[3]-root[1],'component_projected_extents':groups}
r={'source':'unchanged saved baseline blend; same frame 1; actual existing alpha bounds','camera':{'projection':'ORTHO','elevation_degrees':32,'scale_m':scale,'target_z_m':target,'image_size':[512,512]},'views':results}
r['alpha_height_range_px']=max(x['alpha_height'] for x in results.values())-min(x['alpha_height'] for x in results.values())
r['root_to_top_height_range_px']=max(x['root_to_alpha_top_height'] for x in results.values())-min(x['root_to_alpha_top_height'] for x in results.values())
r['below_root_range_px']=max(x['alpha_below_root'] for x in results.values())-min(x['alpha_below_root'] for x in results.values())
r['conclusion']='The 14px raw alpha-height range is not camera/root scale drift: 10px is foot/toe projection below a shared ground origin, and 4px is upper silhouette variation. Keep identical world scale and origin. Root-to-top range is 2px at 256 or 1.5px at 192; raw silhouette-height criterion remains 7px at 256 and needs an explicit criterion distinction, not per-view resizing.'
(REV/'registration-diagnosis.json').write_text(json.dumps(r,ensure_ascii=False,indent=2));print(json.dumps(r,ensure_ascii=False,indent=2))
