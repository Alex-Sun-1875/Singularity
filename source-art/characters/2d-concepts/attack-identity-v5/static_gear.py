"""Complete held-weapon extraction in ORIGINAL 512x768 review coordinates.

make_equipment_mask(before, r, joints) returns a boolean gear-only mask.  Warp
this mask with the same map as the original artwork, then combine it with the
original gripping-arm mask.  Both held and exploration equipment are included.

These reviewed polygons follow each existing weapon, including dark wood,
blue-black metal, bow strings and antialiased edges.  Held silhouettes have no
RGB/material threshold.  Carried straps crossing opaque body pixels retain the
existing bounded material guard; wide old-body rectangles are never copied.
"""
from __future__ import annotations

from pathlib import Path
import json
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

SIZE = (512, 768)


def polygon(points):
    im = Image.new("L", SIZE)
    ImageDraw.Draw(im).polygon(points, fill=255)
    return np.asarray(im) > 0


def line(points, radius):
    im = Image.new("L", SIZE)
    draw = ImageDraw.Draw(im)
    points = [tuple(map(float, p)) for p in points]
    draw.line(points, fill=255, width=max(1, round(radius*2)), joint="curve")
    for x, y in points:
        draw.ellipse((x-radius, y-radius, x+radius, y+radius), fill=255)
    return np.asarray(im) > 0


def circle(center, radius):
    return line([center, center], radius)


def back_body_overlap_guard(mask,array,direction):
    """Keep narrow existing back-gear material where it crosses opaque body.

    This is only the caller-authorized overlap guard for carried straps/tubes;
    held-weapon silhouettes never pass through this colour gate.  Outside the
    torso/leg overlap all alpha pixels of the geometric equipment ROI survive.
    """
    rgb=array[...,:3].astype(int);rr,gg,bb=np.moveaxis(rgb,-1,0)
    yy,xx=np.mgrid[:768,:512]
    xlo,xhi=(185,319) if direction in ("down","up") else ((218,299) if direction=="right" else (212,305))
    body=(xx>=xlo)&(xx<=xhi)&(yy>=205)&(yy<=712)&(array[...,3]>=240)
    material=((rr-gg>4)&(gg-bb>10)&(rr>55))|((bb>rr+9)&(bb>gg+3))|((rgb.min(-1)>140)&(rgb.max(-1)-rgb.min(-1)<45))
    core=ndi.binary_opening(material&mask,iterations=1)
    supported=ndi.binary_dilation(core,iterations=2)
    return mask&(~body|supported)


def weapon_id(record):
    refs = [v["action"] for v in record.get("refs", [])]
    text = " ".join(refs)+" "+record.get("image", "")
    for key in ("L02", "W08", "W07", "L01", "W02", "W11"):
        if key in text:
            return key
    if "staff" in text:
        return "W11"
    if "bow" in text:
        return "W07"
    return "W01"


def is_exploration(record):
    return any("explore_idle" in v["action"] for v in record.get("refs", []))


