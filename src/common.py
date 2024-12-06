import gdb
from enum import Enum, IntEnum

def RemovePrint(str: str, *args):
    print(("[debug]-" + str) % args)

def Val_(o: gdb.Value) -> gdb.Value:
    return o['value_']

def S2V(o: gdb.Value) -> gdb.Value:
    #/* convert a 'StackValue' to a 'TValue' */
    return (o['val']).address

def Tvalue(o: gdb.Value) -> gdb.Value:
    return (o['value_'])

def Novariant(t: int) -> int:
    return t & 0X0F

def Rawtt(o: gdb.Value) -> int:
    #/* raw type tag of a TValue */
    return int(o['tt_'])

def Ttype(o: gdb.Value) -> int:
    return Novariant(Rawtt(o))

def WithVariant(t: int) -> int:
    return (t) & 0X3F

def TtypeTag(o: int) -> int:
    return WithVariant(Rawtt(o))

def MakeVariant(t: int, v: int) -> int:
    return (t | (v << 4))

def CheckType(o: gdb.Value, t: int) -> bool:
    return Ttype(o) == t

def CheckTag(o: gdb.Value, t: int) -> bool:
    return Rawtt(o) == t

def TtIsFunction(o: gdb.Value) -> bool:
    return CheckType(o, LuaType.LUA_TFUNCTION)

def TtIsLClosure(o: gdb.Value) -> bool:
    return CheckTag(o, Ctb(LUA_VLCL))

def TtIsLcf(o: gdb.Value) -> bool:
    return CheckTag(o, LUA_VLCF)

def TtIsCClosure(o: gdb.Value) -> bool:
    return CheckTag(o, Ctb(LUA_VCCL))

def TtIsClosure(o: gdb.Value) -> bool:
    return (TtIsLClosure(o) or TtIsCClosure(o))

def PcRel(pc: gdb.Value, p: gdb.Value) -> int:
    return int(pc - p['code'] - 1)


def Cast2TargetTypePointer(pointer: gdb.Value, targetTypeName: str) -> gdb.Value:
    targetType = gdb.lookup_type(targetTypeName)
    return pointer.cast(targetType.pointer())

def CastTvaluePointer2GcUnionPointer(tvaluePointer: gdb.Value) -> gdb.Value:
    return Cast2TargetTypePointer(tvaluePointer['value_']['gc'], "union GCUnion")

def CastPointer2LuaStatePointer(poninter: gdb.Value) -> gdb.Value:
    return Cast2TargetTypePointer(poninter, "lua_State")

class CallInfoValue(object):
    
    CIST_OAH = (1 << 0)
    CIST_C = (1 << 1)
    CIST_FRESH = (1 << 2)
    CIST_HOOKED = (1 << 3)
    CIST_YPCALL = (1 << 4)
    CIST_TAIL = (1 << 5)
    CIST_HOOKYIELD = (1 << 6)
    CIST_FIN = (1 << 7)
    CIST_TRAN = (1 << 8)
    CIST_CLSRET = (1 << 9)

    def __init__(self, luaStatePointer: gdb.Value, callInfoPointer: gdb.Value):
        self.luaStatePointer = luaStatePointer
        self.callInfoPointer = callInfoPointer

    def IsLua(self) -> bool:
        if self.callInfoPointer == None:
            return False
        return (not (self.callInfoPointer['callstatus'] & CallInfoValue.CIST_C))
    
    def GetClosurePointer(self) -> gdb.Value:
        tvaluePointer = self.callInfoPointer['func']['p']['val'].address
        gcUnionPointer = CastTvaluePointer2GcUnionPointer(tvaluePointer)
        return gcUnionPointer['cl'].address
    
    def GetCallInfoPointer(self) -> gdb.Value:
        return self.callInfoPointer

    def CurrentPc(self):
        if not self.IsLua():
            raise RuntimeError("not Lua CallInfo")
        closurePointer = self.GetClosurePointer()
        return PcRel(self.callInfoPointer['u']['l']['savedpc'], closurePointer['l']['p'])


class LuaType(IntEnum):
    LUA_TNONE = -1
    LUA_TNIL = 0
    LUA_TBOOLEAN = 1
    LUA_TLIGHTUSERDATA = 2
    LUA_TNUMBER = 3
    LUA_TSTRING = 4
    LUA_TTABLE = 5
    LUA_TFUNCTION = 6
    LUA_TUSERDATA = 7
    LUA_TTHREAD = 8
    LUA_NUMTYPES = 9

    # Extra types for collectable non-values
    LUA_TUPVAL = LUA_NUMTYPES 
    LUA_TPROTO = LUA_NUMTYPES + 1
    LUA_TDEADKEY = LUA_NUMTYPES + 2

LuaType2TypeName = {}
for typeEnum in LuaType:
    LuaType2TypeName[typeEnum] = typeEnum.name

MAXIWTHABS = 128

