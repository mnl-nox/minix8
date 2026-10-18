; Captura os dois bytes baixos do contador de instruções.
; Após executar, inspecione RAM[0xFF00] e RAM[0xFF01] no monitor.
start:
    GETCYC
    STA 0xFF00      ; byte baixo do contador após GETCYC
    GETCYH
    STA 0xFF01      ; bits 8–15 após GETCYH
    HLT
