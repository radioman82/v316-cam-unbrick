@ Probe: Ist [self+0x114] (FunctionSelectWindow) beim MSG_MODE_SWITCH_DONE-Zweig gueltig?
@ Hook: 0x5caee  (str.w r6, [r0, #372])  ->  Sprung in Code-Cave 0x1f5140
@ Schreibt /tmp/AS_OK oder /tmp/AS_NULL via system(). KEIN Show()-Aufruf.

.syntax unified
.thumb

.org 0x5caee
b.w	probe

.org 0x1f5140
probe:
	push	{r0, r1, r2, r3, r12, lr}
	ldr.w	r1, [r0, #0x114]
	cbz	r1, probe_null
	adr	r0, str_ok
	blx	0x1c94c
	b	probe_done
probe_null:
	adr	r0, str_null
	blx	0x1c94c
probe_done:
	pop	{r0, r1, r2, r3, r12, lr}
	str.w	r6, [r0, #372]
	b.w	0x5caf2

.align 2
str_ok:
	.asciz	"touch /tmp/AS_OK"
.align 2
str_null:
	.asciz	"touch /tmp/AS_NULL"
