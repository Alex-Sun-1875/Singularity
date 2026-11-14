"""Author real beveled/rounded 3D weapons from the current 2D design authority.

Blender native filled curves preserve contour holes; round shafts, actual gems,
native UV projection and PBR retain the design at oblique angles. Surface Deform
transfers the established bow flex, and the original string/Draw mesh is reused.
No body, wrist pose, arrow-helper or user save changes.
"""
from pathlib import Path
import bpy,json,math,sys,hashlib,argparse
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
BASE=Path(__file__).resolve().parent
ROOT=BASE.parents[2]
RECORDS=json.loads((BASE/'prepared/models.json').read_text(encoding='utf-8'))
OUT=BASE/'models';OUT.mkdir(exist_ok=True)
(BASE/'previews').mkdir(exist_ok=True)
MATS={}

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def activate(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]

def side(role):
    name='DesignEdge_'+role
    if bpy.data.materials.get(name):return bpy.data.materials[name]
    m=bpy.data.materials.new(name);m.use_nodes=True;bs=m.node_tree.nodes.get('Principled BSDF')
    colors={'steel':(.13,.16,.19),'bronze':(.22,.12,.048),'wood':(.105,.065,.033),'greywood':(.13,.115,.090),'leather':(.070,.033,.018),'string':(.22,.16,.09),'blue':(.035,.09,.22)}
    bs.inputs['Base Color'].default_value=(*colors.get(role,colors['steel']),1)
    bs.inputs['Metallic'].default_value=.85 if role in ['steel','bronze'] else 0
    bs.inputs['Roughness'].default_value=.31 if role=='steel' else .40 if role=='bronze' else .7
    return m

def front(row):
    name='Design_'+row['id'].replace('-','_')+'_PBR'
    m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links;bs=n.get('Principled BSDF')
    bs.inputs['Roughness'].default_value=1;bs.inputs['Metallic'].default_value=1
    for kind in ['albedo','normal','orm']:
        image=bpy.data.images.load(str(BASE/'textures'/f'design-{row["id"].lower()}-{kind}.png'),check_existing=True)
        if kind!='albedo':image.colorspace_settings.name='Non-Color'
        t=n.new('ShaderNodeTexImage');t.image=image;t.extension='EXTEND'
        if kind=='albedo':l.new(t.outputs[0],bs.inputs['Base Color'])
        elif kind=='normal':
            normal=n.new('ShaderNodeNormalMap');l.new(t.outputs[0],normal.inputs[1]);l.new(normal.outputs[0],bs.inputs['Normal'])
        else:
            s=n.new('ShaderNodeSeparateColor');l.new(t.outputs[0],s.inputs[0]);l.new(s.outputs[1],bs.inputs['Roughness']);l.new(s.outputs[2],bs.inputs['Metallic'])
    return m

def point(row,xy):
    x=(xy[0]-row['grip'][0])*row['xScale']*(-1 if row['mirrorX'] else 1)
    z=(row['grip'][1]-xy[1])*row['metresPerPixel']
    return x,z

def project(obj,row,paint,edge,round_surface=False):
    obj.data.materials.clear();obj.data.materials.append(paint);obj.data.materials.append(side(edge))
    # Native Smart UV supplies non-collapsed UVs on bevel/edge surfaces.
    activate([obj]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.015);bpy.ops.object.mode_set(mode='OBJECT')
    uv=obj.data.uv_layers.active
    for p in obj.data.polygons:
        visible=abs(p.normal.y)>(.15 if round_surface else .70)
        p.material_index=0 if visible else 1
        if visible:
            for index in p.loop_indices:
                v=obj.data.vertices[obj.data.loops[index].vertex_index].co
                px=row['grip'][0]+v.x/row['xScale']*(-1 if row['mirrorX'] else 1)
                py=row['grip'][1]-v.z/row['metresPerPixel']
                uv.data[index].uv=(px/row['width'],1-py/row['height'])
    obj['design_part']=True
    return obj

