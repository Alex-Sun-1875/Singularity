"""Typeset matched Cocos frames. All moving pixels inside the viewport come from the game."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
from functools import lru_cache
from fractions import Fraction

from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
CACHE = HERE.parents[2] / "src/.tmp/cocos-motion-study-v2"
MEDIA = HERE / "media"
BASE = CACHE / "native"
FPS = 30
FONTS = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts"
PAPER = "#171a19"
TEXT = "#eeeae0"
MUTED = "#b6b8ab"
LINE = "#464a42"
COLOURS = {"战士": "#dfbd85", "弓系": "#a7c6a0", "火系": "#efa069", "雷系": "#aeaefa"}
# Family, display name, live caption, proposed caption, review note
SHOTS = {
    "BASIC_WAR": ("战士","普攻三连","1.85 米  /  110°","2.65 米  /  48°","正面靶距 2.53 米，近侧靶距 1.63 米、偏轴 44°。留意三次受击的是哪一个。"),
    "WAR_01": ("战士","断空斩","3.00 米  /  110°","3.75 米  /  40°","第一刀由下向上，第二刀回切。两次命中沿用同一名锁定目标。"),
    "WAR_02": ("战士","破军突袭","同时交叉","突进停步 · 先挑后压","冲到目标前先挑出第一道刀痕，再向下回切，交点落在同一个命中位置。"),
    "WAR_04": ("战士","裂地审判","落点重击","刃纹预警 · 落点重击","圆形重击先亮出剑刃纹样，落地这一拍再展开裂痕。"),
    "WAR_05": ("战士","破晓裁决","4.375 米  /  120°","5.03 米  /  62°","前两击往返，末击向下压。三个真实伤害段对应三次发力。"),
    "BOW_01": ("弓系","穿云箭","短尾迹","延长收尖的箭迹","看箭头先脱弦，再看已飞过的轨迹。单箭命中正面的目标。"),
    "BOW_05": ("弓系","万箭齐发","分批箭阵","分批箭阵 · 分开的箭路","每支箭保留独立的箭头和收尖尾迹，按现有波次依次抵达敌阵。"),
    "BOW_06": ("弓系","缚足陷阱","放置陷阱","箭羽纹预警","环带刻短羽，圈内用拉满的弓和搭上的箭标出陷阱。"),
    "FIR_01": ("火系","赤焰枪","直线火弹","火枪尖锋 · 飞行余痕","起手向前送出火枪，前锋与尾焰沿同一条弹道运动。"),
    "FIR_02": ("火系","焚星坠落","常规主动技能","终极技能 · 0.78 秒前摇","先看地上的双环焰纹，再看陨星斜落、触地和外扩的火浪。"),
    "THU_02": ("雷系","连锁雷弧","分段闪现","连续粗主弧","主弧从手部连到首个命中点，再从该目标跳到下一名敌人。"),
    "THU_05": ("雷系","万钧雷潮","多次放电","雷纹预警 · 粗主链","每一拍都沿实际命中关系放电，地面残光弱于空中的主链。"),
}


@lru_cache(maxsize=30)
def font(size, bold=False):
    return ImageFont.truetype(str(FONTS / ("msyhbd.ttc" if bold else "msyh.ttc")), size)


def label(draw, xy, value, size, fill=TEXT, bold=False, anchor="lm"):
    draw.text(xy, value, font=font(size, bold), fill=fill, anchor=anchor)


def report(variant, shot):
    return json.loads((BASE / variant / shot / "capture.json").read_text(encoding="utf-8"))


def source(variant, shot, frame):
    with Image.open(BASE / variant / shot / f"{frame:03d}.jpg") as image:
        return image.convert("RGB")


def header(shot, compare):
    family,name,old,new,hint = SHOTS[shot]
    width,height = (1920,628) if compare else (960,572)
    frame = Image.new("RGB",(width,height),PAPER)
    d=ImageDraw.Draw(frame)
    if compare:
        d.rectangle((24,18,27,45), fill=COLOURS[family])
        label(d,(42,31),family+"  /  "+name,31,bold=True)
        label(d,(1894,32),"剑与火   ·   3D 战斗动效",20,MUTED,anchor="rm")
        for x,tag,caption,color in [(24,"现版",old,MUTED),(968,"调整稿",new,COLOURS[family])]:
            label(d,(x,73),tag,20,color,True)
            label(d,(x+88,73),caption,19)
        d.line((24,560,1896,560),fill=LINE,width=1)
        label(d,(24,589),hint,22)
        label(d,(1895,588),"同机位   /   原速",17,MUTED,anchor="rm")
    else:
        label(d,(18,24),family+"  /  "+name,24,bold=True)
        label(d,(942,24),new,17,COLOURS[family],anchor="rm")
        label(d,(18,547),hint,17)
    return frame


def compose(shot, index, compare, base):
    frame=base.copy()
    if compare:
        for x,variant in [(24,"current"),(968,"design")]:
            panel=source(variant,shot,index).resize((928,454),Image.Resampling.LANCZOS)
            frame.paste(panel,(x,96))
    else:
        frame.paste(source("design",shot,index),(0,49))
    return frame


def make_video(filename, ids, compare=True):
    import av
    chapters=[]
    offset=0
    for shot in ids:
        n=report("design",shot)["frames"]
        chapters.append({"id":len(chapters),"time_base":Fraction(1,FPS),"start":offset,"end":offset+n,
                         "metadata":{"title":SHOTS[shot][0]+" · "+SHOTS[shot][1]}})
        offset+=n
    with av.open(str(MEDIA/filename),mode="w",format="mp4",options={"movflags":"+faststart"}) as movie:
        movie.set_chapters(chapters)
        stream=movie.add_stream("libx264",rate=FPS)
        stream.width,stream.height=(1920,628) if compare else (960,572)
        stream.pix_fmt="yuv420p"
        stream.codec_context.thread_count=3
        stream.options={"preset":"veryfast","crf":"16"}
        frame_number=0
        for shot in ids:
            template=header(shot,compare)
            for i in range(report("design",shot)["frames"]):
                frame=av.VideoFrame.from_image(compose(shot,i,compare,template))
                frame.pts=frame_number
                frame.time_base=Fraction(1,FPS)
                for packet in stream.encode(frame):
                    movie.mux(packet)
                frame_number+=1
        for packet in stream.encode():
            movie.mux(packet)


def make_gif():
    shot="BASIC_WAR"
    base=header(shot,True)
    # One shared palette prevents the terrain shimmering between frames.
    samples=Image.new("RGB",(520,170*4))
    for j,i in enumerate([0,14,25,40]):
        samples.paste(compose(shot,i,True,base).resize((520,170)),(0,170*j))
    palette=samples.quantize(256,method=Image.Quantize.MEDIANCUT)
    frames=[]
    for i in range(report("design",shot)["frames"]):
        image=compose(shot,i,True,base).resize((1152,377),Image.Resampling.LANCZOS)
        frames.append(image.quantize(palette=palette,dither=Image.Dither.NONE))
    periods=[(round((i+1)*100/FPS)-round(i*100/FPS))*10 for i in range(len(frames))]
    frames[0].save(MEDIA/"warrior-combo.gif",save_all=True,append_images=frames[1:],duration=periods,loop=0,optimize=False,disposal=1)


def seals():
    allpaths=json.loads(subprocess.check_output(["node",str(HERE/"ring-paths.cjs")],text=True,encoding="utf-8"))
    sheet=Image.new("RGB",(1600,908),PAPER)
    d=ImageDraw.Draw(sheet)
    label(d,(36,42),"技能范围圈",36,bold=True)
    label(d,(1564,45),"正视纹样   /   3D 施放前一刻",21,MUTED,anchor="rm")
    d.line((36,82,1564,82),fill=LINE)
    names=["断刃刻痕","箭羽倒钩","分叉焰舌","折线雷纹"]
    for n,(shot,lines) in enumerate(allpaths.items()):
        x=36+(n%2)*774;y=105+(n//2)*387
        family,name=SHOTS[shot][:2]
        label(d,(x,y+19),family+"  /  "+name,25,COLOURS[family],True)
        label(d,(x+742,y+19),names[n],18,MUTED,anchor="rm")
        # Show the same paths that Cocos consumes, on a neutral flat swatch.
        canvas=Image.new("RGB",(648,795),"#242724")
        scale=284
        for line in lines:
            layer=Image.new("RGBA",canvas.size)
            line_draw=ImageDraw.Draw(layer)
            pts=[(324+px*scale,397-pz*scale) for px,pz in line["points"]]
            colour=tuple(bytes.fromhex(line["colour"][1:]))+(line["alpha"],)
            line_draw.line(pts,fill=colour,width=max(2,round(line["width"]*scale)),joint="curve")
            canvas.paste(layer,mask=layer.getchannel("A"))
        sheet.paste(canvas.resize((216,265),Image.Resampling.LANCZOS),(x,y+50))
        event=report("design",shot)
        release=next(e["time"] for e in event["events"] if e["type"]=="skill_release")
        cast=next(e["time"] for e in event["events"] if e["type"]=="skill_cast")
        i=round((cast + .62*(release-cast))*FPS)
        if shot=="FIR_02":i=16
        img=source("design",shot,i)
        # Keep the entire floor pattern visible; use the real captured viewport without cropping it.
        panel=img.resize((522,256),Image.Resampling.LANCZOS)
        sheet.paste(panel,(x+220,y+54))
        d.line((x,y+335,x+742,y+335),fill=LINE)
    sheet.save(MEDIA/"range-rings.jpg",quality=94,subsampling=0)


def verify_sources(ids):
    for shot in ids:
        pair=[report(v,shot) for v in ("current","design")]
        a,b=pair
        assert a["info"]["origin"]==b["info"]["origin"] and a["info"]["targets"]==b["info"]["targets"],shot
        assert a["buildSHA256"]==b["buildSHA256"] and a["frames"]==b["frames"],shot
        for item in pair:
            assert not item["errors"] and item["info"]["renderer"]=="Actors" and item["info"]["player"]["skeletons"],shot
            assert len(list((BASE/item["variant"]/shot).glob("*.jpg")))==item["frames"],shot
            assert any(e["type"]=="skill_release" for e in item["events"]) or shot=="BASIC_WAR",shot
    assert [e["id"] for e in report("current","BASIC_WAR")["events"] if e["type"]=="hit"]==["study-target-1"]*3
    assert [e["id"] for e in report("design","BASIC_WAR")["events"] if e["type"]=="hit"]==["study-target-0"]*3


def provenance():
    verify_sources(SHOTS)
    flight=report("design","FIR_02")["flightSamples"]
    assert len(flight)>=3 and all(s["cameraBound"] for s in flight)
    travel=[b-a for a,b in zip(flight[0]["head"],flight[-1]["head"])]
    axis=flight[-1]["axis"]
    from math import hypot
    alignment=sum(a*b for a,b in zip(travel,axis))/(hypot(*travel)*hypot(*axis))
    assert alignment>.99
    shots=[]
    offset=0
    for shot in SHOTS:
        data={"skill":shot,"name":SHOTS[shot][1],"startFrame":offset}
        for variant in ["current","design"]:
            rec=report(variant,shot)
            hits=[{"second":e["time"],"id":e["id"]} for e in rec["events"] if e["type"]=="hit"]
            data[variant]={"frames":rec["frames"],"geometry":rec["info"].get("skillGeometry",rec["info"]["geometry"]),"ultimate":rec["info"]["loadout"]["ultimate"],
                           "targets":rec["info"]["targets"],"hitEvents":hits,"clips":rec["clips"],"observed":rec["stats"]}
        offset+=data["design"]["frames"]
        shots.append(data)
    paths=sorted(p for p in MEDIA.iterdir() if p.is_file())
    inputs=sorted(p for p in HERE.iterdir() if p.suffix in {".ts",".cjs",".js",".py"})
    hashes=lambda paths:{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    sample=report("current","BASIC_WAR")
    data={"project":"剑与火","source":"Current local Cocos Web export","bundle":sample["gameMain"],"bundleSHA256":sample["buildSHA256"],
          "scene":sample["info"]["scene"],"view":"native 3D","nativePlayerProfile":sample["info"]["player"]["profile"],
          "viewport":sample["info"]["canvas"],"fps":30,"simulationFPS":60,"frames":offset,
          "captureResult":"Rendered both variants with real Cocos actors, materials, collision and combat events",
          "visualReview":"Representative decoded frames and illustrated range indicators inspected; awaiting user art direction",
          "deliveryState":"Review-only recording. Candidate modules and dimension changes are limited to the recorder session.",
          "meteorProjectedTravelToCardAxisCosine":round(alignment,4),"sourceSHA256":hashes(inputs),"mediaSHA256":hashes(paths),"shots":shots}
    (HERE/"provenance.json").write_text(json.dumps(data,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")


if __name__=="__main__":
    args=argparse.ArgumentParser()
    args.add_argument("output",choices=["warrior","compare","full","rings","provenance"])
    mode=args.parse_args().output
    MEDIA.mkdir(exist_ok=True)
    if mode=="warrior":
        verify_sources(["BASIC_WAR"])
        make_gif()
    elif mode=="provenance":
        provenance()
    elif mode=="rings":
        seals()
    else:
        verify_sources(SHOTS)
        make_video("four-classes-comparison.mp4" if mode=="compare" else "four-classes-full-size.mp4",list(SHOTS),mode=="compare")
