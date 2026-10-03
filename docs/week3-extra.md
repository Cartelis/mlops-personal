# 3 paskaita: papildomos užduotys ir diagnostika

Pagrindinė komandų seka: [week3.md](week3.md). Šie bandymai atliekami
pasirinkus papildomą užduotį arba aiškinantis klaidą; jie nėra dar viena
privaloma pagrindinės laboratorijos seka.

## Konteinerių diagnostika

`week3.py start` jau laukia HTTP ir Docker sveikatos, tikrina UID bei išsaugo
rezultatą. Šios komandos leidžia tą patį apžiūrėti rankomis:

```bash
docker ps --filter label=lt.vu.mlops.week3=true
docker inspect --format '{{.State.Health.Status}}' week3-cpu
docker inspect --format '{{.State.Health.Status}}' week3-onnx
docker exec week3-cpu id
docker logs --tail 20 week3-cpu
```

## Neigiamas HEALTHCHECK bandymas

Atskiras CPU konteineris gauna tyčia nesėkmingą sveikatos komandą.
Laukiama `unhealthy` ir žurnale `1`; tikrinamas klaidos aptikimas.
Docker HEALTHCHECK savaime nepaleidžia proceso iš naujo.
Pašalinamas tik šio bandymo konteinerio ID.

```bash
NEGATIVE_ID=$(docker run -d \
  --label lt.vu.mlops.week3.negative=true \
  --health-cmd='exit 1' --health-interval=1s \
  --health-timeout=1s --health-retries=2 \
  --health-start-period=0s mlops-cpu:local)
for attempt in $(seq 1 15); do
  NEGATIVE_HEALTH=$(docker inspect \
    --format '{{.State.Health.Status}}' "$NEGATIVE_ID")
  if [ "$NEGATIVE_HEALTH" = unhealthy ]; then break; fi
  sleep 1
done
docker inspect --format '{{.State.Health.Status}}' "$NEGATIVE_ID"
docker inspect \
  --format '{{range .State.Health.Log}}{{.ExitCode}} {{end}}' \
  "$NEGATIVE_ID"
docker rm -f "$NEGATIVE_ID"
test "$NEGATIVE_HEALTH" = unhealthy
```

## GPU — tik Linux x86_64 su NVIDIA

Apple Silicon ar vien CPU Docker host neturi CUDA įrenginio. Kitame GPU serveryje taip pat reikia Docker prieigos ir **NVIDIA Container Toolkit**; veikiantis `nvidia-smi` vienas to neįrodo. Dėstytojas prieš paskaitą patikrina [NVIDIA konfigūravimo instrukciją](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html). Jei HPC draudžia Docker, administratorius turi pateikti tinkamą konteinerių kelią; nekurkite fiktyvaus `True` rezultato.

GPU serveryje nuklonuokite savo repo ir pereikite į tą patį `tutorial/fraud-detection` katalogą. Modelio šiam CUDA testui nereikia:

```bash
nvidia-smi
docker version
docker build --platform linux/amd64 -f docker/Dockerfile.gpu -t mlops-gpu:local .
docker run --rm --gpus all mlops-gpu:local python /app/src/serve_gpu.py --check
python3 scripts/week3.py start gpu --port 18082
curl --fail --silent --show-error http://127.0.0.1:18082/health
docker inspect --format '{{.State.Health.Status}}' week3-gpu
docker exec week3-gpu id
```

GPU servisas atlieka tikrą matricų daugybą CUDA įrenginyje ir tikrina rezultatą. Be GPU jis baigiasi klaida — automatinio CPU pakaitalo nėra. Tai CUDA konteinerio pratimas, **ne sklearn fraud modelio inferencija GPU**. `/health` tikrina skaičiavimą tame pačiame ilgai veikiančiame procese. `HEALTHCHECK` visiems trims vaizdams turi prasmingą patikrą.

```bash
mkdir -p docs/week3
trivy image --scanners vuln --severity HIGH,CRITICAL --format json --output docs/week3/trivy-gpu.json mlops-gpu:local
python3 scripts/week3.py scan-report --kinds gpu --gate
docker image inspect --format '{{.Id}} {{.Size}}' mlops-gpu:local
```

Skirtingų kompiuterių įrodymus išsaugokite su platforma ir image ID. GPU ataskaita nepakeičia CPU/ONNX skenų; dirbant atskirai, nukopijuokite GPU JSON į bendrą pateikimo katalogą.

GPU dydis ir išvalymas atliekami tame GPU host:

```bash
python3 scripts/week3.py sizes --kinds gpu
python3 scripts/week3.py cleanup --kinds gpu
```

GPU vaizdui publikuoti pirmiausia tame host užbaikite pagrindinio GHCR skyriaus
prisijungimą bei `OWNER` ir `VERSION` nustatymą. CPU/ONNX tag/push eilučių
nekartokite, jei tų atvaizdų šiame host nėra. Patikrinę GPU skeną vykdykite:

