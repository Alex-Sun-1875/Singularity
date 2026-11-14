"""Clean shoulder construction, hero cloth cowl and subtle role expressions.

Edits only the new editable Cocos sources, before export-only LoD processing.
"""
from pathlib import Path
import bpy,bmesh,math,json
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ROOT=Path(__file__).resolve().parents[2];SOURCE=ROOT/'source-art/characters/cocos';OUT=ROOT/'src/cocos/assets/resources/actors'
IDS=['raphael','mira','lorn','nightqi','kael','evelyn','captain','raider','raider-shield','raider-archer']
def components(obj):
    adjacent=[set() for v in obj.data.vertices]
    for edge in obj.data.edges:a,b=edge.vertices;adjacent[a].add(b);adjacent[b].add(a)
    seen=set()
    for vertex in obj.data.vertices:
        if vertex.index in seen:continue
        stack=[vertex.index];part=[]
        while stack:
            index=stack.pop()
            if index in seen:continue
            seen.add(index);part.append(index);stack.extend(adjacent[index]-seen)
        yield part
def mesh(name,vertices,faces,material,rig,solid=.005):
    data=bpy.data.meshes.new(name);data.from_pydata(vertices,[],faces);data.update();data.materials.append(material);data.uv_layers.new(name='UVMap')
    for loop in data.loops:
        v=data.vertices[loop.vertex_index];data.uv_layers[0].data[loop.index].uv=(v.co.x*3+v.co.y,v.co.z*2)
    obj=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(obj)
    for poly in data.polygons:poly.use_smooth=True
    if solid:
        modifier=obj.modifiers.new('CleanLeatherThickness','SOLIDIFY');modifier.thickness=solid
        bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=modifier.name)
    modifier=obj.modifiers.new('RoundedSeam','BEVEL');modifier.width=.0018;modifier.segments=2
    bpy.context.view_layer.objects.active=obj;bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.parent=rig;group=obj.vertex_groups.new(name='spine_03');group.add(range(len(obj.data.vertices)),1,'REPLACE');modifier=obj.modifiers.new('Skin','ARMATURE');modifier.object=rig
    return obj
def box(name,center,size,mat,rig):
    cx,cy,cz=center;sx,sy,sz=[v/2 for v in size]
    vv=[(cx+x*sx,cy+y*sy,cz+z*sz) for x,y,z in [(-1,-1,-1),(-1,-1,1),(-1,1,-1),(-1,1,1),(1,-1,-1),(1,-1,1),(1,1,-1),(1,1,1)]]
    return mesh(name,vv,[(0,4,5,1),(2,3,7,6),(0,2,6,4),(1,5,7,3),(0,1,3,2),(4,6,7,5)],mat,rig,0)
