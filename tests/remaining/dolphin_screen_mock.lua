-- Synthetic static/dynamic RAM trace for Colosseum Light/Full/XD.
-- Usage: lua tests/remaining/dolphin_screen_mock.lua <script.lua> <colo|xd>
local path, game = assert(arg[1]), assert(arg[2])
local pointerAddr = game == "xd" and 0x4EB6F8 or 0x7EFDCC
local seedAddr = game == "xd" and 0x4E8610 or 0x478C90
local seed = 0x12345
local currentScreen = ""
local displays, squareRoots = 0, 0
ReadValue8 = function(addr)
 if addr == 0x3 then return 0x45 end -- US addresses
 return 10
end
ReadValue16 = function(addr) return 15 end
ReadValue32 = function(addr)
 if addr == pointerAddr then return 0x81000000 end
 if addr == seedAddr then return seed end
 return 0x12345678
end
SetScreenText = function(text)
 displays = displays + 1
 currentScreen = text
end
local oldSqrt = math.sqrt
math.sqrt = function(x)
 squareRoots = squareRoots + 1
 return oldSqrt(x)
end
local ok,err=pcall(dofile,path)
if not ok then error("Lua source loading failed: "..tostring(err)) end
assert(type(onScriptUpdate)=="function" and type(onScriptStart)=="function")
onScriptStart()
for frame=1,8 do
 if frame==5 then seed=0x6789ABC end
 onScriptUpdate()
 print("===FRAME "..frame.."===")
 print(currentScreen)
end
print("DISPLAY_COUNT "..displays)
print("SQRT_COUNT "..squareRoots)
