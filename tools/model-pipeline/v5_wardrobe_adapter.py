"""Fit v5 costume silhouettes onto the existing native65/67 character scene.

Only garment geometry/materials change.  Original hands, shoes, rig/rest matrices
and Action datablocks are not edited. Blender's Data Transfer modifier transfers
the supplied CC0 garment's existing skin weights; there is no skin solver here.
New shapes cover the concept-specific coats/capes absent from the free kits.
"""
from pathlib import Path
import math
import hashlib
import bpy
import bmesh
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parents[2]
TAU = math.tau
PALETTES = {
    'raphael': ((.19,.075,.029),(.035,.095,.085)),
    'mira': ((.105,.007,.018),(.105,.007,.018)),
    'lorn': ((.038,.065,.12),(.037,.055,.09)),
    'nightqi': ((.13,.095,.048),(.095,.135,.085)),
    'kael': ((.43,.225,.045),(.43,.225,.045)),
    'evelyn': ((.025,.055,.13),(.025,.055,.13)),
    'captain': ((.085,.09,.095),(.10,.115,.11)),
    'raider': ((.12,.055,.022),(.17,.075,.033)),
    'raider-shield': ((.095,.047,.023),(.11,.065,.035)),
    'raider-archer': ((.10,.09,.035),(.075,.105,.04)),
}
TROUSERS = {
    'raphael':(.105,.062,.028),'mira':(.08,.045,.024),'kael':(.105,.065,.028),
    'lorn':(.045,.064,.095),'evelyn':(.075,.050,.030),'nightqi':(.10,.072,.038),
    'captain':(.055,.060,.057),'raider':(.085,.052,.026),
    'raider-shield':(.070,.045,.024),'raider-archer':(.085,.075,.038),
}


def _active(obj):
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj


def _material(identity, role, color):
    name = f'V6_{identity}_{role}'
    existing = bpy.data.materials.get(name)
    if existing:
        return existing
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    m.diffuse_color = (*color, 1)
    m['v6MaterialRole'] = role
    m['v6MaterialSource'] = 'Local CC0 scans plus Blender native shader nodes'
    nodes, links = m.node_tree.nodes, m.node_tree.links
    nodes.clear()
    out = nodes.new('ShaderNodeOutputMaterial')
    bs = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bs.outputs['BSDF'], out.inputs['Surface'])
    bs.inputs['Base Color'].default_value = (*color,1)
    bs.inputs['Roughness'].default_value = .76 if role in ['linen','cloth'] else .52
    bs.inputs['Metallic'].default_value = .92 if role in ['steel','brass'] else 0
    if role == 'steel': bs.inputs['Roughness'].default_value = .48
    if role == 'brass': bs.inputs['Roughness'].default_value = .39
    coord = nodes.new('ShaderNodeTexCoord')
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 95 if role in ['leather','steel','brass'] else 170
    noise.inputs['Detail'].default_value = 2
    links.new(coord.outputs['Object'],noise.inputs['Vector'])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*[c*.72 for c in color],1)
    ramp.color_ramp.elements[1].color=(*[min(1,c*1.18) for c in color],1)
    links.new(noise.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs['Color'],bs.inputs['Base Color'])
    color_path=ROOT/'source-art/materials/natural-v1'/('leather' if role=='leather' else 'fabric')/'color-1k.jpg'
    if role in ['leather','linen','cloth'] and color_path.is_file():
        scan=nodes.new('ShaderNodeTexImage');scan.image=bpy.data.images.load(str(color_path),check_existing=True)
        scan.image.colorspace_settings.name='sRGB';scan.projection='BOX';scan.projection_blend=.25
        links.new(coord.outputs['Object'],scan.inputs['Vector'])
        gray=nodes.new('ShaderNodeRGBToBW');links.new(scan.outputs['Color'],gray.inputs['Color'])
        grain=nodes.new('ShaderNodeMixRGB');grain.blend_type='MULTIPLY';grain.inputs[0].default_value=.62 if role=='leather' else .38
        links.new(ramp.outputs['Color'],grain.inputs[1]);links.new(gray.outputs['Val'],grain.inputs[2]);links.new(grain.outputs[0],bs.inputs['Base Color'])
    bump=nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.17 if role not in ['steel','brass'] else .07
    bump.inputs['Distance'].default_value=.0012
    links.new(noise.outputs['Fac'],bump.inputs['Height'])
    links.new(bump.outputs['Normal'],bs.inputs['Normal'])
    # Reuse already licensed/downloaded real scan normals rather than invent a
    # bitmap. Object-space box projection remains valid before root's UV bake.
    normal_path = ROOT/'source-art/materials/natural-v1'/('leather' if role=='leather' else 'fabric')/'normal-1k.jpg'
    if role in ['linen','cloth','leather'] and normal_path.is_file():
        tex=nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(normal_path),check_existing=True)
        tex.image.colorspace_settings.name='Non-Color';tex.projection='BOX';tex.projection_blend=.25
        links.new(coord.outputs['Object'],tex.inputs['Vector'])
        normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=.16
        links.new(tex.outputs['Color'],normal.inputs['Color'])
        links.new(normal.outputs['Normal'],bump.inputs['Normal'])
    return m


