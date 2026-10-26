import subprocess, os

TOOL = r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin'
ASM_CODE = '''
	.syntax unified
	.thumb
	.org 0x5afe0

	.global func_proc
func_proc:
	push	{r4, r5, lr}
	mov	r4, r0			@ r4 = self (PreviewWindow)
	mov	r5, r2			@ r5 = Kachelindex

	ldr.w	r0, [r4, #0x114]	@ FunctionSelectWindow
	bl	0x697ac			@ Close()

	cmp	r5, #3
	beq	.Lsetup

	cmp	r5, #2
	beq	.Lstream

	movs	r2, #4			@ FOTO -> idx 4
	cmp	r5, #0
	beq	.Lpost
	movs	r2, #0			@ VIDEO -> idx 0
.Lpost:
	mov	r0, r4
	bl	0x5ab54			@ ModeChangeProc(self, modus)
	pop	{r4, r5, pc}

.Lsetup:
	movs	r3, #1
	movs	r2, #0x4a		@ MSG 74 = Open SettingWindow
	mov	r1, r4
	mov	r0, r4
	bl	0x5aa08			@ PostMsg(self, self, 74, 1)
	pop	{r4, r5, pc}

.Lstream:
	movw	r0, #0x32a2
	movt	r0, #0x0020		@ r0 = 0x002032a2
	blx	0x1c94c			@ system("/mnt/extsd/start_streaming.sh &")
	pop	{r4, r5, pc}
'''

with open('test_dispatch.s', 'w') as f:
    f.write(ASM_CODE)

subprocess.run([os.path.join(TOOL, 'arm-none-eabi-as.exe'), '-mthumb', '-o', 'test_dispatch.o', 'test_dispatch.s'], check=True)
subprocess.run([os.path.join(TOOL, 'arm-none-eabi-ld.exe'), '-Ttext=0x0', '-o', 'test_dispatch.elf', 'test_dispatch.o'], check=True)
subprocess.run([os.path.join(TOOL, 'arm-none-eabi-objcopy.exe'), '-O', 'binary', 'test_dispatch.elf', 'test_dispatch.bin'], check=True)

data = open('test_dispatch.bin', 'rb').read()
code = data[0x5afe0:]
print(f'Code length: {len(code)} bytes (max 80 bytes)')
assert len(code) <= 80
print('Code hex:', code.hex())
