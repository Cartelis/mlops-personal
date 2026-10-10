# Komandinė užduotis — produkcinė DI sistema

Semestro projektas grupėse po **2–3**. Galutinis rezultatas — veikianti sistema lokaliame Kubernetes klasteryje (papildomai GCP ir/ar HPC) su stebėsena, testavimu ir governance ataskaita.

| | |
|---|---|
| **Grupė** | 2–3 studentai |
| **Temos suderinimas** | iki **2026-10-28** (9 savaitė) |
| **Pateikimas** | **2026-12-09** (15 savaitė), tag `team-final` + ataskaita |
| **Gynimas** | **2026-12-16** (16 savaitė) — Capstone Live Demo Day |
| **Trukmė** | 15 min. pristatymas + 5 min. klausimai; **live demo** |
| **Balai** | iki **4** (40 % kurso). Apginta, jei **≥ 2** |
| **Egzaminas** | galima laikyti tik apginus projektą (≥ 2) **ir** U1+U2 ≥ 1,5 |

Individualių U1/U2 rezultatai (klasteris, MLflow, pipeline’as, serving’as) **pernaudojami** komandiniame projekte — nerašote visko nuo nulio 15 savaitę.

---

## Tikslas

Sukurti produkcinę DI sistemą: duomenų paruošimas → mokymas → registras → hostingas → stebėsena. Vertinama architektūra, atkartojamumas, operacijos ir įrodymai (NFR → testas), ne modelio leaderboard vieta.

## Terminai

| Sav. | Data | Įvykis |
|---|---|---|
| 1 | 2026-09-02 | Grupė, projekto pavadinimas, komandinis GitHub repo |
| 1–2 | — | `requirements.md` v1.0 → v1.1; modelio / duomenų eskizas |
| 8 | 2026-10-21 | U1 (individuali); tarpinis statusas |
| **9** | **2026-10-28** | **Temos suderinimas su lektoriumi** |
| 11 | 2026-11-11 | U2 (individuali) |
| 12 | 2026-11-18 | Konsultacija: projekto statusas |
| **15** | **2026-12-09** | **Pateikimas:** tag `team-final`, ataskaita ≤ 4 psl. |
| **16** | **2026-12-16** | **Gynimas** (Capstone Demo Day) |

Savaitiniai laboratoriniai darbai (tag’ai `v1.0`, `week-03`, …) kaupia projektą. Kiekvienas lab. = commit/tag **komandiniame** repo.

## Projekto etapai

| Savaitės | Ką daryti projekte |
|---|---|
| 1–2 | Reikalavimai, repo, MLflow + DVC |
| 3–5 | Docker, Terraform/GCP, Kubernetes; lokalus klasteris |
| 6–9 | CI/CD, serving, GPU (jei yra), orkestravimas; **temos suderinimas (9 sav.)** |
| 10–13 | Agentas, observability, scaling, saugumas |
| 14–15 | Edge/FL (jei taikoma), testavimas, traceability; `team-final` |
| 16 | Governance ataskaita + live demo |

## Temos ir duomenys

- Temą komanda **pasirenka pati** ir **suderina su lektoriumi iki 9 sav.**
- Kurso **fraud detection** pavyzdys komandiniam projektui **nenaudojamas** (tik referencinis scaffold).
- Duomenys legalūs, be asmens duomenų arba anonimizuoti; rekomenduojami atviri Hugging Face rinkiniai.
- `docs/requirements.md` su versijų istorija ir **atsekamumo matrica**: NFR → testas → įrodymas.

## Reikalavimai

### Problema ir dokumentacija

- Aiški problema, stakeholderiai, FR + NFR su KPI.
- Gyvas `docs/requirements.md` (ne Google Docs).
- Atsekamumo matrica iki gynimo.

### Duomenų ir mokymo pipeline’as

- DVC pipeline’as + MLflow tracking **komandos** MLflow serveryje (registras, alias’ai).
- Orkestravimas: bent DVC + CI; rekomenduojama Ray / Prefect DAG su žmogaus patvirtinimu (HITL).

### Hostingas

- Inferencijos servisas klasteryje.
- CI/CD su kokybės vartu.
- Versijuoti konteinerių vaizdai.
- Parodytas rollback.

### Stebėsena

- Prometheus + Grafana: vėlinimas, klaidos, pralaidumas.
- Evidently dreifo ataskaita.
- ≥ 2 alert’ai.
- `docs/runbook.md`.

### Mastelis, saugumas, testavimas

