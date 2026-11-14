"""Local v5-directed Cocos FBX authoring. Never changes the legacy sources.

Run with Blender 4.5: --background --python this.py -- [--character ID]
"""
from pathlib import Path
import bpy,bmesh,math,json,sys,random,shutil,os
import numpy as np
from mathutils import Vector,Quaternion
from mathutils.kdtree import KDTree
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'source-art/characters/cocos'
OUT=ROOT/'src/cocos/assets/resources/actors'
PACK=ROOT/'src/.tools/makehuman-assets'
SOURCE.mkdir(parents=True,exist_ok=True)
CLIPS={'idle':2.4,'run':.8,'attack_sword':.9,'attack_bow':1.25,'attack_staff':1.2,'spell':1.5,'dodge':.85,'hit':.55,'death':2.1,'interact':1.6}
PROFILES={
 'raphael':dict(base='raphael',height=1.85,width=1.,hair='curly',haircolor=(.12,.060,.029),coat=(.20,.085,.035),cloth=(.72,.66,.53),cape=(.045,.10,.095),length=.08,armor='single',weapon='sword'),
 'mira':dict(base='mira',height=1.70,width=.98,hair='bob',haircolor=(.64,.40,.14),coat=(.22,.022,.027),cloth=(.73,.65,.50),length=.64,armor='none',weapon='daggers'),
 'lorn':dict(base='raphael',height=1.93,width=1.14,hair='short',haircolor=(.035,.025,.021),coat=(.085,.12,.15),cloth=(.12,.16,.19),length=.25,armor='both',weapon='shield'),
 'nightqi':dict(base='mira',height=1.78,width=.97,hair='ponytail',haircolor=(.61,.39,.13),coat=(.14,.10,.055),cloth=(.24,.23,.17),cape=(.13,.16,.12),length=.22,armor='none',weapon='bow'),
 'kael':dict(base='raphael',height=1.68,width=.92,hair='youth',haircolor=(.16,.07,.026),coat=(.47,.25,.065),cloth=(.76,.71,.58),length=.08,armor='none',weapon='maps'),
 'evelyn':dict(base='mira',height=1.76,width=1.04,hair='halfup',haircolor=(.66,.43,.16),coat=(.07,.12,.21),cloth=(.78,.74,.64),length=.47,armor='both',weapon='lantern'),
 'captain':dict(base='raphael',height=1.91,width=1.11,hair='short',haircolor=(.29,.29,.26),coat=(.17,.19,.19),cloth=(.13,.16,.17),cape=(.23,.035,.027),length=.32,armor='both',weapon='hammer'),
 'raider':dict(base='raider',height=1.79,width=1.02,hair='short',haircolor=(.075,.043,.02),coat=(.105,.061,.029),cloth=(.27,.22,.15),length=.14,armor='single',weapon='sword'),
 'raider-shield':dict(base='raider',height=1.88,width=1.19,hair='short',haircolor=(.045,.026,.016),coat=(.14,.075,.027),cloth=(.19,.15,.095),length=.22,armor='both',weapon='shield'),
 'raider-archer':dict(base='raider',height=1.75,width=.94,hair='youth',haircolor=(.11,.055,.021),coat=(.16,.12,.065),cloth=(.29,.28,.19),cape=(.13,.15,.085),length=.16,armor='none',weapon='bow'),
}

