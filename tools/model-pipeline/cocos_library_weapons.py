"""Normalize licensed, UV-authored Equipment01 meshes to existing game sockets."""
from pathlib import Path
import bpy,sys,json,re,shutil,math,os
import numpy as np
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
LIBRARY=ROOT/'src/.tools/makehuman-community/clothes'
OUT=Path(os.environ.get('SINGULARITY_CHARACTER_ASSETS',ROOT/'src/cocos/assets/resources/actors'))/'props'
SOURCE=Path(os.environ.get('SINGULARITY_CHARACTER_SOURCE',ROOT/'source-art/characters/cocos'))
DRAFT=ROOT/'src/.tmp/character-fidelity/weapons'
PROFILES={
    'sword':('joepal_crude_sword',1.00,.12,'steel'),
    'bow':('culturalibre_wooden_bow',1.40,.50,'LibraryBow'),
    'staff':('culturalibre_magic_sceptre',1.75,.46,'LibrarySceptre'),
}

def wood_grip_center(mesh, positions, plane, scale, previous):
    """Intersect the wooden limb, whose middle faces have no middle vertices.

    The pinned author mesh has separate wooden and black-string components.
    Averaging a vertex band at the middle therefore selected only the string.
    """
    adjacency={v.index:set() for v in mesh.vertices}
    for edge in mesh.edges:
        a,b=edge.vertices;adjacency[a].add(b);adjacency[b].add(a)
    components=[];seen=set()
    for start in adjacency:
        if start in seen:continue
        pending=[start];seen.add(start);component=set()
        while pending:
            index=pending.pop();component.add(index)
            for other in adjacency[index]-seen:seen.add(other);pending.append(other)
        components.append(component)
    wood=max(components,key=len);hits=[]
    for edge in mesh.edges:
        if edge.vertices[0] not in wood:continue
        a,b=[positions[index] for index in edge.vertices]
        if (a.z-plane)*(b.z-plane)<=0 and abs(a.z-b.z)>1e-8:
            hits.append(a.lerp(b,(plane-a.z)/(b.z-a.z)))
    if len(hits)<4:raise RuntimeError('Cannot locate the author wooden grip cross-section')
    center=Vector(tuple((min(p[i] for p in hits)+max(p[i] for p in hits))*.5 for i in range(3)))
    center.z=plane
    return center,{'method':'Largest connected wooden component; edge intersections at the author middle grip plane, cross-section bounds center. Artist UVs and geometry retained.',
        'woodVertices':len(wood),'componentVertexCounts':[len(c) for c in components],
        'crossSectionEdgeIntersections':len(hits),'pivotDeltaMeters':list((center-previous)*scale)}


