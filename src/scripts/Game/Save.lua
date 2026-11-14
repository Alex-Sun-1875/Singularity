local Chapter = require("Game.Chapter")
---@class ChapterSave
---@field prefix string
---@field generation number
---@field corrupt string[]
---@field loaded boolean
local Save = {}
Save.__index=Save
local function checksum(text)
    local n=1
    for i=1,#text do n=(n*31+string.byte(text,i))%2147483647 end
    return n
end
local function read(path)
    if not fileSystem:FileExists(path) then return nil end
    local f=File(path,FILE_READ)
    if not f or not f:IsOpen() then return false end
    local text=f:ReadString(); f:Close()
    return text
end
local function write(path,text)
    local f=File(path,FILE_WRITE)
    if not f or not f:IsOpen() then return false end
    f:WriteString(text); f:Close()
    return read(path)==text
end
function Save.New(prefix)
    return setmetatable({prefix=prefix or "whitebranch_m1",generation=0,corrupt={},loaded=false},Save)
end
function Save:Path(slot) return self.prefix.."."..slot..".json" end
function Save:Load()
    self.corrupt={}
    local best,bestGeneration=nil,-1
    for _,slot in ipairs({"a","b"}) do
        local raw=read(self:Path(slot))
        if raw~=nil then
            local ok,game,generation=pcall(function()
                assert(type(raw)=="string" and #raw<400000)
                local envelope=cjson.decode(raw)
                assert(envelope.version==1 and type(envelope.payload)=="string")
                assert(type(envelope.generation)=="number" and envelope.generation>=1 and envelope.generation%1==0)
                assert(envelope.checksum==checksum(envelope.payload))
                return assert(Chapter.Restore(cjson.decode(envelope.payload))),envelope.generation
            end)
            if ok then
                if generation>bestGeneration then best,bestGeneration=game,generation end
            else self.corrupt[#self.corrupt+1]=slot end
        end
    end
    self.generation=math.max(0,bestGeneration)
    self.loaded=true
    local warning=#self.corrupt>0 and "部分存档损坏：已保留原文件，自动保存已暂停。可从菜单新建旅程并备份旧档。" or nil
    return best,warning
end
function Save:Write(game)
    if not self.loaded then self:Load() end
    if #self.corrupt>0 then return false,"损坏存档已保留；请在菜单明确选择新旅程。" end
    local ok,payload=pcall(cjson.encode,game:Snapshot())
    if not ok then return false,"保存失败：无法编码当前进度。" end
    local generation=self.generation+1
    local envelope=cjson.encode({version=1,generation=generation,payload=payload,checksum=checksum(payload)})
    local slot=generation%2==1 and "a" or "b"
    if not write(self:Path(slot),envelope) then return false,"保存失败：无法写入本地存档。" end
    self.generation=generation
    game.dirty=false
    return true
end
function Save:StartFresh(game)
    -- Explicit menu action. Preserve both old slots, including damaged evidence.
    for _,slot in ipairs({"a","b"}) do
        local raw=read(self:Path(slot))
        if raw~=nil then
            if type(raw)~="string" or not write(self.prefix..".backup-"..os.time().."-"..self.generation.."-"..slot..".json",raw) then
                return false,"旧档备份失败，未建立新旅程。"
            end
        end
    end
    self.corrupt={}; self.loaded=true
    -- Write both generations so the previous journey cannot reappear as fallback.
    local ok,err=self:Write(game)
    if not ok then return ok,err end
    return self:Write(game)
end
return Save
