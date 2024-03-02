CVM                     # clear vector mask
MFCL SR2                # SR2 = 64
LS SR3 SR0 0            # SR3 = 1
LS SR4 SR0 1            # SR4 = 2048 <- Store Address
LS SR5 SR0 2            # SR5 = 450 <- Vector Size
LV VR1 SR1              # VR1 = 0...63 (SR1 = 0) (<- JUMP #2 HERE...)
MULVV VR2 VR1 VR1       # VR2 = VR1 * VR1
PACKLO VR3 VR2 VR0      # VR3 = VR2[even] (<- JUMP #1 HERE...)
PACKHI VR4 VR2 VR0      # VR4 = VR2[odd]
ADDVV VR2 VR3 VR4       # VR2 = VR3 + VR4
SRA SR2 SR2 SR3         # SR2 = 64 >> 1 = 32
MTCL SR2                # VL = SR2 = 32
BNE SR2 SR3 -5          # IF SR2 != SR3 i.e SR2 != 1, THEN JUMP -5 (JUMP #1)
ADDVV VR5 VR5 VR2       # WHEN SR2 == 1, VR5 = VR5 + VR2
CVM                     # clear vector mask
POP SR2                 # SR2 = 64
MTCL SR2                # VL = SR2 = 64
ADD SR1 SR1 SR2         # SR1 = SR1 + SR2 = 0 + 64 = 64
SUB SR5 SR5 SR2         # SR5 = SR5 - SR2 = 450 - 64 = 386
BGT SR5 SR0 -14         # IF SR5 > SR0 i.e SR5 > 0, THEN JUMP -14 (JUMP #2)
SV VR5 SR4              # MEM[SR4] = VR5
HALT