def build(production=False,selected=None):
    # A selected production repair preserves the other authoring objects and
    # never exports or rewrites their standalone FBX or textures.
    if production and selected:bpy.ops.wm.open_mainfile(filepath=str(SOURCE/'weapons.blend'))
    else:bpy.ops.wm.read_factory_settings(use_empty=True)
    output=OUT if production else DRAFT
    (output/'textures').mkdir(parents=True,exist_ok=True)
    records={}
    for name,(asset,length,grip_fraction,material_name) in PROFILES.items():
        if selected and name not in selected:continue
        existing=bpy.data.objects.get('Library_'+name)
        if existing:
            mesh=existing.data;bpy.data.objects.remove(existing,do_unlink=True)
            if mesh.users==0:bpy.data.meshes.remove(mesh)
        existing_material=bpy.data.materials.get(material_name)
        if existing_material and existing_material.users==0:bpy.data.materials.remove(existing_material)
        folder=LIBRARY/asset;mesh_path=next(folder.glob('*.obj'))
        bpy.ops.wm.obj_import(filepath=str(mesh_path),forward_axis='NEGATIVE_Z',up_axis='Y')
        obj=bpy.context.object;obj.name='Library_'+name
        # The source objects were authored tilted in a T-pose hand. Principal
        # axis normalization retains their geometry and artist-authored UVs.
        coords=np.array([tuple(v.co) for v in obj.data.vertices]);center=coords.mean(axis=0)
        eigenvalues,eigenvectors=np.linalg.eigh(np.cov((coords-center).T));axis=eigenvectors[:,-1]
        if axis[2]<0:axis=-axis
        rotation=Vector(axis).rotation_difference(Vector((0,0,1)))
        positions=[rotation@Vector(co-center) for co in coords]
        lo=min(p.z for p in positions);hi=max(p.z for p in positions);scale=length/(hi-lo)
        # Center the narrow grip on the long axis, not the visible mesh bounds.
        grip=lo+(hi-lo)*grip_fraction
        around=[p for p in positions if abs(p.z-grip)<(hi-lo)*.025]
        gx=sum(p.x for p in around)/len(around) if around else 0
        gy=sum(p.y for p in around)/len(around) if around else 0
        pivot=Vector((gx,gy,grip));grip_record=None
        if name=='bow':pivot,grip_record=wood_grip_center(obj.data,positions,grip,scale,pivot)
        for vertex,position in zip(obj.data.vertices,positions):vertex.co=(position-pivot)*scale
        obj.location=(0,0,0);obj.rotation_euler=(0,0,0);obj.scale=(1,1,1)
        if name=='bow':
            # Bow's bend sits on the same local Y plane as the former longbow.
            pass
        material=bpy.data.materials.new(material_name);material.use_nodes=True
        bsdf=material.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Roughness'].default_value=.57 if name=='sword' else .80;bsdf.inputs['Metallic'].default_value=.72 if name=='sword' else .05
        text=next(folder.glob('*.mhmat')).read_text();source=folder/re.search(r'^diffuseTexture\s+(.+)$',text,re.M).group(1).strip()
        destination=output/'textures'/('library-'+name+'.png')
        preserve_texture=production and selected and destination.exists()
        if not preserve_texture:shutil.copy2(source,destination)
        image=bpy.data.images.load(str(destination));width,height=image.size
        if max(width,height)>256 and not preserve_texture:
            ratio=256/max(width,height);image.scale(round(width*ratio),round(height*ratio));image.filepath_raw=str(destination);image.file_format='PNG';image.save()
        tex=material.node_tree.nodes.new('ShaderNodeTexImage');tex.image=image;material.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        obj.data.materials.clear();obj.data.materials.append(material)
        # Keep deliberately crisp blade bevels and curved wooden limb normals.
        for polygon in obj.data.polygons:polygon.use_smooth=name!='sword'
        bpy.ops.object.select_all(action='DESELECT');obj.select_set(True);bpy.context.view_layer.objects.active=obj
        bpy.ops.export_scene.fbx(filepath=str(output/(name+'.fbx')),use_selection=True,object_types={'MESH'},axis_forward='Z',axis_up='Y',add_leaf_bones=False,bake_anim=False,path_mode='RELATIVE',apply_unit_scale=True)
        if production:
            original=SOURCE/'textures/props'/source.name;original.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(source,original)
            image.filepath=str(original);image.reload();image.filepath='//textures/props/'+original.name
        records[name]={'asset':asset,'lengthMeters':length,'gripOrigin':[0,0,0],'longAxis':'Cocos +Y','license':'CC0-1.0','creator':'Joel Palmius' if name=='sword' else 'Quaternius; MakeHuman adaptation by culturalibre'}
        if grip_record:records[name]['woodGripAdapter']=grip_record
        obj.hide_render=True;obj.hide_set(True)
        print('[LIBRARY_WEAPON]',name,records[name],flush=True)
    for obj in bpy.data.objects:obj.hide_render=False;obj.hide_set(False)
    destination=SOURCE/'weapons.blend' if production else DRAFT/'weapons.blend'
    bpy.context.preferences.filepaths.save_version=0;bpy.ops.wm.save_as_mainfile(filepath=str(destination))
    if production:
        path=OUT/'manifest.json';manifest=json.loads(path.read_text());manifest.setdefault('libraryFidelity',{}).update(records);path.write_text(json.dumps(manifest,indent=2))

if __name__=='__main__':build('--production' in sys.argv,sys.argv[sys.argv.index('--weapon')+1].split(',') if '--weapon' in sys.argv else None)
