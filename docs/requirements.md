# Fraud Detection API - Reikalavimai v1.0

Data: 2026-09-15 | Autoriai: (komanda)

## 1.1 Problemos aprasymas

Sukurti realaus laiko fraud scoring API korteliu transakcijoms.
Tikslas: recall >= 0.92, false positive <= 0.5%.

## 2. Funkciniai reikalavimai

| ID    | Reikalavimas                              | Prioritetas |
|-------|-------------------------------------------|-------------|
| FR-01 | POST /predict priima JSON transakcija     | Must        |
| FR-02 | Grazina prediction ir score               | Must        |
| FR-03 | GET /health grazina status                | Must        |

## 3. Nefunkciniai reikalavimai

| ID     | Kategorija | Reikalavimas           | KPI                    |
|--------|------------|------------------------|------------------------|
| NFR-01 | Nasumas    | Inference latency      | p95 <= 80 ms @ 500 RPS |
| NFR-02 | Kokybe     | Sukciavimo aptikimas   | Recall >= 0.92         |
| NFR-03 | Kokybe     | False positive rate    | <= 0.5%                |
| NFR-04 | Dreifas    | Precision degradacija  | < 3% per 14 dienu      |
| NFR-05 | Saziningumas | TPR skirtumas regionu | <= 5%                  |
| NFR-06 | Kastai     | Inference kaina        | <= $0.0002/req        |
| NFR-07 | Prieinamumas | Uptime               | >= 99.95%              |

## 3.x Eksperimentų sekimo ir atkartojamumo NFR (v1.1)

| ID     | Kategorija       | Reikalavimas                                                    | KPI                                   |
|--------|------------------|-----------------------------------------------------------------|---------------------------------------|
| NFR-08 | Atkartojamumas   | Bet kuris istorinis run atkuriamas `python reproduce.py <run_id>` | <= 2 min (be duomenų atsisiuntimo), delta accuracy <= 0.005 |
| NFR-09 | Atsekamumas      | Kiekvienas eksperimentas turi MLflow run ID, git commit ir duomenų md5 tag'us; kiekvienas diegiamas modelis – `model_id` | 100 % run'ų |
| NFR-10 | Duomenų versija  | Mokymo duomenų versija fiksuota DVC (`dvc.lock` md5 = run'o `dvc_raw_md5`) | 100 % run'ų |

## 10.x Agentinis elgesys (v1.9)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-38 | Drift aptikimo latencija  | <= 5 min nuo trigger        |
| NFR-39 | Autonominio retrain limit | <= 3 per diena              |
| NFR-40 | Incidento pranesimas      | <= 2 min po deploy          |
| NFR-41 | Agento audito aprėptis    | 100% tool call įrašų        |

## 11.x Stebėsena ir AIOps (v1.10)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-42 | Metrikų scrape intervalas | <= 30 s                     |
| NFR-43 | Alert pranešimo laikas    | <= 2 min nuo firing         |
| NFR-44 | Dreifo report generavimas | <= 10 min                   |
| NFR-45 | Struktūrinio log aprėptis | 100% request handler'ių     |

## 12.x Scaling ir FinOps (v1.11)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-46 | Autoscale reakcijos laikas | <= 3 min iki target replikų |
| NFR-47 | Maks. replikos apkrovoje  | Iki 50                      |
| NFR-48 | Spot kaštų mažinimas      | >= 60% vs on-demand         |
| NFR-49 | Uptime scaling metu       | >= 99.9%                    |

## 13.x Saugumas ir compliance (v1.12)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-50 | Critical CVE produkcijoje | 0 critical                  |
| NFR-51 | Gatekeeper atitiktis      | 100% deployment'ų           |
| NFR-52 | Inference audito aprėptis | 100% /predict               |
| NFR-53 | PII atmetimas API         | 100% PII laukų blokuojama   |

## 14.x Edge ir federated learning (v1.13)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-54 | Edge modelio dydis        | <= 5 MB                     |
| NFR-55 | Edge inference p95        | <= 50 ms (local)            |
| NFR-56 | FL klientu skaicius       | >= 3                        |
| NFR-57 | FL vs centralized gap     | <= 2 pp accuracy            |

## 15.x Testavimas ir validavimas (v1.14)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-58 | Data contract checks      | >= 10 expectations          |
| NFR-59 | E2E pipeline test         | 100% pass CI                |
| NFR-60 | Model regression gate     | accuracy >= 0.95            |
| NFR-61 | Traceability coverage     | 100% critical NFR mapped    |

## 16.x Governance ir capstone (v1.15)

| ID     | Reikalavimas              | KPI                         |
|--------|---------------------------|-----------------------------|
| NFR-62 | Model card completeness   | >= 8 sections               |
| NFR-63 | EU AI Act risk documented | tier + mitigations          |
| NFR-64 | Governance report coverage| >= 90% critical NFRs        |
| NFR-65 | Capstone checklist        | 100% critical items green   |

## 7. Keitimo istorija

| Versija | Data       | Autorius | Pakeitimai |
|---------|------------|----------|------------|
| 1.0     | 2026-09-15 | komanda  | Pradinis dokumentas |
| 1.1     | 2026-09-09 | komanda  | MLflow + DVC pipeline, atkartojamumo NFR (NFR-08–NFR-10) |
| 1.9     | 2026-11-24 | komanda  | Self-healing LangGraph agentas (NFR-38–NFR-41) |
| 1.10    | 2026-12-01 | komanda  | Observability stack (NFR-42–NFR-45) |
| 1.11    | 2026-12-08 | komanda  | Scaling, spot, TCO (NFR-46–NFR-49) |
| 1.12    | 2026-12-15 | komanda  | Security hardening (NFR-50–NFR-53) |
| 1.13    | 2026-12-22 | komanda  | Edge ONNX + Flower FL (NFR-54–NFR-57) |
| 1.14    | 2026-12-29 | komanda  | Testing suite + traceability (NFR-58–NFR-61) |
| 1.15    | 2026-01-05 | komanda  | Governance package + capstone (NFR-62–NFR-65) |