def outline(row,part,paint):
    if not part['contours']:return None
    data=bpy.data.curves.new(row['id']+'_'+part['name'],'CURVE');data.dimensions='2D';data.resolution_u=1;data.fill_mode='BOTH';data.extrude=part['depth'];data.bevel_depth=part['bevel'];data.bevel_resolution=2
    for ring in part['contours']:
        s=data.splines.new('POLY');s.points.add(len(ring)-1)
        for p,xy in zip(s.points,ring):
            x,z=point(row,xy);p.co=(x,z,0,1)
        s.use_cyclic_u=True
    obj=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(obj);obj.rotation_euler.x=math.pi/2
    activate([obj]);bpy.ops.object.convert(target='MESH');obj=bpy.context.object;bpy.ops.object.transform_apply(location=False,rotation=True,scale=True)
    # Blender's native bevel and weighted normals give readable edge highlights.
    for p in obj.data.polygons:p.use_smooth=True
    mod=obj.modifiers.new('Weighted bevel normals','WEIGHTED_NORMAL');mod.keep_sharp=True;mod.weight=50
    bpy.ops.object.modifier_apply(modifier=mod.name)
    return project(obj,row,paint,part['edge'])

def shaft(row,paint):
    pts=row['shaftPoints']
    if not pts:return None
    data=bpy.data.curves.new(row['id']+'_RoundShaft','CURVE');data.dimensions='3D';data.resolution_u=2;data.bevel_depth=.01;data.bevel_resolution=4;data.use_fill_caps=True
    s=data.splines.new('POLY');s.points.add(len(pts)-1)
    for p,entry in zip(s.points,pts):
        x,z=point(row,entry[:2]);p.co=(x,0,z,1);p.radius=entry[2]/.01
    obj=bpy.data.objects.new(data.name,data);bpy.context.collection.objects.link(obj);activate([obj]);bpy.ops.object.convert(target='MESH');obj=bpy.context.object
    for p in obj.data.polygons:p.use_smooth=True
    return project(obj,row,paint,'wood' if row['kind']=='staff' else 'leather',True)

GEMS={
 'W02':[(139,677,12,15)],'W05':[(134,669,11,14),(134,928,10,12)],
 'W06':[(30,358,7,8)],'L01':[(167,666,15,21),(167,926,11,14)],
 'W08':[(52,344,12,15)],'L02':[(110,365,17,20)],'W11':[(59,70,13,22)],
 'W12':[(31,48,10,19)],'W14':[(65,48,11,16)],
 'DR2-03':[(51,72,28,47)],'DU1-04':[(65,98,25,44)]
}
def gems(row,paint):
    result=[]
    for px,py,rx,rz in GEMS.get(row['id'],[]):
        x,z=point(row,(px,py))
        for sign in [-1,1]:
            bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1,radius=1,location=(x,sign*.020,z));obj=bpy.context.object;obj.name=row['id']+'_FacetedInset';obj.scale=(rx*row['xScale'],.012,rz*row['metresPerPixel']);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
            project(obj,row,paint,'steel',True);result.append(obj)
    return result

def tube(row,paint,name,points,radius,edge='steel'):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3;data.resolution_u=10;data.use_fill_caps=True
    s=data.splines.new('BEZIER');s.bezier_points.add(len(points)-1)
    for p,co in zip(s.bezier_points,points):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj);activate([obj]);bpy.ops.object.convert(target='MESH');obj=bpy.context.object
    for p in obj.data.polygons:p.use_smooth=True
    return project(obj,row,paint,edge,True)

