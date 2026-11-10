-- Offline mGBA API mock for P1 behaviour regression. Not an emulator.
-- Usage: lua frlg_mock.lua <script.lua> <idle|tid|seed> <speed> <ticks>
local file, mode, speed, ticks = arg[1], arg[2], tonumber(arg[3] or 1), tonumber(arg[4] or 200)
assert(file and (mode=="idle" or mode=="tid" or mode=="seed"))
local tick, emuFrame, initial, currentSeed = 0, 0, 0xABCD, 0xABCD
local keys, shift, watchpoint = {}, false, nil
local actions, rngTrace = {}, {}
local reads, prints, clears = 0, 0, 0
local function action(s) actions[#actions+1]=s end
C = {GBA_KEY={A=1,B=2,START=4,SELECT=8}}
console = {}
function console:createBuffer(name)
 local buf={text=""}
 function buf:setSize(width,height) end
 function buf:clear() clears=clears+1;self.text="" end
 function buf:print(s) prints=prints+1;self.text=self.text..s end
 return buf
end
input = {}
function input:isKeyActive(n) return n==8388658 and shift end
emu = {}
function emu:reset() emuFrame=0;action("reset") end
function emu:currentFrame() return emuFrame end
function emu:read8(addr)
 reads=reads+1
 if addr==0x080000AE then return 0x52 end -- FireRed
 if addr==0x080000AF then return 0x45 end -- English
 return 0
end
function emu:read16(addr)
 reads=reads+1
 return addr==0x02020000 and initial or 0
end
function emu:read32(addr)
 reads=reads+1
 return addr==0x03005000 and currentSeed or 0
end
function emu:getKeys() return 0 end
function emu:getKey(key) return keys[key] and 1 or 0 end
function emu:addKey(key) keys[key]=true;action("add:"..key.."@"..emuFrame) end
function emu:clearKey(key) keys[key]=nil;action("clear:"..key.."@"..emuFrame) end
function emu:setWatchpoint(cb,addr,size)
 assert(addr==0x02020000 and size==1)
 watchpoint=cb
 return 1
end
function emu:saveStateBuffer()
 action("savebuf@"..emuFrame)
 return {frame=emuFrame,initial=initial,seed=currentSeed}
end
function emu:loadStateBuffer(state)
 action("loadbuf@"..emuFrame.."->"..state.frame)
 emuFrame,initial,currentSeed=state.frame,state.initial,state.seed
end
function emu:saveStateSlot(slot) action("saveSlot@"..emuFrame) end
function emu:loadStateSlot(slot) action("loadSlot@"..emuFrame) end
callbacks={}
function callbacks:add(name,fn)self[name]=fn end
-- Intentionally deterministic fake wall clock. In a ROM run this is os.time.
local realTime=os.time
os.time=function() return math.floor((tick-1)/(60*speed)) end
assert(loadfile(file))()
assert(callbacks.frame,"no frame callback")
local function advances()
 for i=1,32 do
  local name,value=debug.getupvalue(getRngInfo,i)
  if name=="advances" then return value end
 end
 error("unable to inspect private RNG advances via debug API")
end
for i=1,ticks do
 tick,emuFrame=tick+1,emuFrame+1
 currentSeed=(currentSeed*0x41C64E6D+0x6073)&0xFFFFFFFF
 if tick==2 and mode~="idle" then
  shift=true
  keys[mode=="tid" and C.GBA_KEY.START or C.GBA_KEY.SELECT]=true
 elseif tick==3 then
  shift=false
  keys[C.GBA_KEY.START],keys[C.GBA_KEY.SELECT]=nil,nil
 end
 if mode=="tid" and (tick==7 or tick==17 or tick==27) then
  initial=(tick==7 and 5 or tick==17 and 8 or 1)
  action("write:"..initial.."@"..emuFrame)
  watchpoint()
 elseif mode=="seed" and (tick==49 or tick==100) then
  initial=(tick==49 and 0x1111 or 0x2222)
  action("write:"..initial.."@"..emuFrame)
  watchpoint()
 end
 callbacks.frame()
 rngTrace[#rngTrace+1]=tostring(advances())
end
print("ACTIONS_BEGIN")
for _,s in ipairs(actions) do print(s) end
print("ACTIONS_END")
print("RNG_BEGIN")
print(table.concat(rngTrace,","))
print("RNG_END")
print(("METRIC reads=%d prints=%d clears=%d callbacks=%d"):format(reads,prints,clears,tick))
os.time=realTime
