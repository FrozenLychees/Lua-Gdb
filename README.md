# Lua-Gdb
Support outputting lua5.4 information in gdb

# Test environment
gdb: GNU gdb (Ubuntu 8.1.1-0ubuntu1) 8.1.1
lua: lua-5.4.6
os: Ubuntu 18.04.6 LTS

# Usage Examples

```
gdb ./lua-5.4.6/src/lua 

```

load luaGdb.py
You can use the following method or other methods
```
python
> import sys
> sys.path.append(<path/luaGdb>)
> end
```

Execute Lua code and set the breakpoints
```
r example/test_coroutine.lua
break lvm.c:829
break lvm.c:1643
```

Next, use the corresponding commands to view various information
```
(gdb) lua-backtrace 
stack traceback:
        ...ubuntu/Lua-Gdb/example/test_coroutine/test_corouti:11
```


```
(gdb) lua-coroutines 
[m]Thread:  0x5555557ac268
Thread: 0x5555557b2de8
```

```
(gdb) lua-localVal 
name = (for state), value = 1 pos = 0x5555557b2ee0
name = (for state), value = 2 pos = 0x5555557b2ef0
name = (for state), value = 1 pos = 0x5555557b2f00
name = i, value = 1 pos = 0x5555557b2f10
```

```
(gdb) lua-printStack 
[0] --> [(StackValue*)0x5555557b2f10] --> [LUA_TNUMBER][1]

[1] --> [(StackValue*)0x5555557b2f00] --> [LUA_TNUMBER][1]

[2] --> [(StackValue*)0x5555557b2ef0] --> [LUA_TNUMBER][2]

[3] --> [(StackValue*)0x5555557b2ee0] --> [LUA_TNUMBER][1]

[4] --> [(StackValue*)0x5555557b2ed0] --> [LUA_TFUNCTION][((lua_CFunction *)0x5555557aeae0)]

[5] --> [(StackValue*)0x5555557b2ec0] --> [LUA_TNIL][None]

```

```
(gdb) lua-upVal 
name = _ENV, value = ((struct Table *)0x5555557acc10)
```