def quiver_geometry(key, direction, explore):
    """Complete arrow bundles/tubes, with no material or thinness filtering."""
    result=np.zeros((768,512),bool)
    if key not in ("W07","W08","L02"):
        return result
    if explore:
        specs={
            "W07":{
                "down":None,"right":None,
                "up":([(294,174),(340,164),(352,210),(322,237)],[(309,216),(336,231),(303,334),(274,320)]),
                "left":([(310,182),(350,177),(349,225),(319,239)],[(314,227),(339,235),(320,347),(296,339)]),
            },
            "W08":{
                "down":([(160,165),(199,163),(218,211),(184,225)],[(180,210),(206,219),(224,284),(204,291)]),
                "right":([(174,213),(208,211),(212,253),(183,262)],[(183,252),(207,254),(220,333),(195,339)]),
                "up":([(163,179),(201,168),(217,219),(187,231)],[(182,216),(207,209),(239,333),(209,340)]),
                "left":None,
            },
            "L02":{
                "down":([(165,161),(201,153),(218,201),(187,218)],[(184,204),(205,210),(217,253),(197,258)]),
                "right":([(174,199),(203,194),(211,243),(180,250)],[(180,243),(207,244),(208,363),(182,365)]),
                "up":([(302,171),(338,168),(347,213),(315,233)],[(311,221),(339,230),(309,357),(277,345)]),
                "left":([(317,199),(345,190),(348,247),(317,253)],[(316,244),(344,243),(336,357),(309,358)]),
            },
        }
    else:
        specs={
            "W07":{
                "down":None,
                "right":([(157,187),(197,182),(211,232),(174,245)],[(168,235),(202,239),(216,337),(184,344)]),
                "up":([(296,187),(336,182),(350,230),(317,246)],[(310,232),(341,245),(304,345),(272,332)]),
                "left":([(309,184),(348,176),(355,225),(319,243)],[(315,235),(346,238),(326,341),(296,333)]),
            },
            "W08":{
                "down":([(289,149),(325,147),(330,194),(299,209)],[(300,199),(326,204),(330,253),(310,258)]),
                "right":([(159,160),(195,152),(214,203),(179,216)],[(172,207),(201,214),(226,314),(194,322)]),
                "up":([(296,168),(336,159),(350,211),(315,230)],[(311,217),(342,230),(300,347),(271,332)]),
                "left":([(313,162),(352,156),(355,209),(321,226)],[(316,217),(347,225),(326,336),(296,325)]),
            },
            "L02":{
                "down":([(163,166),(202,158),(218,207),(183,222)],[(182,211),(207,217),(220,292),(195,298)]),
                "right":([(165,167),(200,157),(215,207),(182,222)],[(178,211),(205,216),(218,338),(190,342)]),
                "up":([(303,169),(344,161),(353,210),(319,228)],[(315,217),(345,229),(309,348),(278,333)]),
                "left":([(311,162),(351,154),(357,212),(321,229)],[(317,218),(347,225),(334,339),(303,331)]),
            },
        }
    spec=specs[key].get(direction)
    if spec:
        result|=polygon(spec[0])|polygon(spec[1])
    return result