def _recolor_native_slots(obj,identity,role,tint,value=.85):
    """Per-object shader copies keep the licensed UV/PBR detail and metal masks."""
    token=hashlib.sha256(obj.name.encode()).hexdigest()[:6]
    for index,source in enumerate(list(obj.data.materials)):
        if not source:continue
        clone=source.copy();clone.name=f'V6_{identity}_{role}_{token}_{index}'
        clone.use_nodes=True;clone['v6MaterialRole']=role
        clone['v6MaterialSource']='Original Quaternius native UV/PBR, object-local recolor'
        clone['v6OriginalMaterial']=source.name
        nodes,links=clone.node_tree.nodes,clone.node_tree.links
        bs=next((n for n in nodes if n.type=='BSDF_PRINCIPLED'),None)
        if not bs:continue
        base=bs.inputs['Base Color']
        original=base.links[0].from_socket if base.is_linked else None
        original_color=tuple(base.default_value)
        hue=nodes.new('ShaderNodeMixRGB');hue.blend_type='COLOR';hue.inputs[0].default_value=1
        hue.inputs[2].default_value=(*tint,1)
        if original:links.new(original,hue.inputs[1])
        else:hue.inputs[1].default_value=original_color
        multiply=nodes.new('ShaderNodeMixRGB');multiply.blend_type='MULTIPLY';multiply.inputs[0].default_value=1
        multiply.inputs[2].default_value=(value,value,value,1);links.new(hue.outputs[0],multiply.inputs[1])
        final=nodes.new('ShaderNodeMixRGB');final.blend_type='MIX'
        if original:links.new(original,final.inputs[1])
        else:final.inputs[1].default_value=original_color
        links.new(multiply.outputs[0],final.inputs[2])
        metallic=bs.inputs['Metallic']
        if metallic.is_linked:
            mask=nodes.new('ShaderNodeMath');mask.operation='SUBTRACT';mask.use_clamp=True;mask.inputs[0].default_value=1
            links.new(metallic.links[0].from_socket,mask.inputs[1]);links.new(mask.outputs[0],final.inputs[0])
        else:final.inputs[0].default_value=1-min(1,max(0,metallic.default_value))
        links.new(final.outputs[0],base)
        obj.data.materials[index]=clone
    obj['v6MaterialRole']=role


def _tailor_boot_shaft(obj,rig,amount):
    """Small radius edit above the ankle; original sole positions stay exact."""
    for vertex in obj.data.vertices:
        p=vertex.co
        blend=min(1,max(0,(p.z-.16)/.18))
        if not blend:continue
        side='l' if p.x>=0 else 'r'
        ankle=rig.data.bones['foot_'+side].head_local
        knee=rig.data.bones['calf_'+side].head_local
        t=min(1,max(0,(p.z-ankle.z)/max(.001,knee.z-ankle.z)))
        center=ankle.lerp(knee,t)
        factor=1-amount*blend
        p.x=center.x+(p.x-center.x)*factor;p.y=center.y+(p.y-center.y)*factor
    obj.data.update()


def _tailor_bracer(obj,rig):
    for vertex in obj.data.vertices:
        p=vertex.co;side='l' if p.x>=0 else 'r'
        elbow=rig.data.bones['lowerarm_'+side].head_local
        wrist=rig.data.bones['hand_'+side].head_local
        t=min(1,max(0,(p.x-elbow.x)/(wrist.x-elbow.x)))
        center=elbow.lerp(wrist,t)
        p.y=center.y+(p.y-center.y)*.82;p.z=center.z+(p.z-center.z)*.82
    obj.data.update()


def _tag(obj, identity, part, material):
    obj.name=f'{identity}_native_{part}_v6_{obj.name}'
    obj['nativePart']=part
    obj['defaultVisible']=True
    obj['v6Wardrobe']=True
    obj['v6MaterialRole']=material.get('v6MaterialRole','cloth')
    obj.data.materials.clear();obj.data.materials.append(material)
    return obj


def _mesh(name, verts, faces, identity, rig, part, material, source, thickness=0, fit_above=None, fit_mode='OUTSIDE',fit_target=None):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata(verts,[],faces);mesh.update()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4)
    _tag(obj,identity,part,material)
    _active(obj)
    bm=bmesh.new();bm.from_mesh(mesh)
    bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(mesh);bm.free()
    if fit_above is not None:
        fit=obj.vertex_groups.new(name='V6_native_surface_fit')
        indices=[v.index for v in obj.data.vertices if v.co.z>=fit_above]
        if indices:
            fit.add(indices,1,'REPLACE')
            mod=obj.modifiers.new('Fit outer garment to original supplied torso','SHRINKWRAP')
            mod.target=fit_target or source;mod.wrap_method='NEAREST_SURFACEPOINT';mod.wrap_mode=fit_mode
            mod.offset=.009;mod.vertex_group=fit.name
            bpy.ops.object.modifier_apply(modifier=mod.name)
        remaining_fit=obj.vertex_groups.get('V6_native_surface_fit')
        if remaining_fit:obj.vertex_groups.remove(remaining_fit)
    if thickness:
        mod=obj.modifiers.new('Native garment edge thickness','SOLIDIFY')
        mod.thickness=thickness;mod.offset=0;mod.use_even_offset=True
        bpy.ops.object.modifier_apply(modifier=mod.name)
    # Native UV operator creates editable UVs for this small new surface.
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.025)
    bpy.ops.object.mode_set(mode='OBJECT')
    _weights(obj,source,rig)
    for p in obj.data.polygons:p.use_smooth=True
    return obj


