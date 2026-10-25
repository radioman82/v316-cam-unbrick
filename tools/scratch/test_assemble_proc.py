import subprocess, struct

s_code = """
.syntax unified
.thumb

.org 0x5afe0

.global func_proc
func_proc:
    push {r4, r5, lr}
    mov r4, r0              @ r4 = self
    mov r5, r2              @ r5 = sel (0=Foto, 1=Video, 2=Stream, 3=Setup)
    
    cmp r5, #3
    bne .Lnot_setup
    @ SETUP: call BottomBarFunctionProc(self, 1)
    mov r0, r4
    movs r1, #1
    bl 0x5aeac
    pop {r4, r5, pc}

.Lnot_setup:
    @ Close FunctionSelectWindow: r0 = self->func_win (offset 0x114), bl 0x697ac
    ldr.w r0, [r4, #0x114]
    bl 0x697ac
    
    cmp r5, #2
    bne .Lmode_sel
    @ STREAMING: call system("sh /mnt/extsd/start_streaming.sh &")
    ldr r0, =0x1f5130
    blx 0x1c94c             @ system@plt
    pop {r4, r5, pc}

.Lmode_sel:
    @ Get current mode: r0 = GetCurMode(self) (0=Video, 6=Foto)
    mov r0, r4
    bl 0x5a658
    @ If sel == 0 (Foto) and r0 != 6: toggle!
    cmp r5, #0
    bne .Lcheck_video
    cmp r0, #6
    beq .Ldone
    b .Ltoggle

.Lcheck_video:
    @ sel == 1 (Video): if r0 == 0: already video, done!
    cbz r0, .Ldone

.Ltoggle:
    @ PostMsg(self, self, 59, 1)
    movs r3, #1
    movs r2, #59
    mov r1, r4
    mov r0, r4
    bl 0x5aa08

.Ldone:
    pop {r4, r5, pc}
"""

with open(r"d:\v316cm\asm_patch.s", "w") as f:
    f.write(s_code)

as_cmd = [
    r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin\arm-none-eabi-as.EXE',
    '-mthumb', '-o', r'd:\v316cm\asm_patch.o', r'd:\v316cm\asm_patch.s'
]
subprocess.check_call(as_cmd)

objdump_cmd = [
    r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin\arm-none-eabi-objdump.EXE',
    '-d', r'd:\v316cm\asm_patch.o'
]
out = subprocess.check_output(objdump_cmd).decode()
print("Disassembly:")
print(out)
