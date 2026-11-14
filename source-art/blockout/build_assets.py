from pathlib import Path
import bpy, math, os, json
from mathutils import Vector
from math import radians
BASE=str(Path(__file__).resolve().parents[2] / 'assets/blockout')
for folder in ['models','props','sprites','previews']:
 (Path(BASE)/folder).mkdir(parents=True,exist_ok=True)
bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
M={}
def mat(name,c,metal=0,rough=.8):
 m=bpy.data.materials.new(name); m.diffuse_color=(*c,1); m.use_nodes=True; p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*c,1); p.inputs['Metallic'].default_value=metal; p.inputs['Roughness'].default_value=rough; M[name]=m; return m
for args in [('skin',(.55,.34,.22)),('skinlight',(.72,.49,.32)),('leather',(.19,.105,.065)),('leatherlight',(.32,.19,.10)),('teal',(.075,.25,.25)),('tealdark',(.04,.13,.15)),('rust',(.38,.14,.065)),('cloth',(.26,.23,.18)),('metal',(.27,.31,.31),.65,.55),('steel',(.48,.52,.50),.75,.38),('dark',(.055,.065,.065)),('hair',(.10,.065,.04)),('wood',(.32,.19,.08)),('woodlight',(.48,.30,.13)),('stone',(.40,.39,.34)),('red',(.45,.07,.035)),('orange',(.95,.26,.015)),('yellow',(1,.67,.07)),('ivory',(.85,.80,.65))]: mat(*args)
ROOT=None
def parent(obj,name,material):
 obj.name=name; obj.data.materials.append(M[material]); obj.parent=ROOT; return obj
def cube(name,loc,scale,material,bevel=.03,rot=None):
 bpy.ops.mesh.primitive_cube_add(size=1, location=loc); o=bpy.context.object; o.scale=scale; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
 if bevel:
  mod=o.modifiers.new('edge highlights','BEVEL'); mod.width=bevel; mod.segments=1
  o.modifiers.new('weighted corner normals','WEIGHTED_NORMAL')
 if rot:o.rotation_euler=rot
 return parent(o,name,material)
def ico(name,loc,scale,material,sub=1):
 bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub,radius=1,location=loc); o=bpy.context.object; o.scale=scale; return parent(o,name,material)
def cyl(name,loc,r,depth,material,verts=10,rot=None):
 bpy.ops.mesh.primitive_cylinder_add(vertices=verts,radius=r,depth=depth,location=loc); o=bpy.context.object
 if rot:o.rotation_euler=rot
 return parent(o,name,material)
def link(name,a,b,r1,r2,material,verts=8):
 d=Vector(b)-Vector(a); mid=(Vector(a)+Vector(b))/2
 bpy.ops.mesh.primitive_cone_add(vertices=verts,radius1=r1,radius2=r2,depth=d.length,location=mid); o=bpy.context.object; o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return parent(o,name,material)
def panel(name,verts,faces,material):
 mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.update();o=bpy.data.objects.new(name,mesh);bpy.context.collection.objects.link(o);parent(o,name,material);s=o.modifiers.new('cloth thickness','SOLIDIFY');s.thickness=.018;return o
def root(name):
 global ROOT
 ROOT=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(ROOT);ROOT['asset_id']=name;ROOT['units']='meters';return ROOT
def buckle(loc):cube('iron buckle',loc,(.09,.035,.075),'steel',.008)
def sword(x,y,z):
 link('leather wrapped grip',(x,y,z),(x,y,z+.20),.034,.034,'leather',8);cyl('pommel',(x,y,z-.025),.045,.06,'metal');cube('crossguard',(x,y,z+.21),(.28,.055,.045),'metal',.015)
 panel('tapered steel blade',[(x-.055,y,z+.23),(x+.055,y,z+.23),(x+.04,y,z+.73),(x,y,z+.88),(x-.04,y,z+.73),(x,y-.025,z+.23),(x,y-.02,z+.73)],[(0,5,6,4),(5,1,2,6),(4,6,3),(6,2,3)],'steel')
def shield(x,y,z,boss=False):
 if not boss:
  cyl('round shield iron rim',(x,y,z),.27,.09,'metal',14,(radians(90),0,0))
  cyl('round shield wooden face',(x,y-.055,z),.24,.025,'wood',14,(radians(90),0,0))
  cube('shield centre strap',(x,y-.08,z),(.045,.025,.45),'metal',.006)
  ico('shield boss',(x,y-.11,z),(.08,.045,.08),'steel',1)
  return
 w=.5;h=.72
 cube('shield timber core',(x,y,z),(w,.09,h),'wood',.035)
 for xx in [-w/2,w/2]:cube('shield side binding',(x+xx,y-.055,z),(.045,.04,h),'metal',.008)
 for zz in [-h/2,h/2]:cube('shield end binding',(x,y-.055,z+zz),(w,.04,.045),'metal',.008)
 cube('shield centre strap',(x,y-.06,z),(.055,.035,h),'metal',.009);ico('shield boss',(x,y-.10,z),(.09,.05,.09),'steel',1)
