-- Mock-only cache regression for RS checksum script, no ROM or mGBA required.
-- Run: lua tests/rs_checksums/cache_mock.lua "Gen 3/mGBA/RS_RNG_Checksums_mGBA.lua"
-- Requires Lua 5.3+ (bitwise operators); writes a disposable synthetic .sav.
local srcPath = assert(arg[1], "Supply path to optimized checksum Lua")
local file = assert(io.open(srcPath, "rb"))
local source = assert(file:read("*a"))
file:close()

local fixture = os.tmpname()
local function writeFixture(short)
 local file = assert(io.open(fixture, "wb"))
 file:write(string.rep("\0", short and 32 or 0x20000))
 if not short then
  for i = 0, 0x1B do
   local addr = 0xFF7 + i * 0x1000
   file:seek("set", addr - 1)
   -- High byte at 0-based addr, low byte at addr-1.
   file:write(string.char(i, 0xA0 + i))
  end
 end
 file:close()
end
writeFixture(false)

local quotedFixture = string.format("%q", fixture)
source = source:gsub("local savePath = [^\r\n]+", "local savePath = "..quotedFixture, 1)

local realTime = os.time
local now = 100
os.time = function() return now end

local realOpen = io.open
local opens = 0
io.open = function(path,mode)
 if path == fixture and mode == "rb" then opens = opens + 1 end
 return realOpen(path,mode)
end

console = {}
function console:createBuffer()
 return {setSize=function() end,clear=function() end, print=function() end}
end
emu = {}
function emu:read8(addr)
 if addr == 0x80000AE then return 0x56 end  -- Ruby
 if addr == 0x80000AF then return 0x45 end  -- USA
 return 0
end
function emu:read16() return 0 end
function emu:read32() return 0 end
function emu:readRange() return string.rep("\0",8) end
function emu:currentFrame() return 0 end
callbacks = {}
function callbacks:add() end

local compiled, loadError = load(source, "@rs_checksum_under_test", "t")
assert(compiled, loadError)
compiled()
assert(type(getChecksumsList)=="function", "cache getter missing")
assert(type(invalidateChecksumsCache)=="function", "cache invalidation missing")

local checksums, err = getChecksumsList()
assert(not err and checksums and #checksums==28)
local expectedXor = 0
for i = 0, 27 do
 local expected = string.format("%02X%02X\n", 0xA0+i, i)
 assert(checksums[i+1]==expected, ("segment %d mismatch"):format(i))
 expectedXor = expectedXor ~ ((0xA0+i)*256+i)
end
assert(getCurrentXORChecksumSeed(checksums)==expectedXor, "XOR formula drift")
assert(opens==1, "first checksum read failed")

for _ = 1, 960 do
 local same = getChecksumsList()
 assert(same == checksums, "cache not reused during same real second")
end
assert(opens==1, "per-frame IO not eliminated")

now = 101
local fresh = getChecksumsList()
assert(fresh and #fresh==28 and opens==2, "periodic refresh failed")
assert(fresh~=checksums, "refresh did not replace snapshot")

os.remove(fixture)
now = 102
local missing, reason = getChecksumsList()
assert(missing==nil and reason and opens==3, "missing file should be handled")
for _ = 1, 500 do assert(getChecksumsList()==nil) end
assert(opens==3, "missing file retried per simulated frame")

writeFixture(true)
now = 103
local short, shortReason = getChecksumsList()
assert(short==nil and shortReason:find("short") and opens==4, "short file should be handled")

writeFixture(false)
now = 104
local back = getChecksumsList()
assert(back and #back==28 and opens==5, "recovery from short file failed")

now = 99 -- A clock adjustment invalidates cache.
assert(getChecksumsList() and opens==6, "clock rollback was not handled")
invalidateChecksumsCache()
assert(getChecksumsList() and opens==7, "manual invalidate did not refresh")

io.open = realOpen
os.time = realTime
os.remove(fixture)
print("PASS: 28 segment parity, XOR, 960-frame cache, refresh, missing, short, recovery, clock rollback, invalidation")