def exploration_geometry(key,direction):
    result=np.zeros((768,512),bool)
    if key=="W01":
        if direction=="down":
            result|=circle((197,135),11)|line([(198,145),(211,178)],7)|line([(185,186),(228,171)],4)
            result|=line([(194,393),(194,472)],5)
        elif direction=="right":
            result|=circle((200,140),11)|line([(201,151),(203,187)],7)|line([(192,190),(213,187)],4)
            result|=line([(202,189),(206,280),(213,392)],6)
        elif direction=="up":
            result|=circle((307,133),11)|line([(304,143),(292,178)],7)|line([(279,174),(316,191)],4)
            result|=line([(291,185),(264,252),(233,328),(202,409),(179,443)],10)
        else:
            result|=circle((309,141),11)|line([(309,152),(307,183)],7)|line([(295,184),(318,189)],4)
            result|=line([(307,190),(304,285),(298,390)],6)
        return result
    if key in ("W02","L01"):
        if key=="W02":
            hilts={"down":([(155,145),(184,190)],6),"right":([(218,146),(214,188)],6),
                   "up":([(338,142),(319,194)],6),"left":([(313,151),(311,194)],6)}
            guards={"down":[(146,213),(198,189)],"right":[(202,188),(230,195)],
                    "up":[(303,187),(341,205)],"left":[(296,191),(326,200)]}
            straps={"down":[(178,202),(303,326)],"right":[(211,199),(208,297),(208,416)],
                    "up":[(322,204),(292,256),(251,323),(208,411)],"left":[(310,204),(305,290),(303,415)]}
            result|=line(*hilts[direction])|line(guards[direction],4)
            result|=line(straps[direction],15 if direction in ("down","up") else 8)
        else:
            hilts={"down":[(176,166),(195,215)],"right":[(180,163),(198,215)],
                   "up":[(331,150),(313,200)],"left":[(325,165),(312,215)]}
            guard_centers={"down":(194,215),"right":(197,212),"up":(313,200),"left":(312,215)}
            result|=line(hilts[direction],6)
            gx,gy=guard_centers[direction]
            result|=line([(gx-37,gy-9),(gx-24,gy+4),(gx,gy+4),(gx+24,gy-5),(gx+35,gy-18)],4)
            for sign in (-1,1):result|=line([(gx+sign*22,gy),(gx+sign*27,gy-17),(gx+sign*23,gy-27)],3)
            if direction=="down":result|=line([(185,226),(308,347)],12)
            elif direction=="right":result|=line([(198,226),(206,292),(209,350)],8)
            elif direction=="up":result|=polygon([(304,215),(327,224),(241,400),(218,449),(199,441),(215,391)])
            else:result|=line([(311,225),(303,292),(299,353)],8)
        return result
    if key=="W11":
        centers={"down":(182,179),"right":(186,174),"up":(317,181),"left":(324,182)}
        cx,cy=centers[direction]
        # Same ornament topology, translated to its actual carried location.
        result|=polygon([(x+cx-150,y+cy-254) for x,y in STAFF_HEAD["down"]])
        shafts={"down":[(185,215),(192,240)],"right":[(190,205),(202,268),(208,353)],
                "up":[(313,211),(298,267),(283,324),(269,387),(254,462)],
                "left":[(325,214),(317,279),(310,343),(306,406)]}
        result|=line(shafts[direction],9)
        straps={"down":[(188,215),(312,321)],"right":[(212,316),(289,276)],
                "up":[(191,342),(320,345)],"left":[(212,279),(279,321)]}
        result|=line(straps[direction],9)
        return result
    result|=quiver_geometry(key,direction,True)
    if key=="W07":
        paths={
            "down":[[(343,132),(330,140),(326,165),(320,198),(305,231)],[(178,482),(174,509),(181,528)]],
            "right":[[(174,154),(170,175),(183,223),(197,278),(200,329)],[(202,443),(200,475),(195,507),(202,520)]],
            "up":[[(166,135),(179,146),(182,190),(191,234),(204,278),(209,329),(208,371),(194,422),(181,470),(179,496),(184,514)]],
            "left":[[(330,154),(335,179),(329,212),(316,263),(303,311),(303,366),(310,418),(313,470),(306,501),(312,517)]],
        }
        for path in paths[direction]:result|=line(path,7)
        if direction=="down":result|=line([(201,320),(319,211)],10)
        if direction=="up":result|=line([(185,204),(320,294)],10)|line([(166,136),(181,513)],2)
        if direction=="right":result|=line([(173,155),(201,520)],2)
        if direction=="left":result|=line([(331,155),(312,516)],2)
    elif key=="W08":
        paths={
            "down":[([(307,114),(319,134),(317,155),(306,179),(292,201)],5),([(337,343),(350,368),(354,397),(341,428),(326,455),(325,482)],8)],
            "right":[([(205,351),(208,386),(213,420),(205,449),(194,475)],7)],
            "up":[([(308,121),(323,145),(323,168),(306,193),(290,221),(288,248),(294,276),(306,292)],10),
                  ([(307,308),(313,335),(305,361),(309,387),(322,412),(321,437),(306,467)],10)],
            "left":[([(326,120),(339,143),(337,165),(323,192),(312,220),(313,251),(323,278)],9),
                    ([(324,304),(332,333),(339,360),(339,389),(327,420),(313,443),(302,465)],9)],
        }
        for path,radius in paths[direction]:result|=line(path,radius)
        orbs={"right":(205,337),"up":(306,297),"left":(323,288)}
        if direction in orbs:result|=circle(orbs[direction],16)
        straps={"down":[(193,262),(308,263)],"right":[(214,282),(278,245)],
                "up":[(185,248),(305,247)],"left":[(220,247),(296,283)]}
        result|=line(straps[direction],8)
    elif key=="L02":
        circles={"down":[((307,176),25)],"right":[((181,203),25),((192,458),25)],
                 "up":[((193,182),27),((207,463),26)],"left":[((335,196),25),((321,451),25)]}
        for xy,radius in circles[direction]:result|=circle(xy,radius+3)&~circle(xy,radius-5)
        paths={"down":[[(306,206),(290,229)]],
               "right":[[(183,292),(184,314)],[(186,347),(187,376),(195,407),(199,434)]],
               "up":[[(194,212),(209,234),(221,259),(222,281),(213,299)],[(215,343),(219,366),(210,389),(197,413),(190,436)]],
               "left":[[(336,264),(337,291),(334,304)],[(334,339),(329,369),(319,399),(318,429)]]}
        for path in paths[direction]:result|=line(path,11)
        orbs={"right":(187,330),"up":(210,320),"left":(334,320)}
        if direction in orbs:
            result|=circle(orbs[direction],22)
        straps={"down":[(195,214),(312,334)],"right":[(210,296),(278,268)],
                "up":[(185,225),(296,300)],"left":[(218,277),(292,311)]}
        result|=line(straps[direction],9)
    return result