def sculpted_head(row,paint):
    """Round wood branches, a hollow bell and open crystal cages add genuine
    depth; the original design texture remains only their surface treatment."""
    id=row['id'];result=[];mpp=row['metresPerPixel'];gy=row['grip'][1]
    def z(y):return (gy-y)*mpp
    if id=='W11':
        for sign in [-1,1]:
            pts=[(0,sign*.005,z(184)),(sign*.035,sign*.012,z(122)),(sign*.055,0,z(80)),(sign*.030,-sign*.008,z(31)),(-sign*.017,0,z(9))]
            result.append(tube(row,paint,'Twisted greywood branch',pts,.015,'greywood'))
        for sign in[-1,1]:
            pts=[(-.041,-.024,z(148)),(.005,-.038,z(125)),(.038,.0,z(108))] if sign<0 else[(.040,-.024,z(155)),(-.002,-.041,z(132)),(-.039,0,z(116))]
            result.append(tube(row,paint,'Crossed leather head binding',pts,.0045,'leather'))
    elif id=='W12':
        center=z(51);rx=.075;rz=.135
        result.append(tube(row,paint,'Lantern stem socket',[(0,0,z(113)),(0,0,z(82))],.017,'bronze'))
        for angle in [i*math.tau/8 for i in range(8)]:
            x=math.cos(angle)*rx;y=math.sin(angle)*rx
            result.append(tube(row,paint,'Open lantern cage bar',[(x*.55,y*.55,center-rz),(x,y,center-rz*.65),(x,y,center+rz*.70),(x*.4,y*.4,center+rz)],.004,'bronze'))
        for zz,rr in[(center-rz,.050),(center+rz*.76,.072)]:
            result.append(tube(row,paint,'Lantern cage crown',[(math.cos(t)*rr,math.sin(t)*rr,zz)for t in [i*math.tau/24 for i in range(25)]],.005,'bronze'))
    elif id=='W13':
        top=z(18);bottom=z(74);depth=top-bottom
        bpy.ops.mesh.primitive_cone_add(vertices=48,radius1=.102,radius2=.048,depth=depth,end_fill_type='NOTHING',location=(0,0,(top+bottom)/2));obj=bpy.context.object;obj.name='True hollow bell';activate([obj]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
        mod=obj.modifiers.new('Bell wall thickness','SOLIDIFY');mod.thickness=.004;bpy.ops.object.modifier_apply(modifier=mod.name)
        mod=obj.modifiers.new('Rolled bell edges','BEVEL');mod.width=.002;mod.segments=3;bpy.ops.object.modifier_apply(modifier=mod.name)
        for p in obj.data.polygons:p.use_smooth=True
        result.append(project(obj,row,paint,'steel',True))
        result.append(tube(row,paint,'Bell rim',[(.102*math.cos(t),.102*math.sin(t),bottom)for t in[i*math.tau/32 for i in range(33)]],.004,'bronze'))
        result.append(tube(row,paint,'Bell clapper',[(0,0,top),(0,0,bottom-.01)],.006,'bronze'))
        result.append(tube(row,paint,'Bell staff neck',[(0,0,z(125)),(0,0,z(69))],.014,'bronze'))
    elif id=='DU1-04':
        center=z(104);rx=.058;rz=.133
        result.append(tube(row,paint,'Crystal cage stem socket',[(0,0,z(226)),(0,0,z(180))],.016,'bronze'))
        for angle in[i*math.tau/4 for i in range(4)]:
            result.append(tube(row,paint,'Open diamond crystal setting',[(0,0,center-rz),(math.cos(angle)*rx,math.sin(angle)*rx,center),(0,0,center+rz)],.005,'bronze'))
    return result

def rounded_bow_grip(row,paint):
    # A real circular cross-section centered on the existing palm, not a flat
    # strip and not an extra transform of the character's hand.
    bpy.ops.mesh.primitive_cylinder_add(vertices=24,radius=.018,depth=.135,location=(0,0,0));obj=bpy.context.object;obj.name=row['id']+'_RoundPalmGrip'
    bevel=obj.modifiers.new('Grip edge roll','BEVEL');bevel.width=.002;bevel.segments=3;activate([obj]);bpy.ops.object.modifier_apply(modifier=bevel.name)
    for p in obj.data.polygons:p.use_smooth=True
    return project(obj,row,paint,'leather',True)

def join(objects,name):
    objects=[o for o in objects if o];activate(objects);bpy.ops.object.join();obj=bpy.context.object;obj.name=name
    # All exported nodes share the physical palm origin.
    bpy.context.scene.cursor.location=(0,0,0);bpy.ops.object.origin_set(type='ORIGIN_CURSOR')
    return obj

def bow_flex(row,obj):
    original=set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=str(ROOT/'src/cocos/assets/resources/actors/props-native/bow/bow.fbx'))
    imported=[o for o in bpy.data.objects if o not in original]
    target=next(o for o in imported if o.type=='MESH' and o.data.shape_keys)
    world=target.matrix_world.copy();target.parent=None;target.matrix_world=Matrix.Identity(4);target.data.transform(world,shape_keys=True)
    target.data.transform(Matrix.Diagonal((1,1,row['length']/1.4,1)),shape_keys=True)
    for key in target.data.shape_keys.key_blocks:key.value=0
    # First bind on Basis, then let Blender transfer the existing authored flex.
    activate([obj]);mod=obj.modifiers.new('Draw','SURFACE_DEFORM');mod.target=target;mod.falloff=4
    bpy.ops.object.surfacedeform_bind(modifier=mod.name)
    if not mod.is_bound:raise RuntimeError('Native Surface Deform did not bind '+row['id'])
    target.data.shape_keys.key_blocks['Draw'].value=1;bpy.context.view_layer.update()
    bpy.ops.object.modifier_apply_as_shapekey(modifier=mod.name,keep_modifier=False)
    obj.data.shape_keys.key_blocks['Draw'].value=0
    # Extract the author's actual tiny string faces directly. FBX hard-edge
    # duplicates make loose-part separation unreliable for shape-key meshes.
    # This adapter copies original topology and Basis/Draw coordinates exactly.
    reference=target.data.shape_keys.reference_key.data
    draw=target.data.shape_keys.key_blocks['Draw'].data
    faces=json.loads((BASE/'stock-string.json').read_text())['faces']
    used=sorted({i for face in faces for i in face});lookup={old:new for new,old in enumerate(used)}
    if not used:raise RuntimeError('No stock string faces '+row['id'])
    mesh=bpy.data.meshes.new(row['id']+'_OriginalString');mesh.from_pydata([reference[i].co.copy()for i in used],[],[[lookup[i]for i in face]for face in faces]);mesh.update()
    string=bpy.data.objects.new(row['id']+'_AuthoredBowString',mesh);bpy.context.collection.objects.link(string)
    basis=string.shape_key_add(name='Basis');key=string.shape_key_add(name='Draw')
    for vertex,old in zip(key.data,used):vertex.co=draw[old].co
    if min(v.co.x for v in key.data)>-.57:raise RuntimeError('Missing original nock '+row['id'])
    if max(v.co.z for v in basis.data)-min(v.co.z for v in basis.data)<row['length']*.72:raise RuntimeError('Incomplete string '+row['id'])
    mesh.materials.append(side('string'));activate([string]);bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.01);bpy.ops.object.mode_set(mode='OBJECT')
    strings=[string];pieces=[]
    # The adapter consumes only Draw. Discard unused importer Basis duplicates.
    if obj.data.shape_keys:
        reference_key=obj.data.shape_keys.reference_key
        obj.data.shape_keys.key_blocks['Draw'].relative_key=reference_key
        for key in list(obj.data.shape_keys.key_blocks):
            if key!=reference_key and key.name!='Draw':obj.shape_key_remove(key)
    contact=[]
    # Preserve the calibrated nock, but attach both string ends to the newly
    # designed tips. The old string's stock endpoints don't fit every 2D bow.
    for phase in ['Basis','Draw']:
        body_points=[v.co.copy()for v in (obj.data.shape_keys.reference_key.data if phase=='Basis' else obj.data.shape_keys.key_blocks['Draw'].data)]
        tree=BVHTree.FromPolygons(body_points,[list(p.vertices)for p in obj.data.polygons],all_triangles=False)
        all_points=[v.co.copy()for part in strings for v in (part.data.shape_keys.reference_key.data if phase=='Basis'else part.data.shape_keys.key_blocks['Draw'].data)]
        ends=[]
        for sign in [-1,1]:
            extreme=(min if sign<0 else max)(v.z for v in all_points)
            group=[v for v in all_points if abs(v.z-extreme)<.004]
            old=sum(group,Vector())/len(group);hit,_,_,distance=tree.find_nearest(old);hit.y=0
            ends.append((old,hit-old));contact.append({'phase':phase,'end':sign,'oldEndpoint':list(old),'newEndpoint':list(hit),'adaptationMetres':distance})
        max_nock=0
        for part in strings:
            data=part.data.shape_keys.reference_key.data if phase=='Basis'else part.data.shape_keys.key_blocks['Draw'].data
            for v in data:
                old=v.co.copy();endpoint,delta=ends[0 if old.z<0 else 1];weight=min(1,max(0,(abs(old.z)-.08)/max(.001,abs(endpoint.z)-.08)))**2;v.co=old+delta*weight
                if abs(old.z)<.08:max_nock=max(max_nock,(v.co-old).length)
            part.data.update()
        if max_nock>.0001:raise RuntimeError('Arrow nock drift '+row['id'])
        contact.append({'phase':phase,'maxNockDriftMetres':max_nock})
    # Preserve the 2D body's physical proportions and its straight resting
    # string. Per-weapon native morph calibration follows the established hand
    # trajectory without widening the design or moving the character's hand.
    template=json.loads((BASE/'stock-bow-template.json').read_text());old_points=template['positions'];old_draw=template['draw']
    nock_indices=[i for i in used if abs(old_points[i][2])<.08]
    old_base=sum(old_points[i][0]for i in nock_indices)/len(nock_indices);old_full=sum(old_draw[i][0]for i in nock_indices)/len(nock_indices)
    base_ends=[Vector(x['newEndpoint'])for x in contact if x.get('phase')=='Basis'and 'newEndpoint'in x]
    bottom,top=base_ends;line_slope=(top.x-bottom.x)/(top.z-bottom.z);new_base=bottom.x-bottom.z*line_slope
    for part in strings:
        reference=part.data.shape_keys.reference_key.data
        for v,old_index in zip(reference,used):v.co.x=new_base+v.co.z*line_slope+(old_points[old_index][0]-old_base)
    calibration={'scale':(old_full-old_base)/(old_full-new_base),'offset':(old_base-new_base)/(old_full-new_base),'oldRestNockX':old_base,'restNockX':new_base,'fullNockX':old_full,'restingString':'Straight between new tips; original 2D aspect ratio retained','contact':'Affine native Draw adaptation; body/wrist/arrow helpers unchanged'}
    calibration['maxNockCentreErrorMetres']=max(abs((old_base+w*(old_full-old_base))-(new_base+(w*calibration['scale']+calibration['offset'])*(old_full-new_base)))for w in [0,.2,.5,1,1.5])
    (BASE/'models'/(row['id']+'-draw-calibration.json')).write_text(json.dumps(calibration,indent=2)+'\n')
    for part in strings:
        for vertex,reference_vertex in zip(part.data.vertices,part.data.shape_keys.reference_key.data):vertex.co=reference_vertex.co
        part.data.update()
    bpy.context.view_layer.update()
    (BASE/'models'/(row['id']+'-string-contact.json')).write_text(json.dumps(contact,indent=2)+'\n')
    for part in set(imported+pieces):
        if part in strings:continue
        if part.name in bpy.data.objects:bpy.data.objects.remove(part,do_unlink=True)
    return strings

