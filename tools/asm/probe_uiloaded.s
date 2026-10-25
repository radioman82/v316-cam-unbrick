.syntax unified
.thumb
.text

@ OnUILoaded epilogue hook: branch to probe cave
@ Original bytes at 0x6aec0: ldmia.w sp!, {r4, r5, lr}  +  b.w 0x6236c
@ r4 = self (guaranteed valid, no error path here)
.org 0x6aec0
b.w	0x1f5150

@ ---------------------------------------------------------------
@ Cave: probe stub at 0x1f5150
@ Reads [r4+0x114], writes marker file, then does original epilogue
@ ---------------------------------------------------------------
.org 0x1f5150
probe_stub:
	@ Save r0-r3 (we need them for the original tail call later)
	push	{r0, r1, r2, r3}

	@ Load func_win pointer
	ldr.w	r0, [r4, #0x114]

	@ Check if func_win is set
	cbz	r0, probe_skip

	@ func_win is non-NULL — write marker with value
	@ Use a simple approach: system("touch /tmp/UILOADED_OK")
	adr	r1, probestr_ok
	blx	0x1c94c		@ system()
	b	probe_done

probe_skip:
	@ func_win is NULL — write different marker
	adr	r1, probestr_null
	blx	0x1c94c		@ system()

probe_done:
	@ Restore r0-r3
	pop	{r0, r1, r2, r3}

	@ Execute original epilogue:
	@ ldmia.w sp!, {r4, r5, lr}
	@ b.w 0x6236c
	ldmia.w	sp!, {r4, r5, lr}
	b.w	0x6236c

probestr_ok:
	.asciz	"touch /tmp/UILOADED_OK"
	.balign 4

probestr_null:
	.asciz	"touch /tmp/UILOADED_NULL"
	.balign 4
