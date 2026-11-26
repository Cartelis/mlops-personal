# 13 savaitė — „Užrakinkite sistemą" (savarankiška valanda)

Paskaitoje matėte, kaip threat actor'ius žingsnis po žingsnio eina per mūsų sistemą. Dabar jūs — **security komanda**.
Per ~60 min. apsaugosite mažą mokomąją mūsų sistemos kopiją savo kompiuterio klasteryje.

| Užduotis | Laikas | Ką darote | Įrodymas |
|---|---|---|---|
| **0. Paruošimas** | 10 min | klasteris, `preflight.sh`, mokomoji sistema | `Preflight OK` |
| **M1. Admission policies** | 20 min | Gatekeeper + 4 policies: klasteris atmeta nesaugų deploy'ą | `check.sh` M1 |
| **M2. Network isolation** | 15 min | NetworkPolicy: compromised pod'as nebepasiekia MLflow | `check.sh` M2 |
| **M3. Threat model** | 15 min | Threat model + security NFR **jūsų komandiniam projektui** | commit'as |
| *Papildomai* | — | Policies jūsų projekto namespace'ui | — |

> Visos komandos leidžiamos iš `tutorial/fraud-detection/` katalogo.
> Naudokite **tik savo lokalų klasterį**. Patikrinkite: `kubectl config current-context`.

---

## 0. Paruošimas (10 min)

Naudokite **savo esamą minikube klasterį** (pvz. iš 12 sav.) — tada nieko didelio siųstis nereikia.

```bash
minikube start                     # jūsų esamas klasteris
bash security/preflight.sh         # turi baigtis „Preflight OK"
```

`preflight.sh` patikrina įrankius, parsisiunčia darbui reikalingus image'us ir patikrina, ar jūsų **CNI plugin'as tikrai
enforce'ina NetworkPolicy**. Ne visi tai daro: default minikube (containerd + kindnet) ir Calico — taip, minikube su
`--container-runtime=docker` be CNI — ne. Tada M2 „praeitų" nieko neužblokavęs.
**Tik jei 4 žingsnis rodo FAIL** — atskiras profilis su Calico (kiti klasteriai lieka nepaliesti), tada `preflight.sh` dar kartą:

```bash
minikube start -p sec13 --cni=calico --cpus 4 --memory 4g
```

Windows: naudokite WSL arba Git Bash.

Paleiskite mokomąją sistemą — `fraud-api` (viešas servisas) ir `mlflow` (vidinis model registry):

```bash
kubectl apply -f security/lab/base/vault.yaml
kubectl -n vault get pods          # fraud-api ir mlflow -> Running
```

---

## M1. Admission policies (20 min)

**Istorija.** Threat actor'ius viduje bando paleisti savo pod'ą su visomis teisėmis. Mūsų pavyzdyje — „praktikanto" Deployment'as
`model-trainer`: root user'is, `privileged`, be resource limits, image'as `nginx:latest`.

**1. Įsitikinkite, kad šiandien klasteris priima bet ką:**

```bash
kubectl apply -f security/lab/bad-deployment.yaml
kubectl -n vault get pods          # veikia: privileged root konteineris jūsų klasteryje
kubectl delete -f security/lab/bad-deployment.yaml
```

**2. Įdiekite Gatekeeper.** Tai *admission controller'is*: Kubernetes API server'is kiekvieną naują objektą prieš
išsaugodamas nusiunčia Gatekeeper'iui, o šis atsako `allow` arba `deny` su priežastimi.

```bash
kubectl apply -f https://raw.githubusercontent.com/open-policy-agent/gatekeeper/v3.23.1/deploy/gatekeeper.yaml
kubectl -n gatekeeper-system wait --for=condition=Ready pod --all --timeout=180s
```

**3. Įjunkite 4 security policies.** Policy susideda iš dviejų dalių: **ConstraintTemplate** (logika Rego kalba) ir
**Constraint** (kur ją taikyti). Pirma template'ai, tada palaukiame, kol Gatekeeper sukurs jų CRD, ir tik tada — constraint'ai:

```bash
kubectl apply -f security/policies/templates/
kubectl wait --for=jsonpath='{.status.created}'=true constrainttemplate --all --timeout=60s   # laukia, kol sukurti visi 4 CRD
kubectl apply -f security/policies/constraints/
```

Atsidarykite bent vieną template'ą (`security/policies/templates/*.yaml`) ir perskaitykite Rego:
`violation[...] { ... }` reiškia „violation yra, jei **visos** bloko eilutės teisingos".

**4. Bandykite dar kartą:**

```bash
kubectl apply -f security/lab/bad-deployment.yaml
```

Turite gauti `denied` su **5 pranešimais** (4 taisyklės; limits — CPU ir memory atskirai).

**5. Jūsų užduotis.** Pataisykite Deployment'ą, kad jis būtų **priimtas ir veiktų**:

```bash
cp security/lab/bad-deployment.yaml security/lab/good-deployment.yaml
# redaguokite good-deployment.yaml, kol:
kubectl apply -f security/lab/good-deployment.yaml
kubectl -n vault get pods -l app=model-trainer   # Running, ne CreateContainerConfigError
```

> Spąstai: priimtas ≠ veikia. Jei pod'as nestartuoja: `kubectl -n vault describe pod -l app=model-trainer`.
> Ar jūsų image'as *gali* veikti ne kaip root? (Prisiminkite 3 savaitę.)