STAFF_HEAD = {
    "down": [(146,223),(159,223),(171,235),(178,249),(177,268),(169,283),(163,298),
             (146,300),(140,284),(129,274),(125,258),(128,240),(139,231)],
    "right": [(252,215),(265,220),(275,230),(282,245),(281,261),(270,278),
              (260,293),(243,296),(232,280),(228,258),(231,240),(242,227)],
    "up": [(367,216),(380,220),(391,231),(398,248),(394,267),(384,283),
           (380,297),(364,296),(353,281),(345,265),(347,245),(356,228)],
    "left": [(189,253),(201,255),(213,266),(221,282),(219,300),(213,312),
             (213,324),(196,324),(187,308),(175,297),(171,282),(176,267)],
}
STAFF_SHAFT = {
    "down": [(145,289),(163,290),(169,349),(176,410),(180,464),(185,521),
             (190,579),(193,615),(189,636),(175,638),(170,613),(167,563),
             (162,514),(158,464),(153,413),(149,359)],
    "right": [(242,285),(262,289),(257,345),(253,390),(246,442),(239,487),
              (232,531),(225,578),(217,626),(212,643),(196,641),(199,613),
              (205,570),(211,526),(217,483),(224,438),(231,389),(236,339)],
    "up": [(365,288),(382,289),(378,346),(374,396),(366,445),(359,490),
           (352,534),(347,579),(340,624),(334,643),(319,640),(322,613),
           (328,568),(334,524),(340,479),(348,433),(355,386),(360,337)],
    "left": [(195,313),(214,313),(216,364),(218,412),(223,459),(228,505),
             (233,551),(239,594),(244,626),(240,642),(226,643),(221,622),
             (217,579),(211,536),(207,492),(201,449),(198,405),(195,360)],
}

# The simple bow is a continuous narrow wooden curve plus a separate string.
SIMPLE_BOW = {
    "down": [(355,190),(365,204),(368,224),(361,251),(349,283),(341,315),
             (338,349),(342,381),(348,410),(347,438),(339,466),(337,491),
             (344,520),(353,552),(356,580),(349,597)],
    "right": [(317,220),(326,235),(327,250),(314,276),(301,301),(291,326),
              (288,350),(290,375),(299,401),(294,429),(289,451),(289,478),
              (294,501),(306,525),(318,548),(318,571)],
    "up": [(146,239),(138,254),(139,273),(150,304),(161,334),(166,365),
           (168,396),(174,424),(178,452),(176,480),(166,514),(151,550),
           (142,580),(149,602)],
    "left": [(190,220),(184,235),(189,251),(202,275),(219,301),(234,326),
             (242,350),(250,375),(253,403),(249,431),(248,455),(246,478),
             (241,502),(230,526),(214,551),(207,572)],
}
SIMPLE_STRING = {
    "down": [(355,191),(349,596)], "right": [(318,221),(322,579)],
    "up": [(146,240),(149,601)], "left": [(190,221),(208,572)],
}

