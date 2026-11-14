"""Bake a fitted Blender character to native weighted meshes and real animation tracks."""
from pathlib import Path
import json,shutil,math
import bpy
from mathutils import Matrix,Vector
from native_export import write_model,write_animation

C=Matrix(((1,0,0,0),(0,0,1,0),(0,-1,0,0),(0,0,0,1)))
CI=C.inverted()
def values(v): return [float(x) for x in v]
def trs(m):
    p,q,s=m.decompose(); q.normalize()
    return dict(p=values(p),q=[q.w,q.x,q.y,q.z],s=values(s))

def export_character(rig,out,prefix):
    out=Path(out); out.mkdir(parents=True,exist_ok=True)
    bones=list(rig.data.bones); bone_index={b.name:i for i,b in enumerate(bones)}
    rest=[C@rig.matrix_world@b.matrix_local@CI for b in bones]
    inverse=[m.inverted() for m in rest]
    skeleton=[]
    local_bounds=[[] for _ in bones]
    for i,b in enumerate(bones):
        parent=bone_index[b.parent.name] if b.parent else i
        transform=rest[parent].inverted()@rest[i] if b.parent else rest[i]
        data=trs(transform)
        data.update(name=b.name,parent=parent,offset=[inverse[i][r][c] for r in range(3) for c in range(4)])
        skeleton.append(data)
    rig.data.pose_position='REST'; bpy.context.view_layer.update()
    vertices=[]; material_triangles={}; materials=[]; lookup={}
    for obj in rig.children_recursive:
        if obj.type!='MESH' or obj.hide_render: continue
        # Evaluated rest meshes bake fitted shapes, bevels and masks while the
        # bone weights remain vertex attributes. The armature itself is retained.
        evaluated=obj.evaluated_get(bpy.context.evaluated_depsgraph_get())
        mesh=evaluated.to_mesh(preserve_all_data_layers=True,depsgraph=bpy.context.evaluated_depsgraph_get())
        mesh.calc_loop_triangles()
        matrix=C@obj.matrix_world
        normal_matrix=matrix.to_3x3().inverted().transposed()
        uv_layer=mesh.uv_layers.active
        group_names={g.index:g.name for g in obj.vertex_groups}
        local_materials=[]
        for mat in mesh.materials:
            if mat not in materials: materials.append(mat)
            local_materials.append(materials.index(mat))
        for tri in mesh.loop_triangles:
            mat_id=local_materials[tri.material_index] if local_materials else 0
            triangles=material_triangles.setdefault(mat_id,[])
            for li in tri.loops:
                loop=mesh.loops[li]; v=mesh.vertices[loop.vertex_index]
                p=matrix@v.co
                n=(normal_matrix@mesh.corner_normals[li].vector).normalized()
                uv=uv_layer.data[li].uv if uv_layer else (0,0)
                key=(obj.name,v.index,round(uv[0],6),round(uv[1],6),*(round(x,5) for x in n))
                if key not in lookup:
                    influences=sorted([(bone_index[group_names[g.group]],g.weight) for g in v.groups if group_names.get(g.group) in bone_index and g.weight>0.00001],key=lambda x:x[1],reverse=True)[:4]
                    if not influences: influences=[(0,1)]
                    total=sum(w for _,w in influences)
                    joints=[i for i,_ in influences]+[0]*(4-len(influences))
                    weights=[w/total for _,w in influences]+[0]*(4-len(influences))
                    lookup[key]=len(vertices)
                    vertices.append(dict(p=values(p),n=values(n),uv=[float(uv[0]),1.0-float(uv[1])],j=joints,w=weights))
                    for i,w in influences:
                        if w>.01: local_bounds[i].append(inverse[i]@p)
                triangles.append(lookup[key])
        evaluated.to_mesh_clear()
    indices=[]; geometries=[]; ordered_materials=[]
    for mat_id,triangles in material_triangles.items():
        geometries.append(dict(start=len(indices),count=len(triangles)))
        indices.extend(triangles); ordered_materials.append(materials[mat_id])
    for i,points in enumerate(local_bounds):
        if points: skeleton[i]['bounds']=[min(v[a] for v in points)-.015 for a in range(3)]+[max(v[a] for v in points)+.015 for a in range(3)]
    write_model(out/'Character.mdl',dict(vertices=vertices,indices=indices,geometries=geometries,bones=skeleton))
    material_paths=[]
    for index,mat in enumerate(ordered_materials):
        color=list(mat.get('game_color',mat.diffuse_color[:3]))
        rough=float(mat.get('game_roughness',.75)); metallic=float(mat.get('game_metallic',0))
        texture=mat.get('game_texture')
        filename=f'Material-{index:02d}.xml'
        if texture:
            source=Path(texture); destination=out/'Textures'/source.name
            destination.parent.mkdir(exist_ok=True); shutil.copy2(source,destination)
            shader='ActorTexture.shader'
            binding=f'<surfacetexture name="albedo_map" texture="{prefix}/Textures/{source.name}" />'
        else:
            shader='ActorColor.shader'; binding=''
        (out/filename).write_text(f'''<material>
<surfaceshader name="Shaders/BLGL/{shader}" />
{binding}
<parameter name="base_color" value="{' '.join(str(v) for v in color)} 1" />
<parameter name="roughness" value="{rough}" />
<parameter name="metallic" value="{metallic}" />
<parameter name="alpha_cut" value="{.35 if mat.get('game_cutout') else .001}" />
</material>\n''',encoding='utf-8')
        material_paths.append(prefix+'/'+filename)
    rig.data.pose_position='POSE'; scene=bpy.context.scene
    clips={}
    for name in ['idle','run','attack','hit']:
        action=bpy.data.actions.get(name)
        if not action: raise ValueError('Missing authored motion '+name)
        rig.animation_data.action=action
        start,end=action.frame_range; duration=(end-start)/scene.render.fps
        steps=max(2,math.ceil(duration*30))
        tracks=[dict(name=b.name,keys=[]) for b in bones]
        for f in range(steps+1):
            frame=start+(end-start)*f/steps
            scene.frame_set(math.floor(frame),subframe=frame%1)
            bpy.context.view_layer.update()
            world=[C@rig.matrix_world@rig.pose.bones[b.name].matrix@CI for b in bones]
            for i,b in enumerate(bones):
                matrix=world[bone_index[b.parent.name]].inverted()@world[i] if b.parent else world[i]
                key=trs(matrix); key['time']=duration*f/steps
                previous=tracks[i]['keys'][-1]['q'] if tracks[i]['keys'] else None
                if previous and sum(a*b for a,b in zip(previous,key['q']))<0: key['q']=[-v for v in key['q']]
                tracks[i]['keys'].append(key)
        write_animation(out/(name+'.ani'),name,duration,tracks)
        clips[name]=prefix+'/'+name+'.ani'
    rig.animation_data.action=bpy.data.actions['idle']; scene.frame_set(1)
    bpy.context.view_layer.update()
    hand=(C@rig.matrix_world@rig.pose.bones['hand_r'].matrix@CI).to_quaternion()
    sockets={}
    for kind,direction in [('sword',(0,-.65,.76)),('bow',(0,1,0)),('staff',(0,.98,.2))]:
        target=Vector((0,1,0)).rotation_difference(Vector(direction).normalized())
        q=hand.inverted()@target
        sockets[kind]=dict(rotation=[q.w,q.x,q.y,q.z],position=[0,0,-.075])
    lo=[min(v['p'][a] for v in vertices) for a in range(3)]
    hi=[max(v['p'][a] for v in vertices) for a in range(3)]
    manifest=dict(model=prefix+'/Character.mdl',materials=material_paths,clips=clips,
                  bones=len(bones),vertices=len(vertices),triangles=len(indices)//3,bounds=[lo,hi],
                  source='MakeHuman CC0 basemesh and system assets, locally fitted current character',sockets=sockets,
                  shader_resources=['Shaders/BLGL/ActorColor.shader','Shaders/BLGL/ActorTexture.shader'])
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('[NativeCharacter]',len(vertices),'vertices',len(indices)//3,'triangles',len(bones),'bones',len(clips),'motions')
    return manifest
