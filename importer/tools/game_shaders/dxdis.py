"""A small disassembler for DXBC shader model 4 and 5 bytecode, as Unity compiles D3D11 shaders:
enough for the games' create and lit shaders (issue 30). `dis(dxbc)` returns the program as text,
one instruction per line (`mad r0.xy, v1.xyxx, cb0[11].xyxx, cb0[11].zwzz`); `dump.py` names its
constants and textures.

Operands: temporaries `r`, inputs `v`, outputs `o`, samplers `s`, textures `t`, constant buffers
`cb<slot>[<register>]`, literals `l(...)`; `-`, `abs` and `_sat` as in Microsoft's own listings.
Opcodes this doesn't know print as `op<number>`; add them to OPS by their D3D10_SB_OPCODE number.
"""
import struct
import sys
OPS="add and break breakc call callc case continue continuec cut default deriv_rtx deriv_rty discard div dp2 dp3 dp4 else emit emitthencut endif endloop endswitch eq exp frc ftoi ftou ge iadd if ieq ige ilt imad imax imin imul ine ineg ishl ishr itof label ld ld_ms log loop lt mad min max customdata mov movc mul ne nop not or resinfo ret retc round_ne round_ni round_pi round_z rsq sample sample_c sample_c_lz sample_l sample_d sample_b sqrt switch sincos udiv ult uge umul umad umax umin ushr utof xor dcl_resource dcl_constantbuffer dcl_sampler dcl_indexrange dcl_gs_out_topology dcl_gs_in_prim dcl_maxout dcl_input dcl_input_sgv dcl_input_siv dcl_input_ps dcl_input_ps_sgv dcl_input_ps_siv dcl_output dcl_output_sgv dcl_output_siv dcl_temps dcl_indexabletemp dcl_globalflags".split()
REG={0:"r",1:"v",2:"o",3:"x",4:"l",6:"s",7:"t",8:"cb",9:"icb"}
C="xyzw"
def chunks(b):
    n=struct.unpack_from("<I",b,28)[0]
    for i in range(n):
        off=struct.unpack_from("<I",b,32+4*i)[0]
        yield b[off:off+4].decode(), b[off+8:off+8+struct.unpack_from("<I",b,off+4)[0]]
def operand(w,i):
    t=w[i]; i+=1
    ncomp=t&3; sel=(t>>2)&3; typ=(t>>12)&0xff; dim=(t>>20)&3
    mod=""
    if t>>31:
        e=w[i]; i+=1
        m=(e>>6)&0xff; mod={0:"",1:"-",2:"abs ",3:"-abs "}.get(m,"?")
    if ncomp==2:
        if sel==0: comps="."+"".join(C[k] for k in range(4) if (t>>4>>k)&1)
        elif sel==1: comps="."+"".join(C[(t>>(4+2*k))&3] for k in range(4))
        else: comps="."+C[(t>>4)&3]
    else: comps=""
    if typ==4:
        n=4 if ncomp==2 else 1
        vals=[struct.unpack("<f",struct.pack("<I",w[i+k]))[0] for k in range(n)]; i+=n
        return mod+"l("+", ".join(f"{v:.9g}" for v in vals)+")", i
    idx=[]
    for d in range(dim):
        rep=(t>>(22+3*d))&7
        if rep==0: idx.append(str(w[i])); i+=1
        elif rep==2:
            s,i=operand(w,i); idx.append("["+s+"]")
        elif rep==3:
            base=w[i]; i+=1; s,i=operand(w,i); idx.append(f"[{s}+{base}]")
        else: idx.append("?"); i+=1
    name=REG.get(typ,f"T{typ}_")
    if typ==8 and len(idx)==2: s=f"cb{idx[0]}[{idx[1]}]"
    else: s=name+"".join(idx[:1])+"".join(f"[{x}]" for x in idx[1:])
    return mod+s+comps, i
def dis(b):
    out=[]
    for tag,data in chunks(b):
        if tag not in ("SHDR","SHEX"): continue
        w=struct.unpack(f"<{len(data)//4}I",data[:len(data)//4*4])
        i=2
        while i<len(w):
            t=w[i]; op=t&0x7ff
            if op==53:
                ln=w[i+1]; out.append(f"customdata[{ln}]"); i+=ln; continue
            ln=(t>>24)&0x7f
            if ln==0: break
            j=i+1; ext=t>>31
            while ext:
                ext=w[j]>>31; j+=1
            name=OPS[op] if op<len(OPS) else f"op{op}"
            if (t>>13)&1 and op<88: name+="_sat"
            ops=[]
            end=i+ln
            if op in (104,106,94): ops=[str(w[j])] if op==104 else []
            elif op==88:
                s,j=operand(w,j); ops=[s]
            else:
                try:
                    while j<end:
                        s,j=operand(w,j); ops.append(s)
                except Exception as e: ops.append("ERR")
            out.append(name+" "+", ".join(ops)); i=end
    return "\n".join(out)
if __name__=="__main__":
    for p in sys.argv[1:]:
        print("####",p); print(dis(open(p,"rb").read()))
