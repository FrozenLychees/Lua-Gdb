-- gdb -x LuaGdb.py.py -x test/test_coroutine.bp --args src/lua  test/test_coroutine.lua 
-- The Progarm will block at "j = i < 1"  in gdb. 
-- use lua-coroutines, lua-localVal, lua-upVal and other commmands to disaply infomation about lua.

tmp = 100
a = 200
tmp2 = 100
co = coroutine.create(function ()
    
    for i = 1, 3 do
      print("co", i + tmp)
      j = i < 1
      coroutine.yield()
    end
  end)

coroutine.resume(co)    --> co   1

print(coroutine.status(co))   --> suspended

print(coroutine.resume(co))    --> co   2
coroutine.resume(co)    --> co   3

coroutine.resume(co)    -- prints nothing
print(coroutine.resume(co))      --> false   cannot resume dead coroutine