def _weights(obj, source, rig):
    # A long coat must follow the supplied leg skin below the hips; a shoulder
    # drape must follow the supplied upper-arm skin. Torso-only transfer leaves
    # both rigid while the native limbs pass through them during locomotion.
    if source.get('nativePart') == 'body' and not source.get('v6Wardrobe'):
        source = bpy.data.objects.get(rig.get('v6WardrobeWeightProxy', '')) or source
    _active(obj)
    mod=obj.modifiers.new('Original kit skin via native Data Transfer','DATA_TRANSFER')
    mod.object=source;mod.use_vert_data=True;mod.data_types_verts={'VGROUP_WEIGHTS'}
    mod.vert_mapping='POLYINTERP_NEAREST'
    mod.layers_vgroup_select_src='ALL';mod.layers_vgroup_select_dst='NAME'
    bpy.ops.object.datalayout_transfer(modifier=mod.name)
    bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.object.vertex_group_smooth(group_select_mode='ALL',factor=.5,repeat=3)
    bpy.ops.object.mode_set(mode='OBJECT')
    bpy.ops.object.vertex_group_clean(group_select_mode='ALL',limit=.0001,keep_single=True)
    bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL',limit=4)
    bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL',lock_active=False)
    arm=obj.modifiers.new('Original native rig','ARMATURE');arm.object=rig


def _surface(ctx, name, rows, material, part='body', gap=.18, segments=24, hem_wave=.0, thickness=.0035, seam=True,side_slits=False,neckline=True):
    """Native mesh edit of fitted elliptical garment sections (open at front)."""
    identity,rig,source,sx,sz=ctx
    # Add intermediate cross-sections where the kit's legs bend. Long single
    # quads cannot retain a fitted outline when their ends follow native skin.
    dense=[]
    for lower,upper in zip(rows,rows[1:]):
        steps=max(1,math.ceil((upper[0]-lower[0])/.16))
        dense.extend(tuple(a+(b-a)*i/steps for a,b in zip(lower,upper)) for i in range(steps))
    rows=dense+[rows[-1]]
    verts=[];faces=[];grid=[]
    for row,(z,rx,ry,rowgap) in enumerate(rows):
        ring=[]
        for j in range(segments+1):
            t=rowgap+(TAU-2*rowgap)*j/segments
            fold=(math.sin(t*7)*hem_wave)*max(0,1-row/max(1,len(rows)-1))
            zz=z
            # The top neckline descends into a V at the open fronts.
            if neckline and row==len(rows)-1:zz-=.115*max(0,math.cos(t))**2
            verts.append(((rx+fold)*math.sin(t)*sx,-(ry+fold)*math.cos(t),zz*sz))
            ring.append(len(verts)-1)
        grid.append(ring)
    for row in range(len(rows)-1):
        for j in range(segments):
            t=rows[row][3]+(TAU-2*rows[row][3])*(j+.5)/segments
            if side_slits and rows[row][0]<1.10 and min(abs(t-math.pi/2),abs(t-3*math.pi/2))<.39:continue
            if side_slits and rows[row][0]<.94 and abs(t-math.pi)<.14:continue
            faces.append((grid[row][j],grid[row][j+1],grid[row+1][j+1],grid[row+1][j]))
    obj=_mesh(name,verts,faces,identity,rig,part,material,source,thickness,fit_above=(0 if part=='body' else 1.38)*sz,fit_target=bpy.data.objects.get(rig.get('v6WardrobeFitProxy','')))
    verts=[tuple(v.co) for v in list(obj.data.vertices)[:len(verts)]]
    created=[obj]
    if seam:
        trim=_material(identity,'leather',(.14,.075,.031))
        edges=[('opening_L',[r[0] for r in grid]),('opening_R',[r[-1] for r in grid])]
        if not side_slits:edges.append(('hem',grid[0]))
        else:
            # Bound the deliberate side vents. They clear the original legs in
            # locomotion while keeping a long sleeveless front/back silhouette.
            for j in [5,9,19,23]:edges.append((f'side_vent_{j}',[r[j] for r in grid[:4]]))
        for edge,indices in edges:
            points=[Vector(verts[i])+Vector((0,-.002 if edge!='hem' else 0,0)) for i in indices]
            created.append(_seam(ctx,f'{name}_{edge}',points,trim,width=.0032,part=part))
    return created,verts,grid


def _seam(ctx,name,points,material,width=.002,part='body',fit_target=None):
    identity,rig,source,sx,sz=ctx
    # Blender bevelled Curve supplies real piped seam geometry with low detail.
    curve=bpy.data.curves.new(name,'CURVE');curve.dimensions='3D';curve.resolution_u=1
    curve.bevel_depth=width;curve.bevel_resolution=0;curve.resolution_u=1
    sp=curve.splines.new('POLY');sp.points.add(len(points)-1)
    for point,co in zip(sp.points,points):point.co=(*co,1)
    obj=bpy.data.objects.new(name,curve);bpy.context.collection.objects.link(obj)
    obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4)
    _active(obj);bpy.ops.object.convert(target='MESH');obj=bpy.context.object
    _tag(obj,identity,part,material)
    if fit_target:
        fit=obj.modifiers.new('Native embroidery surface projection','SHRINKWRAP')
        fit.target=fit_target;fit.wrap_method='NEAREST_SURFACEPOINT';fit.wrap_mode='ON_SURFACE';fit.offset=.0018
        bpy.ops.object.modifier_apply(modifier=fit.name)
    _weights(obj,fit_target or source,rig)
    return obj


