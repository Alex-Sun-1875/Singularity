"""Read-only scene inspection; writes validation only, does not alter model/render."""
from pathlib import Path
import bpy,json,hashlib
P=Path(__file__).parent;OUT=P.parents[2]/'assets/studies/hero-static-remake'
bpy.ops.wm.open_mainfile(filepath=str(P/'hero_static_bust_feasibility.blend'))
s=bpy.context.scene
head=bpy.data.objects.get('CONTINUOUS LANDMARK FACE / real eye apertures')
r={
 'art_status':'FAILED INTERNAL FEASIBILITY GATE — DO NOT PRODUCE, SHIP, OR RIG',
 'saved_blend_reopened':True,
 'actual_model_render':'previews/static_bust_feasibility_v1.png',
 'image_is_concept_or_projection':False,
 'mesh_objects':sum(o.type=='MESH' for o in s.objects),
 'curve_objects':sum(o.type=='CURVE' for o in s.objects),
 'armatures':sum(o.type=='ARMATURE' for o in s.objects),
 'animation_actions':len(bpy.data.actions),
 'head_vertices':len(head.data.vertices),
 'head_polygons':len(head.data.polygons),
 'external_image_dependencies':[im.filepath for im in bpy.data.images if im.source=='FILE' and not im.packed_file],
 'new_source_only':True,
 'visual_failures':['Exposed bulging eye globes; eye sockets do not occlude them naturally','Wrong facial planes and character likeness','Helmet-shaped hair mass with uniform straight fringe','Scarf reads as rigid sheet, not hanging cloth','Shoulder plate intersects linen sleeve; tailoring incomplete'],
 'stopped_before':['Full body','Rigging','Animation','Game integration','External upload'],
 'next_requirement':'A capable targeted manual anatomical/garment sculpting and hair-grooming workflow, or separately authorized and license-reviewed high-quality base geometry. Current code-only procedural reconstruction has not crossed the quality gap.'
}
for p in [P/'hero_static_bust_feasibility.blend',OUT/'previews/static_bust_feasibility_v1.png']:
 r[p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
(OUT/'technical-facts.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print(json.dumps(r,ensure_ascii=False,indent=2))