LUA_VLCL = MakeVariant(int(LuaType.LUA_TFUNCTION), 0)  # /* Lua closure */
LUA_VLCF = MakeVariant(int(LuaType.LUA_TFUNCTION), 1)  # /* light C function */
LUA_VCCL = MakeVariant(int(LuaType.LUA_TFUNCTION), 2)  # /* C closure */


LUA_VSHRSTR = MakeVariant(LuaType.LUA_TSTRING, 0) 
LUA_VLNGSTR	= MakeVariant(LuaType.LUA_TSTRING, 1) 

def Getstr(tStringPointer: gdb.Value) -> str:
    length = Tsslen(tStringPointer)
    return tStringPointer['contents'].string(length=length)

def Tsslen(tStringPointer: gdb.Value) -> int:
    if int(tStringPointer['tt']) == LUA_VSHRSTR:
        return int(tStringPointer['shrlen'])
    else:
        return int(tStringPointer['u']['lnglen'])

LUA_VNUMINT = MakeVariant(LuaType.LUA_TNUMBER, 0)
LUA_VNUMFLT = MakeVariant(LuaType.LUA_TNUMBER, 1)

def TtIsNumber(o: gdb.Value) -> bool:
    return CheckType(o, LuaType.LUA_TNUMBER)

def TtIsFloat(o: gdb.Value) -> bool:
    return CheckType(o, LUA_VNUMFLT)

def TtIsInteger(o: gdb.Value) -> bool:
    return CheckType(o, LUA_VNUMINT)

def NoLuaClosure(closurePointer: gdb.Value) -> bool:
    return closurePointer == None or closurePointer['c']['tt'] == LUA_VCCL

LUA_VFALSE = MakeVariant(LuaType.LUA_TBOOLEAN, 0)
LUA_VTRUE = MakeVariant(LuaType.LUA_TBOOLEAN, 1)

def TtIsBoolean(o: gdb.Value) -> bool:
    return CheckType(o, LuaType.LUA_TBOOLEAN)

def TtIsFalse(o: gdb.Value) -> bool:
    return CheckType(o, LUA_VFALSE)

def TtIsTrue(o: gdb.Value) -> bool:
    return CheckType(o, LUA_VTRUE)


BIT_ISCOLLECTABLE = (1 << 6)

def IsCollectable(o: gdb.Value) -> bool:
    return Rawtt(o) & BIT_ISCOLLECTABLE

# /* mark a tag as collectable */
def Ctb(t: int) -> int:
    return (t) | BIT_ISCOLLECTABLE

LUA_VTHREAD = MakeVariant(LuaType.LUA_TTHREAD, 0)

def TtIsThread(o: gdb.Value) -> bool:
    return CheckTag(o, Ctb(LUA_VTHREAD))


LUA_VLIGHTUSERDATA = MakeVariant(LuaType.LUA_TLIGHTUSERDATA, 0)
LUA_VUSERDATA = MakeVariant(LuaType.LUA_TUSERDATA, 0)
LUA_VTABLE = MakeVariant(LuaType.LUA_TTABLE, 0)
LUA_VPROTO = MakeVariant(LuaType.LUA_TPROTO, 0)
LUA_VTHREAD = MakeVariant(LuaType.LUA_TTHREAD, 0)
LUA_VUPVAL =  MakeVariant(LuaType.LUA_TUPVAL, 0)

def CheckExp(exp: bool, r: any) -> any:
    if(not exp):
        raise RuntimeError("CheckExp exp is False")
    return r

"""
/* macros to convert a GCObject into a specific value */
#define gco2ts(o)  \
	check_exp(novariant((o)->tt) == LUA_TSTRING, &((cast_u(o))->ts))
#define gco2u(o)  check_exp((o)->tt == LUA_VUSERDATA, &((cast_u(o))->u))
#define gco2lcl(o)  check_exp((o)->tt == LUA_VLCL, &((cast_u(o))->cl.l))
#define gco2ccl(o)  check_exp((o)->tt == LUA_VCCL, &((cast_u(o))->cl.c))
#define gco2cl(o)  \
	check_exp(novariant((o)->tt) == LUA_TFUNCTION, &((cast_u(o))->cl))
#define gco2t(o)  check_exp((o)->tt == LUA_VTABLE, &((cast_u(o))->h))
#define gco2p(o)  check_exp((o)->tt == LUA_VPROTO, &((cast_u(o))->p))
#define gco2th(o)  check_exp((o)->tt == LUA_VTHREAD, &((cast_u(o))->th))
#define gco2upv(o)	check_exp((o)->tt == LUA_VUPVAL, &((cast_u(o))->upv))
"""

def CastU(o: gdb.Value) -> gdb.Value:
    return Cast2TargetTypePointer(o, "union GCUnion")


def GCo2Ts(o: gdb.Value) -> gdb.Value:
    return CheckExp(Novariant(o['tt']) == LuaType.LUA_TSTRING, (CastU(o)['ts']).address)

