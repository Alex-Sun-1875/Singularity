"""Prepare local upload candidates using installed FFmpeg and Pillow only."""
from pathlib import Path
import hashlib, html, json, re, shutil, subprocess
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'promotion'
FFMPEG = Path('C:/Program Files (x86)/Lenovo/LegionZone/2.0.30.11033/SEGamingAI/services/editor/ffmpeg.exe')
FAMILIES = [('BOW', '逐风弓术'), ('WAR', '破军战技'), ('THU', '雷霆秘术'), ('FIR', '烈焰秘术')]
CLASS_LABELS = {'BOW':'弓箭手','WAR':'战士','THU':'雷电法师','FIR':'火系法师'}

def run(args):
    p = subprocess.run([str(FFMPEG), '-hide_banner', '-nostdin', *map(str,args)], capture_output=True, encoding='utf-8', errors='replace')
    if p.returncode: raise RuntimeError(p.stderr[-4000:])
    return p.stderr

def export(source, dest, start=0, duration=None):
    if dest.exists() and dest.stat().st_mtime >= source.stat().st_mtime:
        return
    args = ['-y']
    if start: args += ['-ss', start]
    args += ['-i', source]
    if duration: args += ['-t', duration]
    args += ['-vf','fps=30,format=yuv420p','-c:v','h264_nvenc','-preset','p5','-b:v','14M','-maxrate','18M','-bufsize','28M','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',dest]
    run(args)

def probe(file):
    p = subprocess.run([str(FFMPEG),'-hide_banner','-i',str(file)],capture_output=True,encoding='utf-8',errors='replace')
    text=p.stderr
    duration=re.search(r'Duration: (\d+):(\d+):(\d+\.\d+)',text)
    return {'bytes':file.stat().st_size,'seconds':sum(float(v)*m for v,m in zip(duration.groups(),[3600,60,1])) if duration else None,'h264':bool(re.search(r'Video: h264',text)),'aac':bool(re.search(r'Audio: aac',text)),'fullHD':bool(re.search(r'1920x1080',text)),'fps30':bool(re.search(r'30 fps',text))}

