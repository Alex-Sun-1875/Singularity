local Tests={}
function Tests.Run()
    local Viewport=require("Game.Viewport")
    for _,size in ipairs({{1280,720},{960,600},{720,1280}}) do
        local v=Viewport.Fit({x=12,y=40,w=size[1],h=size[2]})
        local x,y=Viewport.ToWorld(v,v.x+420*v.scale,v.y+380*v.scale)
        assert(math.abs(x-420)<0.001 and math.abs(y-380)<0.001)
        assert(v.scale>0 and v.scale<=size[1]/1600)
    end
    print("[ViewportTest] PASS world pointer mapping across landscape and portrait sizes")
end
return Tests
