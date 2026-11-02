"""Validate the actual saved scene and export; never grants an art-style pass."""
from pathlib import Path
import bpy,json,math,struct,tempfile,numpy as np
from mathutils import Vector
from bpy_extras.object_utils import world_to_camera_view
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'assets/studies/hero-g1-motion-study'
SOURCE=Path(__file__).resolve().parent
bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'hero_g1_motion_study.blend'))
scene=bpy.context.scene;rig=bpy.data.objects['HeroStudy_RIG'];meshes=[o for o in rig.children if o.type=='MESH']
report={'art_approved':False,'gate':'G1 NOT PASSED','checks':{},'weights':{},'known_scope':'idle only; not walk/attack/complete production rig'}
report['checks']['actual_mesh_objects']=len(meshes)
report['checks']['armature_bones']=len(rig.data.bones)
report['checks']['animation_action']=rig.animation_data.action.name
report['checks']['deforming_meshes']=sum(any(m.type=='ARMATURE' and m.object==rig for m in o.modifiers) for o in meshes)
counts={'single_weight_vertices':0,'multi_weight_vertices':0,'unweighted_vertices':0};bad=0
for o in meshes:
 for v in o.data.vertices:
  active=[g.weight for g in v.groups if g.weight>1e-7]
  counts['unweighted_vertices' if not active else 'single_weight_vertices' if len(active)==1 else 'multi_weight_vertices']+=1
  if active and abs(sum(active)-1)>1e-5:bad+=1
report['weights']=counts;report['checks']['non_normalized_weight_vertices']=bad
coords={};anchors=[];feet=[]
for fr in [1,7,13,19,25,31,37,43,49]:
 scene.frame_set(fr);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get()
 p=world_to_camera_view(scene,scene.camera,rig.matrix_world@rig.pose.bones['root'].head);anchors.append([float(p.x*512),float((1-p.y)*512)])
 feet.append([(rig.matrix_world@rig.pose.bones[n].head)[:] for n in ['foot.R','foot.L']])
 sample=[]
 for o in meshes:
  if o.name.startswith(('continuous sculpted adult head','short travel cape','fitted leather jerkin','shaped leather boot last')):
   ev=o.evaluated_get(dg);me=ev.to_mesh();sample.extend([(o.matrix_world@v.co)[:] for v in me.vertices]);ev.to_mesh_clear()
 coords[fr]=sample
report['checks']['projected_root_px_by_sample']=anchors
report['checks']['max_root_drift_px']=max(math.dist(anchors[0],a) for a in anchors)
report['checks']['max_foot_bone_drift_m']=max(math.dist(feet[0][j],f[j]) for f in feet for j in [0,1])
report['checks']['idle_loop_endpoint_max_vertex_delta_m']=max(math.dist(a,b) for a,b in zip(coords[1],coords[49]))
report['checks']['idle_frame13_max_vertex_delta_m']=max(math.dist(a,b) for a,b in zip(coords[1],coords[13]))
report['checks']['packed_image_count']=sum(bool(i.packed_file) for i in bpy.data.images if i.source=='FILE' or i.type=='IMAGE')
report['checks']['external_image_paths_missing']=[i.filepath for i in bpy.data.images if i.filepath and i.name!='Render Result' and not i.packed_file and not Path(bpy.path.abspath(i.filepath)).exists()]
# Independent glTF structure and animation existence, no claim that importer reproduces node bump.
p=OUT/'models/hero_g1_motion_study.glb';data=p.read_bytes();magic,version,length=struct.unpack('<4sII',data[:12]);clen,ctype=struct.unpack('<II',data[12:20]);g=json.loads(data[20:20+clen]);report['glb']={'magic_ok':magic==b'glTF','version':version,'length_matches':length==len(data),'skins':len(g.get('skins',[])),'animations':len(g.get('animations',[])),'animation_channels':[len(a['channels']) for a in g.get('animations',[])],'embedded_images':len(g.get('images',[])),'mesh_nodes_with_skin':sum('skin' in n for n in g.get('nodes',[])),'bytes':len(data)}
assert len(meshes)>0 and len(rig.data.bones)>0
assert counts['unweighted_vertices']==0 and bad==0
assert report['checks']['max_root_drift_px']<1e-6
assert report['checks']['max_foot_bone_drift_m']<1e-7
assert report['checks']['idle_loop_endpoint_max_vertex_delta_m']<1e-6
assert report['checks']['idle_frame13_max_vertex_delta_m']>.005
assert not report['checks']['external_image_paths_missing']
assert report['glb']['skins']>0 and report['glb']['animations']>0
# Re-render from the saved scene, compare actual RGBA pixels (not just file existence).
scene.frame_set(1)
with tempfile.TemporaryDirectory(prefix='hero-study-check-') as td:
 scene.render.filepath=str(Path(td)/'rerender.png');bpy.ops.render.render(write_still=True)
 ia=bpy.data.images.load(scene.render.filepath,check_existing=False)
 ib=bpy.data.images.load(str(OUT/'frames/hero_study__idle__front_right__001.png'),check_existing=False)
 aa=np.empty(len(ia.pixels),dtype=np.float32);bb=np.empty(len(ib.pixels),dtype=np.float32);ia.pixels.foreach_get(aa);ib.pixels.foreach_get(bb)
 report['checks']['saved_blend_rerender_pixel_identical']=np.array_equal(aa,bb)
 bpy.data.images.remove(ia);bpy.data.images.remove(ib)
assert report['checks']['saved_blend_rerender_pixel_identical']
report['technical_checks_passed']=True
(OUT/'technical-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
print(json.dumps(report,ensure_ascii=False,indent=2))