**6. Patikrinkite:** `bash security/check.sh m1`

**Klausimai apmąstymui:**
- Gatekeeper pagal nutylėjimą yra *fail-open* (`failurePolicy: Ignore`). Ką tai reiškia, jei jis nulūžta? Kodėl taip padaryta?
- Kas nutinka pod'ams, kurie jau veikė **prieš** įjungiant policies? Užuomina:
  `kubectl get k8srequirelimits vault-require-limits -o yaml` → `status.violations` (audit).

---

## M2. Network isolation (15 min)

**Istorija.** Threat actor'iaus kodas jau veikia viename pod'e (kenkėjiška dependency, užnuodytas pickle modelis).
Šis pod'as **atitinka visas 4 taisykles**, todėl Gatekeeper jį įleidžia: policies tikrina, *kaip* pod'as
sukonfigūruotas, ne *ką daro* jo kodas.

```bash
kubectl apply -f security/lab/attacker-pod.yaml
kubectl -n vault exec attacker -- wget -qO- -T 3 http://mlflow:5000      # vidinis MLflow matomas!
```

Kubernetes tinklas pagal nutylėjimą yra **flat**: bet kuris pod'as gali prisijungti prie bet kurio kito.

**1. Zero trust: default-deny visam ingress'ui.** NetworkPolicy su tuščiu `podSelector: {}` taikoma visiems
namespace pod'ams ir neleidžia jokio įeinančio ryšio.

```bash
kubectl apply -f security/lab/default-deny.yaml
kubectl -n vault exec attacker         -- wget -qO- -T 3 http://mlflow:5000   # užblokuota
kubectl -n vault exec deploy/fraud-api -- wget -qO- -T 3 http://mlflow:5000   # ...bet ir API nebepasiekia!
```

**2. Jūsų užduotis.** Parašykite `security/lab/allow-mlflow-from-api.yaml`: NetworkPolicy, kuri atidaro **tik vieną kelią**
`fraud-api -> mlflow`, port'as 8080 (container port, ne Service 5000). Pod'us atrinkite pagal `app` label'į.
Pritaikykite ir pakartokite abi `wget` komandas.

**3. Patikrinkite:** `bash security/check.sh m2`

**Klausimas:** kodėl NetworkPolicy atrenka pod'us pagal label'ius (`podSelector`), o ne pagal IP adresus?

---

## M3. Threat model jūsų projektui (15 min)

Komandos repozitorijoje:

1. `docs/threat-model.md` pagal `security/lab/templates/threat-model-template.md`: **≥5 threats** iš bent 3 skirtingų atakos sričių.
2. `docs/requirements.md`: **≥3 security NFR** pagal `security/lab/templates/nfr-template.md`, kiekvienas susietas su threat'u; nauja versija istorijoje.
3. Commit'as.

> Tai tiesiogiai tenkina komandinio projekto reikalavimą (16 sav.): non-root image'ai + Trivy + secrets ne Git'e + **≥1 policy**.

---

## Pasitikrinimas

```bash
bash security/check.sh          # tikslas: „Score: 9/9"
```

Darbas atskirai nevertinamas — `check.sh` ir savęs vertinimo lentelė (`lab/13-security.tex`) yra jūsų checklist'as.
M3 (threat model + security NFR) — jūsų komandinio projekto security dalies pagrindas (16 sav. gynimas).

## Papildomai (jei liko laiko)

- Pridėkite savo projekto namespace'ą į `security/policies/constraints/vault-rules.yaml` → `namespaces: [...]` ir deploy'inkite projektą iš naujo. Kas lūžta?
- Parašykite 5-ą taisyklę: draudžiami `hostPath` volume'ai.
- `kubectl -n vault get secret` + `base64 -d`: kodėl K8s Secret yra encoding, o ne encryption?

## Iš naujo

```bash
bash security/reset.sh          # ištrina vault + policies (Gatekeeper lieka)
bash security/reset.sh --all    # + pašalina Gatekeeper
```

## Troubleshooting

| Simptomas | Priežastis | Sprendimas |
|---|---|---|
| `no matches for kind "K8sRequireLimits"` | constraint'ai pritaikyti per anksti | palaukite ~10 s po template'ų, kartokite |
| blogas Deployment'as vis tiek priimtas | Gatekeeper dar nepasiruošęs (fail-open) | `kubectl -n gatekeeper-system get pods`, palaukite Ready |
| `CreateContainerConfigError` / `container has runAsNonRoot and image will run as root` | image'as reikalauja root | naudokite non-root image'ą (pvz. `nginxinc/nginx-unprivileged:1.27-alpine`) |
| M2: attacker vis tiek pasiekia MLflow | CNI neenforce'ina NetworkPolicy | `bash security/preflight.sh`; perkurkite su `--cni=calico` |
| M2: ir fraud-api nepasiekia | neteisingas label'is arba port'as | `app: fraud-api`; port'as **8080** (ne 5000) |
| `kubectl` keistai elgiasi | kubectl ir klasterio versijos skiriasi >1 | `KUBECTL="minikube -p sec13 kubectl --" bash security/check.sh` |

---

*Kitas šio katalogo turinys (`input_validation.py`, `inference_audit.py` ir kt.) naudojamas `src/serve.py` — jo nekeiskite.*