for identity in IDS:
    bpy.ops.wm.open_mainfile(filepath=str(SOURCE/f'{identity}.blend'))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE');rig.animation_data.action=bpy.data.actions['idle'];bpy.context.scene.frame_set(1)
    neck=rig.data.bones['neck_01'].head_local.z;head=rig.data.bones['head'].head_local;female=identity in ['mira','nightqi','evelyn']
    vest=bpy.data.objects[identity+'_vest_surface'];leather=bpy.data.materials[identity+'_vest'];brass=bpy.data.materials[identity+'_brass']
    for obj in list(rig.children_recursive):
        if obj.name.startswith(('CleanShoulder','ShoulderBuckle','ContinuousTealCowl')):bpy.data.objects.remove(obj,do_unlink=True)
    remove=[]
    for part in components(vest):
        groups={vest.vertex_groups[g.group].name for index in part for g in vest.data.vertices[index].groups if g.weight>1e-5}
        if len(part)==180 and groups=={'spine_03'}:remove.extend(part)
    if remove:
        bm=bmesh.new();bm.from_mesh(vest.data);bm.verts.ensure_lookup_table();bmesh.ops.delete(bm,geom=[bm.verts[i] for i in remove],context='VERTS');bm.to_mesh(vest.data);bm.free()
    shirt=bpy.data.objects['male_casualsuit01'];ev=shirt.evaluated_get(bpy.context.evaluated_depsgraph_get());data=ev.to_mesh();surface=BVHTree.FromPolygons([v.co for v in data.vertices],[list(p.vertices) for p in data.polygons]);ev.to_mesh_clear()
    for side in [-1,1]:
        vv=[];ff=[];rows=24;columns=5;front_y=-.175 if not female else -.155;back_y=.145 if not female else .125
        for j in range(rows):
            t=j/(rows-1);base_x=(.125 if female else .15)+.035*math.sin(t*math.pi);y=front_y+(back_y-front_y)*t
            for i in range(columns):
                x=side*(base_x+(i/(columns-1)-.5)*.042);z=neck-.145+.095*math.sin(t*math.pi)
                hit,normal,index,distance=surface.ray_cast(Vector((x,y,neck+.4)),Vector((0,0,-1)),.75)
                if hit and .08<t<.92:z=max(z,hit.z+.025)
                vv.append((x,y,z))
        for j in range(rows-1):
            for i in range(columns-1):ff.append((j*columns+i,j*columns+i+1,(j+1)*columns+i+1,(j+1)*columns+i))
        mesh('CleanShoulderBand_'+str(side),vv,ff,leather,rig)
        # A closed rectangular frame is an intentional fastening at each end.
        x=side*(.125 if female else .15);y=front_y-.009;z=neck-.125
        for dx in [-.020,.020]:box('ShoulderBuckleVertical',(x+dx,y,z),(.005,.007,.032),brass,rig)
        for dz in [-.016,.016]:box('ShoulderBuckleHorizontal',(x,y,z+dz),(.045,.007,.005),brass,rig)
    if identity=='raphael':
        mat=bpy.data.materials['raphael_mantle'];vv=[];ff=[];columns=64;rows=10
        for j in range(rows):
            t=j/(rows-1)
            for i in range(columns):
                a=i*math.tau/columns;rx=.108+.047*t;ry=.13+.035*t
                z=neck+.014-t*.09+.006*math.cos(a*3)*math.sin(t*math.pi)
                vv.append((math.cos(a)*rx,math.sin(a)*ry-.009,z))
        for j in range(rows-1):
            for i in range(columns):ff.append((j*columns+i,j*columns+(i+1)%columns,(j+1)*columns+(i+1)%columns,(j+1)*columns+i))
        mesh('ContinuousTealCowl',vv,ff,mat,rig,.006)
        # The hero's shoulder fastenings sit beneath his cloak and steel plate;
        # exposed apron-style buckles would sit unnaturally on the drape.
        for obj in list(rig.children_recursive):
            if obj.name.startswith(('CleanShoulder','ShoulderBuckle')):bpy.data.objects.remove(obj,do_unlink=True)
    if identity in ['raphael','mira']:
        skin=bpy.data.objects[identity+'_skin_surface']
        if not skin.get('v5_expression_refinement'):
            ratio=.90 if female else 1.;mouth_z=head.z-.040*ratio
            for vertex in skin.data.vertices:
                p=vertex.co
                if p.y<-.095:
                    corner=math.exp(-((abs(p.x)-.024*ratio)/(.012*ratio))**2-((p.z-mouth_z)/(.012*ratio))**2)
                    asym=(1.0 if p.x>0 else .62) if identity=='raphael' else 1.0
                    p.z+=corner*(.0037 if identity=='mira' else .0035)*asym
                    p.y-=corner*.0007
                    brow=math.exp(-((abs(p.x)-.023*ratio)/(.025*ratio))**2-((p.z-(head.z+.055*ratio))/(.018*ratio))**2)
                    p.z+=brow*(.0013 if identity=='mira' else .0017)
            skin['v5_expression_refinement']='Mira relaxed brows and small bilateral smile' if female else 'Raphael lifted inner brow and asymmetric mouth corner'
            brows=bpy.data.objects.get(identity+'_brows_surface')
            if brows:
                for vertex in brows.data.vertices:vertex.co.z+=.0014 if female else .0017*(1-min(1,abs(vertex.co.x)/.08))
    for prefix,name in [('CleanShoulder','CleanShoulderBands'),('ShoulderBuckle','ShoulderBuckles')]:
        objects=[o for o in rig.children_recursive if o.name.startswith(prefix)]
        if len(objects)>1:
            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:obj.select_set(True)
            bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name=name
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{identity}.blend'),relative_remap=False)
    print('[SOURCE_REFINED]',identity,'replaced collar-band vertices',len(remove),flush=True)
