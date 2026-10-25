import subprocess

ld_cmd = [
    r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin\arm-none-eabi-ld.EXE',
    '--section-start=.text=0x0', '-o', r'd:\v316cm\asm_patch.elf', r'd:\v316cm\asm_patch.o'
]
subprocess.check_call(ld_cmd)

objdump_cmd = [
    r'C:\Program Files (x86)\Arm GNU Toolchain arm-none-eabi\13.3 rel1\bin\arm-none-eabi-objdump.EXE',
    '-d', r'd:\v316cm\asm_patch.elf'
]
out = subprocess.check_output(objdump_cmd).decode()
print("Linked Disassembly:")
for line in out.splitlines():
    if "5afe0" in line or (line.startswith("   5") and ":" in line):
        print(line)
