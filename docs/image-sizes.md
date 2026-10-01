# Docker vaizdų dydžiai — 3 savaitė

Šią ataskaitą užpildo `python3 scripts/week3.py sizes --kinds single cpu onnx`
pagal jūsų vietinius vaizdus. Pirmiausia atlikite [praktikos seką](week3.md).

| Vaizdas | Platforma | Docker .Size MB | Rootfs MB |
|---|---|---:|---:|
| mlops-single:local | dar nematuota | — | — |
| mlops-cpu:local | dar nematuota | — | — |
| mlops-onnx:local | dar nematuota | — | — |

NFR-11: CPU rootfs ≤500 MB, ONNX rootfs ≤300 MB — tikslai, kuriuos reikia
patikrinti. Rootfs: `du --apparent-size`, MB = 1 000 000 baitų; Docker `.Size`
apskaita priklauso nuo image store. Vaizdų ID ir baitai išsaugomi
`docs/week3/image-sizes.json`. GPU matuojamas atskirai jo vykdymo aplinkoje.
