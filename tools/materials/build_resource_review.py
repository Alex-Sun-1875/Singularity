"""Assemble a portable local review of actual texture files, not game UI."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[2]
BASE = ROOT / 'assets/materials/chapter-one-v3'
OUTPUT = BASE / 'review'

NAMES = {'wood_planks_grey': '灰褐木板', 'cobblestone_floor_08': '灰米铺石',
         'leafy_grass': '绿叶草地', 'forest_ground_06': '林间泥土',
         'rock_boulder_dry': '自然灰岩', 'Fabric082A': '中性平织布', 'Grass007': '橄榄阔叶草地'}

TEMPLATE = r'''<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>剑与火 · 第一章资源审阅</title><style>
:root{color-scheme:dark;--bg:#141311;--panel:#211e19;--line:#67533a;--text:#e4d8c1;--muted:#ad9e85;--gold:#bda071}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.6 "Microsoft YaHei",sans-serif}
a{color:var(--gold);text-underline-offset:4px}button,select{font:inherit;color:var(--text);background:#29251e;border:1px solid var(--line);border-radius:2px;min-height:44px;padding:8px 14px;cursor:pointer}
button:hover,select:hover{border-color:var(--gold)}button:focus-visible,select:focus-visible,a:focus-visible{outline:2px solid #d0b377;outline-offset:3px}button[aria-pressed=true]{background:#434a33;border-color:#a39a68}button:disabled{opacity:.4;cursor:default}
header,main,footer{max-width:1440px;margin:auto;padding:24px 32px}header{border-bottom:1px solid var(--line);display:flex;justify-content:space-between;gap:24px;align-items:end}h1,h2{font-family:SimSun,serif;font-weight:400;line-height:1.3;margin:0 0 12px}h1{font-size:32px}h2{font-size:25px}.eyebrow{font-size:13px;letter-spacing:2px;color:var(--muted)}p{margin:8px 0}.muted{color:var(--muted)}.links{display:flex;gap:20px;flex-wrap:wrap;font-size:14px}
.layout{display:grid;grid-template-columns:minmax(420px,1.3fr) minmax(320px,1fr);gap:28px;margin:20px 0 40px}.stage{background:#1d1c19;border:1px solid var(--line);padding:20px}.controls{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}.tile{width:100%;aspect-ratio:1;background-repeat:repeat;background-size:50% 50%;position:relative;border:1px solid #8e8068}.tile-label{position:absolute;top:12px;left:12px;background:#151411e8;padding:5px 10px;font-size:13px;pointer-events:none}.tile.grid:after{content:"";position:absolute;inset:0;pointer-events:none;background-image:linear-gradient(90deg,#e4d8c199 1px,transparent 1px),linear-gradient(#e4d8c199 1px,transparent 1px);background-size:var(--tile-step,50%) var(--tile-step,50%)}
.catalog{display:grid;grid-template-columns:1fr 1fr;gap:12px;align-content:start}.material{padding:0;text-align:left;overflow:hidden;border-color:#534631;background:var(--panel)}.material img{display:block;width:100%;aspect-ratio:1.55;object-fit:cover}.material span{display:block;padding:9px 12px}.details{grid-column:1/-1;background:var(--panel);padding:18px;border-top:1px solid var(--line);font-size:14px}.details dl{display:grid;grid-template-columns:90px 1fr;gap:6px;margin:10px 0}.details dt{color:var(--muted)}.details dd{margin:0;overflow-wrap:anywhere}.note{border-left:2px solid var(--line);padding:8px 16px;color:var(--muted);font-size:14px}
.wide{width:100%;height:auto;display:block;border:1px solid var(--line);margin:16px 0 24px}.section{padding:26px 0;border-top:1px solid var(--line)}iframe{width:100%;height:1040px;background:var(--panel);border:1px solid var(--line)}footer{font-size:13px;color:var(--muted);border-top:1px solid var(--line)}
@media(max-width:850px){header{display:block}header,main,footer{padding:20px}.layout{grid-template-columns:1fr}.links{margin-top:12px}.stage{padding:12px}h1{font-size:27px}iframe{height:1450px}.material span{font-size:14px}}
</style></head><body>
<header><div><div class="eyebrow">剑与火 / 白枝第七远征</div><h1>第一章 · 资源审阅</h1><p class="muted">设计方向：深色界面、细金属边、自然地表、冷暖分区</p></div><nav class="links"><a href="../material-direction-board-v2.png">材质方向稿</a><a href="#pbr">中性光材质</a><a href="#ui">界面独立切图</a></nav></header>
<main><p class="note">这是独立资源预览，不是游戏画面。以下 PBR 候选使用同一来源的配套通道；AI 色彩图作为设计参考保留，没有拼接成假 PBR 材质。</p>
<div class="layout"><section class="stage"><h2 id="title">材质</h2><div class="controls" id="channels"></div><div class="tile" id="tile"><span class="tile-label" id="tile-label">2 × 2 重复</span></div><div class="controls"><label>重复数量 <select id="repeat"><option value="1">1 × 1</option><option value="2" selected>2 × 2</option><option value="4">4 × 4</option></select></label><button id="guide" aria-pressed="false">接边参考线</button><a id="original" target="_blank" rel="noopener">查看原图</a></div><p class="muted" style="font-size:13px">重复数量用于观察接边；实际铺设尺寸见右侧来源记录。参考线可关闭。</p></section><aside class="catalog" id="catalog"><section class="details" id="details"></section></aside></div>
<section class="section" id="pbr"><h2>同一中性灯光下的材质响应</h2><p class="muted">每块平面 2 × 2 米，短线为 50 厘米。布料0.25m与Grass007地表2m的纹理覆盖尺度仅为设计建议，官方物理尺度未知。球体用于观察法线与粗糙度；AO 单独审阅，不烘进底色。</p><img class="wide" src="matched-pbr-neutral.png" alt="Blender中性灯光下的真实配套PBR材质平面与球体；布料和Grass007纹理尺度为设计建议"><p class="note">Blender 离线渲染证明源材质通道能够共同工作；还不能替代 Cocos 镜头、材质转换、mip 和手机性能验收。</p></section>
<section class="section" id="ui"><h2>独立界面素材</h2><p class="muted">细框、按钮状态、状态条与遮罩独立分层；文字和图标不烘焙进底纹。</p><p><a href="../ui-kit/preview.html" target="_blank" rel="noopener">打开原尺寸状态与分层预览</a></p><img class="wide" src="../ui-kit/ui-kit-preview.png" alt="原创细暗铜界面17张独立素材的状态与透明分层预览"><p class="note">此处按页面宽度缩放资源陈列，不代表手机HUD。手机布局与触控仍须在引擎里独立验收。</p></section>
</main><footer>来源、版本、许可及 SHA-256 随资源保存。Powered by Poly Haven · <a href="https://polyhaven.com/license" target="_blank" rel="noopener">Poly Haven CC0</a> · <a href="https://docs.ambientcg.com/license/" target="_blank" rel="noopener">ambientCG CC0</a>。未修改游戏生产资源。</footer>
<script id="materials" type="application/json">__MATERIAL_DATA__</script><script>
const materials=JSON.parse(document.querySelector('#materials').textContent),names={albedo:'底色',normal:'法线',roughness:'粗糙度',ao:'环境遮蔽'},tile=document.querySelector('#tile');let selected=0,channel='albedo';
function path(m,map){return '../'+m.group+'/'+map.file}function mapFor(m,role){return m.maps.find(x=>x.role===role)}
function render(){const m=materials[selected],map=mapFor(m,channel);document.querySelector('#title').textContent=m.name;tile.style.backgroundImage='url("'+path(m,map)+'")';document.querySelector('#original').href=path(m,map);const n=document.querySelector('#repeat').value;tile.style.backgroundSize=(100/n)+'% '+(100/n)+'%';tile.style.setProperty('--tile-step',(100/n)+'%');document.querySelector('#guide').disabled=n==='1';tile.classList.toggle('grid',n!=='1'&&document.querySelector('#guide').getAttribute('aria-pressed')==='true');document.querySelector('#tile-label').textContent=names[channel]+' · '+n+' × '+n+' 重复';document.querySelectorAll('[data-material]').forEach((b,i)=>b.setAttribute('aria-pressed',i===selected));document.querySelector('#channels').replaceChildren(...Object.entries(names).map(([key,label])=>{const b=document.createElement('button');b.textContent=label;b.disabled=!mapFor(m,key);b.setAttribute('aria-pressed',channel===key);b.onclick=()=>{channel=key;render()};return b}));const detail=document.querySelector('#details');detail.replaceChildren();let heading=document.createElement('strong');heading.textContent='来源与规格';detail.append(heading);let dl=document.createElement('dl');for(const [label,value]of [['源材质',m.sourceAsset],['平铺尺寸',m.tileMetres?m.tileMetres.map(v=>Number(v.toFixed(2))).join(' × ')+' m':'官方未提供，待量测'],['本图尺寸',map.size.join(' × ')+' px'],['色彩空间',map.colorSpace],['法线约定',m.normalConvention],['许可',m.license||'CC0-1.0']]){let dt=document.createElement('dt'),dd=document.createElement('dd');dt.textContent=label;dd.textContent=value;dl.append(dt,dd)}detail.append(dl);let a=document.createElement('a');a.href=m.sourcePage;a.textContent='官方资源页面';a.target='_blank';a.rel='noopener';detail.append(a);for(const note of [m.notes,m.visualReview,m.previewScaleNote]){if(!note)continue;let p=document.createElement('p');p.className='muted';p.textContent=note;detail.append(p)}if(!m.tileMetres&&m.previewTileMetres){let p=document.createElement('p');p.className='note';p.textContent='本图纹理预览尺度 '+m.previewTileMetres.join(' × ')+' m，仅为设计建议，不是官方测量。';detail.append(p)}}
const catalog=document.querySelector('#catalog'),details=document.querySelector('#details');materials.forEach((m,i)=>{const b=document.createElement('button');b.className='material';b.dataset.material=i;const img=document.createElement('img');img.src=path(m,mapFor(m,'albedo'));img.alt=m.name+'底色原图';const span=document.createElement('span');span.textContent=m.name;b.append(img,span);b.onclick=()=>{selected=i;if(!mapFor(m,channel))channel='albedo';render()};catalog.insertBefore(b,details)});document.querySelector('#repeat').onchange=render;document.querySelector('#guide').onclick=e=>{const on=tile.classList.toggle('grid');e.currentTarget.setAttribute('aria-pressed',on)};render();
</script></body></html>'''


def main():
    materials = []
    for group in ['pbr-library', 'terrain-library']:
        file = BASE / group / 'manifest.json'
        if not file.exists():
            continue
        data = json.loads(file.read_text(encoding='utf8'))
        for entry in data['materials']:
            if not entry.get('selected', True):
                continue
            item = {**entry, 'group': group,
                    'name': entry.get('label') or NAMES.get(entry.get('sourceAsset'), entry['id'])}
            materials.append(item)
    if not materials:
        raise ValueError('No source material manifests')
    OUTPUT.mkdir(exist_ok=True)
    payload = json.dumps(materials, ensure_ascii=False).replace('</', '<\\/')
    (OUTPUT / 'index.html').write_text(TEMPLATE.replace('__MATERIAL_DATA__', payload), encoding='utf8')
    print('Built resource review:', len(materials), 'complete material candidates')


if __name__ == '__main__':
    main()