def build(identity):
    profile=PROFILES[identity]; random.seed(identity)
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'source-art/characters'/f"{profile['base']}.blend"))
    rig=next(o for o in bpy.data.objects if o.type=='ARMATURE'); rig.name=identity
    rig.animation_data_clear()
    for action in list(bpy.data.actions): bpy.data.actions.remove(action)
    rig.data.pose_position='REST'
    body=next(o for o in rig.children_recursive if o.name.endswith('_body'))
    shirt=bpy.data.objects.get('male_casualsuit01'); boots=bpy.data.objects.get('shoes03')
    fitted_vest=bpy.data.objects.get('TailoredLeatherVest')
    keep={rig,body,shirt,boots,fitted_vest,bpy.data.objects.get('high-poly'),bpy.data.objects.get('eyebrow001')}
    for obj in list(bpy.data.objects):
        if obj not in keep: bpy.data.objects.remove(obj,do_unlink=True)
    # Freeze the current MakeHuman morph mix while retaining skin weights and
    # UVs. Remove the old long-sleeve occlusion masks before exposing forearms.
    for modifier in list(body.modifiers):
        if modifier.type=='MASK' and modifier.name.startswith('Delete.'):body.modifiers.remove(modifier)
    bpy.context.view_layer.update()
    deps=bpy.context.evaluated_depsgraph_get()
    body.data=bpy.data.meshes.new_from_object(body.evaluated_get(deps),preserve_all_data_layers=True,depsgraph=deps)
    weight_body=body.data.copy()
    for modifier in list(body.modifiers):
        if modifier.type!='ARMATURE':body.modifiers.remove(modifier)
    # Torso and legs are covered; retain the face, neck, upper arms, forearms,
    # and hands. This avoids hidden geometry cost and garment intersections.
    bm=bmesh.new();bm.from_mesh(body.data)
    neck_z=rig.data.bones['neck_01'].head_local.z;hip_z=rig.data.bones['pelvis'].head_local.z
    hidden=[f for f in bm.faces if f.calc_center_median().z<neck_z-.22 and (abs(f.calc_center_median().x)<.20 or f.calc_center_median().z<hip_z+.06)]
    bmesh.ops.delete(bm,geom=hidden,context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(body.data);bm.free()
    assert any(v.groups for v in body.data.vertices),'Evaluated source lost skinning'
    names={b.name for b in rig.data.bones}
    tree=KDTree(len(weight_body.vertices))
    for v in weight_body.vertices: tree.insert(v.co,v.index)
    tree.balance()
    folder=OUT/identity; folder.mkdir(parents=True,exist_ok=True)
    texture_folder=folder/'textures'; texture_folder.mkdir(exist_ok=True)
    texture_paths=[]
    def image_material(name,color,rough=.8,metal=0,kind='leather',source=None,alpha=False):
        mat=bpy.data.materials.new(identity+'_'+name); mat.use_nodes=True
        nodes=mat.node_tree.nodes; bsdf=nodes.get('Principled BSDF')
        bsdf.inputs['Base Color'].default_value=(*color,1); bsdf.inputs['Roughness'].default_value=rough; bsdf.inputs['Metallic'].default_value=metal
        mat.diffuse_color=(*color,1)
        path=texture_folder/(name+'.png')
        if source:
            # Save a real local texture, not a packed-only or upstream reference.
            shutil.copy2(source,path)
            im=bpy.data.images.load(str(path),check_existing=False)
            if name in ['skin','brows']:
                pixels=np.array(im.pixels[:],dtype=np.float32).reshape(-1,4)
                tint=(.92,.80,.68) if name=='skin' else ((.48,.27,.09) if female else (.22,.10,.045))
                pixels[:,:3]*=np.asarray(tint);im.pixels.foreach_set(pixels.ravel());im.save()
        else:
            n=256; yy,xx=np.mgrid[:n,:n]; rng=np.random.default_rng(sum(map(ord,name)))
            grain=rng.random((n,n))-.5
            if kind=='cloth': pattern=.93+.05*np.sin(xx*math.pi)+.04*np.sin(yy*math.pi)+grain*.075
            elif kind=='steel': pattern=.95+.04*np.sin(yy*.2)+grain*.11
            elif kind=='hair': pattern=.96+.025*np.sin(xx*.04+np.sin(yy*.03))+grain*.015
            else: pattern=.92+.055*np.sin(xx*.07)*np.sin(yy*.09)+grain*.10
            arr=np.ones((n,n,4),dtype=np.float32)
            for i in range(3): arr[:,:,i]=np.clip(color[i]*pattern,0,1)
            im=bpy.data.images.new(identity+'_'+name,width=n,height=n)
            im.pixels.foreach_set(arr.ravel()); im.filepath_raw=str(path); im.file_format='PNG'; im.save()
        tex=nodes.new('ShaderNodeTexImage'); tex.image=im
        mat.node_tree.links.new(tex.outputs['Color'],bsdf.inputs['Base Color'])
        if alpha:
            mat.node_tree.links.new(tex.outputs['Alpha'],bsdf.inputs['Alpha']); mat.surface_render_method='DITHERED'
        texture_paths.append('textures/'+path.name)
        mat['roughness']=rough; mat['metallic']=metal
        if kind=='hair':bsdf.inputs['Specular IOR Level'].default_value=0;bsdf.inputs['Roughness'].default_value=.94
        return mat
    female=profile['base']=='mira'
    skin_dir=PACK/'skins'/('young_caucasian_female2' if female else 'young_caucasian_male2')
    skin_source=next(skin_dir.glob('*diffuse*.png'))
    skin=image_material('skin',(.8,.6,.45),.68,source=skin_source)
    eyes=image_material('eyes',(.8,.7,.5),.22,source=PACK/'eyes/materials/brown_eye.png')
    brows=image_material('brows',(.1,.05,.02),.8,source=PACK/'eyebrows/eyebrow001/eyebrow001.png',alpha=True)
    linen=image_material('linen',profile['cloth'],.94,kind='cloth')
    wool=image_material('trousers',(.115,.087,.059) if identity!='lorn' else (.07,.08,.09),.95,kind='cloth')
    leather=image_material('vest',profile['coat'],.70)
    dark=image_material('belt',(.065,.033,.017),.72)
    steel=image_material('steel',(.29,.32,.32) if identity!='captain' else (.4,.42,.41),.58,.72,kind='steel')
    brass=image_material('brass',(.45,.27,.085),.42,.72,kind='steel')
    hairmat=image_material('hair',profile['haircolor'],.65,kind='hair')
    wood=image_material('wood',(.22,.11,.042),.81)
    white=image_material('parchment',(.76,.70,.52),.95,kind='cloth')
    for obj,mat in [(body,skin),(boots,dark),(bpy.data.objects.get('high-poly'),eyes),(bpy.data.objects.get('eyebrow001'),brows)]:
        obj.data.materials.clear(); obj.data.materials.append(mat)
    shirt.data.materials.clear(); shirt.data.materials.append(linen); shirt.data.materials.append(wool)
    hip=rig.data.bones['pelvis'].head_local.z; neck=rig.data.bones['neck_01'].head_local.z
    head=rig.data.bones['head'].head_local
    h=neck-hip; ratio=h/.567
    waist_points=[v.co for v in shirt.data.vertices if abs(v.co.z-(hip-.03))<.03]
    waist_rx=max(abs(p.x) for p in waist_points)+.009
    # Short sleeves expose the actual skinned forearms; the old mantle was a
    # cropped shirt including a swollen sleeve cap and is deliberately removed.
    bm=bmesh.new(); bm.from_mesh(shirt.data)
    remove=[]
    for face in bm.faces:
        center=face.calc_center_median(); face.material_index=0 if center.z>hip else 1
        for side in ['l','r']:
            start=rig.data.bones['lowerarm_'+side].head_local
            end=rig.data.bones['lowerarm_'+side].tail_local
            along=(center-start).dot((end-start).normalized())
            if (center-start).length<.40 and along>.09 and abs(center.x)>.28*ratio: remove.append(face); break
    remove=list(set(remove))
    bmesh.ops.delete(bm,geom=remove,context='FACES')
    bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
    bm.to_mesh(shirt.data); bm.free()
    # Keep the complete shirt shoulder and collar. The fitted outer garment is
    # projected onto it; changing shirt vertices created visible arm artifacts.
    for poly in shirt.data.polygons: poly.use_smooth=True
    def bind(obj,bone=None):
        obj.parent=rig; obj.matrix_parent_inverse.identity()
        for name in names:
            if not obj.vertex_groups.get(name): obj.vertex_groups.new(name=name)
        for v in obj.data.vertices:
            if bone: influences=[(bone,1)]
            else:
                _,i,_=tree.find(v.co)
                influences=sorted([(body.vertex_groups[g.group].name,g.weight) for g in weight_body.vertices[i].groups if body.vertex_groups[g.group].name in names],key=lambda p:-p[1])[:4]
            total=sum(w for _,w in influences) or 1
            for name,weight in influences: obj.vertex_groups[name].add([v.index],weight/total,'REPLACE')
        mod=obj.modifiers.new('Skin','ARMATURE'); mod.object=rig
        for poly in obj.data.polygons: poly.use_smooth=True
        return obj
    def mesh(name,verts,faces,mat,bone=None,solid=0):
        data=bpy.data.meshes.new(name); data.from_pydata(verts,[],faces); data.update()
        obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj); data.materials.append(mat)
        # All authored meshes have real UVs, including garments and props.
        uv=data.uv_layers.new(name='UVMap')
        for loop in data.loops:
            co=data.vertices[loop.vertex_index].co; uv.data[loop.index].uv=(co.x*3+co.y,co.z*2)
        bind(obj,bone)
        if solid: mod=obj.modifiers.new('Thickness','SOLIDIFY'); mod.thickness=solid
        return obj
    def box(name,loc,size,mat,bone='pelvis',bevel=.008):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        obj=bpy.context.object; obj.name=name; obj.scale=size
        bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
        for v in obj.data.vertices: v.co+=obj.location
        obj.location=(0,0,0); obj.data.materials.append(mat); bind(obj,bone)
        if bevel:
            m=obj.modifiers.new('RoundedEdges','BEVEL'); m.width=bevel; m.segments=3
        return obj
    def tube(name,points,radius,mat,bone='spine_02',res=2):
        curve=bpy.data.curves.new(name,'CURVE'); curve.dimensions='3D'; curve.resolution_u=1; curve.bevel_depth=radius; curve.bevel_resolution=res
        spline=curve.splines.new('POLY'); spline.points.add(len(points)-1)
        for index,(v,co) in enumerate(zip(spline.points,points)):
            v.co=(*co,1)
            if name in ['BrownCurl','BroadBlondeWave','SweptCrownWave','SweptShortHair','WavyHighPonytail']:
                v.radius=.12+.88*math.sin(math.pi*index/(len(points)-1))**.35
        obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj)
        bpy.ops.object.select_all(action='DESELECT'); obj.select_set(True); bpy.context.view_layer.objects.active=obj
        bpy.ops.object.convert(target='MESH'); obj=bpy.context.object; obj.data.materials.append(mat); bind(obj,bone)
        return obj
    def cuff(side):
        b=rig.data.bones['lowerarm_'+side]; axis=(b.tail_local-b.head_local).normalized(); center=b.head_local+axis*.075
        u=axis.cross(Vector((0,1,0))).normalized(); v=axis.cross(u).normalized()
        for j in range(3):
            c=center+axis*(j*.015)
            tube('RolledLinenCuff_'+side,[c+(u*math.cos(a)+v*math.sin(a))*.053*ratio for a in [i*math.tau/32 for i in range(33)]],.009,linen,'lowerarm_'+side)
    cuff('l'); cuff('r')
    # Fitted open-neck torso. Chest / waist / shoulder dimensions differ by sex.
    segments=48; rings=20; verts=[]; faces=[]
    cloth_surface=BVHTree.FromPolygons([v.co for v in shirt.data.vertices],[list(p.vertices) for p in shirt.data.polygons])
    for j in range(rings):
        t=j/(rings-1)
        for i in range(segments):
            a=i*math.tau/segments;c=abs(math.cos(a));front=math.sin(a)<0
            # A continuous upper boundary gives a true V neck and low armholes
            # without deleting grid cells into visible staircase edges.
            if c<.62:drop=(.26-.20*c/.62) if front else (.09-.03*c/.62)
            else:drop=.06+(c-.62)/.38*.17
            top=neck-drop*ratio;z=hip-.075*ratio+t*(top-hip+.075*ratio)
            physical_t=max(0,min(1,(z-hip+.08*ratio)/(h+.09*ratio)))
            anchors=[(0,waist_rx),(.28,waist_rx*.84),(.72,.18 if female else .21),(1,.185 if female else .205)]
            for (ta,ra),(tb,rb) in zip(anchors,anchors[1:]):
                if ta<=physical_t<=tb:rx=ra+(rb-ra)*(physical_t-ta)/(tb-ta);break
            ry=(.133+.009*math.sin(physical_t*math.pi))*ratio
            direction=Vector((math.cos(a),math.sin(a),0));point,normal,index,distance=cloth_surface.ray_cast(Vector((0,0,z)),direction,.7)
            if point:position=point+direction*.012
            else:position=Vector((math.cos(a)*rx,math.sin(a)*ry-.006,z))
            verts.append(position)
    for j in range(rings-1):
        for i in range(segments):
            faces.append((j*segments+i,j*segments+(i+1)%segments,(j+1)*segments+(i+1)%segments,(j+1)*segments+i))
    bpy.data.objects.remove(fitted_vest,do_unlink=True)
    fitted_vest=mesh('FittedLeatherBodice',verts,faces,leather,solid=.006)
    for v in fitted_vest.data.vertices:
        for g in list(v.groups):fitted_vest.vertex_groups[g.group].remove([v.index])
        t=max(0,min(1,(v.co.z-hip)/h));index=min(2,int(t*3));fraction=t*3-index
        chain=['pelvis','spine_01','spine_02','spine_03']
        fitted_vest.vertex_groups[chain[index]].add([v.index],1-fraction,'REPLACE')
        fitted_vest.vertex_groups[chain[index+1]].add([v.index],fraction,'REPLACE')
    # Continuous broad shoulder straps join front and back around clean
    # armholes; they are authored surfaces rather than a cut shirt boundary.
    for side in [-1,1]:
        vv=[];ff=[];rows=18;cols=5
        top_ring=verts[-segments:]
        front_peak=max((p for p in top_ring if p.y<0 and p.x*side>0),key=lambda p:p.z)
        back_peak=max((p for p in top_ring if p.y>0 and p.x*side>0),key=lambda p:p.z)
        for j in range(rows):
            t=j/(rows-1);center=front_peak.lerp(back_peak,t)
            for i in range(cols):
                x=center.x+side*(.045 if female else .055)*math.sin(t*math.pi)+(i/(cols-1)-.5)*.052
                vv.append((x,center.y,center.z+.035*ratio*math.sin(t*math.pi)))
        for j in range(rows-1):
            for i in range(cols-1):ff.append((j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i))
        mesh('TailoredShoulderStrap',vv,ff,leather,'spine_03',.005)
    tube('ContinuousVestNeckline',verts[-segments:]+[verts[-segments]],.0035,leather,'spine_03')
    if identity in ['lorn','evelyn','captain']:
        armor=image_material('armor',tuple(c*.65+.065 for c in profile['coat']),.44,.70,kind='steel')
        vv=[];ff=[];rows=15;cols=19
        for j in range(rows):
            t=j/(rows-1);z=hip+.11*ratio+t*(h-.22*ratio)
            for i in range(cols):
                u=i/(cols-1);x=(u-.5)*.36*ratio
                y=-.155*ratio+.035*ratio*(abs(u-.5)*2)**2
                vv.append((x,y,z))
        for j in range(rows-1):
            for i in range(cols-1):ff.append((j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i))
        mesh('FittedSteelCuirass',vv,ff,armor,solid=.009)
        tube('CuirassGoldLowerRim',vv[:cols],.003,brass)
    # Open long vest/coattails are separate panels, with leg-following weights.
    length=profile['length']*ratio
    if length>.1:
        vv=[];ff=[];cols=64;rows=22
        for j in range(rows):
            t=j/(rows-1);z=hip-.045-t*length
            for i in range(cols):
                a=i*math.tau/cols
                rx=waist_rx*(1.015+t*.24);ry=(.20 if math.sin(a)<0 else .13)*ratio*(1+t*.10)
                vv.append((math.cos(a)*rx,math.sin(a)*ry+.007*math.sin(a*6)*t,z))
        for j in range(rows-1):
            for i in range(cols):
                a=(i+.5)*math.tau/cols
                if math.sin(a)<-.82 and abs(math.cos(a))<.48:continue
                ff.append((j*cols+i,j*cols+(i+1)%cols,(j+1)*cols+(i+1)%cols,(j+1)*cols+i))
        mesh('ContinuousLongVestPanels',vv,ff,leather,solid=.006)
        tube('LongVestBackHem',[p for i,p in enumerate(vv[-cols:]) if math.sin(i*math.tau/cols)>-.82],.0016,brass,'pelvis')
    # Waist and diagonally crossing baldric, stitched seams, engraved scrolls.
    def front_y(x,z):
        nearby=sorted((v.co for v in fitted_vest.data.vertices if v.co.y<0),key=lambda p:(p.x-x)**2+(p.z-z)**2)[:8]
        return min(p.y for p in nearby)-.010
    vv=[];ff=[]
    for z in [hip-.044,hip-.010]:
        for i in range(64):
            a=i*math.tau/64;vv.append((math.cos(a)*(waist_rx+.004),math.sin(a)*.152*ratio,z))
    for i in range(64):ff.append((i,(i+1)%64,(i+1)%64+64,i+64))
    mesh('FittedFlatWaistBelt',vv,ff,dark,'pelvis',.004)
    box('BeltBuckle',(.025,-.164*ratio,hip-.027),(.052,.010,.039),brass)
    for side in [-1,1]:
        for xoffset in [.073,.135]:
            points=[]
            end_z=min((p for p in verts[-segments:] if p.y<0),key=lambda p:abs(p.x-side*xoffset*ratio)).z-.015
            for k in range(24):
                z=hip-.065*ratio+k/23*(end_z-hip+.065*ratio); x=side*xoffset*ratio
                points.append((x,front_y(x,z)-.004,z))
            tube('TailoringSeam',points,.0017,brass)
        for j in range(8):
            z=hip+.035+j*h*.095; x=side*.133*ratio
            points=[(x+side*.012*math.sin(t),front_y(x,z)-.006,z+.018*math.cos(t)) for t in [k*math.tau/24 for k in range(25)]]
            tube('EmbossedLeatherScroll',points,.0009,brass)
    for j in range(6):
        z=hip+.02+j/5*(h-.30*ratio);box('VestClasp',(0,front_y(0,z)-.01,z),(.012,.012,.017),brass,'spine_02',.003)
    points=[]
    for i in range(29):
        x=-.17*ratio+.34*ratio*i/28;z=neck-.045-i/28*(h-.07);points.append((x,front_y(x,z)-.018,z))
    vv=[];ff=[]
    for i,p in enumerate(points):
        vv.extend([(p[0]-.013,p[1]-.004,p[2]-.008),(p[0]+.013,p[1]-.004,p[2]+.008)])
        if i:ff.append((2*i-2,2*i-1,2*i+1,2*i))
    if identity not in ['mira','evelyn']:mesh('FlatDiagonalSwordBaldric',vv,ff,dark,'spine_02',.003)
    for side in [-1,1]:
        box('ToolPouch',(side*.20*ratio,.015,hip-.11),(.10,.065,.145),leather)
        box('ToolPouchFlap',(side*.20*ratio,-.027,hip-.07),(.105,.018,.053),dark)
        box('PouchBuckle',(side*.20*ratio,-.04,hip-.077),(.018,.008,.02),brass)
    if profile.get('cape'):
        cape=image_material('mantle',profile['cape'],.95,kind='cloth')
        if identity=='raphael':
            # Short angled drape with shoulder opening, free edge below collar.
            for back in [False,True]:
                vv=[];ff=[]; cols=20; rows=15
                for j in range(rows):
                    t=j/(rows-1)
                    for i in range(cols):
                        u=i/(cols-1)
                        x=((- .03-.13*t+u*(.19+.25*t)) if back else (-.03+u*(.19+.12*t)))*ratio
                        z=neck+.025*ratio-t*.24*ratio-.075*u*ratio-.012*math.sin(u*math.pi)
                        # A shallow hanging catenary and broad cloth folds keep
                        # the drape from reading as a rigid rectangular board.
                        y=((.14+.04*math.sin(t*math.pi/2)-u*.035) if back else (-.16-.035*math.sin(t*math.pi/2)+u*.055))*ratio
                        y+=(1 if back else -1)*(.017*math.sin(u*math.pi*5)*math.sin(t*math.pi*.8)+.015*math.sin(u*math.pi)*math.sin(t*math.pi))
                        vv.append((x,y,z))
                for j in range(rows-1):
                    for i in range(cols-1): ff.append((j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i))
                mesh('ShortAsymmetricTealDrape',vv,ff,cape,'spine_03',.006)
                tube('MantleStitchedHem',vv[-cols:],.002,brass,'spine_03')
            tube('TealMantleCollar',[(.115*math.cos(a)*ratio,.09*math.sin(a)*ratio,neck-.012) for a in [i*math.tau/48 for i in range(49)]],.025,cape,'spine_03')
            for fold in range(3):
                pts=[]
                for i in range(32):
                    t=i/31;pts.append(((-.035+.27*t)*ratio,(-.165+.095*t-.010*fold)*ratio,neck-.02-.085*t-.012*fold+.010*math.sin(t*math.pi)))
                tube('MantleFoldedEdge',pts,(.010-fold*.002)*ratio,cape,'spine_03')
        else:
            vv=[];ff=[];cols=25;rows=22
            for j in range(rows):
                t=j/(rows-1)
                for i in range(cols):
                    u=i/(cols-1); x=(u-.5)*(.48+.15*t)*ratio
                    z=neck-.015-t*(.95 if identity=='nightqi' else .78)*ratio-.06*abs(u-.5)
                    y=(.13+.09*t+.024*math.cos(u*math.pi*10)*t)*ratio
                    vv.append((x,y,z))
            for j in range(rows-1):
                for i in range(cols-1): ff.append((j*cols+i,j*cols+i+1,(j+1)*cols+i+1,(j+1)*cols+i))
            mesh('TravelCloak',vv,ff,cape,'spine_02',.007)
            tube('CloakHem',vv[-cols:],.003,brass,'spine_02')
            tube('CloakCollar',[(.11*math.cos(a)*ratio,.09*math.sin(a)*ratio,neck-.012) for a in [i*math.tau/48 for i in range(49)]],.036,cape,'spine_03')
    # Star brooch has real five-point relief geometry.
    center=Vector((.045*ratio,-.17*ratio,neck-.047))
    vv=[center+Vector((math.sin(i*math.pi/5)*(.026 if i%2==0 else .011),-.004,math.cos(i*math.pi/5)*(.026 if i%2==0 else .011))) for i in range(10)]
    if identity=='raphael':mesh('StarBrooch',vv,[tuple(range(10))],brass,'spine_03',.007)
    if profile['armor']!='none':
        for side in (['r'] if profile['armor']=='single' else ['r','l']):
            shoulder=rig.data.bones['upperarm_'+side].head_local
            vv=[];ff=[];steps=32;bands=10
            for j in range(bands):
                phi=.05+j/(bands-1)*1.53
                for i in range(steps):
                    a=i*math.tau/steps
                    vv.append((shoulder.x+.115*ratio*math.sin(phi)*math.cos(a),shoulder.y+.098*ratio*math.sin(phi)*math.sin(a),shoulder.z+.063*ratio*math.cos(phi)+.02))
            for j in range(bands-1):
                for i in range(steps):ff.append((j*steps+i,j*steps+(i+1)%steps,(j+1)*steps+(i+1)%steps,(j+1)*steps+i))
            mesh('SteelPauldron_'+side,vv,ff,steel,'upperarm_'+side,.008)
            tube('PauldronBrassRim_'+side,vv[-steps:]+[vv[-steps]],.0038,brass,'upperarm_'+side)
    # Volumetric hair, with broad waves for the women and looping curls for hero.
    hc=Vector((head.x,head.y+.008,head.z+.070*ratio))
    female_hair=profile['hair'] in ['bob','ponytail','halfup']
    def hair_point(a,t,wave=True):
        front=max(0,-math.sin(a))**.7
        limit=(2.62-1.42*front) if female_hair else (2.08-.70*front)
        phi=.025+t*limit
        radial=math.sin(min(phi,math.pi/2))
        bump=(.012*math.sin(phi*7+a*3)) if wave and female_hair else 0
        rx=(.111 if female_hair else .089)*ratio+bump
        ry=(.115 if female_hair else .098)*ratio+bump
        return hc+Vector((rx*radial*math.cos(a),ry*radial*math.sin(a),.120*ratio*math.cos(phi)))
    vv=[];ff=[];cols=64;rows=22
    for j in range(rows):
        for i in range(cols):vv.append(hair_point(i*math.tau/cols,j/(rows-1)))
    for j in range(rows-1):
        for i in range(cols):ff.append((j*cols+i,j*cols+(i+1)%cols,(j+1)*cols+(i+1)%cols,(j+1)*cols+i))
    mesh('ShapedHairScalp',vv,ff,hairmat,'head')
    if profile['hair']=='curly':
        for i in range(115):
            a=i*2.399963+random.uniform(-.13,.13); u=(i+.5)/115; zz=1-1.62*u
            radial=math.sqrt(max(.01,1-zz*zz)); n=Vector((math.cos(a)*radial,math.sin(a)*radial,zz))
            c=hc+Vector((n.x*.105*ratio,n.y*.104*ratio,n.z*.125*ratio))
            # Keep curls off the eyes while covering temples and nape.
            if n.y<-.55 and zz<.12: continue
            tangent=n.cross(Vector((0,0,1)))
            if tangent.length<.1:tangent=Vector((1,0,0))
            tangent.normalize(); bitangent=n.cross(tangent).normalized(); radius=random.uniform(.016,.028)*ratio
            turn=random.uniform(1.05,1.8)*math.pi;phase=random.uniform(0,math.tau)
            pts=[]
            for k in range(22):
                u=k/21;t=phase+u*turn
                pts.append(c+(tangent*math.cos(t)+bitangent*math.sin(t))*radius*(1-.25*u)+n*(.012*math.sin(u*math.pi)))
            tube('BrownCurl',pts,random.uniform(.008,.011)*ratio,hairmat,'head',1)
    elif profile['hair'] in ['bob','ponytail','halfup']:
        for i in range(30):
            a=i*math.tau/30;pts=[]
            for k in range(42):
                t=k/41;point=hair_point(a+.07*math.sin(t*math.pi*3+i*.2),t)
                point+=Vector((math.cos(a),math.sin(a),.1))*.006*ratio
                if profile['hair']=='halfup' and math.sin(a)>-.55:
                    point.z-=max(0,t-.45)*.48*ratio
                    point.x+=.018*math.sin(t*math.pi*5+i*.3)*max(0,t-.3)
                pts.append(point)
            tube('BroadBlondeWave',pts,.016*ratio,hairmat,'head',1)
        if profile['hair']=='ponytail':
            for i in range(24):
                a=i*math.tau/24; pts=[]
                for k in range(40):
                    t=k/39; pts.append((.035*math.cos(a)+.027*math.sin(t*math.pi*5+a),head.y+.12+.07*t+.018*math.sin(a),head.z+.12-t*.48*ratio))
                tube('WavyHighPonytail',pts,.011*ratio,hairmat,'head',2)
            tube('PonytailTie',[(.041*math.cos(a),head.y+.12+.025*math.sin(a),head.z+.08) for a in [i*math.tau/32 for i in range(33)]],.006,dark,'head')
    else:
        for i in range(70):
            a=i*2.399963; zz=.98-i/70*1.22; radial=math.sqrt(max(.01,1-zz*zz))
            c=hc+Vector((math.cos(a)*radial*.089*ratio,math.sin(a)*radial*.095*ratio,zz*.112*ratio))
            if math.sin(a)<-.5 and zz<.25:continue
            pts=[c+Vector((.018*math.sin(t*math.pi),-.027*t,.013*math.sin(t*math.pi))) for t in [k/10 for k in range(11)]]
            tube('SweptShortHair',pts,.011*ratio,hairmat,'head',1)
    # Hand-mounted props are separate named skinned nodes (toggle renderer).
    def sword(side='r',short=False):
        hand=rig.data.bones['hand_'+side].head_local; top=hand+Vector((0,-.015,.055))
        length=.36 if short else .66
        verts=[top+Vector((x,y,z)) for x,y,z in [(-.022,0,0),(.022,0,0),(.015,-.006,length*.83),(0,0,length),(-.015,-.006,length*.83),(0,.007,length*.4)]]
        mesh('EquippedDagger_'+side if short else 'EquippedSword',verts,[(0,1,2,3,4),(0,5,1),(1,5,2),(2,5,3),(3,5,4),(4,5,0)],steel,'hand_'+side)
        tube('SwordGrip_'+side,[hand+Vector((0,0,-.06)),top],.013,dark,'hand_'+side)
        box('SwordCrossguard_'+side,top,(.12,.022,.018),brass,'hand_'+side)
    weapon=profile['weapon']
    if weapon in ['sword','daggers']: sword('r',weapon=='daggers')
    if weapon=='daggers':sword('l',True)
    if weapon in ['shield','hammer']:
        hand=rig.data.bones['hand_l'].head_local
        c=hand+Vector((.04,-.095,.12)); vv=[]
        for i in range(32):
            a=i*math.tau/32; vv.append(c+Vector((math.sin(a)*.27,-.015,math.cos(a)*.48)))
        mesh('EquippedLargeShield',vv,[tuple(range(32))],wood,'hand_l',.032)
        tube('ShieldSteelRim',vv+[vv[0]],.019,steel,'hand_l')
        for z in [-.22,0,.22]:box('ShieldIronBand',c+Vector((0,-.038,z)),(.46,.02,.028),steel,'hand_l')
        if weapon=='hammer':
            hand=rig.data.bones['hand_r'].head_local
            tube('HammerHandle',[hand+Vector((0,0,-.18)),hand+Vector((0,0,.5))],.02,dark,'hand_r')
            box('EquippedWarhammer',hand+Vector((0,0,.48)),(.22,.09,.12),steel,'hand_r')
        else:sword()
    if weapon=='bow':
        hand=rig.data.bones['hand_l'].head_local; pts=[hand+Vector((0,-.14*math.sin(t*math.pi),-.67+1.34*t)) for t in [i/48 for i in range(49)]]
        tube('EquippedLongbow',pts,.013,wood,'hand_l'); tube('BowString',[pts[0],hand,pts[-1]],.0015,linen,'hand_l')
        box('BackQuiver',(.16,.19,hip+.19),(.08,.09,.4),dark,'spine_02')
        for i in range(7):tube('QuiverArrow',[(.13+(i%3)*.018,.2,hip+.25),(.13+(i%3)*.018,.2,hip+.7)],.0035,wood,'spine_02')
    if weapon=='maps':
        box('MapCase',(.2,-.03,hip-.13),(.075,.065,.28),dark)
        for i in range(3):tube('RolledMap',[(.19+i*.019,-.07,hip-.09),(.19+i*.019,-.07,hip+.10)],.015,white,'pelvis')
        box('FoldedMap',(-.19,-.08,hip-.03),(.11,.025,.075),white)
    if weapon=='lantern':
        hand=rig.data.bones['hand_r'].head_local; c=hand+Vector((0,0,-.22))
        glass=image_material('lanternGlow',(.90,.43,.075),.35,kind='steel')
        box('LanternLight',c,(.10,.10,.13),glass,'hand_r')
        for dx in [-.065,.065]:
            for dy in [-.065,.065]:tube('LanternFrame',[(c.x+dx,c.y+dy,c.z-.09),(c.x+dx,c.y+dy,c.z+.09)],.006,brass,'hand_r')
        box('LanternCap',c+Vector((0,0,.10)),(.15,.15,.025),brass,'hand_r')
        box('LanternBase',c+Vector((0,0,-.10)),(.15,.15,.025),brass,'hand_r')
        tube('LanternHandle',[hand,hand+Vector((0,0,-.10)),c+Vector((0,0,.11))],.006,brass,'hand_r')
        for side in [-1,1]:
            box('WhiteRepairPatch',(side*.13,-.16,hip-.19),(.09,.012,.12),white,'pelvis')

    # Limit actual exported vertex influences, normalize and remove empty groups.
    for obj in rig.children_recursive:
        if obj.type!='MESH':continue
        for v in obj.data.vertices:
            influences=sorted([(g.group,g.weight) for g in v.groups if obj.vertex_groups[g.group].name in names and g.weight>1e-6],key=lambda p:-p[1])
            for index,weight in influences[4:]:obj.vertex_groups[index].remove([v.index])
            total=sum(w for _,w in influences[:4])
            for index,weight in influences[:4]:obj.vertex_groups[index].add([v.index],weight/total,'REPLACE')
    # Animation authoring uses explicit two-bone hand targets on the real rig.
    rig.data.pose_position='POSE'; scene=bpy.context.scene; scene.render.fps=30
    def orient(name,direction):
        pb=rig.pose.bones[name]; rest=rig.data.bones[name]
        desired=(rest.tail_local-rest.head_local).normalized().rotation_difference(Vector(direction).normalized())@rest.matrix_local.to_quaternion()
        base=rest.matrix_local.to_quaternion()
        if pb.parent:base=pb.parent.matrix.to_quaternion()@pb.parent.bone.matrix_local.to_quaternion().inverted()@base
        pb.rotation_quaternion=base.inverted()@desired; bpy.context.view_layer.update()
    def arm(side,target,bend=(0,-1,0)):
        a=rig.pose.bones['upperarm_'+side]; b=rig.pose.bones['lowerarm_'+side]
        start=a.head.copy(); target=Vector(target); delta=target-start; distance=min(delta.length,(a.length+b.length)*.985)
        direction=delta.normalized(); end=start+direction*distance
        mid=(a.length*a.length-b.length*b.length+distance*distance)/(2*distance)
        bend=Vector(bend); bend=(bend-direction*bend.dot(direction)).normalized()
        elbow=start+direction*mid+bend*math.sqrt(max(.0001,a.length*a.length-mid*mid))
        orient(a.name,elbow-start); orient(b.name,end-elbow)
    def turn(name,angle,axis=(1,0,0)):
        rest=rig.data.bones[name].matrix_local.to_quaternion(); return rest.inverted()@Quaternion(axis,angle)@rest
    def pose(kind,t):
        for pb in rig.pose.bones:pb.rotation_mode='QUATERNION';pb.rotation_quaternion=Quaternion();pb.location=(0,0,0);pb.scale=(1,1,1)
        phase=t*math.tau; attack=math.sin(t*math.pi)**2
        for side,sign in [('l',1),('r',-1)]:
            for finger in ['index','middle','ring','pinky']:
                for joint in [1,2,3]:
                    name=f'{finger}_{joint:02d}_{side}';rig.pose.bones[name].rotation_quaternion=turn(name,sign*(.8 if side=='r' else .35),(0,1,0))
        bpy.context.view_layer.update()
        targets={'l':Vector((.225*ratio,-.055,hip-.19*ratio)),'r':Vector((-.225*ratio,-.055,hip-.19*ratio))}
        if kind=='idle':rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',math.sin(phase)*.012)
        elif kind=='run':
            for side,offset,sign in [('l',0,1),('r',math.pi,-1)]:
                s=math.sin(phase+offset)
                rig.pose.bones['thigh_'+side].rotation_quaternion=turn('thigh_'+side,s*.70)
                rig.pose.bones['calf_'+side].rotation_quaternion=turn('calf_'+side,-max(0,s)*1.15)
                rig.pose.bones['foot_'+side].rotation_quaternion=turn('foot_'+side,-s*.23)
                targets[side]=Vector((sign*.24*ratio,-.08-s*.19,hip-.12*ratio+max(0,-s)*.10))
            rig.pose.bones['Root'].location.z=.022*(1-math.cos(phase*2));rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',.10)
        elif kind=='attack_sword':
            targets['r']=Vector(((-.23+.38*attack)*ratio,-.11-.39*attack,hip+.01+.48*attack))
            rig.pose.bones['spine_03'].rotation_quaternion=turn('spine_03',-.25*math.sin(phase),(0,0,1))
            rig.pose.bones['thigh_l'].rotation_quaternion=turn('thigh_l',.12*attack)
        elif kind=='attack_bow':
            draw=math.sin(min(t/.7,1)*math.pi/2) if t<.7 else max(0,1-(t-.7)/.3)
            targets['l']=Vector((.32*ratio,-.43*ratio,neck-.15*ratio));targets['r']=Vector((-.08-.18*draw,-.23+.18*draw,neck-.10*ratio))
            rig.pose.bones['spine_03'].rotation_quaternion=turn('spine_03',.20*draw,(0,0,1))
        elif kind=='attack_staff':
            targets['r']=Vector((-.20,-.10-.34*attack,hip+.12+.23*attack));targets['l']=Vector((.15,-.15-.2*attack,hip+.26))
            rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',.12*math.sin(phase))
        elif kind=='spell':
            for side,sign in [('l',1),('r',-1)]:targets[side]=Vector((sign*(.22+.15*attack)*ratio,-.08-.24*attack,hip-.08+attack*.65*ratio))
            rig.pose.bones['head'].rotation_quaternion=turn('head',-.1*attack)
        elif kind=='dodge':
            rig.pose.bones['Root'].location=Vector((.18*math.sin(phase),.02,-.19*attack))
            rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',-.37*attack,(0,1,0))
            for side in ['l','r']:
                rig.pose.bones['thigh_'+side].rotation_quaternion=turn('thigh_'+side,.5*attack);rig.pose.bones['calf_'+side].rotation_quaternion=turn('calf_'+side,-.8*attack)
            targets['r'].z+=.24*attack;targets['l'].z+=.2*attack
        elif kind=='hit':
            rig.pose.bones['spine_02'].rotation_quaternion=turn('spine_02',-.27*attack);rig.pose.bones['neck_01'].rotation_quaternion=turn('neck_01',-.18*attack)
            targets['r'].y-=.15*attack;targets['l'].y-=.12*attack
        elif kind=='death':
            fall=min(1,t/.72);ease=fall*fall*(3-2*fall)
            rig.pose.bones['Root'].rotation_quaternion=turn('Root',1.51*ease)
            rig.pose.bones['Root'].location.z=.15*ease
            rig.pose.bones['thigh_l'].rotation_quaternion=turn('thigh_l',.20*ease)
            rig.pose.bones['calf_r'].rotation_quaternion=turn('calf_r',-.35*ease)
            # Keep arms aligned with the falling body via fixed local rotations.
        elif kind=='interact':
            targets['r']=Vector((-.15,-.10-.31*attack,hip-.08+.32*attack));targets['l']=Vector((.22,-.10-.10*attack,hip-.14+.10*attack))
            rig.pose.bones['head'].rotation_quaternion=turn('head',.16*attack)
        bpy.context.view_layer.update()
        if kind=='death':
            # Explicit local rest-relative hang avoids a world-space hand target
            # counter-rotating the fall. The final 28% of this clip is held.
            root=rig.pose.bones['Root']; rotation=root.rotation_quaternion.copy(); location=root.location.copy()
            root.rotation_quaternion=Quaternion();root.location=(0,0,0);bpy.context.view_layer.update()
            arm('l',targets['l']);arm('r',targets['r'])
            root.rotation_quaternion=rotation;root.location=location
        else:
            arm('l',targets['l']);arm('r',targets['r'])
        bpy.context.view_layer.update()
    # Death arms use rest local hanging transforms copied from standing stance.
    for kind,duration in CLIPS.items():
        action=bpy.data.actions.new(kind);action.use_fake_user=True;rig.animation_data_create();rig.animation_data.action=action
        count=max(18,round(duration*30))
        for i in range(count+1):
            pose(kind,i/count);frame=1+duration*30*i/count
            for pb in rig.pose.bones:pb.keyframe_insert('rotation_quaternion',frame=frame);pb.keyframe_insert('location',frame=frame)
        # Keep sampled keys linear; overshoot can put extremities under the floor.
        for fc in action.fcurves:
            for key in fc.keyframe_points:key.interpolation='LINEAR'
    rig.animation_data.action=bpy.data.actions['idle'];scene.frame_set(1);bpy.context.view_layer.update()
    # Fit broad straps over the actual posed shirt shoulder, rather than
    # estimating an arch that can sink through the sleeve cap or float above it.
    evaluated_shirt=shirt.evaluated_get(bpy.context.evaluated_depsgraph_get());shirt_mesh=evaluated_shirt.to_mesh()
    shoulder_surface=BVHTree.FromPolygons([v.co for v in shirt_mesh.vertices],[list(p.vertices) for p in shirt_mesh.polygons])
    for obj in [fitted_vest]+[o for o in rig.children_recursive if o.name.startswith('ContinuousVestNeckline')]:
        for vertex in obj.data.vertices:
            direction=Vector((vertex.co.x,vertex.co.y,0)).normalized()
            point,normal,index,distance=shoulder_surface.ray_cast(Vector((0,0,vertex.co.z)),direction,.65)
            if point:vertex.co=point+direction*(.026 if obj==fitted_vest else .029)
    for obj in rig.children_recursive:
        if obj.type=='MESH' and obj.name.startswith('TailoredShoulderStrap'):
            side=1 if sum(v.co.x for v in obj.data.vertices)>0 else -1
            ring=[v.co.copy() for v in fitted_vest.data.vertices[-segments:]]
            front_peak=max((p for p in ring if p.y<0 and p.x*side>0),key=lambda p:p.z)
            back_peak=max((p for p in ring if p.y>0 and p.x*side>0),key=lambda p:p.z)
            for vertex in obj.data.vertices:
                t=(vertex.index//5)/17;column=vertex.index%5;center=front_peak.lerp(back_peak,t)
                vertex.co=Vector((center.x+side*(.045 if female else .055)*math.sin(t*math.pi)+(column/4-.5)*.052,center.y,center.z+.035*ratio*math.sin(t*math.pi)))
                point,normal,index,distance=shoulder_surface.ray_cast(Vector((vertex.co.x,vertex.co.y,neck+.35)),Vector((0,0,-1)),.65)
                if point and point.z>neck-.24:
                    blend=math.sin(t*math.pi)**.4
                    vertex.co.z=vertex.co.z*(1-blend)+(point.z+.018)*blend
                if abs(vertex.co.x)<.105:vertex.co.x=.105 if vertex.co.x>0 else -.105
    evaluated_shirt.to_mesh_clear()
    # Author prop orientation in the relaxed grip, then transform it back to
    # bind space. This avoids the A-pose hand basis tilting a bow or sword.
    for obj in rig.children_recursive:
        if obj.type!='MESH':continue
        used={obj.vertex_groups[g.group].name for v in obj.data.vertices for g in v.groups if g.weight>.001}
        if len(used)==1 and next(iter(used)) in ['hand_r','hand_l']:
            name=next(iter(used));rest=rig.data.bones[name];pb=rig.pose.bones[name]
            inverse=(pb.matrix@rest.matrix_local.inverted()).inverted()
            for v in obj.data.vertices:v.co=inverse@(pb.head+(v.co-rest.head_local))
    def bounds():
        points=[];deps=bpy.context.evaluated_depsgraph_get()
        for obj in rig.children_recursive:
            if obj.type=='MESH':
                ev=obj.evaluated_get(deps);data=ev.to_mesh()
                points.extend(obj.matrix_world@v.co for v in data.vertices);ev.to_mesh_clear()
        return [min(p[i] for p in points) for i in range(3)],[max(p[i] for p in points) for i in range(3)]
    lo,hi=bounds();scale=profile['height']/(hi[2]-lo[2]);rig.scale*=scale
    rig.scale.x*=profile['width'];bpy.context.view_layer.update();lo,hi=bounds();rig.location.z-=lo[2]
    bpy.context.view_layer.update()
    # Apply authored non-armature modifiers in bind pose. Keep source masks and
    # shape keys editable; Blender's FBX exporter evaluates those source meshes.
    rig.data.pose_position='REST';bpy.context.view_layer.update()
    for obj in rig.children_recursive:
        if obj.type!='MESH':continue
        bpy.context.view_layer.objects.active=obj
        for modifier in list(obj.modifiers):
            if modifier.type!='ARMATURE' and not obj.data.shape_keys:bpy.ops.object.modifier_apply(modifier=modifier.name)
    rig.data.pose_position='POSE';bpy.context.view_layer.update()
    # Consolidate skinned surfaces by material to avoid a renderer per curl or
    # stitch. Equipment stays as two clearly named hand-mounted renderer nodes.
    def join_objects(objects,name):
        if len(objects)<2:
            if objects:objects[0].name=name
            return
        bpy.ops.object.select_all(action='DESELECT')
        for o in objects:o.select_set(True)
        bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join();objects[0].name=name
    for side in ['r','l']:
        objects=[]
        for obj in rig.children_recursive:
            if obj.type!='MESH':continue
            used={obj.vertex_groups[g.group].name for v in obj.data.vertices for g in v.groups if g.weight>.001}
            if used=={'hand_'+side}:objects.append(obj)
        join_objects(objects,'Equipped_'+profile['weapon']+'_'+side)
    by_material={}
    for obj in rig.children_recursive:
        if obj.type=='MESH' and not obj.name.startswith('Equipped_') and not obj.data.shape_keys and len(obj.data.materials)==1:
            by_material.setdefault(obj.data.materials[0].name,[]).append(obj)
    for material,objects in by_material.items():join_objects(objects,material+'_surface')
    bpy.ops.object.select_all(action='DESELECT');rig.select_set(True)
    for obj in rig.children_recursive:obj.select_set(True)
    bpy.context.view_layer.objects.active=rig
    fbx=folder/f'{identity}.fbx'
    bpy.ops.export_scene.fbx(filepath=str(fbx),use_selection=True,object_types={'ARMATURE','MESH'},axis_forward='Z',axis_up='Y',global_scale=1,apply_unit_scale=True,apply_scale_options='FBX_SCALE_ALL',use_mesh_modifiers=True,mesh_smooth_type='FACE',add_leaf_bones=False,use_armature_deform_only=False,bake_anim=True,bake_anim_use_all_bones=True,bake_anim_use_nla_strips=False,bake_anim_use_all_actions=True,bake_anim_force_startend_keying=True,bake_anim_step=1,bake_anim_simplify_factor=0,path_mode='RELATIVE',embed_textures=False)
    meshes=[o for o in rig.children_recursive if o.type=='MESH'];triangles=sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in meshes)
    max_influences=max(sum(g.weight>1e-6 and o.vertex_groups[g.group].name in names for g in v.groups) for o in meshes for v in o.data.vertices)
    manifest={'id':identity,'resource':f'actors/{identity}/{identity}','fbx':fbx.name,'source':f'source-art/characters/cocos/{identity}.blend','axis':{'forward':'Z','up':'Y','meters':True},'clips':{k:{'name':k,'duration':v,'loop':k in ['idle','run'],'holdFinalPose':k=='death'} for k,v in CLIPS.items()},'bones':sorted(names),'textures':texture_paths,'materials':[{ 'name':m.name,'roughness':m.get('roughness',.8),'metallic':m.get('metallic',0)} for m in {m for o in meshes for m in o.data.materials}],'triangles':triangles,'maxInfluences':max_influences,'sockets':{'rightHand':'hand_r','leftHand':'hand_l'},'equippedNodes':[o.name for o in meshes if o.name.startswith('Equipped')],'profile':profile,'license':'MakeHuman system assets CC0; local authored wardrobe, volumetric hair, props and motions.'}
    (folder/'manifest.json').write_text(json.dumps(manifest,indent=2))
    scene.unit_settings.system='METRIC';scene.unit_settings.scale_length=1
    bpy.context.preferences.filepaths.save_version=0
    for material in {m for o in meshes for m in o.data.materials}:
        for node in material.node_tree.nodes:
            if node.type=='TEX_IMAGE' and node.image:
                absolute=Path(bpy.path.abspath(node.image.filepath));node.image.filepath='//'+os.path.relpath(absolute,SOURCE).replace('\\','/')
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/f'{identity}.blend'),relative_remap=False)
    print('[COCOS_CHARACTER]',identity,triangles,'triangles',len(names),'bones',len(CLIPS),'clips',flush=True)

selected=sys.argv[sys.argv.index('--character')+1] if '--character' in sys.argv else None
for identity in (selected.split(',') if selected else PROFILES):build(identity)