# Separate the broad embossed limbs from thin antler-shaped silver tips.  This
# retains their full shape without keeping a broad strip of the original leg.
ORNATE_MAIN = {
    "down": [(349,221),(338,245),(324,264),(316,285),(312,307),(315,329),(327,347)],
    "right": [(348,248),(333,266),(319,283),(309,301),(307,320),(314,338),(318,345)],
    "up": [(134,263),(140,279),(150,291),(161,301)],
    "left": [(160,281),(179,297),(199,313),(218,331),(229,350),(242,372)],
}
ORNATE_LOWER = {
    "down": [(335,420),(340,441),(351,461),(366,476),(385,485)],
    "right": [(319,399),(306,418),(302,438),(307,459),(319,480)],
    "up": [(158,431),(166,447),(166,465),(158,484),(143,500),(126,510)],
    "left": [(267,452),(275,475),(270,497),(258,519),(244,538)],
}
ORNATE_TIPS = {
    "down": [[(348,160),(360,173),(365,190),(363,209),(351,230)],
             [(339,183),(351,191),(355,207)],[(336,217),(341,229),(337,242)],
             [(385,484),(396,502),(400,522),(393,541),(382,551)],
             [(374,479),(381,499),(373,514)],[(390,494),(402,508)]],
    "right": [[(343,193),(352,205),(356,221),(349,238),(338,250)],
              [(333,215),(340,226),(338,238)],[(327,233),(329,244)],
              [(319,480),(333,492),(341,511),(338,532),(327,548)],
              [(319,482),(324,500),(315,517)],[(337,501),(347,514)]],
    "up": [[(144,205),(133,216),(127,235),(132,253),(144,270)],
           [(145,228),(136,236),(134,247)],[(141,248),(138,260)],
           [(126,510),(116,525),(113,545),(119,560),(131,571)],
           [(128,508),(127,529),(137,541)],[(120,521),(110,535)]],
    "left": [[(160,243),(151,254),(148,270),(154,286),(167,298)],
             [(170,267),(163,276),(165,288)],[(180,290),(176,302)],
             [(244,538),(236,551),(240,569),(252,580),(262,580)],
             [(247,541),(252,556),(260,559)],[(240,552),(234,561),(242,575)]],
}
ORNATE_GRIP = {
    "down": ((331,351),[(331,361),(337,405)],[(348,161),(399,527)]),
    "right": ((317,345),[(318,355),(319,389)],[(350,205),(341,536)]),
    "up": ((157,309),[(153,355),(151,417)],[(136,222),(119,549)]),
    "left": ((242,377),[(244,389),(253,439)],[(154,260),(259,580)]),
}

MOON_UPPER = {
    "down": [(389,253),(371,271),(366,291),(359,312),(358,336),(366,357)],
    "right": [(345,251),(329,268),(315,289),(311,312),(316,333),(326,347)],
    "up": [(135,293),(130,304),(143,320),(153,340),(157,356),(149,372)],
    "left": [(349,309),(337,326),(323,346),(314,367),(316,386),(323,393)],
}
MOON_LOWER = {
    "down": [(354,420),(347,439),(349,460),(360,482),(373,499)],
    "right": [(313,405),(302,423),(302,445),(315,469),(328,489)],
    "up": [(162,425),(166,447),(160,469),(148,489),(137,505)],
    "left": [(322,448),(308,469),(307,487),(321,509),(338,531)],
}
MOON_CIRCLES = {
    "down": [((386,225),27),((360,530),27)],
    "right": [((336,221),27),((317,513),27)],
    "up": [((143,268),27),((143,527),27)],
    "left": [((345,279),30),((328,538),25)],
}
MOON_GRIPS = {
    "down": ((361,379),[(360,356),(354,407)],[(392,223),(389,530)]),
    "right": ((316,368),[(320,346),(313,402)],[(366,224),(349,528)]),
    "up": ((151,389),[(160,370),(159,424)],[(122,268),(118,529)]),
    "left": ((322,412),[(323,393),(322,448)],[(352,256),(354,565)]),
}


