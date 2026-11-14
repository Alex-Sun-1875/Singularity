-- Based on the official scaffold-2d lifecycle: UI.Init -> tree -> UI.SetRoot.
local UI=require("urhox-libs/UI")
local Chapter=require("Game.Chapter")
local Save=require("Game.Save")
local Hud=require("Game.Hud")
local Scene3D=require("Game.Scene3D")
ChapterApp={}
local App=ChapterApp
function App:Rebuild() Hud.Build(self); self.lastMode=self:Mode() end
function App:UpdateHud() Hud.Update(self) end
function App:Mode() return tostring(self.screen)..":"..tostring(self.game.dialogue)..":"..self.game.status..":"..tostring(self.game.flags.complete)..":"..tostring(self.celebrated) end
function App:SaveNow(feedback)
    if not self.started then return end
    local ok,err=self.store:Write(self.game)
    if not ok then self.saveWarning=err; self.game:Say(err)
    elseif feedback then self.game:Say("本地进度已保存。") end
    self.saveTime=0
end
function App:Begin()
    if self.scene3d and not self.scene3d:CharactersReady() then
        self.game:Say("当前v5角色模型尚未完成，3D版本仍在制作中。")
        return
    end
    self.screen=nil; self.started=true; self:Rebuild(); self:SaveNow()
end
function App:Open(screen)
    if self.screen=="title" then return end
    self.screen=screen; self:SaveNow(); self:Rebuild()
end
function App:NewJourney()
    local g=Chapter.New(os.time()%2147483000)
    local ok,err=self.store:StartFresh(g)
    if not ok then self.saveWarning=err; self:Open("pause"); return end
    self.game=g; self.screen=nil; self.celebrated=false; self.hasSave=true; self.saveWarning=nil; self:Rebuild()
end
function App:Quit() self:SaveNow(); engine:Exit() end
function Start()
    graphics.windowTitle="剑与火 · 被截获的星片"
    input.mouseVisible=true
    UI.Init({fonts={{family="sans",weights={normal="Fonts/MiSans-Regular.ttf"}}},scale=UI.Scale.DEFAULT})
    App.store=Save.New(); App.game,App.saveWarning=App.store:Load()
    App.hasSave=App.game~=nil
    App.game=App.game or Chapter.New(os.time()%2147483000)
    App.scene3d=Scene3D.New(App)
    App.screen="title"; App.started=false; App.saveTime=0
    App.celebrated=App.game.flags.complete
    App.moveX,App.moveY=0,0
    App.viewportW,App.viewportH=UI.GetViewportSize()
    App:Rebuild()
    SubscribeToEvent("Update","HandleUpdate")
    SubscribeToEvent("KeyDown","HandleKeyDown")
    print("[Chapter] Ready. Local single-player, no cloud binding.")
end
local function down(key) return input:GetKeyDown(key) and 1 or 0 end
function HandleUpdate(_,eventData)
    local dt=eventData["TimeStep"]:GetFloat()
    if not App.game then return end
    if App.scene3d then App.scene3d:Update(dt) end
    local width,height=UI.GetViewportSize()
    if width~=App.viewportW or height~=App.viewportH then
        App.viewportW,App.viewportH=width,height; App:Rebuild()
    end
    local mode=App:Mode()
    if mode~=App.lastMode then App:Rebuild() end
    if App.screen or App.game.dialogue or App.game.status=="dead" or (App.game.flags.complete and not App.celebrated) then App:UpdateHud(); return end
    local mx=down(KEY_D)+down(KEY_RIGHT)-down(KEY_A)-down(KEY_LEFT)+App.moveX
    local my=down(KEY_S)+down(KEY_DOWN)-down(KEY_W)-down(KEY_UP)+App.moveY
    App.moving=math.abs(mx)+math.abs(my)>0.1
    local angle=App.mouseAim and App.aim or nil
    if App.touchAttack and not App.mouseAim then
        local nearest,dist=nil,math.huge
        for _,e in ipairs(App.game:Map().enemies) do
            local d=(e.x-App.game.player.x)^2+(e.y-App.game.player.y)^2
            if e.hp>0 and d<dist and not App.game:Blocked(App.game.player.x,App.game.player.y,e.x,e.y,0) then nearest,dist=e,d end
        end
        if nearest then angle=math.atan(nearest.y-App.game.player.y,nearest.x-App.game.player.x) end
    end
    local oldX,oldY=App.game.player.x,App.game.player.y
    App.game:Step(dt,{x=mx,y=my,angle=angle,attack=App.worldAttack or App.touchAttack or input:GetKeyDown(KEY_J),dash=App.dash})
    App.dash=false
    if oldX~=App.game.player.x or oldY~=App.game.player.y then App.game.dirty=true end
    App.saveTime=App.saveTime+dt
    if App.game.dirty and App.saveTime>2 then App:SaveNow() end
    App:UpdateHud()
end
function HandleKeyDown(_,eventData)
    if eventData["Repeat"] and eventData["Repeat"]:GetBool() then return end
    local key=eventData["Key"]:GetInt()
    if App.screen=="title" then if key==KEY_RETURN or key==KEY_SPACE then App:Begin() end; return end
    if key==KEY_ESCAPE then
        if App.screen then App:Open(nil) else App:Open("pause") end
        return
    end
    if key==KEY_B then
        if App.screen=="inventory" then App:Open(nil) else App:Open("inventory") end
        return
    end
    if App.screen or App.game.dialogue or App.game.status~="playing" then return end
    if key==KEY_E then App.game:Interact()
    elseif key==KEY_SPACE then App.dash=true
    elseif key==KEY_Q then App.game:Fire()
    elseif key==KEY_R then App.game:Skill()
    elseif key==KEY_1 then App.game:Equip("W01")
    elseif key==KEY_2 then App.game:Equip("W07")
    elseif key==KEY_3 then App.game:Equip("W11")
    elseif key==KEY_TAB then
        local ids={"W01","W07","W11","L01","L02"}
        local current=1
        for i,id in ipairs(ids) do if id==App.game.weapon then current=i end end
        for step=1,#ids do local id=ids[(current+step-1)%#ids+1]; if App.game.owned[id] then App.game:Equip(id); break end end
    end
end
function Stop()
    if App.started then App:SaveNow() end
    UI.Shutdown()
end
