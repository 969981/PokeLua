-- Mock-only per-frame RNG and Emerald TID-Bot trace for E/RS mGBA scripts.
-- Usage: lua tests/optimization/mgba_exact_mock.lua <E|RS> <script.lua>
local game, file = assert(arg[1]), assert(arg[2])
assert(game=="E" or game=="RS")
local tick, frame = 0, 0
local seed, tid = 0, 0
local shift = false
local buttons = {}
local savedWatch = nil
local events = {}
local printCalls = 0
local realOsTime=os.time
os.time=function()return math.floor(tick/60)end
C={GBA_KEY={A=1,B=2,START=4,SELECT=8}}
console={}
function console:createBuffer()
 local buf={}
 function buf:setSize() end
 function buf:clear() end
 function buf:print()printCalls=printCalls+1 end
 return buf
end
local dummy=console:createBuffer()
input={}
function input:isKeyActive(k) return k==8388658 and shift end
emu={}
function emu:reset()frame=0;events[#events+1]="reset"end
function emu:currentFrame()return frame end
function emu:read8(addr)
 if addr==0x80000AE then return game=="E" and 0x45 or 0x56 end
 if addr==0x80000AF then return 0x45 end
 return 0
end
function emu:read16(addr)
 if addr==0x2020000 then return tid end
 return seed & 0xFFFF
end
function emu:read32(addr) return seed end
function emu:readRange()return string.rep("\0",16) end
function emu:getKey(k)return buttons[k] and 1 or 0 end
function emu:getKeys()
 if tick==9 or tick==10 then return 0x120 end
 if tick==20 or tick==21 then return 0x110 end
 if tick==29 then return 0x120 end
 return 0
end
function emu:addKey(k)buttons[k]=true;events[#events+1]="add:"..k.."@"..frame end
function emu:clearKey(k)buttons[k]=nil;events[#events+1]="clear:"..k.."@"..frame end
function emu:saveStateBuffer()
 events[#events+1]="save@"..frame
 return {frame=frame,seed=seed,tid=tid}
end
function emu:loadStateBuffer(t)
 events[#events+1]="load@"..frame.."->"..t.frame
 frame,seed,tid=t.frame,t.seed,t.tid
end
function emu:setWatchpoint(fn) savedWatch=fn;return 1 end
function emu:saveStateSlot() end
function emu:loadStateSlot() end
callbacks={}
function callbacks:add(name,fn)self[name]=fn end

local handle=assert(io.open(file,"rb"))
local script=assert(handle:read("*a"));handle:close()
if game=="E" then
 script=script:gsub("local botTargetTIDs%s*=%s*{[^}]*}", "local botTargetTIDs = {1234}", 1)
end
local compiled,err=load(script,"@mgba_source","t")
assert(compiled,err)
compiled()
assert(callbacks.frame)

-- No ROM: stub heavyweight screen decoding, but still exercise showRngInfo,
-- mode input, and the original Bot control in each callback.
updateCaptureBuffer=function() showRngInfo(dummy) end
updateBreedingBuffer=function() showRngInfo(dummy) end
updateRoamerBuffer=function() showRngInfo(dummy) end
updatePandoraBuffer=function() showRngInfo(dummy) end
updatePokemonInfoBuffer=function()
 showRngInfo(dummy)
 getInfoInput(dummy)
end
-- Keep upstream updateTIDBotBuffer intact: it owns Bot logic in the original
-- and owns rendering only in P1. In both paths its exact-lane logic still runs.

local function readModeIndex()
 local target= pollInfoModeInput or getInfoInput
 for i=1,25 do
  local name,value=debug.getupvalue(target,i)
  if not name then break end
  if name=="infoIndex" then return value end
 end
 return -1
end

local advancesTrace={}
for i=1,240 do
 tick=tick+1
 frame=frame+1
 seed=(seed * 0x41C64E6D + 0x6073) & 0xFFFFFFFF
 if game=="E" then
  if tick==2 then shift=true; buttons[C.GBA_KEY.START]=true end
  if tick==3 then shift=false; buttons[C.GBA_KEY.START]=nil end
  if tick==45 or tick==85 or tick==140 then
   tid=(tick==45 and 10 or tick==85 and 20 or 1234)
   events[#events+1]="watch:"..tid.."@"..frame
   assert(savedWatch,"write watchpoint missing")
   savedWatch()
  end
 end
 callbacks.frame()
 local _,curr,adv=getRngInfo()
 advancesTrace[#advancesTrace+1]=string.format("%08X/%d/%d",curr,adv,readModeIndex())
end
print("EVENTS")
for _,event in ipairs(events) do print(event) end
print("ADVANCES")
print(table.concat(advancesTrace,","))
print("PRINTS "..printCalls)
os.time=realOsTime
