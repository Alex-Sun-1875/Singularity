from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'data/story'
read=lambda n:json.loads((P/n).read_text(encoding='utf-8'))
C=read('chapters.json');R=read('characters.json');A=read('asset-manifest.json');S=read('story-source.json')
art=json.loads((ROOT/'assets/blockout/manifest.json').read_text(encoding='utf-8'))
checks=[]
def ck(condition,message):
 assert condition,message
 checks.append(message)
def ids(rows):
 out=[r['id'] for r in rows];ck(len(out)==len(set(out)),f'Unique IDs for collection of {len(out)} records');return set(out)
chapter_ids=ids(C['chapters']);character_ids=ids(R['characters']);asset_ids=ids(A['assets']);palette_ids=ids(A['palettes'])
all_ids=set();objective_count=route_count=checkpoint_count=reward_count=0
for c in C['chapters']:
 areas=ids(c['areas']);objectives=ids(c['objectives']);cps=ids(c['checkpoints']);rewards=ids(c['rewards']);routes=ids(c['routes']);interacts=ids(c['terrain_interactions'])
 for group in [areas,objectives,cps,rewards,routes,interacts]:
  ck(not all_ids.intersection(group),f"Globally unique nested IDs in {c['id']}");all_ids.update(group)
 objective_count+=len(objectives);route_count+=len(routes);checkpoint_count+=len(cps);reward_count+=len(rewards)
 ck(len(routes)==3,f"Exactly three reconverging routes for {c['id']}")
 ck(len(cps)==3,f"Three checkpoints for {c['id']}")
 for route in c['routes']:
  ck(route['start_area_id'] in areas and route['end_area_id'] in areas,f"Route endpoints resolve {route['id']}")
  ck(route['rejoins_main_path'] and route['required_consumable'] is None,f"No consumable gate or plot branch {route['id']}")
 for cp in c['checkpoints']:ck(cp['area_id'] in areas,f"Checkpoint area resolves {cp['id']}")
 reached=set()
 for objective in c['objectives']:
  ck(set(objective['prerequisite_objective_ids'])<=reached,f"Objective DAG reachable in sequence {objective['id']}")
  reached.add(objective['id'])
 for reward in c['rewards']:ck(reward['objective_id'] in objectives,f"Reward objective resolves {reward['id']}")
 ck(set(c['completion']['required_objective_ids'])<=objectives,f"Completion objectives resolve {c['id']}")
 ck(c['completion']['next_chapter_id'] in chapter_ids|{None},f"Next chapter resolves {c['id']}")
 ck(c['unlock_after'] in chapter_ids|{None},f"Chapter prerequisite resolves {c['id']}")
 ck(set(c['enemy_character_ids'])<=character_ids and c['boss']['character_id'] in character_ids,f"Enemy references resolve {c['id']}")
 ck(c['boss']['reward_id'] in rewards,f"Boss reward reference resolves {c['id']}")
 ck(set(c['required_asset_ids'])<=asset_ids,f"Asset references resolve {c['id']}")
 for d in c['intro_dialogue']+c['outro_dialogue']:ck(d['character_id'] in character_ids and d['skippable'],f"Skippable dialogue character resolves {c['id']}")
for i,c in enumerate(C['chapters']):
 ck(c['number']==i+1,f"Chapter ordinal {c['id']}")
 ck(c['unlock_after']==(C['chapters'][i-1]['id'] if i else None),f"Linear chapter prerequisite {c['id']}")
 ck(c['completion']['next_chapter_id']==(C['chapters'][i+1]['id'] if i+1<len(C['chapters']) else None),f"Linear chapter ending {c['id']}")
for r in R['characters']:
 ck(r['model_asset_id'] in asset_ids,f"Character model mapping resolves {r['id']}")
 ck(set(r['chapters'])<=chapter_ids,f"Character chapter membership resolves {r['id']}")
 ck(set(r['palette'])<=palette_ids,f"Character palette resolves {r['id']}")
art_by={r['id']:r for r in art['assets']};matched=set();verified_paths=set()
for a in A['assets']:
 ck(set(a['chapter_ids'])<=chapter_ids and set(a['depends_on_asset_ids'])<=asset_ids,f"Asset dependencies resolve {a['id']}")
 ck(a['status'] in A['status_definitions'],f"Known asset status {a['id']}")
 for f in a['file_paths']+a.get('verification_refs',[])+([a['source_scene_path']] if 'source_scene_path' in a else []):
  path=(P/f).resolve();ck(path.is_file(),f"Asset path exists {f}");verified_paths.add(str(path))
 if 'source_asset_id' in a:
  actual=art_by[a['source_asset_id']];matched.add(actual['id'])
  ck(a['triangles_actual']==actual['triangles'],f"Exact triangle count {a['id']}")
  ck(a['status']=='delivered_blockout' and a['verified'] and not a['rigged'] and not a['animation_clips'] and a['engine_integration_status']=='not_integrated',f"Honest static-only status {a['id']}")
for field in ['source_manifest','editable_source','rebuild_script']:
 f=A['provenance'][field];ck((P/f).is_file(),f'Provenance path exists {f}');verified_paths.add(str((P/f).resolve()))
ck(matched==set(art_by),'All 15 real art assets mapped once or more without omitted props')
ck(S['chapters']==C['chapters'] and S['characters']==R['characters'],'DOCX source matches canonical chapter and character JSON')
ck(S['asset_plan']['technical']==A['budgets_estimate'],'DOCX budgets match asset manifest')
ck(A['count_summary_actual']['total_glb']==len(art['assets'])==15,'Actual GLB count is 15')
ck(len([a for a in A['assets'] if a.get('source_asset_id') and a['kind']=='character'])==6,'Six delivered character bases')
ck(len([a for a in A['assets'] if a.get('source_asset_id') and a['kind']=='prop'])==9,'Nine delivered prop bases')
ck(C['scope']['demo_chapter_ids']==['ch01'] and all(c['status']=='future_planned' for c in C['chapters'][1:]),'Only first chapter in demo scope; no implemented chapter claim')
ck(all(a['status']=='delivered_blockout' and a.get('final_art_accepted') is False for a in A['assets'] if 'source_asset_id' in a),'Existing geometry is internal blockout only, not accepted final art')
ck(sum(a.get('approved_style_reference',False) for a in A['assets'])==1,'Exactly one user-approved style concept reference')
ck(A['art_direction']['final_accepted_character_count']==0,'No unapproved final-quality character claim')
ck(not [a for a in A['assets'] if a['status'] in ['integrated_tested','in_production','delivered_static_base']],'No ambiguous completion or integration status')
ck(any(a['id']=='ref_player_four_view_v2' and a['kind']=='design_reference' for a in A['assets']),'High-detail four-view image is a design reference, not a model')
report={'passed':True,'checks_passed':len(checks),'chapters':len(chapter_ids),'characters':len(character_ids),'objectives':objective_count,'routes':route_count,'checkpoints':checkpoint_count,'unique_rewards':reward_count,'asset_slots':len(asset_ids),'actual_art_assets_mapped':len(matched),'unique_art_file_paths_verified':len(verified_paths),'test_scope':['JSON parse and required field shape','unique stable IDs','ordered objective reachability','chapter progression and reconverging routes','character and asset references','file paths and observed art manifest counts','static-only completion status','DOCX content source consistency'],'limitations':['No game logic is executed by this content validator.','No chapters or assets have been integrated into the prototype by this task.'],'checks':checks}
(P/'content-validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='checks'},ensure_ascii=False,indent=2))
