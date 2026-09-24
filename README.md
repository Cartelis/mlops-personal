# fraud-detection — 2–4 savaičių praktinis projektas

Kurso semestro artefaktas: sintetinė sukčiavimo aptikimo užduotis (RandomForest,
1 000 eilučių, 10 požymių). Katalogas pildosi kiekvieną savaitę — šiuo metu jame
2 savaitės („Atkartojamumas ir eksperimentų sekimas“) medžiaga,
3 savaitės CPU/ONNX vykdymo failai ir 4 savaitės GCP Terraform pavyzdys
(GCS, Artifact Registry, IAM, Cloud Run).

**3 savaitė:** [praktikos PDF, nuo 30 p.](https://klevas.mif.vu.lt/~linp/mlops/mlops-pratybos.pdf#page=30).
Komandas kopijuokite iš PDF kodo blokų. GPU ir CI reikalingi papildomi failai,
kurie nėra šio minimalaus rinkinio dalis.

**4 savaitė:** žingsniai yra [`infra/README.md`](infra/README.md).
Pirmas `terraform apply` palieka viešą `hello` atvaizdą, tada į Artifact Registry
keliamas 3 savaitės CPU atvaizdas (`linux/amd64`). Po darbo būtina
`terraform destroy` — kreditai skaičiuojami, kol resursai gyvi.
`infra/terraform.tfvars` ir Terraform state į Git nekeliami.

**Instrukcijos žingsnis po žingsnio — pratybų medžiagoje (2 savaitės praktika).**
Trumpai:

1. nusikopijuokite šį katalogą į **savo** Git repozitoriją (šiame repo pakeitimai negalimi);
2. `uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt`
3. `python scripts/bootstrap.py` — sugeneruoja duomenis ir pradinį modelį;
4. toliau — pagal pratybų žingsnius 1–6 (MLflow serveris, DVC, `dvc repro`, `reproduce.py`).

Testams papildomai: `uv pip install -r requirements-dev.txt`, tada
`python -m pytest tests/`.
