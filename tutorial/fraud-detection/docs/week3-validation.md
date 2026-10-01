# 3 paskaitos medžiagos patikra

2026-09-16 perkelta sutrumpinta ir išbandyta 3 paskaitos medžiaga.
Pagrindinė studento seka yra [week3.md](week3.md), papildomos užduotys —
[week3-extra.md](week3-extra.md), Ubuntu diegimas — [setup-ubuntu.md](setup-ubuntu.md).

Prieš perkėlimą tie patys vykdymo šaltiniai tikrinti atskiroje kurso kopijoje:
modelio paruošimas, CPU/ONNX build, API, ne-root, HEALTHCHECK, Trivy/SBOM ir
GHCR publikavimas praėjo. API patikra apima 100 įvesčių bei 212 papildomų
lauko tvarkos, metaduomenų ir neteisingų užklausų patikrų. Sutrumpinta pagrindinė
seka turi 31 loginę komandą, įskaitant GHCR ir Git.

Po perkėlimo šios darbo kopijos kodas patikrintas CPU konteineryje su anksčiau
paruoštais demonstraciniais modeliais: 32 testai ir 21 papildoma patikra praėjo.
`main_public.tex`, `lab_pub.tex` ir `slides/week_3.tex` sėkmingai sukompiliuoti
su Tectonic. Patikros PDF saugomi už šios repozitorijos ribų.

Šio repo studentų rezultatai turi būti sugeneruoti iš naujo. Kitų darbo
kopijų image ID, skenai ir serverių išrašai čia nekopijuojami. Naujai sukurti
vaizdai gali turėti kitus dydžius, digest ir CVE radinius.

Repo šaknies workflow pritaikytas `main` šakai. Žymos su `-cpu` vykdo tik
CPU/ONNX; pilna žyma papildomai parenka GPU. Šios repozitorijos nuotolinio CI
rezultatą patvirtina tik jo paties sėkmingas Actions bandymas.

GPU vykdymui reikia NVIDIA Linux aplinkos; naujo Ubuntu diegimo Mac bandymas
nepatvirtina. Detalūs laboratorijos rezultatai atsiranda `docs/week3/` po
komandų vykdymo. Sintetiniai duomenys ir vienas parengties matavimas nėra
realaus modelio kokybės ar SLA įrodymas.
