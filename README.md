# fraud-detection — 2–3 savaičių praktinis projektas

Kurso semestro artefaktas: sintetinė sukčiavimo aptikimo užduotis (RandomForest,
1 000 eilučių, 10 požymių). Katalogas pildosi kiekvieną savaitę — šiuo metu jame
2 savaitės („Atkartojamumas ir eksperimentų sekimas“) medžiaga ir
3 savaitės CPU/ONNX vykdymo failai.

**3 savaitė:** [praktikos PDF, nuo 30 p.](https://klevas.mif.vu.lt/~linp/mlops/mlops-pratybos.pdf#page=30).
Komandas kopijuokite iš PDF kodo blokų. GPU ir CI reikalingi papildomi failai,
kurie nėra šio minimalaus rinkinio dalis.

**Instrukcijos žingsnis po žingsnio — pratybų medžiagoje (2 savaitės praktika).**
Trumpai:

1. nusikopijuokite šį katalogą į **savo** Git repozitoriją (šiame repo pakeitimai negalimi);
2. `uv venv .venv && source .venv/bin/activate && uv pip install -r requirements.txt`
3. `python scripts/bootstrap.py` — sugeneruoja duomenis ir pradinį modelį;
4. toliau — pagal pratybų žingsnius 1–6 (MLflow serveris, DVC, `dvc repro`, `reproduce.py`).

Testams papildomai: `uv pip install -r requirements-dev.txt`, tada
`python -m pytest tests/`.
