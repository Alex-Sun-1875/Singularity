"""Evidence layout only. Pixels are actual renders / unchanged reference crops.
No image-generation, relighting, retouching, fabricated animation, or model beautification.
"""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,hashlib,subprocess,math
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'assets/studies/hero-g1-motion-study';PRE=OUT/'previews';PRE.mkdir(exist_ok=True)
font='/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'
fontb='/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'
def F(s,b=False):return ImageFont.truetype(fontb if b else font,s,index=2)
def text(draw,xy,s,size=24,color='#E4E3DB',bold=False):draw.text(xy,s,font=F(size,bold),fill=color)
def place(canvas,im,rect,fit=True):
 x,y,w,h=rect;im=im.convert('RGBA')
 if fit:
  k=min(w/im.width,h/im.height);im=im.resize((round(im.width*k),round(im.height*k)),Image.Resampling.LANCZOS)
 canvas.alpha_composite(im,(round(x+(w-im.width)/2),round(y+(h-im.height)/2)))
def trim(path):
 im=Image.open(path).convert('RGBA');return im.crop(im.getchannel('A').getbbox())
# Comparison uses original concept crop, not a new generated picture.
can=Image.new('RGBA',(1800,1260),'#202726');d=ImageDraw.Draw(can)
text(d,(48,30),'剑与火｜主角制作进度对照',38,bold=True)
text(d,(50,86),'概念决定目标；模型单独验收。本次为真实可编辑技术样板，尚未通过精细美术验收。',24,'#B9C6C1')
cols=[(40,'获批方向参考','概念图，不是模型渲染'),(630,'上一版静态研究','未验收；无骨架'),(1220,'本次绑定／材质研究','实际 Blender 渲染；仍未验收')]
for x,title,sub in cols:
 d.rounded_rectangle((x,145,x+540,953),radius=14,fill='#343B38');text(d,(x+20,162),title,28,bold=True);text(d,(x+20,207),sub,21,'#CFD4CB')
ref=Image.open(ROOT/'assets/concepts/character-direction-v1.png').crop((18,30,589,850))
place(can,ref,(60,250,500,680))
place(can,trim(ROOT/'assets/studies/player-refined/previews/player_refined_mesh.png'),(650,250,500,680))
place(can,trim(PRE/'hero_study_front.png'),(1240,250,500,680))
text(d,(48,978),'固定 32° 镜头 · 四向同一缩放 · 约 120 px 高',25,bold=True)
for i,di in enumerate(['front_right','back_right','back_left','front_left']):
 im=trim(OUT/'frames'/('hero_study__idle__'+di+'__001.png'));k=120/370;im=im.resize((round(im.width*k),120),Image.Resampling.LANCZOS);place(can,im,(60+i*170,1024,150,128),False)
 text(d,(76+i*170,1160),['右前','右后','左后','左前'][i],20,'#B9C6C1')
