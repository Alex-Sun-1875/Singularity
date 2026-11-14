require("validation.CharacterPreview")
local startPreview=Start
function Start()
    startPreview()
    local name,phase="run",.25
    for _,arg in ipairs(GetArguments()) do
        name=arg:match("^%-motion=(%a+)$") or name
        phase=tonumber(arg:match("^%-phase=([%d.]+)$")) or phase
    end
    local p=CharacterPreviewState
    local animation=cache:GetResource("Animation",p.assets.clips[name])
    p.controller:PlayExclusive(p.assets.clips[name],0,false,0)
    p.controller:SetTime(p.assets.clips[name],animation.length*phase)
    p.controller:SetSpeed(p.assets.clips[name],0)
end
