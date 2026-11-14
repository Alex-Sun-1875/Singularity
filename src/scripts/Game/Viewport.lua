local Viewport={}
function Viewport.Fit(l)
    local scale=math.min(l.w/1600,l.h/900)
    return {x=l.x+(l.w-1600*scale)/2,y=l.y+(l.h-900*scale)/2,scale=scale}
end
function Viewport.ToWorld(v,x,y) return (x-v.x)/v.scale,(y-v.y)/v.scale end
return Viewport
