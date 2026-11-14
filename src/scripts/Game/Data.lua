local Data = {}

Data.WIDTH, Data.HEIGHT = 1600, 900
Data.Weapons = {
    W01 = {name="佣兵长剑", kind="sword", description="免费近战攻击；武器技追步斩。"},
    W07 = {name="白蜡木短弓", kind="bow", description="普通箭无限；武器技发射贯穿箭。"},
    W11 = {name="灰木短杖", kind="staff", description="免费奥术弹；武器技发射聚束。"},
    L01 = {name="风暴王的遗嘱", kind="sword", legendary=true, description="近战可能留下雷痕；武器技引爆并连锁。"},
    L02 = {name="阿斯特拉的回信", kind="bow", legendary=true, description="箭矢飞出后折返；移动身体改变回返轨迹。"},
}

Data.Dialogues = {
    offer = {speaker="弥菈", title="第三只杯子", lines={
        "她把第三只杯子倒扣，随后将一块金属样片放在灯下。",
        "「他们截走了一只遗物匣。替我拿回来，我们共同署名，分成写在契约上。」",
        "她用手挡住灯光。零散星点，落在桌面的旧刀痕里。",
    }, choices={{id="accept",text="先说分成。我接这份委托。"},{id="ask_letter",text="先把你藏着的那封信给我看。"},{id="leave",text="我再考虑一下。"}}},
    accepted = {speaker="弥菈",title="被截获的星片",lines={
        "「沿野路去隘口。主路有守卫，高地能绕到他们侧面。」",
        "「别急着撬锁。封签下面那条细线，会让你后悔。」",
    },choices={{id="leave",text="前往野路。"}}},
    letter = {speaker="拉斐尔", title="一封不该存在的信",lines={
        "完整星片在背光下，投出一片没有登记过的星座。",
        "信纸上的日期，就在不久之前。落款是：伊芙琳·灰。",
        "「请让我们看一次真正的早晨。」",
        "那些被宣布阵亡的人，可能仍在地下活着。",
    },choices={{id="read_letter",text="记下落款。回去找弥菈问清楚。"}}},
    debrief = {speaker="弥菈",title="未说完的契约",lines={
        "她认出了信上的字迹，却迟迟没有伸手去拿。",
        "「先把门打开。我会告诉你，我为什么让她等到现在。」",
        "遗物匣已经取回。这份委托的真正目的，才刚刚显露。",
    },choices={{id="finish",text="本地小章节完成 · 继续探索"}}},
}

local function enemy(id,x,y,kind)
    local elite = kind == "elite"
    return {id=id,x=x,y=y,spawnX=x,spawnY=y,kind=kind or "raider",hp=elite and 260 or 70,
        maxHp=elite and 260 or 70,windup=0,cooldown=0,vx=0,vy=0,counted=false,mark=0}
end

function Data.World()
    return {
        camp = {name="石桥旅店", subtitle="一份比雇主说的更危险的委托", enemies={},barrels={},
            walls={{x=550,y=100,w=290,h=105},{x=610,y=650,w=340,h=110},{x=1040,y=140,w=150,h=200}},
            chests={}, props={{x=430,y=325,kind="table"},{x=230,y=545,kind="fire"}},
            exits={{x=1480,y=430,to="road",label="野路"}}},
        road = {name="隘口野路",subtitle="可以走主路，也可以从北侧林缘绕行",enemies={
            enemy("road_guard_1",600,420),enemy("road_guard_2",700,490),
            enemy("road_guard_3",1060,350),enemy("road_guard_4",1190,540)},
            barrels={{id="road_barrel_1",x=640,y=400,alive=true},{id="road_barrel_2",x=715,y=400,alive=true},
                {id="road_barrel_3",x=1120,y=520,alive=true}},
            walls={{x=330,y=210,w=180,h=105},{x=780,y=450,w=130,h=180},{x=1080,y=160,w=210,h=105}},
            chests={{id="road_cache",x=500,y=160,kind="iron",amount=3,opened=false},
                {id="road_coin",x=940,y=730,kind="gold",amount=15,opened=false},
                {id="road_relic",x=1330,y=180,kind="relic",amount=3,opened=false}},
            props={{x=410,y=265,kind="ruin"},{x=1170,y=205,kind="ruin"}},
            exits={{x=90,y=430,to="camp",label="旅店"},{x=1500,y=410,to="pass",label="劫车隘口"}}},
        pass = {name="劫车隘口",subtitle="取回遗物匣；油桶与侧翼都是机会",enemies={
            enemy("pass_guard_1",660,380),enemy("pass_guard_2",780,510),
            enemy("pass_guard_3",980,310),enemy("pass_warden",1160,430,"elite")},
            barrels={{id="pass_barrel_1",x=720,y=350,alive=true},{id="pass_barrel_2",x=790,y=350,alive=true},
                {id="pass_barrel_3",x=1040,y=490,alive=true}},
            walls={{x=350,y=120,w=240,h=125},{x=410,y=650,w=220,h=90},{x=950,y=650,w=260,h=105}},
            chests={{id="pass_cache",x=250,y=700,kind="iron",amount=3,opened=false}},
            props={{x=1420,y=405,kind="wagon"},{x=470,y=180,kind="ruin"}},
            exits={{x=90,y=430,to="road",label="野路"}}},
    }
end

return Data
