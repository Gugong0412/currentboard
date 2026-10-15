DDI Current Board Phase2-2 R2 / 12-channel design modification DRAFT / 2026-10-15

BASE: DDI_Phase2_2_R1_KiCad.zip, SHA-256: 1b187dc51e4337e9bd532c7e0a98f2f429918a4ae3b4c05d0b1c2c0d1116f1d8
No GitHub write performed. Original R1 retained unchanged.

Changes:
- VDDI_LPDP and VDDI_OSC added alongside existing VDDI: share U520, separate fixed 20-ohm Kelvin shunts and INA228.
- U520 feedback: R525 DNP / R526 FIT (local pre-shunt sense), remote compensation disabled; actual VDDI drops and regulation require testing.
- AVDDH2 now S/O common and GM separate measurement, single shared MOSCATO source, 3.01-ohm fixed shunts.
- VGH1/VGH2 two measurement branches from common VGH source, 3.01-ohm provisional; peak/5uA accuracy UNVERIFIED.
- VGL1/VGL2 common VGL source floating domain, 20-ohm provisional; shared ISO supply and bus, I2C2 address 0x40 / 0x41.
- Newly added INA228 U760=0x46, U770=0x47, U780=0x48, U790=0x49 (I2C1), U840=0x41 (I2C2). New ALERT pins not routed to MCU; diagnostic polling only.
- J1403 expansion 2x6: LPDP, OSC, AVDDH2_GM, VGH2 with adjacent GND; J1404 separate VGL2 with GND. Existing J1400/1401/1402 reused.
- VDDIO1V2 and SYS_1V8 remain U600/U620 non-measured, SYS_1V8 shared with MOSCATO.
- No new individual EN GPIO; source groups enable simultaneously.

Measurements (DMM fixed ranges, user-provided):
VDDI_DIG 1.317mA/11uA (10mA); LPDP 142/82uA, OSC 200/200uA, VDDI 280/160uA, VCI 30/30uA, AVDDH1 300/300uA (all 1mA).
AVDDH2 S/O 6mA/150uA and GM 2.5mA/250uA (10mA); VGH1 200/10uA, VGH2 25/25uA, VGL1 160uA/0(display), VGL2 150/100uA (1mA).
Low 1Hz mean is dominated by long blank interval and does not constrain instantaneous current. 0 displayed for VGL1 is not zero-accuracy evidence.

IMPORTANT VALIDATION LIMIT:
- KiCad CLI is unavailable. No new KiCad schematic export, ERC, or PCB DRC was performed. The old XML/ERC/PDF evidence was intentionally excluded.
- Source contract nets and firmware values are generated from same revised model, NOT independently validated against KiCad 8.
- Critical: before fabrication, open project in KiCad8 and export fresh netlist; check every Ref.pin, net label, copper bridge and NC; run full ERC and audit address labels/pin directions/footprints.
- R2 B8_VGL2 is a provisional separate sub-sheet using direct labels on component pins; KiCad connection interpretation and sheet instance path MUST be checked.
- Peak current (including rail 4.7uF/2.2uF charge), shunt thermal rating, voltage burden and ±0.5% @5uA are UNVERIFIED.
- No whole-project PASS. Manufacturing release remains HOLD.
