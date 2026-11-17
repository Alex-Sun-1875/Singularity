"""Create a candidate skill-row study from existing game UI assets."""
from pathlib import Path
from PIL import Image
import json
import base64

OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
THREAD=Path('C:/Users/Alexa/.codex/visualizations/2026/11/17/01a1e853-dfaa-7992-913a-6822bff2eef8')
ASSETS=OUT/'assets'
ASSETS.mkdir(exist_ok=True)
UI=ROOT/'src/cocos/assets/resources/ui'
paths={}
for index in range(1,5):
    source=UI/f'combat-relief/rpg-war-{index:02d}.png'
    image=Image.open(source).convert('RGBA')
    inset=round(min(image.size)*.047)
    image=image.crop((inset,inset,image.width-inset,image.height-inset)).resize((120,120),Image.Resampling.LANCZOS)
    paths[f'ICON{index}']=ASSETS/f'war-{index:02d}.png'
    image.save(paths[f'ICON{index}'],optimize=True)
for key,name in [('ROW','prep-skill-row-v5.png'),('FRAME','rpg-skill-icon-frame-v6.png')]:
    paths[key]=UI/'quiet-bronze'/name

fragment=(OUT/'skill-preview.template.html').read_text(encoding='utf-8')
for key,path in paths.items():
    fragment=fragment.replace('{{'+key+'}}','data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode('ascii'))
(THREAD/'skill-selection.html').write_text(fragment,encoding='utf-8')
reference=Image.open('C:/Users/Alexa/AppData/Local/Temp/codex-clipboard-c6a0ae8b-5e2a-4644-803a-54c961dc88de.png')
reference.crop((1498,671,2116,1035)).resize((618,364),Image.Resampling.LANCZOS).save(OUT/'reference-list.jpg',quality=90)
spec={
 'date':'2026-11-17','status':'candidate_pending_user_review','scope':'Skill list selection and content alignment; no runtime edits.',
 'source':'User screenshot plus existing prep-skill-row-v5 and combat-relief assets.',
 'diagnosis':[
  'SkillBook.ts sizes the visible row to hu-4 but fixes the icon at 40.',
  'The title and role use fixed vertical offsets; the secondary label can extend beyond a shortened row.',
  'PreparationControls.rowBackground adds the bright gold skill-selected skin.',
  'Gold in the shield icon communicates the defensive skill identity and is preserved.'
 ],
 'candidateLogical':{'visibleRowHeight':52,'hitHeight':52,'rowGap':8,'iconSize':36,'contentPaddingX':12,
                     'titleSize':16.5,'roleSize':11.5,'titleLineHeight':21,'roleLineHeight':16,'labelGap':1,
                     'levelColumnWidth':48,'selectionStroke':1.5,'selectionCornerLength':11},
 'selection':{'color':'#EDE4CB','shape':'Four short inset ivory corners over the existing normal row skin.',
              'qualityOrSkillIdentity':'Unchanged; no whole-icon recoloring, no bright gold selection skin.'},
 'states':{'idle':'Original warm dark row, quiet bronze edge, warm ivory title.',
           'selected':'Same geometry and typography; short ivory corners with a soft neutral inset.',
           'locked':'Keep a readable muted title, the unlock-level column and the skill icon; still browsable.'},
 'validation':{'designGeneration':'complete','userReview':'pending','cocosRuntime':'not_started','tapTapDevice':'not_started'}
}
(OUT/'design-spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'preview':str(THREAD/'skill-selection.html'),'bytes':len(fragment.encode('utf-8'))},ensure_ascii=False))
