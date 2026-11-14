local UI=require("urhox-libs/UI")
local Data=require("Game.Data")
local WorldView=require("Game.SceneInput")
local Images=require("urhox-libs/UI/Core/ImageCache")
local Hud={}
local C={ink={25,32,29,245},border={139,119,76,200},gold={224,196,132},paper={235,224,196},muted={176,184,161},green={58,83,66}}
local function label(text,size,props)
    props=props or {}; props.text=text; props.fontSize=size or 16; props.fontColor=props.fontColor or C.paper
    return UI.Label(props)
end
local function button(text,callback,props)
    props=props or {}; props.text=text; props.onClick=callback
    props.height=props.height or 46; props.fontSize=props.fontSize or 15
    props.fontColor=props.fontColor or C.paper; props.backgroundColor=props.backgroundColor or {48,60,49,250}
    props.borderColor=C.border; props.borderWidth=1; props.borderRadius=4
    return UI.Button(props)
end
local Stick=UI.Widget:Extend("ChapterStick")
function Stick:Init(props) UI.Widget.Init(self,props); self.app=props.app end
function Stick:Set(event)
    local l=self:GetAbsoluteLayout()
    local x,y=(event.x-l.x-l.w/2)/38,(event.y-l.y-l.h/2)/38
    local n=math.max(1,math.sqrt(x*x+y*y))
    self.app.moveX,self.app.moveY=x/n,y/n
end
function Stick:OnPointerDown(event) self.pointer=event.pointerId; self:Set(event); self.app.mouseAim=false end
function Stick:OnPointerMove(event) if self.pointer==event.pointerId then self:Set(event) end end
function Stick:OnPointerUp(event) if self.pointer==event.pointerId then self.pointer=nil; self.app.moveX,self.app.moveY=0,0 end end
function Stick:OnPointerCancel() self.pointer=nil; self.app.moveX,self.app.moveY=0,0 end
function Stick:Render(g)
    local l=self:GetAbsoluteLayout(); local x,y=l.x+l.w/2,l.y+l.h/2
    nvgBeginPath(g); nvgCircle(g,x,y,48); nvgFillColor(g,nvgRGBA(22,31,27,210)); nvgFill(g)
    nvgStrokeColor(g,nvgRGBA(158,147,105,160)); nvgStrokeWidth(g,1); nvgStroke(g)
    nvgBeginPath(g); nvgCircle(g,x+self.app.moveX*28,y+self.app.moveY*28,20)
    nvgFillColor(g,nvgRGBA(170,177,139,190)); nvgFill(g)
end
local HoldButton=UI.Button:Extend("ChapterHoldButton")
function HoldButton:OnPointerDown(event)
    UI.Button.OnPointerDown(self,event)
    if event:IsPrimaryAction() then self.props.app.touchAttack=true end
end
function HoldButton:OnPointerUp(event) UI.Button.OnPointerUp(self,event); self.props.app.touchAttack=false end
function HoldButton:OnPointerCancel(event) UI.Button.OnPointerCancel(self,event); self.props.app.touchAttack=false end
local Banner=UI.Widget:Extend("ChapterPortraitBanner")
function Banner:Render(g)
    local l=self:GetAbsoluteLayout()
    local image=Images.Get("image/raphael.png")
    if image<=0 then return end
    local w,h=Images.GetSize("image/raphael.png")
    local s=l.w/820
    nvgSave(g); nvgIntersectScissor(g,l.x,l.y,l.w,l.h)
    nvgBeginPath(g); nvgRect(g,l.x,l.y,l.w,l.h)
    nvgFillPaint(g,nvgImagePattern(g,l.x+l.w/2-1210*s,l.y+l.h/2-180*s,w*s,h*s,0,image,1)); nvgFill(g)
    nvgRestore(g)
end
local function quest(g)
    if g.flags.complete then return "委托完成 · 前往地下遗迹的线索已得到" end
    if g.flags.read_letter then return "返回石桥旅店，与弥菈核对求援信" end
    if g.flags.recovered then return "阅读遗物匣里的求援信" end
    if g.flags.accepted then return g.scene=="camp" and "沿东侧野路，前往劫车隘口" or "取回隘口马车上的遗物匣" end
    return "与弥菈交谈，接下遗物匣委托" end