def sword_geometry(key, direction):
    if key == "W01":
        paths = {
            "down": [(154,396),(154,425),(150,443),(145,460),(132,500),(114,560),(90,634)],
            "right": [(228,408),(243,440),(249,450),(254,460),(269,500),(292,560),(321,635)],
            "up": [(337,393),(347,426),(353,443),(360,460),(370,500),(383,560),(400,628)],
            "left": [(225,405),(228,432),(218,451),(208,480),(186,560),(163,631)],
        }
        path = paths[direction]
        result = line(path, 7.5)
        # Sword guards are wider than the blade but still have a bounded ROI.
        guards={"down":[(135,434),(169,455)],"right":[(223,460),(267,438)],
                "up":[(330,449),(373,429)],"left":[(207,432),(247,451)]}
        result |= line(guards[direction],3.5)
        return result
    centers = {"W02":{"down":148,"right":251,"up":370,"left":271},
               "L01":{"down":155,"right":254,"up":369,"left":278}}
    x = centers[key][direction]
    result = line([(x,432),(x,483)], 4.5)
    if key == "W02":
        result |= polygon([(x-6,494),(x+7,494),(x+6,663),(x+1,706),
                           (x-5,673)])
        result |= polygon([(x-41,503),(x-34,491),(x-18,486),(x-8,480),
                           (x,484),(x+9,480),(x+20,487),(x+34,490),(x+41,502),
                           (x+28,497),(x+15,499),(x+7,506),(x-6,506),
                           (x-17,498),(x-29,497)])
        result |= circle((x,490), 9)
    else:
        result |= polygon([(x-5,501),(x+6,501),(x+5,663),(x,700),(x-5,666)])
        result |= polygon([(x-27,484),(x-17,480),(x-6,475),(x+5,475),(x+18,481),
                           (x+28,484),(x+22,498),(x+10,507),(x-9,507),(x-23,499)])
        result |= circle((x,491), 11)
        for sign in (-1,1):
            result |= line([(x+sign*10,489),(x+sign*25,478),(x+sign*30,465),
                            (x+sign*28,454)], 3.5)
            result |= line([(x+sign*16,496),(x+sign*34,489),(x+sign*42,478)], 3)
            result |= line([(x+sign*20,500),(x+sign*37,497)], 2.5)
    return result


def make_equipment_mask(before, r, joints):
    """Return only held gear in the unwarped source's 512x768 coordinates."""
    array = np.asarray(before)
    if array.shape != (768,512,4):
        raise ValueError("before must be the original normalized 512x768 RGBA frame")
    key, direction = weapon_id(r), r["direction"]
    result = np.zeros((768,512), bool)
    if is_exploration(r):
        return back_body_overlap_guard(exploration_geometry(key,direction),array,direction) & (array[...,3]>0)
    if key == "W11":
        result = polygon(STAFF_HEAD[direction]) | polygon(STAFF_SHAFT[direction])
    elif key == "W07":
        result = line(SIMPLE_BOW[direction], 6.5) | line(SIMPLE_STRING[direction], 2)
    elif key == "W08":
        result = line(ORNATE_MAIN[direction], 13) | line(ORNATE_LOWER[direction], 12)
        for points in ORNATE_TIPS[direction]:
            result |= line(points, 3.5)
        orb, handle, string = ORNATE_GRIP[direction]
        result |= circle(orb, 14) | line(handle, 5.5) | line(string, 2)
    elif key == "L02":
        result = line(MOON_UPPER[direction], 11) | line(MOON_LOWER[direction], 11)
        for ordinal,(xy, radius) in enumerate(MOON_CIRCLES[direction]):
            moon=circle(xy, radius+3) & ~circle(xy, radius-5)
            if direction=="left":
                # The ring passes behind the old shoulder/leg on this facing;
                # those occluding body pixels are not equipment.
                moon[:,:327 if ordinal==0 else 315]=False
            result |= moon
        orb, handle, string = MOON_GRIPS[direction]
        result |= circle(orb, 21) | line(handle, 7) | line(string, 2.5)
        # Preserve existing translucent blue light outside solid body pixels.
        # This uses alpha, not colour, and cannot bring back an opaque torso.
        glow = circle(orb, 62) & (array[...,3] < 240)
        result |= glow
    else:
        result = sword_geometry(key, direction)
    result|=back_body_overlap_guard(quiver_geometry(key,direction,False),array,direction)
    if key in ("W07","W08","L02") and direction=="up":
        result|=back_body_overlap_guard(line([(192,218),(309,298)],9),array,direction)
    if key=="W01":
        carried={"down":[(194,405),(194,486)],"right":[(204,215),(207,393)],
                 "up":[(310,204),(227,392)],"left":[(301,204),(300,393)]}
        result|=back_body_overlap_guard(line(carried[direction],7 if direction in ("down","right","left") else 10),array,direction)
    # Keep the grip connection.  The caller restores the same original hand
    # pixels on top, so cutting a wrist capsule here would also cut handles.
    return result & (array[...,3] > 0)