def leather_case(row):
    # Matching silhouette-length case. The real new hilt, without shrinking,
    # remains above it. Native bevel geometry adds ferrule/tooling/rim depth.
    start=(row['grip'][1]-(row['guardY']-row['height']*.035))*row['metresPerPixel']
    length=max(.35,row['grip'][1]*row['metresPerPixel']-start)
    bpy.ops.mesh.primitive_cone_add(vertices=16,radius1=.022,radius2=.009,depth=length,location=(0,0,start+length/2));case=bpy.context.object;case.name=row['id']+'_LeatherScabbard';case.scale.y=.48;activate([case]);bpy.ops.object.transform_apply(location=True,rotation=False,scale=True)
    case.data.materials.append(side('leather'));case['design_part']=True
    parts=[case]
    for z,radius in [(start,.023),(start+length*.53,.017),(start+length*.98,.010)]:
        bpy.ops.mesh.primitive_torus_add(major_radius=radius-.002,minor_radius=.002,major_segments=24,minor_segments=6,location=(0,0,z));band=bpy.context.object;band.name=row['id']+'_ScabbardFerrule';band.scale.y=.48;activate([band]);bpy.ops.object.transform_apply(location=True,rotation=False,scale=True);band.data.materials.append(side('bronze'if row['id']in['W03','DE06']else'steel'));parts.append(band)
    return parts