local function modal(app,title,kicker,contents)
    local w,h=UI.GetViewportSize()
    local body={label(kicker,12,{fontColor=C.gold}),label(title,30,{fontColor=C.paper,marginBottom=10})}
    for _,widget in ipairs(contents) do body[#body+1]=widget end
    return UI.Panel{position="absolute",left=0,right=0,top=0,bottom=0,backgroundColor={7,14,12,210},alignItems="center",justifyContent="center",children={
        UI.Panel{width=math.min(760,w-36),maxHeight=h-28,padding=28,gap=12,backgroundColor=C.ink,borderWidth=1,borderColor=C.border,borderRadius=6,children=body}
    }}
end
function Hud.Build(app)
    app.worldAttack,app.touchAttack=false,false
    app.moveX,app.moveY=0,0
    local g=app.game
    local w=UI.GetViewportSize()
    local compact=w<1150
    local view=WorldView{app=app,position="absolute",left=0,top=0,right=0,bottom=0}
    local hp=label("",15,{fontColor=C.paper})
    local resources=label("",13,{fontColor=C.muted})
    local title=label("",22,{fontColor=C.gold})
    local objective=label("",15,{fontColor=C.paper})
    local toast=label("",15,{textAlign="center",fontColor=C.gold,position="absolute",left=30,right=30,bottom=compact and 174 or 126,height=28,pointerEvents="none"})
    local root=UI.Panel{width="100%",height="100%",children={view,
        UI.Panel{position="absolute",left=18,top=16,width=compact and 225 or 270,gap=4,padding=12,backgroundColor=C.ink,borderWidth=1,borderColor=C.border,borderRadius=4,pointerEvents="none",children={
            label("拉斐尔  /  白枝远征",13,{fontColor=C.gold}),hp,resources,
        }},
        UI.Panel{position="absolute",left=compact and 260 or 320,right=18,top=16,height=96,gap=6,padding=12,backgroundColor=C.ink,borderWidth=1,borderColor=C.border,borderRadius=4,pointerEvents="none",children={title,objective}},
        button("B  整备",function() app:Open("inventory") end,{id="open_inventory",position="absolute",right=116,top=124,width=96}),
        button("Esc  菜单",function() app:Open("pause") end,{id="open_pause",position="absolute",right=18,top=124,width=90}),
        toast,
        Stick{app=app,position="absolute",left=14,bottom=18,width=108,height=108},
        label("WASD / 方向键",12,{fontColor=C.muted,position="absolute",left=12,bottom=6,width=120,textAlign="center",pointerEvents="none"}),
    }}
    local weapons=UI.Panel{position="absolute",left=compact and 18 or 145,bottom=compact and 136 or 25,flexDirection="row",gap=8,children={}}
    for i,id in ipairs({"W01","W07","W11"}) do
        weapons:AddChild(button(tostring(i).."  "..({"长剑","短弓","短杖"})[i],function() g:Equip(id) end,{width=compact and 94 or 112}))
    end
    root:AddChild(weapons)
    local actions=UI.Panel{position="absolute",right=18,bottom=24,flexDirection="row",gap=8,alignItems="center",children={
        button("E  互动",function() g:Interact() end,{id="interact",width=80}),
        button("Q  火油",function() g:Fire() end,{width=80}),
        button("R  武器技",function() g:Skill() end,{width=94}),
        button("空格  闪避",function() app.dash=true end,{width=98}),
    }}
    root:AddChild(actions)
    local attack=HoldButton{app=app,text="攻击  /  J",position="absolute",right=18,bottom=80,width=112,height=48,fontSize=17,fontColor=C.paper,backgroundColor={84,72,43},borderColor=C.border,borderWidth=1,borderRadius=4}
    root:AddChild(attack)
    local skillInfo=label("",12,{fontColor=C.muted,position="absolute",left=145,right=150,bottom=82,height=26,pointerEvents="none"})
    root:AddChild(skillInfo)
    if not compact then root:AddChild(label("鼠标指向瞄准 · 按住左键 / J 攻击 · Tab切换武器",12,{fontColor=C.muted,position="absolute",left=145,bottom=7,pointerEvents="none"})) end
    app.widgets={hp=hp,resources=resources,title=title,objective=objective,toast=toast,skill=skillInfo}
    local content=nil
    if app.screen=="title" then
        content=modal(app,"被截获的星片","第一章  ·  阵亡者的晚饭",{
            Banner{height=160},
            label("第三只杯子倒扣在桌上。弥菈要你取回一只遗物匣，却对匣子里的那封信只字未提。",17),
            label("接约 → 穿过野路 → 隘口夺匣 → 读信返程。约 8—12 分钟。",14,{fontColor=C.muted}),
            button(app.scene3d and not app.scene3d:CharactersReady() and "3D角色制作中 · 等待模型" or (app.hasSave and "继续旅程" or "启程"),function() app:Begin() end,{id="begin",backgroundColor=C.green,disabled=app.scene3d and not app.scene3d:CharactersReady()}),
            label(app.saveWarning or "键盘：WASD移动，鼠标瞄准，左键/J攻击，E互动。触屏可用左侧摇杆与右侧按钮。",14,{fontColor=app.saveWarning and {236,164,114} or C.muted}),
        })
    elseif g.status=="dead" then
        content=modal(app,"火还没有熄灭","暂时倒下",{
            label("返回旅店篝火休整。已取得的物品、已打败的守卫和任务选择都会保留。",17),
            button("在篝火重整",function() g:Retry(); app.screen=nil; app:Rebuild() end,{backgroundColor=C.green}),
        })
    elseif g.dialogue then
        local d=Data.Dialogues[g.dialogue]
        ---@type Widget[]
        local body={label(d.speaker,15,{fontColor=C.gold})}
        for _,lineText in ipairs(d.lines) do body[#body+1]=label(lineText,17) end
        for _,choice in ipairs(d.choices) do
            body[#body+1]=button(choice.text,function() g:Choose(choice.id); app:SaveNow(); app:Rebuild() end,{id="choice_"..choice.id,height=48,textAlign="left"})
        end
        content=modal(app,d.title,"人物对话",body)
    elseif app.screen=="inventory" then
        ---@type Widget[]
        local body={label("在安全处整备武器。普通攻击不消耗资源；武器技消耗20专注，冷却6秒。",15,{fontColor=C.muted})}
        for _,id in ipairs({"W01","W07","W11","L01","L02"}) do
            local item=Data.Weapons[id]
            if g.owned[id] then
                body[#body+1]=button((g.weapon==id and "● " or "")..item.name.."  ·  "..item.description,function() g:Equip(id); app:Rebuild() end,{id="equip_"..id,height=54,fontSize=14,backgroundColor=item.legendary and {77,64,40} or C.green})
            else body[#body+1]=label("未发现 · "..item.name.."（遗物箱18% / 隘口精英25%）",14,{fontColor=C.muted}) end
        end
        body[#body+1]=button("返回旅程  /  B",function() app:Open(nil) end,{id="close_inventory"})
        content=modal(app,"行囊与武器","整备",body)
    elseif app.screen=="pause" or app.screen=="new_confirm" then
        if app.screen=="new_confirm" then
            content=modal(app,"开始一段新旅程？","新旅程",{
                label("当前存档会先备份，再从旅店重新开始。新的掉落结果会随旅程确定。",17),
                button("备份并重新开始",function() app:NewJourney() end),
                button("返回菜单",function() app:Open("pause") end),
            })
        else
            content=modal(app,"旅程已暂停","石桥旅店 · 本地进度",{
                label("WASD / 方向键移动，鼠标瞄准；左键 / J攻击；空格闪避；E互动；Q投火油；R武器技；1—3 / Tab切换武器。",17),
                label(app.saveWarning or "任务、探索和拾取会自动保存。可以随时关闭窗口，下次继续。",15,{fontColor=C.muted}),
                button("继续旅程  /  Esc",function() app:Open(nil) end,{backgroundColor=C.green}),
                button("保存进度",function() app:SaveNow(true); app:Rebuild() end),
                button("新旅程…",function() app:Open("new_confirm") end),
                button("保存并退出",function() app:Quit() end),
            })
        end
    elseif g.flags.complete and not app.celebrated then
        content=modal(app,"被截获的星片","小章节完成",{
            label("遗物匣已经归还，求援信指向暮钟矿道。弥菈终于说出那个被她遮住的名字：伊芙琳。",18),
            label("下一幕：阵亡者的重逢。当前可玩版本到此为止，你仍可探索这三处场景，寻找未发现的传奇。",15,{fontColor=C.muted}),
            button("继续探索",function() app.celebrated=true; app:Rebuild() end,{backgroundColor=C.green}),
        })
    end
    if content then root:AddChild(content) end
    UI.SetRoot(root,true)
    app.root=root
    app:UpdateHud()
end
function Hud.Update(app)
    local g,p,w=app.game,app.game.player,app.widgets
    w.hp:SetText(string.format("生命 %d / 120  ·  专注 %d",math.ceil(p.hp),math.floor(p.focus)))
    w.resources:SetText(string.format("金币 %d   ·   废铁 %d   ·   火油 %d/3",p.gold,p.iron,p.oil))
    w.title:SetText("01  /  "..g:Map().name)
    w.objective:SetText(quest(g))
    w.toast:SetText(g.toastTime>0 and g.toast or "")
    w.skill:SetText(Data.Weapons[g.weapon].name..string.format("   ·   R %s  /  闪避 %s",p.skill>0 and string.format("%.1fs",p.skill) or "就绪",p.dash>0 and string.format("%.1fs",p.dash) or "就绪"))
end
return Hud
