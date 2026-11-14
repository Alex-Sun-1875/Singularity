from pathlib import Path
BASE=Path(__file__).resolve().parent
source=(BASE.parent/'3d-appearance-v2/build.py').read_text(encoding='utf-8')
prefix=source[:source.index('# Only replace the hairstyle.')].replace('appearance-v2','appearance-v3')
tail=source[source.index('assert {o.name:mesh_digest(o)for o in face_objects}'):]
tail=tail.replace('raphael-refined','raphael-polish').replace('2d-design-v2','2d-design-v3').replace('3d-appearance-v2','3d-appearance-v3').replace('export_all_influences=False','export_all_influences=False,export_vertex_color=\'NONE\',export_all_vertex_colors=False').replace("'hairstyle':meta","'hairstyle':{'method':'Original native hair; smooth subdivision and restrained silhouette/forelock adjustment','source':'Quaternius CC0'}")
prefix=prefix.replace("else'cloth-charcoal.png'if part in","else'hair-silver.png'if part=='hair' else'cloth-charcoal.png'if part in")
hair='''# Smooth and tailor the ORIGINAL hairstyle; the original face is untouched.
hair=next(o for o in objects if o.get('nativePart')=='hair');z0=min(v.co.z for v in hair.data.vertices);z1=max(v.co.z for v in hair.data.vertices);center=Vector((0,.012,(z0+z1)*.5))
for vertex in hair.data.vertices:
    co=vertex.co;t=max(0,min(1,(co.z-z0)/(z1-z0)));co.x*=1+.075*t;co.y=center.y+(co.y-center.y)*(1+.035*t);co.z+=.006*t*(1-t)*4
    if co.y<-.025 and t>.30:co.y-=.006*(t-.30)/.70;co.x+=.003*t
pipeline.select([hair]);modifier=hair.modifiers.new('Smooth native short waves','SUBSURF');modifier.levels=1;modifier.render_levels=1;bpy.ops.object.modifier_apply(modifier=modifier.name)
for polygon in hair.data.polygons:polygon.use_smooth=True
for material in hair.data.materials:
    bs=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED');image=next(n for n in material.node_tree.nodes if n.type=='TEX_IMAGE'and n.image.colorspace_settings.name=='sRGB');material.node_tree.links.new(image.outputs['Color'],bs.inputs['Base Color']);bs.inputs['Roughness'].default_value=.72
    records[material.name]['sourcePBR']['effectiveFactors']['roughness']=.72
'''
(BASE/'build.py').write_text(prefix+hair+tail,encoding='utf-8')
print('Prepared original-model refinement pipeline')