def character(asset,kind):
 r=root(asset); boss=kind==2; enemy=kind>0; cloth='rust' if enemy else 'teal';skin='skin' if boss else 'skinlight'; W=1.15 if boss else 1
 # adult five-head readable proportions, feet at 0
 for side in [-1,1]:
  x=side*.13*W
  link('trouser upper leg',(x,0,.51),(x,.015,.91),.105*W,.12*W,'cloth')
  link('shin leather boot',(x,-.005,.13),(x,0,.52),.075*W,.095*W,'leather')
  cube('boot toe',(x,-.085,.105),(.18*W,.30,.18),'leather',.045)
  cube('boot iron toe cap',(x,-.18,.11),(.185*W,.105,.11),'metal',.022)
  for zz in [.27,.44]:cube('boot fastening',(x,-.08,zz),(.16,.025,.035),'leatherlight',.006)
  ico('knee plate',(x,-.077,.54),(.10,.045,.115),'metal',1)
 link('coat torso',(0,0,.88),(0,0,1.34),.23*W,.28*W,'leather',8)
 # front tunic panels and split skirt
 for side in [-1,1]:
  cube('overlapping leather tasset',(side*.135,-.095,.84),(.23,.12,.25),'leatherlight',.025, (0,side*.13,side*.06))
  for z in [1.10,1.20,1.30]:cube('segmented breast plate',(side*.105*W,-.205,z),(.19*W,.055,.085),'metal',.015,(0,0,side*.04))
 cube('utility belt',(0,-.01,.98),(.49*W,.36,.075),'dark',.018);buckle((0,-.205,.98))
 cube('diagonal baldric',(0,-.24,1.23),(.065,.035,.40),'leatherlight',.008,(0,-.45,0))
 cube('belt pouch',(-.24*W,-.04,.92),(.13,.15,.17),'leather',.025);cube('pouch flap',(-.24*W,-.12,.97),(.14,.025,.08),'leatherlight',.01)
 if not enemy:
  cyl('oil flask glass body',(.27,-.06,.91),.055,.15,'dark',8);cyl('oil flask stopper',(.27,-.06,1.005),.025,.04,'wood',8);cube('flask label',(.27,-.115,.92),(.06,.012,.06),'ivory',.005)
 # cloth cloak pleats behind torso
 panel('short travel cloak', [(-.26,.09,1.39),(0,.18,1.42),(.26,.09,1.39),(-.32,.24,.90),(-.12,.30,.84),(.10,.29,.89),(.31,.25,.94)],[(0,1,4,3),(1,5,4),(1,2,6,5)],cloth)
 for side in [-1,1]:
  sx=side*.30*W; elbow=(side*.37*W,-.025,1.07);hand=(side*.39*W,-.14,.88 if side==1 else 1.00)
  link('upper sleeve',(sx,0,1.32),elbow,.095,.105,cloth)
  link('forearm leather bracer',elbow,hand,.085,.07,'leather')
  ico('bare hand',hand,(.073,.07,.09),skin,1)
  ico('shoulder guard',(sx,-.005,1.34),(.145 if boss else .12,.145,.10),'steel' if (boss and side<0) else 'metal',1)
  cube('bracer band',(side*.38*W,-.09,1.06),(.14,.10,.045),'metal',.008)
 link('neck',(0,0,1.35),(0,0,1.49),.072,.072,skin)
 ico('head',(0,-.005,1.62),(.145,.12,.185),skin,2)
 # faceted cheeks, strong nose, visible eyes and brows
 ico('nose',(0,-.126,1.615),(.036,.063,.049),skin,1)
 for side in [-1,1]:
  cube('eye white',(side*.057,-.116,1.66),(.042,.014,.018),'ivory',.004)
  cube('eye pupil',(side*.055,-.126,1.661),(.014,.009,.016),'dark',.002)
  cube('brow',(side*.057,-.124,1.69),(.061,.018,.014),'hair',.004,(0,side*.10,0))
 cube('mouth',(0,-.118,1.555),(.058,.014,.009),'leather',.003)
 if kind==0:
  ico('swept dark hair',(0,.015,1.75),(.148,.12,.095),'hair',2)
  for x,z in [(-.11,1.71),(-.07,1.76),(.03,1.78)]:ico('hair swept lock',(x,-.083,z),(.06,.055,.075),'hair',1)
  cyl('scarf collar',(0,0,1.425),.13,.105,'teal',8)
  panel('scarf hanging end',[(-.13,-.17,1.44),(-.02,-.18,1.42),(-.07,-.24,1.14),(-.17,-.24,1.19)],[(0,1,2,3)],'teal')
  sword(.39*W,-.14,.88)
 else:
  ico('cropped hair',(0,.025,1.75),(.145,.12,.075),'hair',1)
  if kind==1:
   ico('iron kettle helmet',(0,0,1.765),(.17,.14,.10),'metal',2);cyl('helmet brim',(0,-.005,1.735),.182,.035,'metal',10)
  else:
   ico('short beard',(0,-.06,1.51),(.10,.083,.07),'hair',1)
   cube('extra raised shoulder plate',(-.34,0,1.40),(.27,.28,.12),'metal',.035,(0,-.15,0))
  shield(-.43*W,-.20,1.02,boss)
  link('weapon handle',(.39*W,-.14,.77),(.39*W,-.14,1.38 if boss else 1.40),.032,.045,'wood')
  if boss:cube('square sledgehammer head',(.39*W,-.14,1.38),(.32,.14,.17),'metal',.025);cube('hammer striking face',(.56*W,-.14,1.38),(.04,.16,.18),'steel',.01)
  else:
   link('heavy club',(.39,-.14,1.16),(.39,-.14,1.46),.06,.09,'wood',7)
   for zz in [1.21,1.40]:cyl('club iron band',(.39,-.14,zz),.085,.04,'metal',7)
 return r