def main():
    """Bounded source/extracted-gear proof images; no runtime or static edits."""
    here = Path(__file__).resolve().parent
    sys.path.insert(0, str(here.parent/"local-qwen21-unified-v3"))
    import prepare
    spec_path = here/"prepare_v5.py"
    import importlib.util
    spec = importlib.util.spec_from_file_location("static_gear_pose_helper", spec_path)
    helper = importlib.util.module_from_spec(spec);spec.loader.exec_module(helper)
    manifest = json.loads(prepare.MANIFEST.read_text())
    frames = prepare.inventory(manifest)
    old = {(r["image"],r["index"]):r for r in json.loads((helper.V4/"inventory.json").read_text())["frames"]}
    poses = {(r["image"],r["index"]):r for r in json.loads((helper.V4/"pose-landmarks.json").read_text())["frames"]}
    out = here/"edits/static-gear-validation";out.mkdir(parents=True,exist_ok=True)
    report=[]
    for full_key in ("W01","W02","L01","W07","W08","L02","W11",
                     "explore-W01","explore-W02","explore-L01","explore-W07","explore-W08","explore-L02","explore-W11"):
        explore=full_key.startswith("explore-")
        key=full_key.removeprefix("explore-")
        page = Image.new("RGB",(1440,290),"#34383b");draw=ImageDraw.Draw(page)
        for di,direction in enumerate(prepare.DIRECTIONS):
            record=prepare.find(frames,("explore_idle_" if explore else "idle_")+key,direction,0)
            sheet=Image.open(prepare.ACTOR/record["image"]).convert("RGBA")
            before=prepare.canvas(record,{record["image"]:sheet})
            k=record["image"],record["index"]
            pose=helper.adapt_pose(record,old[k],poses[k],sheet)
            joints=np.full((33,2),np.nan)
            for value in pose["joints"].values():
                if value["review"] is not None:joints[value["mediapipeIndex"]]=value["review"]
            mask=make_equipment_mask(before,record,joints)
            layer=np.asarray(before).copy();layer[~mask]=0;layer=Image.fromarray(layer)
            layer.save(out/f"{full_key}-{direction}-gear.png")
            Image.fromarray(np.uint8(mask)*255).save(out/f"{full_key}-{direction}-mask.png")
            for off,pic in ((0,before),(180,layer)):
                thumb=pic.resize((180,270),Image.Resampling.LANCZOS)
                page.paste(thumb,(di*360+off,20),thumb)
            draw.text((di*360+3,2),full_key+" / "+direction+" source | gear",fill="white")
            report.append(dict(weapon=key,exploration=explore,direction=direction,pixels=int(mask.sum())))
        page.save(out/f"{full_key}-review.jpg",quality=92)
    (out/"report.json").write_text(json.dumps(report,indent=2))
    print(json.dumps(dict(heldWeapons=7,explorationWeapons=7,facings=4,sourceRGBAUnchanged=True,
                         heldNoMaterialFiltering=True,carriedBodyOverlapGuard=True,report=str(out/"report.json"))))


if __name__ == "__main__":
    main()
