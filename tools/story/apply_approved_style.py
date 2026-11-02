from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'data/story'
read=lambda n:json.loads((P/n).read_text(encoding='utf-8'))
def write(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
A=read('asset-manifest.json');R=read('characters.json');C=read('chapters.json');S=read('story-source.json')
style='细节丰富的写实手绘2.5D，成人比例，可信皮革层次、自然布褶和钢铁高光；严格参考已选角色概念图的质感与轮廓，不以明显棱角和方块式低模作为最终外观。'
A['status_definitions']['delivered_blockout']='文件已交付且通过静态检查，但仅作为内部灰盒、轮廓或比例参考，未获最终美术风格认可。'
A['snapshot_note']='用户选定细致角色概念图并要求不要明显低模。现有6角色、9道具GLB及33张静态图仅为内部占位/制作参考，不是通过最终美术验收的角色包。文件有效性与最终美术质量分别记录。'
A['art_direction']={'approved_reference_path':'../../assets/concepts/character-direction-v1.png','quality_target':style,'presentation_route':'优先使用高质量预渲染或绘制的2.5D角色精灵；可编辑中等精度源模型单独制作与验收，不把二维立绘称作三维模型。','final_art_acceptance':'成人头身比例、自然肩肘膝轮廓、细节完整但缩小可读；材质有层次而不是纯色方块；不得只用平滑法线掩盖不匹配的几何。','final_accepted_character_count':0}
for a in A['assets']:
 if a['status']=='delivered_static_base':
  a['status']='delivered_blockout';a['final_art_accepted']=False;a['quality_role']='internal_blockout_only'
A['count_summary_actual']['quality_status']='内部占位资产数量，不是用户已认可的最终美术数量'
A['count_summary_actual']['final_accepted_character_assets']=0
A['count_summary_design']['note']='首章优先制作3个正式战斗角色。现有6个静态人物和9个道具仅是内部占位起点；中等精度模型与高细节2.5D外观另行验收。'
T=A['budgets_estimate']
T['note']='性能指标仅为待实机验证的起始目标。最终角色先达到已选概念图的质感；源模型面数不是预渲染2.5D精灵的运行成本，不用低面数限制最终造型。'
T['blockout_geometry_budget']=T.pop('character_triangles',{'player':[1500,3000],'regular_enemy':[1500,3000],'boss':[1800,3500],'npc':[1500,3000]})
T['source_geometry_target']='最终源模型面数待中等精度试制后决定；先保证成人比例、轮廓和材质层次，不采用明显棱角的低模外观。'
T['prop_triangles_blockout']=T.pop('prop_triangles',[50,800])
T['sprite_frame_size_px_estimate']=[256,512]
T['sprite_frame_size_note']='运行精灵先测试256或512像素；最终取决于相机缩放、清晰度与包体，不等于现有占位图256像素即获认可。'
T['texture_policy']='高质量源素材可使用分层材质与细节；运行端按角色大小烘焙到共享精灵图集。图集尺寸与压缩方式经真机对比后决定，不给每个小道具携带独立4K贴图。'
T['observed_baseline']['note']='只描述内部占位文件：纯色PBR、较多独立网格，无绑定动画。此数量不代表最终美术验收或整体性能通过。'
R['visual_direction']['quality_target']=style
R['visual_direction']['readability']='成人比例，玩家青绿、普通敌人锈红、指挥官蓝灰；细节与材质需达到所选概念图方向，同时在2.5D镜头下保留可读剪影。'
for r in R['characters']:
 if r.get('model_status')=='delivered_static_base':
  r['model_status']='delivered_blockout';r['model_scope']='现有静态分件GLB与四方向透明图仅作内部灰盒参考，非最终角色美术。目标为细致写实手绘2.5D与成人比例；正式模型、绑定、动作、碰撞和引擎接入仍需分别制作验收。'
  r['final_art_accepted']=False
for ch in C['chapters']:
 for route in ch['routes']:
  route['method']=route['method'].replace('也可近战潜入方向','也可直接从后门近战突入')
S['characters']=R['characters'];S['chapters']=C['chapters']
S['principles'][3]='俯视斜角2.5D呈现。美术严格沿用已选三人概念图的细致写实手绘方向：成人比例、自然布褶、皮革层次与钢铁质感。角色与装备组合保持原创，不照搬已有游戏人物；最终外观不能明显低模。'
S['delivery_boundary']='剧情与四章数据已定义；四章尚未接入现有JS原型。现有6角色和9道具GLB、24张角色静态方向图、9张道具预览及Blender源场景只作为内部占位参考，不是用户认可的最终角色美术。正式视觉采用已选概念图的细致质感，绑定、动作、碰撞与引擎接入仍待制作验收。'
S['scope_now'][-1]='首章3个战斗角色先达到已选概念图的细致2.5D质感；现有静态灰盒用于尺寸、装备拆分与接入试验。'
S['scope_later'][1]='骨骼绑定与正式动画、八方向扩展、更多音效和地形细节；不能以内部灰盒代替已选美术方向'
S['asset_plan']['summary']='最终角色采用已选三人概念图的细致写实手绘2.5D方向，不做明显棱角的低模成品。优先完成行路人、围路兵、路障头目；成人比例、自然布褶、皮革与钢铁细节需要同时成立。高质量2.5D精灵和可编辑三维源模型是不同交付物，分别验收。'
S['asset_plan']['completion_snapshot']='现有6角色和9道具GLB、24张角色方向图、9张道具预览可用作内部占位参考；15个GLB已回导核对，33张PNG无裁切。它们是约五头身、纯色材质的简化低模基础，未达到已选概念图的最终质感。无骨架、蒙皮、正式动作、UV贴图、碰撞或LOD；未接入JS原型，也未在Cocos中验证。'
S['asset_plan']['rows']=[
 {'item':'正式战斗角色','unique':'3 优先制作','priority':'P0','reuse':'行路人、围路兵、路障头目；按已选概念图的成人比例与细致材质制作'},
 {'item':'现有角色占位','unique':'6 内部参考','priority':'非最终美术','reuse':'静态GLB与Blender源文件可编辑；NPC和罗铎由共用模块衍生'},
 {'item':'现有静态方向图','unique':'24 内部参考','priority':'非最终美术','reuse':'6角色乘4方向，256像素透明图；不是正式外观或动作帧'},
 {'item':'现有道具占位','unique':'9 内部参考','priority':'P0至P1','reuse':'油桶、木箱、栅栏、石墙、营火、战利品箱、钢剑、木盾、木桥段'},
 {'item':'首章必要场景件','unique':'4 待制作','priority':'P0','reuse':'粮车、木门、大岩石、检查点旗；可选掉落袋另列P1'},
 {'item':'地形和反馈','unique':'6地形 12图标 10音效','priority':'P0 规划','reuse':'场景不抢人物细节；声音原创或许可明确'},
 {'item':'盾兵与弩手','unique':'2变体 规划','priority':'P2','reuse':'复用围路兵身体和已有装备；完整架盾与远程动作后做'}]
S['asset_plan']['technical']=T
S['asset_plan']['pipeline']='先以已选概念图校准成人比例、装备轮廓和材质细节，再制作可编辑源模型或高质量2.5D精灵。运行端优先验证预渲染精灵与现有JS画面的适配；源模型与二维图分别保留，不把立绘当作已完成模型。'
S['asset_plan']['quality_boundary']='现有五头身、纯色材质的简化低模只用于内部占位。最终角色要有成人头身比例、自然肩肘膝形体、可辨识布褶与皮革钢片层次；不能仅凭平滑法线或增加面数就宣称达到参考图。无正式动作、绑定或集成的文件必须继续标明。'
S['asset_plan']['palette_note']='暖石与炭灰形成场景底色，玩家青绿、普通兵锈红、罗铎蓝灰、火为橙色。配色统一不等于降低细节：皮革、布料、钢铁应有可信的高光、粗糙度和自然变化，缩小后仍清楚。'
S['asset_plan']['art_direction']=A['art_direction']
S['acceptance'].append({'id':'gate08','name':'符合已选美术方向','test':'成人比例、自然布褶、皮革与钢铁层次接近已选概念图；不接受明显方块式低模作最终外观。最终二维精灵、源模型和动作质量分别检查。'})
# Idempotent append.
S['acceptance']=list({x['id']:x for x in S['acceptance']}.values())
for x in S['acceptance']:
 if x['id']=='gate05':x['test']='现有6角色9道具仅为内部占位，文件检查通过不等于美术通过。正式外观、动画、碰撞、引擎接入逐项验收；首章缺少场景件须补齐。'
for x in S['implementation']:
 if x['id']=='task05':
  x['task']='制作并接入首批正式角色外观'
  x['done']='先让首章3角色达到已选概念图质感，再检查朝向、脚底与遮挡；补做粮车、木门等；动作与源模型独立验收。'
S['next_action']='先完成首章可通关与可恢复白盒，同时按已选概念图打磨首批正式角色外观；内部低模只作测试占位。第二至第四章保留设计与数据，不在首章验收前同时开工。'
write('asset-manifest.json',A);write('characters.json',R);write('chapters.json',C);write('story-source.json',S)
print('Applied approved detailed art direction; all existing geometry/sprites are internal blockout only.')
# Delivered 2D references are not models or registered gameplay sprite sheets.
A['status_definitions']['delivered_design_reference']='已生成并检查的二维设计参考，不是绑定模型、动作序列或已注册可用的游戏精灵图集。'
refs=[
 ('concept_character_direction','已选角色美术方向概念图','../../assets/concepts/character-direction-v1.png',True,['ch01']),
 ('concept_ch01_environment','首章场景美术方向概念图','../../assets/concepts/chapter01-environment-v1.png',False,['ch01']),
 ('ref_player_four_view_v2','高细节主角四向设计参考','../../assets/concepts/player-four-view-v2.png',False,['ch01','ch02','ch03','ch04'])]
for id,name,path,approved,chapters in refs:
 if (P/path).is_file():
  row={'id':id,'name':name,'kind':'design_reference','priority':'P0','unique_asset_count':1,'status':'delivered_design_reference','chapter_ids':chapters,'reuse':'供外观、比例和材质制作参考；不代表实际游戏截图、模型渲染或已完成角色动画。','depends_on_asset_ids':[],'file_paths':[path],'verified':True,'approved_style_reference':approved,'final_production_art_accepted':False,'source':'image_generation_using_original_project_direction','quality_role':'art_direction_reference_only'}
  if id=='ref_player_four_view_v2':
   row.update({'pixel_size_actual':[1024,1536],'file_mode_actual':'RGBA','transparency_verified':True,'limitations':['静态四视角设计参考，非三维模型','装备与形体跨视角一致性仍需制作校准','未注册统一脚底原点、动画帧或2.5D游戏相机角度']})
  A['assets']=[a for a in A['assets'] if a['id']!=id]+[row]
A['count_summary_actual']['design_reference_images']=sum(a['kind']=='design_reference' for a in A['assets'])
A['art_direction']['additional_design_reference_asset_id']='ref_player_four_view_v2'
S['asset_plan']['art_direction']=A['art_direction']
S['asset_plan']['additional_reference_note']='另有高细节主角四向设计参考图，已检查1024乘1536像素RGBA与透明边缘。它只是静态设计转向图，不是三维模型、绑定动作或可直接播放的精灵图集；跨方向一致性和2.5D视角仍需制作校准。'
S['asset_plan']['additional_reference_path']='../../assets/concepts/player-four-view-v2.png'
S['delivery_boundary']='剧情与四章数据及已选美术标准已定义；高细节主角四向图仅为设计参考，正式生产素材仍待完成。现有6角色和9道具GLB、24张角色静态方向图、9张道具预览及Blender源场景只作内部占位，不是用户认可的最终角色美术。以下四章、正式外观、绑定动作、碰撞与引擎接入尚未完成。'
write('asset-manifest.json',A);write('story-source.json',S)
print('Registered approved concept plus high-detail four-view design reference separately from models.')
S['document_purpose']='作为独立开发的首版设计基线，固定完整故事与四章结构，明确首章应该先做什么，以及角色、道具和材料如何复用。正文中的游玩时长与性能预算均为起始目标，素材数量和文件检查结果按当前快照单列。'
S['navigation']=[{'page':1,'topic':'开发边界与体验目标'},{'page':2,'topic':'完整主线与叙事规则'},{'page':3,'topic':'第一章 断路'},{'page':4,'topic':'第二章 旧矿道'},{'page':5,'topic':'第三章 河岸粮仓'},{'page':6,'topic':'第四章 灰石城门'},{'page':7,'topic':'人物与美术识别'},{'page':8,'topic':'剑火成长与游戏材料'},{'page':9,'topic':'角色外观标准'},{'page':10,'topic':'首批素材与技术预算'},{'page':11,'topic':'首章任务与验收'}]
write('story-source.json',S)