def _vine_embroidery(ctx,target,long=False):
    """A few millimetre-wide stems/leaf stitches, projected onto real cloth."""
    identity,rig,source,sx,sz=ctx
    thread=_material(identity,'thread',(.26,.15,.045));thread['v6MaterialRole']='cloth'
    bs=next(n for n in thread.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    bs.inputs['Roughness'].default_value=.68
    made=[]
    for sign in [-1,1]:
        z0,z1=(.50,1.30) if long else (1.10,1.39)
        x=sign*(.105 if long else .112)*sx
        stem=[Vector((x+sign*math.sin(i*math.pi/6)*.003,-.30,(z0+(z1-z0)*i/6)*sz)) for i in range(7)]
        made.append(_seam(ctx,f'fine_vine_stem_{sign}',stem,thread,.00085,fit_target=target))
        for i in range(1,6):
            center=stem[i]
            side=sign*(1 if i%2 else -1)
            leaf=[center,center+Vector((side*.010*sx,0,.008*sz)),center+Vector((side*.014*sx,0,.004*sz))]
            made.append(_seam(ctx,f'fine_leaf_stitch_{sign}_{i}',leaf,thread,.00075,fit_target=target))
    return made


def _cape_stitches(ctx,target,hem_points):
    identity,rig,source,sx,sz=ctx
    thread=_material(identity,'thread',(.26,.15,.045));thread['v6MaterialRole']='cloth'
    made=[]
    for j in range(2,len(hem_points)-2,2):
        center=Vector(hem_points[j]);along=(Vector(hem_points[j+1])-Vector(hem_points[j-1])).normalized()*.0034
        up=Vector((0,0,.004))
        for sign in [-1,1]:
            points=[center-along-up*sign,center+along+up*sign]
            made.append(_seam(ctx,f'fine_cape_crossstitch_{j}_{sign}',points,thread,.0007,'cape',fit_target=target))
    return made


def _details(ctx,name,centres,material,radius=.005,part='body'):
    identity,rig,source,sx,sz=ctx
    bm=bmesh.new()
    for center in centres:
        bmesh.ops.create_uvsphere(bm,u_segments=8,v_segments=4,radius=radius,matrix=Matrix.Translation(Vector(center)))
    mesh=bpy.data.meshes.new(name);bm.to_mesh(mesh);bm.free()
    obj=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(obj)
    obj.parent=rig;obj.matrix_parent_inverse=Matrix.Identity(4)
    _tag(obj,identity,part,material);_weights(obj,source,rig)
    return obj


def _ribbon(ctx,name,a,b,width,material,part='body'):
    a,b=Vector(a),Vector(b);direction=(b-a).normalized()
    side=direction.cross(Vector((0,1,0))).normalized()*width/2
    verts=[tuple(a-side),tuple(a+side),tuple(b+side),tuple(b-side)]
    identity,rig,source,sx,sz=ctx
    return _mesh(name,verts,[(0,1,2,3)],identity,rig,part,material,source,.004)


def _cape(ctx,name,color,long=False,short=False,armored=False):
    identity,rig,source,sx,sz=ctx
    material=_material(identity,'cloth',color)
    # Back drape plus two shoulder wings. The front remains open for hand and
    # weapon readability; the hero's asymmetric cut clears his single pauldron.
    rows=([(.22,.35,.27,.78),(.65,.31,.25,.76),(1.05,.24,.225,.72),(1.35,.27,.19,.65),(1.49,.28,.16,.60),(1.565,.075,.085,.50)] if long else
          [(1.265 if short else .91,.29,.225,.64),(1.40,.285,.19,.56),(1.49,.27,.155,.48),(1.565,.075,.085,.45)])
    if identity=='raphael':
        # An asymmetric short shoulder cloth, not a full travelling cloak.
        verts=[];faces=[];seg=24
        for row,(z,rx,ry,g) in enumerate(rows):
            for j in range(seg+1):
                t=1.4+(TAU-.45-1.4)*j/seg
                zz=z+(.075*math.sin(t) if row==0 else 0)
                verts.append((rx*math.sin(t)*sx,-ry*math.cos(t),zz*sz))
        for r in range(len(rows)-1):
            for j in range(seg):k=r*(seg+1)+j;faces.append((k,k+1,k+seg+2,k+seg+1))
        obj=_mesh(name,verts,faces,identity,rig,'cape',material,source,.005)
        seam=_seam(ctx,name+'_bound_hem',[Vector(v) for v in verts[:seg+1]],_material(identity,'brass',(.30,.19,.065)),.0015,'cape')
        return [obj,seam]+_cape_stitches(ctx,obj,verts[:seg+1])
    created,verts,grid=_surface(ctx,name,rows,material,part='cape',segments=28,hem_wave=.007,thickness=.005)
    return created


def _coat(ctx,name,color,hem,long=False,armor=False):
    identity,rig,source,sx,sz=ctx
    role='steel' if armor else 'cloth'
    material=_material(identity,role,color)
    rx=[.34 if long else .205,.205,.18,.156,.181,.205]
    rows=[(hem,rx[0],.235 if long else .157,.24),(.98,rx[1],.163,.20),(1.09,rx[2],.15,.17),(1.18,rx[3],.145,.15),(1.37,rx[4],.157,.35),(1.49,rx[5],.125,.82)]
    if hem>=.97:rows=rows[1:];rows[0]=(hem,.197,.156,.23)
    created,verts,grid=_surface(ctx,name,rows,material,segments=28,hem_wave=.003 if long else 0,side_slits=long)
    brass=_material(identity,'brass',(.32,.20,.067))
    # Buttons track both opening edges, so they are actually on the garment.
    centres=[]
    for r in range(1,len(rows)-1):
        for index in [grid[r][0],grid[r][-1]]:
            point=Vector(verts[index]);point.y-=.006;centres.append(point)
    created.append(_details(ctx,name+'_fasteners',centres,brass,.0043))
    # Lapels have their own folded surface and are not printed triangles.
    for side in [-1,1]:
        points=[(side*.148*sx,-.112,1.49*sz),(side*.07*sx,-.163,1.35*sz),(side*.047*sx,-.159,1.24*sz)]
        created.append(_seam(ctx,name+('_lapel_L' if side<0 else '_lapel_R'),list(map(Vector,points)),material,.009))
    return created


def _cuirass(ctx, color, heavy=False):
    identity,rig,source,sx,sz=ctx
    steel=_material(identity,'steel',color)
    created=[]
    # Independently overlapping plates give the v5 segmented silhouette;
    # actual bevel/solidify edges distinguish armour from dyed Ranger cloth.
    bands=[(1.21,1.49,.185,.164),(1.14,1.225,.166,.150),(1.065,1.155,.184,.157)]
    if heavy:bands.extend([(.985,1.08,.205,.165),(.91,1.00,.22,.17)])
    for i,(bottom,top,rx,ry) in enumerate(bands):
        rows=[(bottom,rx*(1.015 if i else 1),ry,0),(top,rx,ry,0)]
        if i==0:rows=[(bottom,rx,ry,0),(1.39,.196,.166,0),(top,.205,.135,.08)]
        made,verts,grid=_surface(ctx,f'layered_cuirass_{i}',rows,steel,segments=24,thickness=.009,seam=False,neckline=False)
        created.extend(made)
        created.append(_seam(ctx,f'plate_rolled_edge_{i}',[Vector(verts[x])+Vector((0,-.002,0)) for x in grid[0]],_material(identity,'brass',(.25,.16,.055)),.0023))
    created.append(_ribbon(ctx,'diagonal_cuirass_baldric',(.15*sx,-.17,1.46*sz),(-.115*sx,-.174,1.16*sz),.022,_material(identity,'leather',(.12,.061,.027))))
    return created


def _quiver(ctx):
    identity,rig,source,sx,sz=ctx
    # Closed base / open mouth, with actual arrow shafts and feathers.
    verts=[];faces=[];segments=12
    for z,r in [(1.01,.038),(1.43,.052),(1.455,.052),(1.455,.043),(1.40,.043)]:
        for j in range(segments):
            t=TAU*j/segments;verts.append((-.15*sx+r*math.cos(t),.225+r*math.sin(t),(z+.15*r*math.cos(t))*sz))
    for row in range(4):
        for j in range(segments):a=row*segments+j;b=row*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
    faces.append(tuple(range(segments-1,-1,-1)))
    made=[_mesh('back_quiver',verts,faces,identity,rig,'quiver',_material(identity,'leather',(.12,.058,.022)),source)]
    shaftmat=_material(identity,'leather',(.24,.13,.048))
    for i in range(4):
        x=(-.175+i*.016)*sx
        made.append(_seam(ctx,f'quiver_arrow_{i}',[Vector((x,.225,1.35*sz)),Vector((x-.015,.238,1.63*sz))],shaftmat,.0025,'quiver'))
    featherverts=[];featherfaces=[]
    for i in range(4):
        x=(-.19+i*.016)*sx;k=len(featherverts)
        featherverts.extend([(x-.01,.236,1.58*sz),(x,.236,1.64*sz),(x+.012,.236,1.625*sz),(x+.005,.236,1.575*sz)])
        featherfaces.append(tuple(range(k,k+4)))
    made.append(_mesh('quiver_fletching',featherverts,featherfaces,identity,rig,'quiver',_material(identity,'linen',(.42,.36,.23)),source,.001))
    return made


def _cuffs(ctx,arm_source):
    identity,rig,source,sx,sz=ctx
    material=_material(identity,'linen',(.68,.59,.43));made=[]
    # Rolled linen cuffs use existing arm locations and native arm skinning.
    for side in [-1,1]:
        x=rig.data.bones['lowerarm_'+('l' if side>0 else 'r')].head_local.x+side*.013;z=rig.data.bones['lowerarm_'+('l' if side>0 else 'r')].head_local.z
        y=rig.data.bones['lowerarm_'+('l' if side>0 else 'r')].head_local.y
        verts=[];faces=[];segments=16
        for xx,rr in [(x-side*.025,.055),(x,.061),(x+side*.022,.055)]:
            for j in range(segments):t=TAU*j/segments;verts.append((xx,y+rr*math.cos(t),z+rr*math.sin(t)))
        for r in range(2):
            for j in range(segments):a=r*segments+j;b=r*segments+(j+1)%segments;faces.append((a,b,b+segments,a+segments))
        made.append(_mesh('rolled_sleeve_'+str(side),verts,faces,identity,rig,'arms',material,arm_source,.003))
    return made


def _shirt_front(ctx,material):
    """Clean linen insert and standing collar beneath an open tailored coat."""
    identity,rig,source,sx,sz=ctx
    verts=[];faces=[]
    rows=[(1.035,.050,-.13),(1.18,.065,-.133),(1.37,.100,-.137),(1.49,.090,-.105)]
    for z,width,y in rows:verts.extend([(-width*sx,y+.023,z*sz),(0,y,z*sz),(width*sx,y+.023,z*sz)])
    for r in range(3):
        for j in range(2):a=r*3+j;faces.append((a,a+1,a+4,a+3))
    insert=_mesh('linen_shirt_inset',verts,faces,identity,rig,'body',material,source,.002)
    return [insert,_standing_collar(ctx,material)]


def _standing_collar(ctx,material):
    identity,rig,source,sx,sz=ctx
    verts=[];faces=[];segments=20
    collar_rows=[(1.545,.078,.080),(1.595,.066,.070)] if identity=='raphael' else [(1.49,.070,.074),(1.535,.075,.08)]
    for z,rx,ry in collar_rows:
        for j in range(segments+1):
            t=TAU*j/segments if identity=='raphael' else .18+(TAU-.36)*j/segments
            verts.append((rx*math.sin(t)*sx,-ry*math.cos(t)+(.025 if identity=='raphael' else 0),(z-.012*max(0,math.cos(t)))*sz))
    for j in range(segments):faces.append((j,j+1,j+segments+2,j+segments+1))
    collar=_mesh('linen_standing_collar',verts,faces,identity,rig,'body',material,source,.003)
    return collar


def _hero_neck_yoke(ctx,material):
    identity,rig,source,sx,sz=ctx;verts=[];faces=[];segments=24
    for z,rx,ry,cy in [(1.495,.205,.138,0),(1.545,.078,.080,.025)]:
        for j in range(segments+1):
            t=TAU*j/segments;verts.append((rx*math.sin(t)*sx,-ry*math.cos(t)+cy,z*sz))
    for j in range(segments):faces.append((j,j+1,j+segments+2,j+segments+1))
    return _mesh('leather_neck_shoulder_yoke',verts,faces,identity,rig,'body',material,source,.002)


def apply(identity, rig, manifest):
    """Edit currently loaded source scene and return JSON-safe modification data."""
    if identity not in PALETTES:raise ValueError(f'Unsupported v5 wardrobe identity: {identity}')
    if any(o.get('v6Wardrobe') for o in bpy.data.objects):
        raise RuntimeError('v5 wardrobe must run once on the unmodified native-production source scene')
    originals=[o for o in bpy.data.objects if o.type=='MESH' and o.get('nativePart') and not o.get('v6Wardrobe')]
    body=next(o for o in originals if o.get('nativePart')=='body' and 'belt' not in o.name.lower())
    arm_source=next(o for o in originals if o.get('nativePart')=='arms' and 'bracer' not in o.name.lower())
    sx=abs(rig.data.bones['upperarm_l'].head_local.x)/.1919
    sz=rig.data.bones['neck_01'].head_local.z/1.5205
    if identity in ['lorn','raider-shield','captain']:sx*=1.075
    old_pose=rig.data.pose_position;rig.data.pose_position='REST';bpy.context.view_layer.update()
    # Join copies of the supplied torso/trousers through Blender's native join
    # to make one temporary fitting/weight-transfer target. This prevents long
    # coat hips intersecting the original trousers; no proxy is exported.
    proxy_sources=[body]+[o for o in originals if o.get('nativePart')=='legs']
    proxies=[]
    for source in proxy_sources:
        obj=source.copy();obj.data=source.data.copy();bpy.context.collection.objects.link(obj)
        for key in list(obj.keys()):del obj[key]
        obj.name='V6_native_fitting_proxy';obj.hide_render=True;proxies.append(obj)
    _active(proxies[0])
    for obj in proxies:obj.select_set(True)
    bpy.ops.object.join();proxy=proxies[0]
    rig['v6WardrobeFitProxy']=proxy.name
    weight_sources=[proxy,arm_source]
    weight_copies=[]
    for source in weight_sources:
        obj=source.copy();obj.data=source.data.copy();bpy.context.collection.objects.link(obj)
        for key in list(obj.keys()):del obj[key]
        obj.name='V6_native_weight_proxy';obj.hide_render=True;weight_copies.append(obj)
    _active(weight_copies[0])
    for obj in weight_copies:obj.select_set(True)
    bpy.ops.object.join();weight_proxy=weight_copies[0]
    rig['v6WardrobeWeightProxy']=weight_proxy.name
    ctx=(identity,rig,body,sx,sz)
    coat,cape=PALETTES[identity];added=[];removed=[];changes=[]
    linen=_material(identity,'linen',(.65,.56,.42))
    leather=_material(identity,'leather',coat if identity in ['raphael','nightqi','raider','raider-shield','raider-archer'] else (.13,.067,.028))
    try:
        # Reuse the original well fitted underwear, trousers, sleeves and shoes.
        # Keep original diffuse/normal detail on hands/boots/legs untouched.
        for o in originals:
            p=o.get('nativePart')
            if p=='legs':
                _recolor_native_slots(o,identity,'cloth',TROUSERS[identity],.88)
            if p=='feet':
                _recolor_native_slots(o,identity,'leather',(.075,.033,.013),.36 if identity=='raphael' else .52 if identity=='mira' else .74)
                if identity in ['raphael','mira']:_tailor_boot_shaft(o,rig,.14 if identity=='raphael' else .10)
            if p=='arms' and 'bracer' in o.name.lower() and identity=='raphael':
                _recolor_native_slots(o,identity,'leather',(.075,.032,.013),.76)
                _tailor_bracer(o,rig)
            if p=='body':
                if 'belt' in o.name.lower():
                    _recolor_native_slots(o,identity,'leather',(.09,.042,.016),.84)
                    continue
                underlayer=_material(identity,'cloth',coat) if identity in ['lorn','evelyn','captain','raider-shield'] else leather
                material=linen if identity in ['mira','kael'] else underlayer
                o.data.materials.clear();o.data.materials.append(material);o['v6MaterialRole']=material['v6MaterialRole']
            if p=='arms' and identity in ['raphael','mira','kael'] and 'bracer' not in o.name.lower() and any('regular' in m.name.lower() for m in o.data.materials if m):
                for index,material in enumerate(o.data.materials):
                    if material and not any(token in material.name.lower() for token in ['regular','skin','superhero']):
                        o.data.materials[index]=linen
            if p=='pauldrons':
                if identity in ['nightqi','raider-archer']:
                    removed.append(o.name);bpy.data.objects.remove(o,do_unlink=True);continue
                metal=_material(identity,'steel',(.23,.25,.24) if identity=='raphael' else (.085,.105,.13))
                o.data.materials.clear();o.data.materials.append(metal);o['v6MaterialRole']='steel'
        if identity=='raphael':
            # Remove the old Ranger tunic's flared tails; the new short leather
            # hem replaces them. This never touches shoes, legs, hands or rig.
            bm=bmesh.new();bm.from_mesh(body.data)
            bmesh.ops.delete(bm,geom=[v for v in bm.verts if v.co.z<1.035*sz or v.co.z>1.515*sz],context='VERTS')
            bm.to_mesh(body.data);bm.free();body.data.update()
            added.append(_hero_neck_yoke(ctx,leather))
            added.append(_standing_collar(ctx,linen))
            added+=_cape(ctx,'short_asymmetric_teal_drape',cape,short=True)
            # Fitted leather panels cover the source tunic, with an actual
            # short hem instead of pretending the same green shirt is a vest.
            rows=[(1.04,.182,.15,.06),(1.17,.155,.144,.06),(1.34,.184,.157,.055),(1.47,.204,.13,.48)]
            made,verts,grid=_surface(ctx,'fitted_leather_jerkin',rows,leather,segments=24)
            added+=made
            added+=_vine_embroidery(ctx,made[0])
            added+=_cuffs(ctx,arm_source)
            added.append(_ribbon(ctx,'surveyors_crossbelt',(.16*sx,-.173,1.47*sz),(-.12*sx,-.17,1.13*sz),.024,_material(identity,'leather',(.105,.048,.017))))
            changes+=['Asymmetric short teal cape with millimetre-scale bound hem and fine cross-stitches','Fitted brown leather jerkin, small leaf-vine embroidery, diagonal baldric and real rolled linen cuffs','Original single steel pauldron retained','Object-local original-UV brown cloth trousers and deep-brown boots/bracers; metal buckle masks preserved','Boot shafts and separate bracer shells modestly narrowed, with original soles/hands untouched']
        elif identity=='mira':
            waistcoat=_coat(ctx,'burgundy_split_long_waistcoat',coat,.32,long=True)
            added+=waistcoat
            added+=_vine_embroidery(ctx,waistcoat[0],long=True)
            added+=_cuffs(ctx,arm_source)
            changes+=['Sleeveless burgundy long split waistcoat with folded lapels, opening piping, fine leaf stitching and brass fasteners','Native fitted linen sleeves retained with rolled cuffs','Object-local original-UV brown cloth and deep-brown leather footwear, preserving original PBR/metallic details; upper boot shafts modestly narrowed']
        elif identity=='kael':
            added+=_coat(ctx,'ochre_short_travelling_jacket',coat,1.00)
            added+=_cuffs(ctx,arm_source)
            changes+=['Short ochre open travelling jacket with actual hem/lapels/fasteners and rolled sleeves']
        elif identity=='nightqi':
            added+=_cape(ctx,'long_grey_green_travelling_cloak',cape,long=True)
            added+=_quiver(ctx)
            changes+=['Long open grey-green cloak with bound edges','Back quiver, four separate shafts and fletching','Removed inappropriate steel pauldrons']
        elif identity in ['lorn','captain','evelyn','raider-shield']:
            platecolor={'lorn':(.065,.095,.16),'captain':(.13,.145,.15),'evelyn':(.04,.073,.135),'raider-shield':(.075,.068,.055)}[identity]
            added+=_cuirass(ctx,platecolor,heavy=identity!='evelyn')
            if identity=='evelyn':
                surcoat=_coat(ctx,'split_deep_blue_guard_surcoat',coat,.40,long=True)
                added+=surcoat
                # White repairs sit on the visible front skirt, not under it.
                for index,(x,z,w,h) in enumerate([(-.13,.76,.08,.055),(.14,.58,.09,.065),(-.10,.43,.065,.045)]):
                    verts=[((x-w/2)*sx,-.185,(z-h/2)*sz),((x+w/2)*sx,-.185,(z-h/2)*sz),((x+w/2)*sx,-.185,(z+h/2)*sz),((x-w/2)*sx,-.185,(z+h/2)*sz)]
                    added.append(_mesh('white_field_repair_'+str(index),verts,[(0,1,2,3)],identity,rig,'body',linen,surcoat[0],.002,fit_above=0,fit_mode='ON_SURFACE'))
                changes+=['Deep-blue long split guard coat with three real white repair patches','Layered blue steel cuirass above tailored coat']
            elif identity=='lorn':
                added+=_cape(ctx,'short_indigo_guard_mantle',cape,short=True)
                changes+=['Broader indigo layered plate silhouette and short navy mantle']
            elif identity=='captain':
                added+=_cape(ctx,'grey_company_command_cloak',cape,long=True)
                changes+=['Grey company command cloak and grey heavy plate; kept separate from future Adrian']
            else:changes+=['Heavier brown/iron shield-infantry layered cuirass']
            # The free male Ranger only supplies one pauldron; mirror the
            # existing licensed mesh through native transform then retransfer.
            pauldrons=[o for o in originals if o.name in bpy.data.objects and o.get('nativePart')=='pauldrons']
            for source in pauldrons:
                if min(v.co.x for v in source.data.vertices)>-.03:
                    obj=source.copy();obj.data=source.data.copy();bpy.context.collection.objects.link(obj)
                    obj.name=f'{identity}_native_pauldrons_v6_mirrored_original';obj['v6Wardrobe']=True
                    for v in obj.data.vertices:v.co.x*=-1
                    bm=bmesh.new();bm.from_mesh(obj.data);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(obj.data);bm.free()
                    for mod in list(obj.modifiers):obj.modifiers.remove(mod)
                    for group in list(obj.vertex_groups):obj.vertex_groups.remove(group)
                    _weights(obj,arm_source,rig);added.append(obj)
                    changes.append('Mirrored original CC0 pauldron mesh with native arm-skin transfer')
        elif identity=='raider':
            added+=_coat(ctx,'short_rough_leather_jerkin',coat,.98)
            # A single actual plate distinguishes the swordsman from peasant.
            verts=[(.18*sx,-.06,1.48*sz),(.31*sx,-.035,1.48*sz),(.34*sx,.11,1.46*sz),(.20*sx,.17,1.48*sz),(.24*sx,.05,1.57*sz)]
            added.append(_mesh('single_scavenged_shoulder',verts,[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],identity,rig,'pauldrons',_material(identity,'steel',(.13,.12,.10)),arm_source,.009))
            changes+=['Short rough leather jerkin, one scavenged shoulder plate; light swordsman silhouette']
        elif identity=='raider-archer':
            added+=_cape(ctx,'short_moss_archer_cloak',cape)
            added+=_quiver(ctx)
            changes+=['Short moss archer cloak and back quiver; source hood visibility retained']
        # Replace the peasant shirt's flared torso after skin transfer with a
        # clean inset/collar. Simple face deletion leaves the supplied shoulder
        # frills jagged at the neckline; separate sleeves/hands stay untouched.
        if identity in ['mira','kael']:
            # The free peasant kit has very baggy breeches. Tailor the existing
            # trouser mesh (original UVs/weights retained) beneath the v5 coat;
            # do not let the old hip bulk punch through the fitted side vents.
            for trousers in originals:
                if trousers.name not in bpy.data.objects or trousers.get('nativePart')!='legs':continue
                for vertex in trousers.data.vertices:
                    z=vertex.co.z/sz
                    blend=min(1,max(0,(z-.48)/.16))*min(1,max(0,(1.16-z)/.12))
                    if not blend:continue
                    center=rig.data.bones['thigh_l' if vertex.co.x>=0 else 'thigh_r'].head_local.x
                    vertex.co.x=center+(vertex.co.x-center)*(1-.26*blend)
                    vertex.co.y=.045+(vertex.co.y-.045)*(1-.25*blend)
                trousers.data.update()
            added+=_shirt_front(ctx,linen)
            removed.append(body.name);bpy.data.objects.remove(body,do_unlink=True)
            changes.append('Replaced concealed peasant torso/frills with clean inset linen front and standing collar; original separate sleeves/hands unchanged')
            changes.append('Tailored the original peasant breeches to a slimmer v5 trouser fit; original UVs, weights and knee/boot geometry retained')
        # Consolidate piped trim/buttons per material/part, preserving the runtime
        # hood/hair selection groups. Root remains free to bake a single atlas.
        combined=[]
        buckets={}
        for obj in added:
            material=obj.data.materials[0] if obj.data.materials else None
            key=(obj.get('nativePart'),material.name if material else '')
            buckets.setdefault(key,[]).append(obj)
        for objects in buckets.values():
            if len(objects)>1:
                _active(objects[0])
                for o in objects:o.select_set(True)
                bpy.ops.object.join()
            combined.append(objects[0])
        added=combined
        # Rebuild the public part manifest from actual surviving source meshes.
        parts={}
        for obj in bpy.data.objects:
            if obj.type=='MESH' and obj.get('nativePart'):
                p=obj['nativePart'];entry=parts.setdefault(p,{'nodes':[],'defaultVisible':bool(obj.get('defaultVisible',True))})
                entry['nodes'].append(obj.name)
        manifest['parts']=parts
        manifest['v6Wardrobe']={'changes':changes,'nativeWeightTransfer':'POLYINTERP_NEAREST + native limit_total(4)/normalize_all'}
        return {'added':[o.name for o in added],'removed':removed,'changes':changes,'sourceLicenses':[
            {'source':'Original Quaternius Ranger/Peasant garment geometry and skin weights','license':'CC0-1.0','manifest':'source-art/characters/library-kits/sources.json'},
            {'source':'Poly Haven leather_white/fabric color and normal scans already stored in natural-v1','license':'CC0-1.0','path':'source-art/materials/natural-v1'},
            {'source':'New concept-specific garment mesh edits, Blender Solidify/Curve/Data Transfer','license':'Project-authored'}],
            'addedTriangles':sum(sum(max(0,len(p.vertices)-2) for p in o.data.polygons) for o in added),
            'materials':[m.name for m in bpy.data.materials if m.name.startswith(f'V6_{identity}_')]}
    finally:
        if proxy.name in bpy.data.objects:bpy.data.objects.remove(proxy,do_unlink=True)
        if weight_proxy.name in bpy.data.objects:bpy.data.objects.remove(weight_proxy,do_unlink=True)
        if 'v6WardrobeFitProxy' in rig:del rig['v6WardrobeFitProxy']
        if 'v6WardrobeWeightProxy' in rig:del rig['v6WardrobeWeightProxy']
        rig.data.pose_position=old_pose
        bpy.context.view_layer.update()
