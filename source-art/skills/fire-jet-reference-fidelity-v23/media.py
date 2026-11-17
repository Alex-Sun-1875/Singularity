"""Compare the selected image with the unmodified compiled game's new recording."""
from pathlib import Path
import importlib.util,json,hashlib
from PIL import Image,ImageDraw
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
CACHE=ROOT/'src/.tmp/fire-jet-reference-fidelity-v23/final/FIR_04';MEDIA=HERE/'media'
spec=importlib.util.spec_from_file_location('base_media',HERE.parent/'fire-spells-design-v5/media.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
report=json.loads((CACHE/'capture.json').read_text(encoding='utf8'))
def frame(i):
 out=Image.new('RGB',(1280,758),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(24,31),'烈焰喷流 · 按选定参考纠正',27,'#f9bc77',True)
 base.text(d,(1254,31),'当前 Cocos 游戏录制',17,'#bfb3a2',anchor='rm')
 out.paste(Image.open(CACHE/f'{i:03}.jpg'),(0,58))
 age=i/30-.55;phase='法阵蓄势' if age<0 else '通透火舌竖直上喷' if age<4 else '火势逐渐回落' if age<5.8 else '消散完成'
 base.text(d,(24,712),phase,22,'#f9bc77');base.text(d,(1254,712),f'{i/30:.1f}s',18,'#bfb3a2',anchor='rm')
 base.text(d,(24,744),'五点一列 · 双环与原图曲纹 · 保留火舌空隙 · 无后期特效叠加',18,'#ded3c2')
 return out
def compare():
 out=Image.new('RGB',(1200,1050),'#191614');d=ImageDraw.Draw(out)
 base.text(d,(28,35),'烈焰喷流 · 选定参考 / 当前游戏',30,'#f9bc77',True)
 base.text(d,(28,78),'按法阵直径统一缩放，保留实际火焰形状和透明度。',20,'#bfb3a2')
 original=Image.open(HERE.parent/'fire-selected-reference-v18/user-selected-effect.jpg').convert('RGB')
 actual=Image.open(CACHE/'036.jpg').convert('RGB');p=report['info']['jetProjection']
 def crop(im,cx,cy,diameter):
  return im.crop((round(cx-diameter*.7),round(cy-diameter*1.95),round(cx+diameter*.7),round(cy+diameter*.42))).resize((504,853),Image.Resampling.LANCZOS)
 for x,title,im in [(28,'用户选定参考',crop(original,497,428,110)),(652,'当前游戏实录',crop(actual,*p['centre'],p['diameter']))]:
  base.text(d,(x,124),title,23,'#f9bc77',True);out.paste(im,(x,152))
 out.save(MEDIA/'reference-vs-game.jpg',quality=95,subsampling=0)
def verify():
 assert not report['errors'] and not report['consoleErrors']
 main=next((ROOT/'src/cocos/build/concept-2d/assets/main').glob('index.*.js'))
 assert hashlib.sha256(main.read_bytes()).hexdigest()==report['gameHash']
 jets=[s for m in report['metrics'] for s in m['ground']['active'] if s['kind']=='jets']
 assert jets and all(s['emitters']==5 and s['vertices']==20 for s in jets)
 assert not report['metrics'][-1]['ground']['active']
 lifecycle=json.loads((HERE/'runtime-lifecycle.json').read_text(encoding='utf8'));assert all(s['coreUnchanged'] for s in lifecycle)
 textures={};production=ROOT/'src/cocos/assets/resources/vfx/production';build=ROOT/'src/cocos/build/concept-2d/assets'
 for name in ['fire-ground-jets-v22','fire-jet-seal-v22']:
  source=production/(name+'.png');uuid=json.loads((production/(name+'.png.meta')).read_text(encoding='utf8'))['uuid'];expected=Image.open(source).convert('RGBA').tobytes()
  files=list(build.glob(f'*/native/{uuid[:2]}/{uuid}.*.png'));assert any(Image.open(f).convert('RGBA').tobytes()==expected for f in files)
  textures[name]=hashlib.sha256(source.read_bytes()).hexdigest()
 return{'gameHash':report['gameHash'],'nativeFrames':report['frames'],'seconds':report['frames']/30,'fiveEmitters':True,'oneFlameSurfacePerVent':True,'clearAndPauseResumePassed':True,'runtimeErrors':report['errors'],'consoleErrors':report['consoleErrors'],'sourceSha256':hashlib.sha256((ROOT/'src/cocos/assets/scripts/features/combat/runtime/FireGroundEffects.ts').read_bytes()).hexdigest(),'textures':textures,'gameplayChanges':'none','artAcceptance':'Local comparison inspected; final user acceptance pending','taptapDeviceValidation':'pending'}
if __name__=='__main__':
 checks=verify();compare();frame(36).save(MEDIA/'game-overview.jpg',quality=94)
 base.video(MEDIA/'ground-flame-reference-corrected.mp4',(frame(i) for i in range(report['frames'])),(1280,758))
 (HERE/'verification.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
 print(json.dumps(checks,ensure_ascii=False))
