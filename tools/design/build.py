import json
from pathlib import Path
from docx_layout import *

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'data/story'
d=json.loads((BASE/'story-source.json').read_text())
doc=build_document()
doc.core_properties.title=d['title']
names={x['id']:x['name'] for x in d['characters']}

def h(s): return heading(doc,s,2)
def p(s,**kw): return para(doc,s,**kw)
def top(s): return heading(doc,s,1,True)
def join(items): return '；'.join(x.rstrip('。；') for x in items)+'。'

# 1 Project synopsis and boundaries
heading(doc,d['title'],0)
p(d['version']+'　'+d['date'])
p(d['decision'])
p(d['document_purpose'])
h('体验目标')
for x in d['principles']: bullet(doc,x)
h('现在做什么')
for x in d['scope_now']: bullet(doc,x)
h('后续再做')
p(join(d['scope_later']))
h('明确不做')
for x in d['scope_excluded']: bullet(doc,x)
h('当前交付边界')
p(d['delivery_boundary'])

# 2 Complete story, a practical four-act arc
top('完整主线与叙事规则')
plot_start=len(doc.paragraphs)
plot=d['plot']
for title,key in [('找回一辆粮车','opening'),('重新连通补给线','development'),('保粮而不是烧仓','turn'),('亲手打开灰石城门','ending')]:
    h(title); p(plot[key])
h('让场景交代证据')
for x in plot['environmental_evidence']: bullet(doc,x)
h('叙事规则')
for x in plot['rules']: bullet(doc,x)
for par in doc.paragraphs[plot_start:]:
    if par.style.name=='Normal':
        par.paragraph_format.line_spacing=Pt(18)
        par.paragraph_format.space_after=Pt(6)
        for run in par.runs: font(run,12)

# 3-6 One coherent production page per chapter
for c in d['chapters']:
    top('第'+str(c['number'])+'章 '+c['title'])
    mins=c['target_minutes_estimate']
    p(('首章试玩待实现' if c['number']==1 else '后续规划 暂不实施')+'　目标 '+str(mins[0])+' 至 '+str(mins[1])+' 分钟')
    p(c['summary'])
    h('区域与主线目标')
    p(' → '.join(x['name'] for x in c['areas']))
    p(' → '.join(x['text'] for x in c['objectives'])+'。')
    h('三条战术路线')
    table(doc,['路线','通过方式与风险','可选奖励'],[[r['name'],r['method']+r['risk'],r['optional_reward']] for r in c['routes']],[1.05,4.85,1.2])
    b=c['boss']
    h('关底战斗')
    p(b['arena'])
    p(join(b['telegraphs']+b['actions']))
    p(b['terrain_solution']+b['adds'])
    h('地形与通关保障')
    p(join(x['rule'] for x in c['terrain_interactions']))
    h('奖励与持久变化')
    p(join(x['name']+'：'+x['effect'] for x in c['rewards']))
    p('检查点：'+'、'.join(x['name'] for x in c['checkpoints'])+'。'+c['completion']['world_change'])
    p(c['id']+'　'+' / '.join(x['id'] for x in c['checkpoints']),small=True,after=3)
    h('可跳过对白')
    p('开场　'+'　'.join(names[x['character_id']]+'：'+x['text'] for x in c['intro_dialogue']))
    p('收尾　'+'　'.join(names[x['character_id']]+'：'+x['text'] for x in c['outro_dialogue']))

# 7 Cast and recognizable art direction
top('人物与美术识别')
p(d['principles'][3])
for c in d['characters'][:4]:
    h(c['name']+' '+c['role'])
    p(c['silhouette'])
    p(c['motivation']+c.get('arc',''))
    p(c['voice'])
h('敌人与复用关系')
table(doc,['角色','可读轮廓','战斗职责'],[[c['name'],c['silhouette'],c.get('combat','')] for c in d['characters'][4:]],[.85,3.2,3.05])

# 8 Builds and material economy
top('剑火成长与游戏材料')
b=d['builds']
p(b['shared_base'])
for key in ['sword','fire']:
    x=b[key]; h(x['name']+' '+x['style']); p(x['demo_modifier']); p('后续：'+join(x['later_modifiers']))
