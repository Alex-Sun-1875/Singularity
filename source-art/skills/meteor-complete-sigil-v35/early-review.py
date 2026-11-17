"""Compare real early seal frames with the supplied reference, without colour edits."""
from pathlib import Path
import argparse, json
from PIL import Image,ImageDraw,ImageFont,ImageOps

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
REFERENCE=ROOT/'source-art/skills/fire-reference-alignment-v32/assets/approved-reference.png'

def crop_bounds(cx,cy,radius,height,factor):
 ppm=1272/(2*height);hw=radius*ppm*1.15;hh=radius*ppm*factor*1.25
 return [max(0,round(cx-hw)),max(0,round(cy-hh)),min(2560,round(cx+hw)),min(1272,round(cy+hh))]

def main():
 p=argparse.ArgumentParser();p.add_argument('--stage',default='final');p.add_argument('--rank',type=int,default=1);args=p.parse_args()
 for empty in (False,True):
  suffix='-empty' if empty else '';folder=HERE/f'{args.stage}{suffix}-r{args.rank}';early=folder/'early'
  seal=json.loads((early/'FIR_02-seal-preview.json').read_text(encoding='utf8'));flight=json.loads((early/'FIR_02-flight-60.json').read_text(encoding='utf8'))
  body=flight['meteor']['active'][0];target=body['screen']['target'];cx=target['x'];cy=1272-target['y']
  cue=next(c for c in seal['native']['cues'] if c['kind']=='drop' and c['skillId']=='FIR_02');radius=cue['geometry']['radiusMetres']
  bounds=crop_bounds(cx,cy,radius,seal['cameraHeight'],seal['cameraGroundVerticalFactor'])
  current=Image.open(early/'FIR_02-seal-preview.jpg').convert('RGB').crop(bounds);current.save(early/'FIR_02-seal-preview-crop.jpg',quality=95,subsampling=0)
  old_folder=ROOT/f'source-art/skills/meteor-ignition-glow-v34/final{suffix}-r{args.rank}';old_report=json.loads((old_folder/'capture.json').read_text(encoding='utf8'));old_shot=json.loads((old_folder/'FIR_02.json').read_text(encoding='utf8'))
  cast=next(e for e in old_shot['events'] if e['type']=='skill_cast' and e.get('skillId')=='FIR_02');old_metric=min(old_shot['metrics'],key=lambda m:abs(m['time']-cast['time']-.2))
  old_body=next(b for m in old_shot['metrics'] for b in m['meteor']['active'] if b.get('screen'));old_target=old_body['screen']['target'];old_cy=1272-old_target['y']
  old_bounds=crop_bounds(old_target['x'],old_cy,cast['geometry']['radiusMetres'],old_report['info']['cameraHeight'],old_report['info']['cameraGroundVerticalFactor'])
  old_image=Image.open(ROOT/old_report['cache']/'FIR_02'/f'{old_metric["frame"]:03}.jpg').convert('RGB').crop(old_bounds)
  reference_bounds=[220,830,590,1000];reference=Image.open(REFERENCE).convert('RGB').crop(reference_bounds)
  board=Image.new('RGB',(1560,440),'#1d1916');draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',20);small=ImageFont.truetype('C:/Windows/Fonts/msyh.ttc',16)
  draw.text((18,16),'原稿图片 · 法阵局部',font=font,fill='#efbb7f');board.paste(reference,(75,169))
  for x,title,im,centre_y,roi in [(520,'v34 · 上轮实际截图',old_image,old_cy,old_bounds),(1040,'v35 · 当前实际截图',current,cy,bounds)]:
   draw.text((x+18,16),title,font=font,fill='#efbb7f');scale=370/im.width;im=im.resize((370,round(im.height*scale)),Image.Resampling.LANCZOS);board.paste(im,(x+75,round(250-(centre_y-roi[1])*scale)))
  draw.text((18,408),'圈宽接近原稿 · 保留各自透视 · 仅裁切/等比缩放，未改色或亮度',font=small,fill='#cfc3b5')
  path=early/'FIR_02-seal-colour-three-way.jpg';board.save(path,quality=95,subsampling=0)
  evidence={'referenceSource':str(REFERENCE.relative_to(ROOT)),'referenceCropBounds':reference_bounds,'oldActualCompiledSha256':old_report['gameHash'],'oldActualFrame':old_metric['frame'],'oldActualCropBounds':old_bounds,
   'currentActualFrame':seal['frame'],'currentActualCastAge':seal['castAge'],'currentActualCropBounds':bounds,'currentActualSource':'FIR_02-seal-preview.jpg','processing':'Only crop and uniform scaling, each original perspective preserved. No colour or brightness adjustment.'}
  (early/'FIR_02-seal-colour-three-way.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  rear=current.crop((0,0,current.width,round(cy-bounds[1]+10)));rear.save(early/'FIR_02-seal-rear-crop.jpg',quality=95,subsampling=0)
  old_rear=old_image.crop((0,0,old_image.width,round(old_cy-old_bounds[1]+10)))
  original_rear=Image.open(REFERENCE).convert('RGB').crop((216,821,578,905))
  rear_board=Image.new('RGB',(1800,510),'#1d1916');rear_draw=ImageDraw.Draw(rear_board)
  for index,(title,image) in enumerate([('原稿后方 · 原有陨石遮挡保留',original_rear),('v34 · 实际后方',old_rear),('v35 · 实际后方',rear)]):
   rear_draw.text((index*600+16,16),title,font=font,fill='#efbb7f');image=ImageOps.contain(image,(570,390),Image.Resampling.LANCZOS);rear_board.paste(image,(index*600+15,70+(390-image.height)//2))
  rear_draw.text((16,480),'仅裁切/等比缩放 · 各自原透视/原明暗 · 完整性以实际纹路判断',font=small,fill='#cfc3b5')
  rear_board.save(early/'FIR_02-seal-rear-three-way.jpg',quality=95,subsampling=0)
  previous=HERE/f'final{suffix}-r{args.rank}'
  if args.stage!='final' and (previous/'capture.json').exists():
   before_report=json.loads((previous/'capture.json').read_text(encoding='utf8'));before_shot=json.loads((previous/'FIR_02.json').read_text(encoding='utf8'))
   before_cast=next(event for event in before_shot['events'] if event['type']=='skill_cast' and event.get('skillId')=='FIR_02')
   before_metric=min(before_shot['metrics'],key=lambda metric:abs(metric['time']-before_cast['time']-.2))
   before_image=Image.open(ROOT/before_report['cache']/'FIR_02'/f"{before_metric['frame']:03}.jpg").convert('RGB').crop(bounds)
   comparison=Image.new('RGB',(1600,820),'#1d1916');comparison_draw=ImageDraw.Draw(comparison)
   for offset,title,image in [(0,'v35 r1 · 修改前真实预警',before_image),(800,'v35 r2 · 当前真实预警',current)]:
    comparison_draw.text((offset+16,18),title,font=font,fill='#efbb7f');image=ImageOps.contain(image,(760,690),Image.Resampling.LANCZOS);comparison.paste(image,(offset+20,70+(690-image.height)//2))
   comparison_draw.text((16,786),'同一默认镜头与固定裁区 · 原像素明暗/透视 · 仅裁切与等比缩放',font=small,fill='#cfc3b5')
   comparison.save(early/'FIR_02-seal-r1-vs-r2-native.jpg',quality=95,subsampling=0)
   (early/'FIR_02-seal-r1-vs-r2-native.json').write_text(json.dumps({'beforeCompiledSha256':before_report['gameHash'],'beforeFrame':before_metric['frame'],'currentFrame':seal['frame'],'sharedNativeCropBounds':bounds,'processing':'Same fixed native crop, uniform resize only. No colour, brightness or perspective changes.'},ensure_ascii=False,indent=2)+'\n',encoding='utf8')
  print(path)

if __name__=='__main__':main()