def board(files, dest, columns=2, thumb=(640,360)):
    font_path=Path('C:/Windows/Fonts/msyh.ttc')
    font=ImageFont.truetype(str(font_path),20) if font_path.exists() else ImageFont.load_default()
    rows=(len(files)+columns-1)//columns
    result=Image.new('RGB',(thumb[0]*columns,(thumb[1]+38)*rows),'#15181b')
    d=ImageDraw.Draw(result)
    for i,(file,title) in enumerate(files):
        x,y=(i%columns)*thumb[0],(i//columns)*(thumb[1]+38)
        result.paste(Image.open(file).convert('RGB').resize(thumb,Image.Resampling.LANCZOS),(x,y))
        d.text((x+12,y+thumb[1]+6),title,font=font,fill='#e6cc95')
    result.save(dest,quality=90)

def main():
    upload=OUT/'upload'; videos=OUT/'videos'; records=OUT/'records'; previews=OUT/'previews'
    for p in [upload,videos,records,previews]: p.mkdir(parents=True,exist_ok=True)
    for family,name in FAMILIES:
        record=json.loads((records/(family+'.json')).read_text(encoding='utf-8'))
        appearance=record['configuration']['appearance']
        if record['buildProfile']!='test' or record['errors'] or not record['mainUnchanged'] or record['result']['level']!=20 or not record['result']['kills'] or record['area']!='H14' or record.get('panels',{}).get('area')!='H14' or record['result'].get('movedDistance',0)<20 or not appearance['hidden'] or not any(h['id']=='dante' and h['selected'] for h in appearance['hairstyles']):
            raise RuntimeError('Recording is not ready: '+family)
        export(videos/'raw'/(family+'.webm'),videos/(family+'-Lv20-combat.mp4'))
        export(videos/'raw'/(family+'-panels.webm'),videos/(family+'-Lv20-panels.mp4'))
        print('Encoded',family,flush=True)
    export(videos/'raw'/'WORLD-exploration.webm',videos/'WORLD-exploration.mp4')

    # Readable official names come from the game; no captions or overlays are burned in.
    segments=[(family,.35,13.0) for family,_ in FAMILIES]
    concat=[]
    for family,start,length in segments:
        clip=records/f'edit-combat-{family}.mp4'
        export(videos/(family+'-Lv20-combat.mp4'),clip,start,length)
        concat.append(clip)
    panel_segments=[]
    for family,shot,length in [('BOW','artifact',2.4),('BOW','artifact-effect',2.4),('BOW','legendary',2.4),('BOW','legendary-effect',2.4),('WAR','attributes',2.4),('FIR','checks',2.4)]:
        panel=json.loads((records/(family+'-panels.json')).read_text(encoding='utf-8'))
        take=next(x for x in panel['panels']['timeline'] if x['name']==shot)
        if panel['errors'] or not panel['mainUnchanged'] or any(x.get('nonOverlapping') is False for x in panel['panelChecks']):
            raise RuntimeError('Panel validation failed: '+family)
        start=take['start']+(.05 if shot.endswith('-effect') else .8);length=min(length,take['end']-start-.1)
        clip=records/f'edit-panel-{family}-{shot}.mp4';export(videos/(family+'-Lv20-panels.mp4'),clip,start,length);concat.append(clip)
        panel_segments.append((family,shot,start,length))
    list_file=records/'concat.txt';list_file.write_text('\n'.join("file '"+str(p).replace('\\','/')+"'" for p in concat),encoding='utf-8')
    reel=videos/'SwordAndFire-Lv20-four-classes.mp4'
    run(['-y','-f','concat','-safe','0','-i',list_file,'-vf','fps=30,format=yuv420p','-c:v','h264_nvenc','-preset','p5','-b:v','14M','-maxrate','18M','-bufsize','28M','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',reel])
    shutil.copy2(reel,upload/'01-four-classes-gameplay.mp4')

    selected=[('BOW-volley.jpg','02-archer-combat.jpg','逐风弓术 · 万箭齐发'),('WAR-4_2.jpg','03-warrior-combat.jpg','破军战技 · 近战'),('THU-4_2.jpg','04-thunder-combat.jpg','雷霆秘术 · 连锁'),('FIR-4_2.jpg','05-fire-combat.jpg','烈焰秘术 · 范围群攻'),('BOW-artifact.jpg','06-character-equipment.jpg','神器 · 王庭的逐星'),('FIR-checks.jpg','07-skill-ranks.jpg','满阶技能'),('THU-profession.jpg','08-professions.jpg','四种职业'),('BOW-attributes.jpg','09-character-attributes.jpg','人物属性'),('BOW-legendary.jpg','10-legendary-equipment.jpg','传奇 · 逐月之弦'),('BOW-artifact-effect.jpg','11-artifact-effect.jpg','神器专属效果')]
    loading=('game-loading.jpg','01-loading-screen.jpg','游戏加载界面 · 实际载入进度')
    if (OUT/'screenshots'/loading[0]).exists(): selected.insert(0,loading)
    for source,target,title in selected: shutil.copy2(OUT/'screenshots'/source,upload/target)
    for name in ['icon-512.png','cover-landscape-1920x1080.jpg','cover-square-1440x1440.jpg']:shutil.copy2(OUT/'branding'/name,upload/name)
    board([(upload/target,title) for _,target,title in selected],previews/'selected-materials.jpg')
    board([(upload/target,title) for source,target,title in selected if source in ['BOW-volley.jpg','WAR-4_2.jpg','THU-4_2.jpg','FIR-4_2.jpg']],previews/'four-classes.jpg')
    for family,name in FAMILIES:
        board([(OUT/'screenshots'/f'{family}-{stamp}.jpg',f'{name} · {stamp.replace("_", ".")}s') for stamp in ['1_3','4_2','7_8','11_5']],previews/(family+'-combat.jpg'))

    files=[]
    for file in sorted(upload.iterdir()):
        entry={'path':file.relative_to(OUT).as_posix(),'bytes':file.stat().st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
        if file.suffix=='.mp4':
            entry.update(probe(file));entry['technicalPass']=entry['h264'] and entry['aac'] and entry['fullHD'] and entry['fps30'] and 15<entry['seconds']<120 and entry['bytes']<500_000_000
            run(['-v','error','-i',file,'-f','null','-']);entry['fullDecodePass']=True
        elif file.suffix.lower() in ['.jpg','.png']:
            with Image.open(file) as im:entry['dimensions']=list(im.size);im.verify()
            entry['technicalPass']=entry['bytes']<2_000_000
        files.append(entry)
    clips=[]
    for file in sorted(videos.glob('*.mp4')): clips.append({'path':file.relative_to(OUT).as_posix(),**probe(file)})
    manifest={'game':'剑与火：破晓之战','date':'2026-11-17','version':json.loads((ROOT/'package.json').read_text(encoding='utf-8'))['version'],'status':'Local review candidates. Not uploaded. Not TapTap device-certified.','setup':{'level':20,'skillRank':5,'naturalSkillBudget':False,'area':'H14','hairstyle':'dante','headgearHidden':True,'headEquipment':'A02','equipmentEnhancementCap':2,'gemTier':2,'maxOpenSocketsAtLevel20':2,'disposableContext':True,'normalSaveModified':False,'gameplayRulesModified':False,'appearanceFeatureAdded':True},'officialSources':['https://developer.taptap.cn/minigameapidoc/quick-start/guide/game-publish/material/','https://developer.taptap.cn/docs/store/release/publish/material/'],'uploadCandidates':files,'individualVideos':clips,'families':[{k:json.loads((records/(f+'.json')).read_text(encoding='utf-8'))[k] for k in ['family','name','area','mainSha256','buildProfile','recording']} for f,_ in FAMILIES]}
    manifest['editorial']={'professionOrder':[f for f,_ in FAMILIES],'combatSegments':segments,'ending':'character and skill panels','removedTail':'4-second town exploration segment reported as stuttering; raw footage retained outside selection'}
    manifest['editorial']['panelArea']='H14'
    manifest['editorial']['imageOrder']=['cover','loading','BOW','WAR','THU','FIR','equipment','skills','attributes']
    if (records/'game-loading.json').exists():manifest['loadingCapture']=json.loads((records/'game-loading.json').read_text(encoding='utf-8'))
    manifest['platformUpdates']={p.stem:json.loads(p.read_text(encoding='utf-8')) for p in records.glob('taptap-*.json')}
    if manifest['platformUpdates']:manifest['status']='Some artwork uploaded to the TapTap draft. See platformUpdates for exact uploaded, pending and ordering status. Not submitted, published or TapTap device-certified.'
    progress=manifest['platformUpdates'].get('taptap-upload-progress',{})
    if progress.get('video',{}).get('selectedInDraft'):
        manifest['status']='Release 0.3.60, artwork, nine ordered screenshots and promotional video saved to TapTap draft. See platformUpdates for qualification and platform validation status. Game review not submitted; not published or TapTap device-certified.'
    if (records/'archer-volley.json').exists():manifest['editorial']['archerScreenshot']=json.loads((records/'archer-volley.json').read_text(encoding='utf-8'))
    manifest['editorial']['panelSegments']=panel_segments
    manifest['panelCaptures']=[{k:json.loads((records/(f+'-panels.json')).read_text(encoding='utf-8'))[k] for k in ['family','mainSha256','buildProfile','panels','panelChecks']} for f,_ in FAMILIES]
    manifest['editorial']['movement']={f:json.loads((records/(f+'.json')).read_text(encoding='utf-8'))['result']['movedDistance'] for f,_ in FAMILIES}
    (OUT/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    cards=''.join(f'<figure><a href="upload/{target}"><img loading="lazy" src="upload/{target}" alt="{html.escape(title)}"></a><figcaption>{html.escape(title)}</figcaption></figure>' for _,target,title in selected)
    classes=''.join(f'<article><h3>{CLASS_LABELS[family]} · {name}</h3><video controls preload="metadata" poster="screenshots/{family}-'+('volley' if family=='BOW' else '4_2')+f'.jpg" src="videos/{family}-Lv20-combat.mp4"></video><p><a href="videos/{family}-Lv20-panels.mp4">人物／装备／技能面板片段</a> · <a href="previews/{family}-combat.jpg">查看战斗关键帧</a></p></article>' for family,name in FAMILIES)
    equipment=''.join(f'<article><h3>{CLASS_LABELS[family]} · 传奇与神器</h3><a href="screenshots/{family}-artifact.jpg"><img loading="lazy" src="screenshots/{family}-artifact.jpg" alt="{CLASS_LABELS[family]}神器装备"></a><p><a href="screenshots/{family}-artifact-effect.jpg">神器专属效果</a> · <a href="screenshots/{family}-legendary.jpg">传奇大图</a> · <a href="screenshots/{family}-legendary-effect.jpg">传奇专属效果</a></p></article>' for family,_ in FAMILIES)
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>剑与火 · 宣传素材</title><style>body{margin:0;background:#15191b;color:#e9e4da;font:16px/1.7 "Microsoft YaHei",sans-serif}main{max-width:1280px;padding:48px 24px;margin:auto}h1{font-size:34px;margin:0}h2{margin-top:48px;color:#dfbf7b}h3{margin:12px 0}p{color:#b6b6ae}a{color:#dfbf7b}video,img{width:100%;display:block;border-radius:6px}section.grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}figure{margin:0}figcaption{padding:10px 0}.note{border-left:3px solid #bc9d5b;padding:12px 20px;background:#202526}article{border-top:1px solid #343a3c;padding-top:12px}@media(max-width:720px){section.grid{grid-template-columns:1fr}main{padding:24px 16px}}</style><main><h1>剑与火：破晓之战</h1><p>固定宣传素材库 · 四职业 · H14鹰背岩林 · 20级 · 银白但丁发型</p><div class="note">本地Cocos预览录制，技能5阶为专门展示配置；装备按20级上限培养，头部装备属性保留，仅隐藏外观。尚未上传，TapTap真机复录与最终观感确认待完成。<a href="README.md">素材说明</a> · <a href="manifest.json">规格与来源清单</a></div><h2>四职业合集</h2><video controls preload="metadata" poster="branding/cover-landscape-1920x1080.jpg" src="videos/SwordAndFire-Lv20-four-classes.mp4"></video><h2>精选截图</h2><section class="grid">'''+cards+'''</section><h2>每个职业独立展示</h2><section class="grid">'''+classes+'''</section><h2>其他补充</h2><section class="grid"><figure><img src="screenshots/world-town.jpg" alt="城镇探索"><figcaption>城镇探索备用截图</figcaption></figure><figure><img src="screenshots/world-map.jpg" alt="探索地图"><figcaption>实际探索地图备用画面</figcaption></figure></section><h2>宣传封面与图标</h2><section class="grid"><img src="branding/cover-landscape-1920x1080.jpg" alt="横版宣传插画"><img src="branding/cover-square-1440x1440.jpg" alt="方形宣传插画"></section><p>宣传插画用于封面，不替代游戏画面。上传前先检查目标后台当前物料要求。</p></main></html>'''
    page=page.replace('<h2>其他补充</h2>','<h2>传奇与神器</h2><section class="grid">'+equipment+'</section><h2>其他补充</h2>')
    page=page.replace('<h2>四职业合集</h2>','<h2>宣传封面</h2><img src="branding/cover-landscape-1920x1080.jpg" alt="宣传封面"><h2>游戏加载界面</h2><img src="upload/01-loading-screen.jpg" alt="真实游戏加载界面"><h2>四职业合集</h2>')
    page=page.replace('尚未上传，TapTap真机复录与最终观感确认待完成。','部分图像已上传至TapTap草稿；包体、视频与最新截图排序的状态见来源清单。未提审或发布，TapTap真机复录待完成。')
    if progress.get('video',{}).get('selectedInDraft'):page=page.replace('部分图像已上传至TapTap草稿；包体、视频与最新截图排序的状态见来源清单。未提审或发布，TapTap真机复录待完成。','release包体、封面、九张有序截图及四职业视频已加入TapTap草稿。资质进度见来源清单；游戏版本未提审或发布，TapTap真机验收待完成。')
    (OUT/'index.html').write_text(page,encoding='utf-8')
    print(json.dumps({'uploadFiles':len(files),'technicalPass':all(f['technicalPass'] for f in files),'reel':probe(reel)},ensure_ascii=False),flush=True)

if __name__=='__main__':main()
