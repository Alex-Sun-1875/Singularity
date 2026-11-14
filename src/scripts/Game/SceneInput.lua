-- Transparent UI input surface over the actual 3D viewport. No portrait tokens.
local UI=require("urhox-libs/UI")
local SceneInput=UI.Widget:Extend("ChapterSceneInput")
function SceneInput:Init(props) UI.Widget.Init(self,props); self.app=props.app end
function SceneInput:Pointer(event)
    if not self.app.scene3d then return end
    local width,height=UI.GetViewportSize()
    local x,y=self.app.scene3d:GroundPoint(event.x/width,event.y/height)
    if not x then return end
    local p=self.app.game.player
    self.app.aim=math.atan(y-p.y,x-p.x)
    self.app.mouseAim=event.pointerType=="mouse"
end
function SceneInput:OnPointerDown(event)
    self:Pointer(event)
    if event:IsPrimaryAction() then self.app.worldAttack=true end
end
function SceneInput:OnPointerMove(event) self:Pointer(event) end
function SceneInput:OnPointerUp() self.app.worldAttack=false end
function SceneInput:OnPointerCancel() self.app.worldAttack=false end
function SceneInput:Render(g)
    if not self.app.scene3d then return end
    local width,height=UI.GetViewportSize()
    local game=self.app.game
    local function text(x,y,heightOffset,label)
        local p=self.app.scene3d:ScreenPoint(x,y,heightOffset)
        if p.x<0 or p.x>1 or p.y<0 or p.y>1 then return end
        nvgFontFace(g,"sans"); nvgFontSize(g,15)
        nvgTextAlign(g,NVG_ALIGN_CENTER+NVG_ALIGN_MIDDLE)
        nvgFillColor(g,nvgRGBA(15,22,17,220)); nvgText(g,p.x*width+1,p.y*height+2,label)
        nvgFillColor(g,nvgRGBA(237,223,184,255)); nvgText(g,p.x*width,p.y*height,label)
    end
    for _,gate in ipairs(game:Map().exits) do text(gate.x,gate.y,0.7,"E  ·  "..gate.label) end
    for _,chest in ipairs(game:Map().chests) do if not chest.opened then text(chest.x,chest.y,1,"E  ·  搜寻") end end
    if self.app.scene3d.actors.mira then text(420,380,2.1,"弥菈  ·  E 交谈") end
    if game.scene=="camp" then text(230,545,0.5,"E  ·  篝火休整") end
    if game.scene=="pass" then text(1420,405,1.6,"E  ·  遗物匣") end
end
return SceneInput
