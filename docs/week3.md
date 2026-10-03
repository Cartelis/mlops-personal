# 3 paskaita: trumpa Docker laboratorija

Pagrindinis kelias: **paruošti modelį → build → API → scan → GHCR → Git**.
GPU atliekamas atskirai. CI, multi-arch, pull ir diagnostika yra
[papildomos užduotys](week3-extra.md).

## 0. Pasiruošimas

Ubuntu 22.04/24.04 reikia Docker su Buildx, Python 3.10+, curl, Trivy,
Git ir GitHub CLI (`gh`). Vienkartinis [diegimas ir prieiga](setup-ubuntu.md)
atliekami prieš laboratoriją. `docker version` turi rodyti Client ir Server.
Bendrą serverį paruošia administratorius. Mac naudokite Docker Desktop ir Bash.

Kurso repo terminale:

```bash
bash
cd "$(git rev-parse --show-toplevel)/tutorial/fraud-detection"
```

Jei į savo repo nukopijavote tik scaffold turinį, jo šaknis jau tinkama:
`cd` praleiskite. Visas komandas vykdykite tame pačiame terminale. Eilutė su
`\` tęsiasi kitoje eilutėje; ties klaida sustokite ir ją pataisykite.

Prepare perrašo demonstracinius modelius ir sintetinius CSV. Ankstesnius
savo duomenis išsaugokite kitur. Reikia interneto, bent 8 GB RAM ir 15 GB disko.

## 1. Build, API ir saugumas

Peržiūrėkite `docker/Dockerfile.single`, `Dockerfile.cpu`, `Dockerfile.onnx`
ir projekto šaknies `.dockerignore`. Failai jau paruošti repo. Žemiau ta pati
seka kaip [`scripts/week3-local.sh`](../scripts/week3-local.sh):

```bash
#!/usr/bin/env bash
# Run from tutorial/fraud-detection. Every command is also safe to paste separately.
set -eu
mkdir -p models data

# Use the same Python and sklearn versions for training and container serving.
docker build -f docker/Dockerfile.prepare -t mlops-prepare:week3 .
docker run --rm --user "$(id -u):$(id -g)" \
  -v "$PWD/models:/app/models" -v "$PWD/data:/app/data" mlops-prepare:week3

docker build -f docker/Dockerfile.single -t mlops-single:local .
docker build -f docker/Dockerfile.cpu -t mlops-cpu:local .
docker build -f docker/Dockerfile.onnx -t mlops-onnx:local .

# These commands return once HTTP and Docker HEALTHCHECK are ready.
python3 scripts/week3.py start cpu --port 18080
python3 scripts/week3.py start onnx --port 18081
curl -fsS http://127.0.0.1:18080/health
curl -fsS http://127.0.0.1:18080/predict \
  -H 'Content-Type: application/json' \
  -d '{"f0":0.1,"f1":-0.2,"f2":0.3,"f3":0.0,
       "f4":0.1,"f5":0.2,"f6":0.0,"f7":0.1,
       "f8":0.2,"f9":0.0}'
python3 scripts/week3.py api-check
python3 scripts/week3.py sizes --kinds single cpu onnx

trivy image --scanners vuln --severity HIGH,CRITICAL -f json \
  -o docs/week3/trivy-cpu.json mlops-cpu:local
trivy image --scanners vuln --severity HIGH,CRITICAL -f json \
  -o docs/week3/trivy-onnx.json mlops-onnx:local
trivy image -f spdx-json -o docs/week3/sbom-cpu.json mlops-cpu:local
python3 scripts/week3.py scan-report --gate
```

**Laukiama:** CPU/ONNX `healthy`, UID ne 0, API ir CRITICAL vartas PASS.
`start` paleidžia `docker run -d`, laukia iki 90 s ir išsaugo parengties laiką.
`api-check` patikrina 100 įvesčių, laukų tvarką, metaduomenis bei HTTP 422.
Todėl nereikia tų pačių patikrų pakartoti rankomis.

Rezultatai: `docs/image-sizes.md`, `docs/security-scan.md` ir `docs/week3/` JSON/SBOM.
CPU rootfs tikslas ≤500 MB, ONNX ≤300 MB; ONNX parengtis ≤5 s, kai vaizdas vietinis.
Docker `.Size` apskaita priklauso nuo image store; ataskaitoje rootfs matuojamas
atskirai su `du --apparent-size`. Nepasiektą tikslą paaiškinkite. Matavimas nėra
SLA, sintetiniai duomenys nepatvirtina realaus fraud modelio kokybės.

## 2. GHCR publikavimas

Pirmą `gh auth login` užbaikite naršyklėje; jau autorizavę CLI šią eilutę praleiskite.
Esamo SSH rakto iš naujo kelti nereikia (`Skip`). Pasirinkite dar nenaudotą
`VERSION`. Tokeno į failą ar pokalbį nekopijuokite.

```bash
#!/usr/bin/env bash
# Publish the local CPU/ONNX images after their scans pass.
# Run from tutorial/fraud-detection; authenticate interactively, never paste tokens.
set -eu
gh auth login --hostname github.com --git-protocol ssh --web \
  --scopes write:packages,read:packages
OWNER=$(gh api user --jq '.login | ascii_downcase')
gh auth token | docker login ghcr.io -u "$OWNER" --password-stdin
VERSION=v1.2.2-cpu
python3 scripts/week3.py scan-report --kinds cpu onnx --gate
docker tag mlops-cpu:local "ghcr.io/$OWNER/week3-cpu:$VERSION"
docker push "ghcr.io/$OWNER/week3-cpu:$VERSION"
docker tag mlops-onnx:local "ghcr.io/$OWNER/week3-onnx:$VERSION"
docker push "ghcr.io/$OWNER/week3-onnx:$VERSION"
```

Abu `push` turi išvesti digest. Tai vietinės architektūros vaizdai;
CRITICAL radiniai sustabdo publikavimą, HIGH radinius aptarkite ataskaitoje.
Seka saugoma [`scripts/week3-ghcr.sh`](../scripts/week3-ghcr.sh).

## 3. Git ir atsiskaitymas

Scaffold kodas ir workflow jau yra Git. Įtraukite savo pakeitimus ir matavimus.
Prieš commit peržiūrėkite stage, kad nepatektų kitų užduočių failai:

```bash
git add .dockerignore docker/ src/ scripts/ security/ docs/ \
  constraints-week3.txt requirements-*.txt
git diff --cached
git commit -m "feat: Week 3 containers"
git push -u origin HEAD
```

`nothing to commit` reiškia, kad pakeitimai jau išsaugoti. Pateikite Dockerfile,
GHCR adresus ir digest, Git commit, skenus/SBOM, API rezultatą, NFR-11–NFR-14
matavimus ir dydžių palyginimą. CI yra papildoma 3.4 užduotis.

Baigus demonstraciją:

```bash
python3 scripts/week3.py cleanup --kinds cpu onnx
```

Šalinami tik šio checkout pažymėti CPU/ONNX konteineriai, vaizdai ir duomenys lieka.
GPU, neigiamas HEALTHCHECK, multi-arch, CI bei trikčių sprendimai:
[week3-extra.md](week3-extra.md). Pasiruošimui kitai savaitei perskaitykite
`infra/README.md`; GCP išteklių šiai paskaitai kurti nereikia.