```bash
python3 scripts/week3.py scan-report --kinds gpu --gate
docker tag mlops-gpu:local "ghcr.io/$OWNER/week3-gpu:$VERSION"
docker push "ghcr.io/$OWNER/week3-gpu:$VERSION"
```


## GitHub Actions (3.4, papildoma užduotis)

Workflow jau yra repo šaknies `.github/workflows/week3-containers.yml`.
Scaffold vidinė kopija skirta atskiram studento repo. Fork nustatymuose
įjunkite Actions. Išsaugoję pakeitimus pagal pagrindinę Git seką, sukurkite
**naują** žymą; jau paskelbtų žymų neperrašykite:

```bash
git tag -a week3-v1.2.2-cpu -m "Week 3 CPU and ONNX"
git push origin week3-v1.2.2-cpu
```

Galūnė `-cpu` vykdo tik CPU/ONNX amd64 ir arm64 darbus; pilnam GPU leidimui
rinkitės naują žymą be šios galūnės. CI paruošia modelį, testuoja API, tikrina
ne-root, vykdo Trivy ir tik po sėkmės publikuoja su `GITHUB_TOKEN`.
CI adresai: `ghcr.io/<owner>/<repo>/mlops-cpu:v1.2.2-cpu` ir analogiškas
`mlops-onnx`. Tai atskirai sukurti vaizdai, jų digest skiriasi nuo vietinių.
Patikrinkite visų darbų sėkmę bei abiejų architektūrų manifestus. GPU build
be NVIDIA įrenginio nepatvirtina CUDA skaičiavimo.

## Vietinis multi-arch eksperimentas be GHCR

Norint išbandyti abiejų architektūrų build be registry paskyros, iš to paties projekto katalogo:

```bash
docker buildx inspect week3-builder || docker buildx create --name week3-builder --driver docker-container
docker buildx inspect week3-builder --bootstrap
docker buildx build --builder week3-builder --platform linux/amd64,linux/arm64 -f docker/Dockerfile.onnx --output type=oci,dest=/tmp/week3-onnx-multiarch.tar .
```

OCI archyvas yra build įrodymas; jis dar nepublikuotas į GHCR. `--load` į klasikinius vienos platformos image store netinka kelių architektūrų rezultatui. Emuliacija gali būti gerokai lėtesnė. CI natyvūs runneriai papildomai tikrina API kiekvienoje platformoje.

## GHCR pull ir digest patikra

Po rankinio publikavimo tame pačiame terminale, kuriame nustatyti `OWNER`
ir `VERSION`, galima papildomai patikrinti atsiuntimą. CPU pavyzdys:

```bash
docker pull "ghcr.io/$OWNER/week3-cpu:$VERSION"
docker image inspect --format '{{json .RepoDigests}}' \
  "ghcr.io/$OWNER/week3-cpu:$VERSION"
```

ONNX atveju `week3-cpu` pakeiskite į `week3-onnx`. `docker push` irgi išveda
registry digest. Vien prisijungimas ar vietinis tag nėra publikavimo įrodymas.

## Trikčių šalinimas

| Klaida | Veiksmas |
|---|---|
| `Cannot connect to Docker daemon` | Paleisti Docker Desktop/Engine; pakartoti `docker version`. |
| Neranda `Dockerfile.prepare` | Grįžti į `tutorial/fraud-detection`, ne `docker/` katalogą. |
| Trūksta modelio `COPY` metu | Pirmiausia atlikti prepare build ir vienkartinį bootstrap/export. |
| 8080/18080 portas užimtas | Nenaikinti svetimo proceso; `start --port` pasirinkti kitą portą ir perduoti jį `api-check --cpu/--onnx`. |
| `PermissionError` / `ModuleNotFoundError` | Palyginti savo Dockerfile su repo; naudojamas `/opt/venv`, kopijuojami ir `security`, `observability`. |
| GHCR 401/403 | Patikrinti paskyrą, packages leidimus ir paketo prieigą; Git SSH raktas nėra Docker registry tokenas. |
| Actions „job was not started“ dėl payments / spending limit | Repo savininkas sutvarko GitHub **Billing & plans**, tada pakartoja workflow; kol nėra vykdytų žingsnių, CI ir GHCR nelaikomi patikrintais. |
| CUDA `False` / nėra runtime | Patikrinti tikrą NVIDIA Linux host, driver ir Container Toolkit; Mac CUDA neturi. |
| Skenas grąžina CRITICAL | Peržiūrėti pataisytą paketą/bazinį vaizdą, rebuild ir rescan; neapeiti vartų. |

Techninis pagrindas: [Docker build kontekstas](https://docs.docker.com/build/concepts/context/#dockerignore-files), [multi-platform build](https://docs.docker.com/build/building/multi-platform/), [GHCR autentifikacija](https://docs.github.com/en/packages/working-with-a-github-packages-registry/working-with-the-container-registry).