chars=[character('model_player',0),character('model_raider',1),character('model_roadblock_boss',2)]
# Modular NPC variants share original multipart bases, not separately sculpted characters.
mat('tan',(.42,.31,.18));mat('grayhair',(.35,.34,.31));mat('bluegray',(.17,.23,.28))
def variant(base,name,removals,material_map):
 r=root(name)
 for src in list(base.children):
  if any(src.name.startswith(p) for p in removals):continue
  o=src.copy();o.data=src.data.copy();bpy.context.collection.objects.link(o);o.parent=r
  for slot in o.material_slots:
   if slot.material.name in material_map:slot.material=M[material_map[slot.material.name]]
 return r
r=variant(chars[0],'model_ahe',['tapered steel blade','crossguard','pommel','leather wrapped grip','segmented breast plate','shoulder guard','knee plate','boot iron toe','swept dark hair','hair swept lock','oil flask'],{'teal':'rust','leather':'tan','tealdark':'rust'})
# tied-back hair and long practical split coat, ledger with visible page edge
ico('tied hair crown',(0,.035,1.74),(.15,.13,.10),'hair',2);ico('hair bun',(0,.13,1.67),(.075,.075,.085),'hair',2)
for side in [-1,1]:cube('long coat panel',(side*.14,.015,.73),(.24,.29,.36),'tan',.025,(0,side*.06,0))
cube('ledger cover',(-.38,-.13,1.04),(.18,.12,.29),'rust',.015);cube('ledger page block',(-.38,-.20,1.04),(.15,.025,.25),'ivory',.005)
cube('satchel',(.25,.09,.86),(.16,.19,.23),'leather',.022);chars.append(r)
r=variant(chars[0],'model_zhou',['tapered steel blade','crossguard','pommel','leather wrapped grip','segmented breast plate','shoulder guard','knee plate','boot iron toe','scarf','short travel cloak','oil flask'],{'teal':'cloth','hair':'grayhair','skinlight':'skin'})
# heavy leather work apron and a modest smithing hammer
panel('smith apron',[(-.18,-.23,1.33),(.18,-.23,1.33),(.22,-.24,.67),(-.22,-.24,.67)],[(0,1,2,3)],'leatherlight')
cube('apron pocket',(0,-.26,1.02),(.20,.035,.13),'leather',.014)
link('smith hammer handle',(.39,-.14,.80),(.39,-.14,1.20),.025,.025,'wood')
cube('smith hammer head',(.39,-.14,1.21),(.22,.10,.10),'metal',.015)
ico('gray beard',(0,-.07,1.51),(.10,.08,.07),'grayhair',1);chars.append(r)
r=variant(chars[2],'model_luoduo',['square sledgehammer','hammer striking face','weapon handle','cropped hair'],{'rust':'bluegray','hair':'grayhair'})
ico('command helmet crown',(0,.005,1.76),(.165,.145,.11),'metal',2)
cube('helmet crest ridge',(0,.005,1.85),(.035,.25,.065),'steel',.015)
for side in [-1,1]:cube('helmet cheek guard',(side*.135,-.015,1.64),(.03,.12,.17),'metal',.014)
sword(.39*1.15,-.14,.88);chars.append(r)

