# Docker vaizdų dydžiai — 3 savaitė

MB = 1 000 000 baitų. Rootfs: išpakuotų failų dydis (`du --apparent-size`). Docker `.Size` priklauso nuo image store; containerd atveju tai suspausto turinio dydis, todėl jo nepainioti su rootfs ar bendra disko vieta.

| Vaizdas | Platforma | Docker .Size MB | Rootfs MB |
|---|---|---:|---:|
| mlops-single:local | linux/amd64 | 160.44 | 480.6 |
| mlops-cpu:local | linux/amd64 | 122.93 | 379.95 |
| mlops-onnx:local | linux/amd64 | 87.63 | 247.88 |

NFR-11: CPU rootfs <=500 MB, ONNX rootfs <=300 MB — tikslai; faktines neatitiktis aptarti.

GPU vaizdas šioje aplinkoje neišmatuotas.