text(d,(810,1005),'已做：连续头部／前臂、单侧肩甲、原创 UV 材质、21 骨架待机。',23)
text(d,(810,1050),'仍缺：写实脸与发型、衣装受力褶与磨损、walk / sword 动作。',23,'#E6C795')
text(d,(810,1095),'绑定：胸腰／裤膝／披布渐变权重；多数甲片和装备单骨权重。',21,'#B9C6C1')
text(d,(810,1135),'未接入游戏，未做真机性能验证；面数与导出成功不代表质量通过。',21,'#B9C6C1')
text(d,(48,1210),'源工程与导出均保存在项目 studies 目录；获批原图、旧研究及玩法代码未覆盖。',20,'#91A19A')
can.convert('RGB').save(PRE/'hero_g1_reference_comparison.png')
# Four actual camera frames on three neutral backgrounds; no paintover.
can=Image.new('RGBA',(1536,1100),'#202726');d=ImageDraw.Draw(can);text(d,(36,25),'实际模型渲染｜方向、透明边缘与材质检查',32,bold=True)
for i,di in enumerate(['front_right','back_right','back_left','front_left']):
 x=(i%2)*768;y=92+(i//2)*500
 bg=Image.new('RGBA',(512,460),'#7C7F79' if i%2 else '#C7C6BA');im=Image.open(OUT/'frames'/('hero_study__idle__'+di+'__001.png')).convert('RGBA');im=im.resize((460,460),Image.Resampling.LANCZOS);bg.alpha_composite(im,(26,0));can.alpha_composite(bg,(x+25,y));text(d,(x+555,y+185),['右前','右后','左后','左前'][i],27,bold=True)
can.convert('RGB').save(PRE/'hero_g1_four_views.png')
# Motion frame panels. Every character pixel comes from actual per-frame Blender output.
video_frames=PRE/'video-frames';video_frames.mkdir(exist_ok=True)
metadata=[];hashes=[]
for i in range(8):
 path=OUT/'frames'/('hero_study__idle__front_right__%03d.png'%(i+1));im=Image.open(path).convert('RGBA');bbox=im.getchannel('A').getbbox();hashes.append(hashlib.sha256(path.read_bytes()).hexdigest())
 metadata.append({'file':str(path.relative_to(OUT)),'frame':i+1,'source_frame':1+6*i,'durationMs':250,'untrimmed_size':[512,512],'crop_rect':[bbox[0],bbox[1],bbox[2]-bbox[0],bbox[3]-bbox[1]],'root_anchor_untrimmed':[256,432],'root_anchor_cropped':[256-bbox[0],432-bbox[1]],'bbox':bbox,'event':None,'loop':True})
 c=Image.new('RGBA',(960,900),'#292F2D');dr=ImageDraw.Draw(c);text(dr,(38,23),'主角真实骨架待机｜未验收技术样板',30,bold=True);text(dr,(40,67),'2 秒循环 · 8 张独立渲染采样 · 不是概念图动画',22,'#BBC7C0')
 im=im.resize((768,768),Image.Resampling.LANCZOS);c.alpha_composite(im,(96,95));rx=96+384;ry=95+648
 dr.line((rx-9,ry,rx+9,ry),fill='#E8BA70',width=2);dr.line((rx,ry-9,rx,ry+9),fill='#E8BA70',width=2)
 text(dr,(38,846),'根点固定；只检验轻微呼吸。未验证行走、攻击或完整关节变形。',22,'#E6C795')
 c.convert('RGB').save(video_frames/('%03d.png'%(i+1)))
(OUT/'idle-frames.json').write_text(json.dumps({'status':'study_only_not_production','direction':'front_right','frames':metadata,'unique_render_sha256':hashes,'sample_count':8,'loop_duration_ms':2000},ensure_ascii=False,indent=2))
# Measurement, not artistic acceptance.
checks={'distinct_render_files':len(set(hashes)),'frame_count':8,'all_rgba':all(Image.open(p).mode=='RGBA' for p in (OUT/'frames').glob('*.png')),'minimum_alpha_safe_margin_px':min(min(m['bbox'][0],m['bbox'][1],512-m['bbox'][2],512-m['bbox'][3]) for m in metadata),'directions':{},'notes':'No atlas is delivered. RGBA figures below are uncompressed full-frame pixel lower bounds, not PNG size.'}
for di in ['front_right','back_right','back_left','front_left']:
 im=Image.open(OUT/'frames'/('hero_study__idle__'+di+'__001.png'));bb=im.getchannel('A').getbbox();checks['directions'][di]={'bbox':bb,'visual_height_px':bb[3]-bb[1]}
checks['full_frame_pixel_bytes_8_samples']={str(n):8*n*n*4 for n in [192,256,512]}
checks['disk_bytes_11_unique_pngs']=sum(p.stat().st_size for p in (OUT/'frames').glob('*.png'))
checks['technical_image_checks_passed']=checks['distinct_render_files']==8 and checks['minimum_alpha_safe_margin_px']>=8
(OUT/'image-validation.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
# Repeat actual two-second loop four times; no frame interpolation fabricated by optical flow.
subprocess.run(['ffmpeg','-y','-v','error','-framerate','4','-i',str(video_frames/'%03d.png'),'-vf','loop=loop=3:size=8:start=0','-t','8','-r','24','-c:v','libx264','-crf','18','-pix_fmt','yuv420p','-movflags','+faststart',str(PRE/'hero_g1_idle_preview.mp4')],check=True)
print(json.dumps(checks,ensure_ascii=False,indent=2))