props=[]
r=root('prop_oil_barrel');props.append(r)
# bulging coopered barrel
for i in range(12):
 a=2*math.pi*i/12;cube('painted stave',(.22*math.cos(a),.22*math.sin(a),.32),(.11,.07,.58),'red',.012,(0,0,a+math.pi/2))
for z in [.08,.29,.55]:cyl('iron hoop',(0,0,z),.28,.035,'metal',12)
cyl('barrel lid',(0,0,.62),.235,.025,'wood',12);cyl('bung',(.10,0,.64),.025,.025,'dark',8)
r=root('prop_supply_crate');props.append(r)
for z in [.10,.27,.44]:
 for s in [-1,1]:cube('crate plank',(0,s*.24,z),(.52,.05,.145),'woodlight',.01);cube('crate side',(s*.24,0,z),(.05,.44,.145),'wood',.01)
for s in [-1,1]:cube('crate upright',(s*.19,-.28,.27),(.06,.045,.53),'wood',.01)
for y in [-.17,0,.17]:cube('lid plank',(0,y,.53),(.52,.15,.045),'woodlight',.008)
r=root('prop_breakable_fence');props.append(r)
for x in [-.52,.52]:cube('fence post',(x,0,.42),(.13,.13,.84),'wood',.015)
for z in [.28,.61]:cube('fence cross beam',(0,-.025,z),(1.22,.09,.13),'woodlight',.015)
cube('diagonal brace',(0,.04,.42),(1.1,.08,.075),'wood',.01,(0,-.43,0))
r=root('prop_stone_wall');props.append(r)
for row in range(3):
 for col in range(4):cube('rough masonry',((col-1.5)*.31+(row%2)*.06,0,.12+row*.23),(.295,.30,.215),'stone',.035)
r=root('prop_campfire');props.append(r)
for i in range(9):
 a=i*math.pi*2/9;ico('fire ring stone',(.3*math.cos(a),.3*math.sin(a),.07),(.12,.09,.08),'stone',1)
for a in [-.65,.65]:cube('charred log',(0,0,.09),(.48,.10,.10),'wood',.02,(0,0,a))
for x,y,z,r in [(-.09,0,.24,.10),(.07,.03,.28,.12),(0,-.08,.22,.08)]:link('solid stylized flame',(x,y,.13),(x+.035,y,z+.2),r,0,'orange',6);link('flame heart',(x,y-.035,.13),(x+.015,y-.03,z+.06),r*.60,0,'yellow',5)
r=root('prop_loot_chest');props.append(r)
cube('chest box',(0,0,.21),(.65,.42,.40),'wood',.035);cube('chest lid',(0,0,.44),(.66,.43,.12),'woodlight',.035)
for x in [-.23,.23]:cube('chest iron strap',(x,-.22,.28),(.045,.025,.42),'metal',.008);cube('lid strap',(x,0,.505),(.045,.44,.025),'metal',.008)
cube('lock plate',(0,-.24,.34),(.10,.035,.13),'metal',.008);cyl('lock keyhole',(0,-.266,.34),.014,.012,'dark',8,(radians(90),0,0))
r=root('prop_steel_sword');props.append(r);sword(0,0,.04)
r=root('prop_wood_shield');props.append(r);shield(0,0,.39,True)
r=root('prop_bridge_segment');props.append(r)
for x in [-.43,.43]:cube('bridge bearer',(x,0,.08),(.12,1.6,.16),'wood',.02)
for i in range(8):cube('bridge plank',(0,(i-3.5)*.19,.19),(1.0,.17,.08),'woodlight' if i%3 else 'wood',.015,(0,0,(-1 if i%2 else 1)*.018))
# common stage
ROOT=None
scene=bpy.context.scene;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=False
scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGBA';scene.render.film_transparent=True
scene.world.color=(.32,.32,.32);scene.view_settings.view_transform='AgX'
def aim(o,p):o.rotation_euler=(Vector(p)-o.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(4,-6,4));cam=bpy.context.object;cam.name='Fixed isometric camera';scene.camera=cam;cam.data.type='ORTHO';cam.data.ortho_scale=2.35
for name,loc,power,size in [('warm key',(-3,-4,6),550,4),('cool fill',(4,-1,3),240,3),('rim',(1,4,4),420,3)]:
 bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size;aim(o,(0,0,1))
