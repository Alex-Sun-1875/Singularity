from pathlib import Path
import json, os
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'data/story'
read=lambda n:json.loads((P/n).read_text(encoding='utf-8'))
def write(n,d):(P/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
A=read('asset-manifest.json');R=read('characters.json')
for id,name,file in [('ref_raider_detail_v2','围路兵高细节正背面设计参考','raider-detail-reference-v2.png'),('ref_captain_detail_v2','路障头目高细节正背面设计参考','captain-detail-reference-v2.png')]:
 rel='../../assets/concepts/'+file
 im=Image.open(P/rel)
 row={'id':id,'name':name,'kind':'design_reference','priority':'P0','unique_asset_count':1,'status':'delivered_design_reference','chapter_ids':['ch01'],'reuse':'正背面静态设计研究；不代表已校准四方向或可播放的游戏精灵图集。','depends_on_asset_ids':['concept_character_direction'],'file_paths':[rel],'verified':True,'pixel_size_actual':list(im.size),'file_mode_actual':im.mode,'approved_style_reference':False,'final_production_art_accepted':False,'quality_role':'art_direction_reference_only','limitations':['部分视角近似，不能作为已验证四方向精灵表','角色外观跨视角一致性与2.5D镜头仍需校准','不是三维模型、绑定、动作或游戏集成']}
 A['assets']=[a for a in A['assets'] if a['id']!=id]+[row]
refined=json.loads((ROOT/'assets/studies/player-refined/manifest.json').read_text())
val=json.loads((ROOT/'assets/studies/player-refined/validation.json').read_text())
assert val['passed'] and refined['triangles']==val['triangles']==25246
files=[os.path.relpath(ROOT/'assets/studies/player-refined'/f, P) for f in refined['files']]+['../../assets/studies/player-refined/sprites/model_player_refined_'+d+'.png' for d in ['front_right','back_right','back_left','front_left']]
assert all((P/f).is_file() for f in files)
row={'id':'study_player_refined_mesh','name':'主角中等精度结构研究','kind':'geometry_study','priority':'P1','unique_asset_count':1,'status':'delivered_blockout','chapter_ids':['ch01'],'reuse':'可用于结构和材料试验，仍明显程式化，未达到已选概念图质感；不是最终角色模型。','depends_on_asset_ids':['model_player','concept_character_direction'],'file_paths':files,'verified':True,'triangles_actual':refined['triangles'],'mesh_parts_actual':refined['mesh_parts'],'rigged':False,'animation_clips':[],'engine_integration_status':'not_integrated','final_art_accepted':False,'quality_role':'unapproved_structure_study','external_manifest_path':'../../assets/studies/player-refined/manifest.json','verification_refs':['../../assets/studies/player-refined/validation.json','../../assets/studies/player-refined/sprite-validation.json'],'source_scene_path':'../../source-art/player-refined/player_refined.blend','limitations':['面数增加不代表已达到参考图','无正式雕刻细节、绑定或动画','附带四张512像素静态渲染仅供检查，不是已认可游戏角色外观']}
A['assets']=[a for a in A['assets'] if a['id']!=row['id']]+[row]
A['count_summary_actual']['design_reference_images']=sum(a['kind']=='design_reference' for a in A['assets'])
A['count_summary_actual']['additional_unapproved_geometry_studies']=1
A['count_summary_actual']['additional_study_glb']=1
A['count_summary_actual']['additional_study_static_render_png']=4
A['count_summary_actual']['total_glb_including_studies']=16
A['count_summary_actual']['scope_note']='total_glb=15 是首批6角色9道具的基模数量；另有1个主角结构研究GLB，不新增角色、不计入最终美术通过数。额外研究渲染与高细节设计参考不混入首批33张静态图计数。'
for r in R['characters']:
 if r['id']=='char_player':r['additional_study_asset_ids']=['ref_player_four_view_v2','study_player_refined_mesh']
 if r['id']=='enemy_raider':r['additional_study_asset_ids']=['ref_raider_detail_v2']
 if r['id']=='boss_roadblock':r['additional_study_asset_ids']=['ref_captain_detail_v2']
# Character descriptions in DOCX source remain identical; adding only optional asset mappings.
S=read('story-source.json');S['characters']=R['characters']
S['asset_plan']['supplemental_studies_note']='补充围路兵与路障头目的高细节正背面设计研究图，不将近似视角视为已校准四方向精灵表。另有25246三角面的主角结构试制，仍未达到已选参考图风格，只作内部研究，不能按正式角色交付验收。'
write('asset-manifest.json',A);write('characters.json',R);write('story-source.json',S)
print('Added 2 front/back design studies and 1 unapproved 25246-triangle structural study; final art count remains zero.')