def export(objects,name,row,stowed=False):
    folder=OUT/name;folder.mkdir(exist_ok=True)
    fbx=folder/(name+'.fbx');activate(objects)
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'MESH'},axis_forward='Z',axis_up='Y',bake_space_transform=True,bake_anim=False,use_mesh_modifiers=False,mesh_smooth_type='FACE',path_mode='RELATIVE',colors_type='NONE',use_custom_props=False)
    mats=[]
    for o in objects:
        for m in o.data.materials:
            if m and m.name not in mats:mats.append(m.name)
    return {'id':name,'equipment':row['id'],'source':str((BASE/'sources'/(row['id']+'.blend')).relative_to(ROOT)).replace('\\','/'),'fbx':str(fbx.relative_to(ROOT)).replace('\\','/'),'sha256':sha(fbx),'materials':mats,'triangles':sum(len(o.data.loop_triangles) if (o.data.calc_loop_triangles() is None) else 0 for o in objects),'stowed':stowed,'morphs':sorted(set(k.name for o in objects if o.data.shape_keys for k in o.data.shape_keys.key_blocks if k!=o.data.shape_keys.reference_key))}

def render(objects,id):
    scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=20;scene.cycles.device='CPU';scene.render.threads_mode='FIXED';scene.render.threads=4
    scene.render.resolution_x=500;scene.render.resolution_y=900;scene.render.resolution_percentage=100;scene.render.film_transparent=True;scene.view_settings.view_transform='AgX'
    pts=[o.matrix_world@Vector(v)for o in objects for v in o.bound_box];lo=Vector([min(v[k]for v in pts)for k in range(3)]);hi=Vector([max(v[k]for v in pts)for k in range(3)]);center=(lo+hi)/2
    scene.world=bpy.data.worlds.new('Soft studio');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.3,.36,.40,1);scene.world.node_tree.nodes['Background'].inputs[1].default_value=.4
    bpy.ops.object.camera_add(location=center+Vector((1.6,-4,.35)));camera=bpy.context.object;camera.rotation_euler=(center-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=(hi-lo).z*1.13;scene.camera=camera
    for offset,power,size in [((-2,-3,3),500,3),((2,1,2),600,2),((1,-1,-2),80,2)]:
        bpy.ops.object.light_add(type='AREA',location=center+Vector(offset));light=bpy.context.object;light.data.energy=power;light.data.shape='DISK';light.data.size=size;light.rotation_euler=(center-light.location).to_track_quat('-Z','Y').to_euler()
    scene.render.filepath=str(BASE/'previews'/(id+'-three-quarter.png'));scene.render.image_settings.file_format='PNG';bpy.ops.render.render(write_still=True)

def author(row,preview=False):
    bpy.ops.wm.read_factory_settings(use_empty=True);paint=front(row)
    objects=[outline(row,p,paint)for p in row['parts']if not(p['name']=='head'and row['id']in['W11','W12','W13','DU1-04'])]+[shaft(row,paint)]+gems(row,paint)+sculpted_head(row,paint)
    if row['kind']=='bow':objects.append(rounded_bow_grip(row,paint))
    obj=join(objects,'Design_'+row['id'].replace('-','_'));objects=[obj]
    if row['kind']=='bow':objects+=bow_flex(row,obj)
    (BASE/'sources').mkdir(exist_ok=True);bpy.context.preferences.filepaths.save_version=0
    for im in bpy.data.images:
        if im.source=='FILE' and Path(bpy.path.abspath(im.filepath)).is_file():im.pack()
    bpy.context.scene['design_authority']=json.dumps({k:row.get(k)for k in ['id','name','source','sourceSHA256','designScope','gripContract']},ensure_ascii=False)
    bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'sources'/(row['id']+'.blend')))
    name='design-'+row['id'].lower();record=export(objects,name,row)
    if row['modelKind']=='sword':
        hilt=obj.copy();hilt.data=obj.data.copy();bpy.context.collection.objects.link(hilt)
        # Native bmesh plane cut only on the separate sheathed presentation.
        import bmesh
        cut=(row['grip'][1]-(row['guardY']-row['height']*.04))*row['metresPerPixel']
        bm=bmesh.new();bm.from_mesh(hilt.data);bmesh.ops.bisect_plane(bm,geom=list(bm.verts)+list(bm.edges)+list(bm.faces),plane_co=(0,0,cut),plane_no=(0,0,1),clear_outer=True,dist=1e-6);bm.to_mesh(hilt.data);bm.free();hilt.name='Sheathed_'+row['id']
        record['stowedModel']=export([hilt]+leather_case(row),'design-stowed-'+row['id'].lower(),row,True)
        for o in list(bpy.context.scene.objects):
            if o not in objects:bpy.data.objects.remove(o,do_unlink=True)
    if preview:render(objects,row['id'])
    (BASE/'models'/(row['id']+'.json')).write_text(json.dumps(record,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('DESIGN_WEAPON_READY',row['id'],record['triangles'],record['morphs'],flush=True)

def quiver():
    bpy.ops.wm.read_factory_settings(use_empty=True);objects=[]
    bpy.ops.mesh.primitive_cylinder_add(vertices=40,radius=.062,depth=.43,end_fill_type='NOTHING');body=bpy.context.object;body.name='Sewn leather quiver';body.data.materials.append(side('leather'));mod=body.modifiers.new('Leather wall','SOLIDIFY');mod.thickness=.003;activate([body]);bpy.ops.object.modifier_apply(modifier=mod.name);objects.append(body)
    bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.062,depth=.008,location=(0,0,-.216));bottom=bpy.context.object;bottom.data.materials.append(side('leather'));objects.append(bottom)
    for z in[-.21,.18,.215]:
        bpy.ops.mesh.primitive_torus_add(major_radius=.063,minor_radius=.004,major_segments=40,minor_segments=8,location=(0,0,z));o=bpy.context.object;o.data.materials.append(side('bronze'));objects.append(o)
    for i in range(6):
        t=i*math.tau/6;x=.035*math.cos(t);y=.035*math.sin(t);top=.43+(i%3)*.018
        bpy.ops.mesh.primitive_cylinder_add(vertices=8,radius=.0027,depth=.46,location=(x,y,top-.23));o=bpy.context.object;o.data.materials.append(side('wood'));objects.append(o)
        for angle in[0,math.pi*2/3,math.pi*4/3]:
            bpy.ops.mesh.primitive_uv_sphere_add(segments=8,ring_count=4,radius=1,location=(x+math.cos(angle)*.006,y+math.sin(angle)*.006,top-.035));o=bpy.context.object;o.scale=(.010,.002,.034);o.rotation_euler.z=angle;o.data.materials.append(side('string'));objects.append(o)
    obj=join(objects,'Design_Quiver');activate([obj]);bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT');bpy.ops.uv.smart_project(angle_limit=math.radians(66),island_margin=.02);bpy.ops.object.mode_set(mode='OBJECT')
    for p in obj.data.polygons:p.use_smooth=True
    (BASE/'sources').mkdir(exist_ok=True);bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'sources/quiver.blend'))
    record=export([obj],'design-quiver',{'id':'quiver'});(OUT/'quiver.json').write_text(json.dumps(record,indent=2)+'\n',encoding='utf-8')

if __name__=='__main__':
    argv=sys.argv[sys.argv.index('--')+1:]if'--'in sys.argv else[];parser=argparse.ArgumentParser();parser.add_argument('--ids',default=','.join(r['id']for r in RECORDS));parser.add_argument('--preview',action='store_true');args=parser.parse_args(argv)
    for id in args.ids.split(','):author(next(r for r in RECORDS if r['id']==id),args.preview)
    quiver()