h('成长节奏')
table(doc,['里程碑','解锁','选择边界'],[[r['milestone'],r['unlock'],r['choice']] for r in b['progression']],[1.35,2.05,3.7])
h('装备与材料')
p(b['equipment'])
table(doc,['材料','首章上限目标','用途与来源'],[[x['name'],str(x['cap_demo_estimate']),x['purpose']+'来源：'+x['source']+'。'] for x in b['materials']],[.75,1.2,5.15],center=(1,))
p(b['balance'])

# 9 Approved visual direction is visible, not just described.
top('角色外观标准')
a=d['asset_plan']; t=a['technical']
art=a['art_direction']
pic=doc.add_paragraph()
pic.alignment=WD_ALIGN_PARAGRAPH.CENTER
pic.paragraph_format.line_spacing=1
pic.paragraph_format.space_after=Pt(4)
pic.paragraph_format.keep_with_next=True
inline=pic.add_run().add_picture(str((BASE/art['approved_reference_path']).resolve()),width=Inches(6.8))
inline._inline.docPr.set('descr','行路人 围路兵 路障头目的角色美术方向概念图')
caption=p('角色美术方向概念图 不是游戏截图或模型渲染',small=True)
caption.alignment=WD_ALIGN_PARAGRAPH.CENTER
h('最终角色标准')
p(art['quality_target'])
p(art['final_art_acceptance'])
p(a['quality_boundary'])
h('二维与三维分别验收')
p('已通过最终角色美术验收：'+str(art['final_accepted_character_count'])+' 个。')
p(art['presentation_route'])
p(a['palette_note'])
p(a['provenance'])

# 10 Asset status and deliberately provisional technical budgets.
top('素材状态与技术预算')
p(a['completion_snapshot'])
table(doc,['类别','数量及状态','优先级','复用与范围'],[[r['item'],r['unique'],r['priority'],r['reuse']] for r in a['rows']],[1.2,1.1,.9,3.9],center=(1,2))
h('移动端起始预算')
p(t['note'])
fmt=lambda v:' 至 '.join(str(x) for x in v)
ob=t['observed_baseline']
techrows=[
 ['源模型精度',t['source_geometry_target']],
 ['内部占位实测','角色 '+fmt(ob['character_triangles_actual'])+' 三角面；道具 '+fmt(ob['prop_triangles_actual'])+' 三角面。非最终质量指标。'],
 ['运行精灵',t['sprite_frame_size_note']],
 ['图集与方向','共享图集起始目标 '+str(t['shared_texture_atlas_px'][0])+' × '+str(t['shared_texture_atlas_px'][1])+'；先 '+str(t['sprite_direction_count_initial'])+' 方向，后扩 '+str(t['sprite_direction_count_later'])+' 方向'],
 ['运行目标',str(t['runtime_target_fps'])+' FPS；'+str(t['draw_calls_target_max'])+' 次绘制；常态 '+str(t['active_enemies_target'])+' 敌人，峰值 '+str(t['active_enemies_peak'])+'；同时 '+str(t['fire_patch_concurrent_target_max'])+' 火区'],
 ['包体与内存','首批压缩素材 ≤ '+str(t['initial_asset_compressed_mb_target_max'])+' MB；每章 ≤ '+str(t['chapter_asset_compressed_mb_target_max'])+' MB；内存软目标 ≤ '+str(t['memory_mb_soft_target_max'])+' MB'],
]
table(doc,['项目','预算目标'],techrows,[1.25,5.85])
p(t['texture_policy'])
h('数据文件约定')
p(d['id_contract'])

# 11 Actionable integration sequence and acceptance gates
top('首章任务与验收')
p(d['next_action'])
table(doc,['顺序','任务','完成条件'],[[str(i+1),r['task'],r['done']] for i,r in enumerate(d['implementation'])],[.5,1.85,4.75],center=(0,))
h('验收要点')
for r in d['acceptance']: p(r['test'],bold_lead=r['name']+'　',after=3)
h('存档约定')
s=d['save_summary']
p('保存时机：'+join(s['trigger'])+s['death'])
p(s['atomicity'])

# Keep all headings black and punctuation-free even if future source wording changes.
for par in doc.paragraphs:
    if par.style.name in ['Title','Subtitle','Heading 1','Heading 2','Heading 3']:
        for r in par.runs: font(r,color='000000')
out=ROOT/'docs/design/jian-yu-huo-design-v1.docx'
doc.save(out)
print(out)
print('paragraphs',len(doc.paragraphs),'tables',len(doc.tables))