Bent **po vieną** elementą iš kiekvienos temos:

- mastelis: HPA + apkrovos testas;
- saugumas: non-root vaizdai + Trivy + Secret’ai (ne Git’e) + ≥ 1 policy;
- testai CI: duomenų kontraktas, modelio kokybė, E2E.

### Governance

- Model card (≥ 8 skyriai).
- Trumpa rizikų / EU AI Act klasifikacija.

### Ataskaita ir gynimas

- Ataskaita **iki 4 psl.**: metodologija, architektūros diagrama, rezultatai, išvados.
- 16 sav.: 15 min. pristatymas + 5 min. klausimai; **live demo produkcinėje aplinkoje** (ne tik skaidrės).

## Išplėstinė dalis (papildomi balai iki 4)

- GPU mokymas (lokaliai arba HPC);
- self-healing agentas;
- edge / federated learning variantas;
- kaštų analizė GCP.

## Vertinimas (iki 4 balų)

| Kriterijus | Ką rodyti |
|---|---|
| Reikalavimai, architektūra, atsekamumo matrica | NFR su įrodymais, diagrama atitinka demo |
| Duomenų + mokymo pipeline’as | DVC, MLflow, registras, orkestravimas |
| Hostingas + CI/CD + rollback | live `/predict`, žalias/raudonas vartas, rollback |
| Stebėsena, dreifas, alert’ai, runbook | dashboard + bent 2 alert’ai + runbook |
| Mastelis / saugumas / testavimas | HPA+load; Trivy/non-root/secrets/policy; testai CI |
| Ataskaita + model card | ≤ 4 psl.; card ≥ 8 skyriai |
| Gynimas | 15+5 min.; live demo; atsakymai į klausimus |

Projektas **neapgintas**, jei < 2 balai — egzamino laikyti negalima.

## Pateikimo checklist (`team-final`)

- [ ] Komandinis GitHub repo, tag `team-final`
- [ ] README: paleidimas nuo nulio, portai, kas demoja ką
- [ ] `docs/requirements.md` + atsekamumo matrica
- [ ] `docs/architecture.md` (ar ekvivalentas)
- [ ] `docs/runbook.md`
- [ ] Ataskaita ≤ 4 psl.
- [ ] Model card ≥ 8 skyriai + EU AI Act / rizikų santrauka
- [ ] CI žalias; parodytas raudonas kokybės vartas ir rollback
- [ ] Live inferencija klasteryje
- [ ] Prometheus/Grafana + Evidently + ≥ 2 alert’ai

## Lūkesčiai

**Tikimasi**

- Viena sistema, kurią galima paleisti ir paliesti gynimo metu.
- Kiekvienas narys paaiškina **savo** dalį ir bent vieną svetimą failą (live edit).
- NFR nėra šūkiai: kiekvienas svarbus NFR turi matavimą arba testą.
- Komanda žino, kas nutiks dreifui / nukritus accuracy / nutrūkus Pod’ui (runbook).
- Individualios U1/U2 žinios sujungtos, o ne trys nesusiję notebook’ai.

**Nėra tikimasi**

- Naujo SOTA modelio ar privalomo GPU.
- Kad visos 16 savaičių temos būtų implementuotos vienodai giliai — branduolys aukščiau, išplėstinė dalis iki maksimumo.
- Fraud detection kaip projekto temos.

**Dažnos klaidos**

- Tema nesuderinta iki 9 sav.
- Demo tik iš laptop’o, be klasterio.
- Stebėsena „planuojame Grafana“ be veikiančio dashboard.
- Secret’ai commit’inti.
- Ataskaita 12 psl. arba vien screenshot’ai be architektūros.
- Vienas narys kalba, kiti neatsako į klausimus.

## Gynimo formatas (16 sav.)

1. Problema ir NFR (2 min.).
2. Architektūra (2 min.).
3. Live kelias: duomenys / MLflow / `/predict` / dashboard (6–8 min.).
4. Vienas governance artefaktas (model card arba atsekamumo eilutė).
5. Klausimai (5 min.), įskaitant live edit.

## Ryšys su individualiomis užduotimis

| Individualu (U1, U2) | Komanda |
|---|---|
| Savo repo, savo modelis | Bendras repo, suderinta tema |
| Mini platforma vienam žmogui | Produkcinis srautas + stebėsena + governance |
| Tag `u1-final`, `u2-final` | Tag `team-final` |
| Iki 3 balų kartu | Iki 4 balų |


