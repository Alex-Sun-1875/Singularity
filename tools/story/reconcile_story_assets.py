from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'data/story'
A=ROOT/'assets/blockout'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(name,data): (P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
manifest=read(P/'asset-manifest.json'); chars=read(P/'characters.json'); ch=read(P/'chapters.json'); s=read(P/'story-source.json')
actual=read(A/'manifest.json'); validation=read(A/'validation.json'); spritecheck=read(A/'sprite-validation.json')
actual_by={a['id']:a for a in actual['assets']}; checks={a['id']:a for a in validation['results']}
mapping={'prop_barrel_oil':'prop_oil_barrel','prop_crate_supply':'prop_supply_crate','prop_barricade_wood':'prop_breakable_fence','prop_bridge_plank':'prop_bridge_segment','prop_brazier':'prop_campfire'}
for extra,name,prio,chapters in [('prop_stone_wall','石墙模块','P0',['ch01','ch02','ch04']),('prop_loot_chest','战利品箱','P0',['ch01','ch02','ch03','ch04']),('prop_steel_sword','钢剑道具','P0',['ch01','ch02','ch03','ch04']),('prop_wood_shield','方木盾道具','P1',['ch01','ch02','ch03','ch04'])]:
 if not any(x['id']==extra for x in manifest['assets']):
  manifest['assets'].append({'id':extra,'name':name,'kind':'prop','priority':prio,'unique_asset_count':1,'status':'planned','chapter_ids':chapters,'reuse':'共用比例与材质，武器盾牌可挂接角色；不自带动作或防御逻辑。','depends_on_asset_ids':[],'file_paths':[],'verified':False})
for row in manifest['assets']:
 source_id=mapping.get(row['id'],row['id']); actual_row=actual_by.get(source_id)
 if actual_row:
  assert checks[source_id]['import_success'] and checks[source_id]['triangle_match']
  files=[actual_row['file']]+actual_row.get('sprites',[])+([actual_row['preview']] if 'preview' in actual_row else [])
  assert all((A/f).is_file() for f in files)
  row.update({'source_asset_id':source_id,'status':'delivered_static_base','verified':True,'file_paths':['../../assets/blockout/'+f for f in files],'triangles_actual':actual_row['triangles'],'mesh_parts_actual':actual_row['mesh_parts'],'rigged':False,'animation_clips':[],'engine_integration_status':'not_integrated','verification_refs':['../../assets/blockout/validation.json','../../assets/blockout/sprite-validation.json'],'source_scene_path':'../../source-art/blockout/sword_and_fire_assets.blend'})
 elif row['id']=='sprite_demo_pack':
  files=[f for x in actual['assets'] if x['kind']=='character' for f in x['sprites']]
  row.update({'name':'六角色四方向静态透明图','unique_asset_count':24,'status':'delivered_static_base','verified':True,'file_paths':['../../assets/blockout/'+f for f in files],'frame_size_px_actual':[256,256],'depends_on_asset_ids':['model_player','model_raider','model_roadblock_boss','model_ahe','model_zhou','model_luoduo'],'reuse':'6角色乘4方向，共24张静态图；方向是观察角，不是动作帧。','verification_refs':['../../assets/blockout/sprite-validation.json'],'engine_integration_status':'not_integrated'})
 elif row['status']=='in_production':
  row['status']='planned'
manifest['path_base']='relative_to_this_manifest'
manifest['snapshot_note']='已核对实际静态基模与透明图文件。delivered_static_base 仅代表文件已交付并通过静态检查，不代表正式动画、碰撞、地形逻辑或引擎集成已完成。'
manifest['provenance']={'description':'本项目原创程序化几何与材料，未下载第三方模型或纹理；概念图独立列明，不是模型渲染。','public_license':'not_selected','source_manifest':'../../assets/blockout/manifest.json','editable_source':'../../source-art/blockout/sword_and_fire_assets.blend','rebuild_script':'../../source-art/blockout/build_assets.py','legal_note':'素材出处记录不构成排他性或版权法律保证。'}
manifest['budgets_estimate']['character_triangles']={'player':[1500,3000],'regular_enemy':[1500,3000],'boss':[1800,3500],'npc':[1500,3000]}
manifest['budgets_estimate']['prop_triangles']=[50,800]
manifest['budgets_estimate']['sprite_frame_size_px_estimate']=[256,256]
manifest['budgets_estimate']['observed_baseline']={'character_triangles_actual':[1720,2536],'prop_triangles_actual':[132,748],'material_count_per_character_actual':[10,11],'note':'静态基模在单件面数起始预算内，但有较多独立网格与材料。整体绘制次数、内存、帧率未测，需合并网格、共享材料、精灵批次或LOD评估。'}
manifest['count_summary_design'].update({'character_bases_demo':3,'character_bases_additional_delivered':3,'npc_or_final_boss_future':3,'prop_slots_demo':14,'static_direction_sprite_slots_demo':12,'static_direction_sprite_slots_additional':12,'note':'首章战斗用3角色；额外交付阿禾、老周、罗铎3个静态衍生基模。所有章节仍未实现。14个首章道具槽位中9个有静态文件，4个关键场景件与1个可选掉落袋待制作。'})
manifest['count_summary_actual']={'character_glb':6,'prop_glb':9,'total_glb':15,'character_static_direction_png':24,'prop_preview_png':9,'editable_blend':1,'rigged_characters':0,'animation_clips':0,'engine_integrated_assets':0,'verification':'15 GLB 均在 Blender 中重新导入，三角面数匹配；33 PNG 通过透明边界与裁切检查。'}
# Assert current full count rather than treating design slots as completed.
assert len(actual['assets'])==15 and sum(x['kind']=='character' for x in actual['assets'])==6
for c in chars['characters']:
 if c['model_asset_id'] in actual_by:
  c['model_scope']='已交付静态分件GLB、四方向256像素透明图及共享可编辑Blender源场景；无骨架、蒙皮、关节枢轴、动作、碰撞或引擎接入。'
  c['model_status']='delivered_static_base'
  c['source_scene_path']='../../source-art/blockout/sword_and_fire_assets.blend'
 else:c['model_status']='planned'
 if c['id']=='enemy_raider':
  c['silhouette']='锈红布甲，铁帽，铁箍短棍和小圆木盾；与玩家青绿披布明显区分。小盾只用于造型，基础兵不使用完整架盾防御。'
 if c['id']=='enemy_shield':
  c['silhouette']='复用围路兵身体，改用宽方木盾并抬高肩线；显著的架盾姿态区分基础兵。'
 if c['id']=='boss_roadblock':c['silhouette']='围路兵体型加宽约15%，非对称肩甲，大方盾与单手短柄铁锤，腰挂门钥匙；不做巨型怪物。'
 if c['id']=='char_luoduo':c['current_base_note']='当前静态衍生基模使用蓝灰披风；目标锈色短披风仍需在最终角色精修时统一。'
 if c['id']=='char_ahe':c['current_base_note']='当前静态基模已具土黄长衣、账册、挎包与发髻；红围巾作为后续外观识别目标。'
s['characters']=chars['characters']
s['scope_now'][-1]='首章3个战斗角色优先接入；另有3个NPC或终章人物静态衍生基模；9个已做基础道具和必要场景件复用。'
s['delivery_boundary']='本版完成剧情与数据定义，并已有6个角色和9个道具的静态GLB基模、24张角色四方向透明图、9张道具预览及可编辑Blender源场景。无骨架、蒙皮、正式动作、碰撞或引擎接入。现有JS原型只验证连续区域、推击、火、拾取和头目等基础循环，以下四章尚未实现。'
s['asset_plan']['summary']='已交付6个角色和9个道具的静态基模。首章战斗优先使用行路人、围路兵、路障头目；阿禾、老周、罗铎为共用网格模块衍生的静态基础。角色共24张四方向256像素透明图，道具9张透明预览，另有可编辑Blender源场景。'
s['asset_plan']['completion_snapshot']='15个GLB均已在Blender重新导入且三角面数匹配，33张PNG已检查透明边界与裁切。角色1720至2536三角面，道具132至748三角面；属于简化低多边形静态基础，不是概念图的写实质感成品。无骨架、蒙皮、正式关节枢轴、动作、UV贴图、碰撞或LOD；未接入JS原型，也未在Cocos中验证。'
s['asset_plan']['rows']=[
 {'item':'角色静态基模','unique':'6 已交付','priority':'P0优先3个','reuse':'行路人、围路兵、路障头目优先接入；阿禾、老周、罗铎为模块化衍生'},
 {'item':'角色静态方向图','unique':'24 已交付','priority':'P0','reuse':'6角色乘4方向，256像素透明PNG；不是动作帧'},
 {'item':'道具静态基模','unique':'9 已交付','priority':'P0至P1','reuse':'油桶、木箱、栅栏、石墙、营火、战利品箱、钢剑、木盾、木桥段'},
 {'item':'首章必要场景件','unique':'4 待制作','priority':'P0','reuse':'粮车、木门、大岩石、检查点旗；可选掉落袋另列P1'},
 {'item':'地形模块','unique':'6 规划','priority':'P0','reuse':'平地、坡道、岩壁、低台、路边、棚顶，复用已有石墙与桥'},
 {'item':'界面与声音','unique':'12图标 10音效 规划','priority':'P0','reuse':'原创或许可明确；先完成攻击、拾取和目标反馈'},
 {'item':'盾兵与弩手','unique':'2变体 规划','priority':'P2','reuse':'复用围路兵身体；完整架盾与远程动作后做'}]
s['asset_plan']['technical']=manifest['budgets_estimate']
s['asset_plan']['quality_boundary']='人物约五头身，使用几何层次与纯色材质表达装备；概念图中的面部、布纹和磨损细节未烘焙进网格。基础兵的小盾不代表已有防御行为。阿禾红围巾、罗铎锈色披风与最终比例属于后续统一项。'
s['asset_plan']['provenance']='几何与材料为本项目原创程序化制作，未下载第三方模型或纹理；未选择公开许可。概念图是独立的美术方向图，不是游戏截图或模型渲染。'
s['asset_plan']['concept_paths']=['../../assets/concepts/character-direction-v1.png','../../assets/concepts/chapter01-environment-v1.png']
s['asset_plan']['actual_preview_paths']=['../../assets/blockout/previews/character_lineup.png','../../assets/blockout/previews/npc_lineup.png']
for task in s['implementation']:
 if task['id']=='task05':task['done']='首章3个战斗角色与可复用道具进入画面；朝向、脚底、遮挡一致；补做粮车、木门等场景件，正式动作独立验收。'
for gate in s['acceptance']:
 if gate['id']=='gate05':gate['test']='现有6角色与9道具静态文件可打开，24张角色图和9张道具图完整；首章缺少场景件须补齐。动画、碰撞、集成分别标记，不能混称完成。'
# Drop optional loot-bag from P0; loot chest is available for fixed rewards.
for row in manifest['assets']:
 if row['id']=='prop_loot_bag':row['priority']='P1';row['reuse']='可选；首章可先复用已交付战利品箱，不阻塞首章。'
write('asset-manifest.json',manifest);write('characters.json',chars);write('story-source.json',s)
print('Reconciled 15 actual static GLB + 33 PNG, with explicit asset ID mapping and pending props.')
# Unify low-level silhouettes to the delivered originals; these details are not user constraints.
blue={'id':'palette_bluegray','name':'指挥官蓝灰','#':'#56677A','hex':'#56677A','roughness_estimate':0.95,'metallic_estimate':0,'use':'罗铎披风，区别于普通兵的锈红布'}
blue.pop('#')
if not any(x['id']==blue['id'] for x in manifest['palettes']):manifest['palettes'].append(blue)
for c in chars['characters']:
 c.pop('current_base_note',None)
 if c['id']=='char_ahe':
  c['silhouette']='女性，土黄长外衣，发髻，账册与小挎包；无武器，装备重实用不性感化。'
  c['palette']=['palette_cloth','palette_leather']
 if c['id']=='char_luoduo':
  c['silhouette']='暗钢胸甲，蓝灰短披风，低矮钢盔脊，方盾与钢剑；脸部可见，不戴夸张角盔。'
  c['palette']=['palette_charcoal','palette_iron','palette_bluegray']
  c['combat']='方盾冲锋、两段重斩、号令弩兵；优先复用近战骨架，新增动作后再做终章。'
for cc in ch['chapters']:
 if cc['id']=='ch04':cc['boss']['telegraphs']=[t.replace('长盾','方盾') for t in cc['boss']['telegraphs']]
 if cc['id']=='ch01':
  cc['boss']['visual_note']='方盾和单手锤形成较宽轮廓；首版不强制增加一套破盾机制，沿用冲撞失衡与攻击后摇。'
s['characters']=chars['characters'];s['palettes']=manifest['palettes'];s['chapters']=ch['chapters']
s['asset_plan']['quality_boundary']='人物约五头身，使用几何层次与纯色材质表达装备；概念图中的面部、布纹和磨损细节未烘焙进网格。围路兵的小盾为轻装轮廓，路障头目使用大方盾与单手锤，罗铎以蓝灰披风区别于锈红普通兵；装备外形不等于已实现战斗逻辑。'
s['asset_plan']['palette_note']='暖石与炭灰组成场景底色，玩家青绿、普通兵锈红、罗铎蓝灰、火为橙色。木、布、皮、铁共享材质；细小磨损用大色块和少量边缘变化表达，避免移动端噪点。'
write('asset-manifest.json',manifest);write('characters.json',chars);write('chapters.json',ch);write('story-source.json',s)
print('Aligned all canonical silhouettes to actual static bases.')