def GCo2U(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VUSERDATA, (CastU(o)['u']).address)

def GCo2Lcl(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VLCL, (CastU(o)['cl']['l']).address)

def GCo2Ccl(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VCCL, (CastU(o)['cl']['c']).address)

def GCo2Cl(o: gdb.Value) -> gdb.Value:
    return CheckExp(Novariant(o['tt']) == LuaType.LUA_TFUNCTION, (CastU(o)['cl']).address)

def GCo2T(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VTABLE, (CastU(o)['h']).address)

def GCo2P(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VPROTO, (CastU(o)['p']).address)

def GCo2Th(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VTHREAD, (CastU(o)['th']).address)

def GCo2Upv(o: gdb.Value) -> gdb.Value:
    return CheckExp((o['tt']) == LUA_VUPVAL, (CastU(o)['upv']).address)



#define clvalue(o)	check_exp(ttisclosure(o), gco2cl(val_(o).gc))
#define clLvalue(o)	check_exp(ttisLclosure(o), gco2lcl(val_(o).gc))
#define fvalue(o)	check_exp(ttislcf(o), val_(o).f)
#define clCvalue(o)	check_exp(ttisCclosure(o), gco2ccl(val_(o).gc))
def ClValue(o: gdb.Value) -> gdb.Value:
    return CheckExp(TtIsCClosure(o), GCo2Cl(Val_(o)['gc']))

def ClLvalue(o: gdb.Value) -> gdb.Value:
    return CheckExp(TtIsLClosure(o), GCo2Lcl(Val_(o)['gc']))

def FValue(o: gdb.Value) -> gdb.Value:
    return CheckExp(TtIsLcf(o, Val_(o)['f']))

def ClCValue(o: gdb.Value) -> gdb.Value:
    return CheckExp(TtIsCClosure(o), GCo2Ccl(Val_(o)['gc']))


"""
/*
@@ LUA_IDSIZE gives the maximum size for the description of the source
** of a function in debug information.
** CHANGE it if you want a different size.
*/
"""
LUA_IDSIZE = 60



class TValueObj(object):

    def __init__(self, tValuePointer) -> None:
        self.tValuePointer = tValuePointer
    
    def GetType(self) -> LuaType:
        return Ttype(self.tValuePointer)

    def GetTypeName(self) -> str:
        return LuaType2TypeName[Ttype(self.tValuePointer)]
    
    def GetValue(self) -> any:
        """
        return python obj
        """

        tType = self.GetType()
        value = self.tValuePointer['value_']
        if tType == LuaType.LUA_TNUMBER:
            if TtIsInteger(self.tValuePointer):
                return int(value['i'])
            else:
                return float(value['n'])
        elif tType == LuaType.LUA_TBOOLEAN:
            if TtIsTrue(self.tValuePointer):
                return True
            else:
                return False
        elif tType == LuaType.LUA_TFUNCTION:
            return str("((lua_CFunction *)" + str(value['f']) + ")")
        elif tType == LuaType.LUA_TLIGHTUSERDATA:
            return str("((void *)" + str(value['p']) + ")")
        elif tType == LuaType.LUA_TNIL or tType == LuaType.LUA_TNONE:
            return None
        elif tType == LuaType.LUA_TSTRING:
            return Getstr(value['p'])
        elif tType == LuaType.LUA_TTABLE:
            return str("((struct Table *)" + str(value['p']) + ")")



LUAI_MAXSTACK = 1000000
LUA_REGISTRYINDEX = (-LUAI_MAXSTACK - 1000)

def LuaUpValueIndex(i: int) -> int:
    return LUA_REGISTRYINDEX - i

def IsPseudo(i: int) -> bool:
    return i <= LUA_REGISTRYINDEX

def IsUpValue(i: int) -> bool:
    return i < LUA_REGISTRYINDEX


def Index2Value(LuaStatePointer: gdb.Value, idx: int) -> gdb.Value:
    callInfoPointer = LuaStatePointer['ci']
    if(idx > 0):
        o = callInfoPointer['func']['p'] + idx
        if(o >= LuaStatePointer['top']['p']):
            return LuaStatePointer['l_G']['nilvalue'].address
        else:
            return S2V(o)
    elif (not IsPseudo(idx)):
         return S2V(LuaStatePointer['top']['p'] + idx)
    elif (idx == LUA_REGISTRYINDEX):
        return LuaStatePointer['l_G']['l_registry'].address
    else:
        idx = LUA_REGISTRYINDEX - idx
        if(TtIsCClosure(S2V(callInfoPointer['func']['p']))):
            func = ClCValue(S2V(callInfoPointer['func']['p']))
            return func['upvalue'][idx - 1].address if idx <= func['nupvalues'] else LuaStatePointer['l_G']['nilvalue'].address
        else:
            return LuaStatePointer['l_G']['nilvalue'].address