allroots=chars+props
manifest={'project':'Sword and Fire / 剑与火','version':'0.1-static-base','path_base':'relative_to_this_manifest','status':'internal blockout, not accepted final art','final_art_accepted':False,'license':'No public license selected','provenance':'Original generated geometry and materials for this project, privately delivered; no third-party downloaded assets. Not a legal guarantee of exclusivity.','units':'meters','character_forward':'-Y','up_axis_source':'Z','glb_up_axis':'Y','pivot':'ground center','rig':'Static multipart meshes under root empties; no skeleton, skinning or animation clips.','sprites':{'size':[256,256],'camera':'orthographic, elevation 32 degrees, horizontal azimuth 45/135/225/315 degrees','background':'transparent','directions':['front_right','back_right','back_left','front_left']},'assets':[]}
def descendants(r):return [r]+list(r.children_recursive)
def show(r):
 for rr in allroots:
  for o in descendants(rr):o.hide_render=rr!=r
def export(r,folder):
 bpy.ops.object.select_all(action='DESELECT')
 for o in descendants(r):o.select_set(True)
 bpy.context.view_layer.objects.active=r
 path=f'{folder}/{r.name}.glb';bpy.ops.export_scene.gltf(filepath=BASE+'/'+path,export_format='GLB',use_selection=True,export_apply=True,export_yup=True,export_animations=False)
 dg=bpy.context.evaluated_depsgraph_get();tri=0
 for o in r.children_recursive:
  if o.type=='MESH':
   m=o.evaluated_get(dg).to_mesh();m.calc_loop_triangles();tri+=len(m.loop_triangles);o.evaluated_get(dg).to_mesh_clear()
 manifest['assets'].append({'id':r.name,'file':path,'triangles':tri,'mesh_parts':len(r.children_recursive),'kind':'character' if r in chars else 'prop','animations':[]})
for r in allroots:export(r,'models' if r in chars else 'props')
scene.render.resolution_x=256;scene.render.resolution_y=256;scene.render.resolution_percentage=100
for r in chars:
 show(r)
 for a,direction in zip([45,135,225,315],manifest['sprites']['directions']):
  az=radians(a);cam.location=(5*math.sin(az),-5*math.cos(az),.95+5*math.tan(radians(32)));aim(cam,(0,0,.95));cam.data.ortho_scale=2.12
  scene.render.filepath=f'{BASE}/sprites/{r.name}_{direction}.png';bpy.ops.render.render(write_still=True)
for r in props:
 show(r);cam.location=(3,-3,3);aim(cam,(0,0,.35));cam.data.ortho_scale=1.95 if r.name=='prop_bridge_segment' else 1.65
 scene.render.filepath=f'{BASE}/props/{r.name}.png';bpy.ops.render.render(write_still=True)
# Two review lineups; all characters stay separated in editable scene.
for group,filename in [(chars[:3],'character_lineup'),(chars[3:],'npc_lineup')]:
 for rr in allroots:
  for o in descendants(rr):o.hide_render=rr not in group
 for i,r in enumerate(group):r.location.x=(i-1)*1.60
 cam.location=(3,-9,5.1);aim(cam,(0,0,.90));cam.data.ortho_scale=5.4
 scene.render.resolution_x=1200;scene.render.resolution_y=650;scene.render.filepath=f'{BASE}/previews/{filename}.png';bpy.ops.render.render(write_still=True)
for i,r in enumerate(chars):r.location=((i%3-1)*1.7,(i//3)*2.5,0)
for i,r in enumerate(props):r.location=((i%5-2)*1.7,5+(i//5)*2,0)
for r in allroots:
 for o in descendants(r):o.hide_render=False
scene.render.filepath='//renders/'
bpy.ops.wm.save_as_mainfile(filepath=str(Path(__file__).with_name('sword_and_fire_assets.blend')))
D={'model_player': ('char_player', '行路人'), 'model_raider': ('enemy_raider', '围路兵'), 'model_roadblock_boss': ('boss_roadblock', '路障头目'), 'model_ahe': ('char_ahe', '阿禾'), 'model_zhou': ('char_zhou', '老周'), 'model_luoduo': ('char_luoduo', '罗铎')}
for a in manifest['assets']:
 if a['kind']=='character':
  a['story_id'],a['name_zh']=D[a['id']];a['sprites']=[f"sprites/{a['id']}_{d}.png" for d in manifest['sprites']['directions']]
 else:a['preview']=f"props/{a['id']}.png"
with open(BASE+'/manifest.json','w') as f:json.dump(manifest,f,ensure_ascii=False,indent=2)
print('ASSET_BUILD_COMPLETE')
