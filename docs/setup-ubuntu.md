# Studentų Ubuntu 22.04 / 24.04 paruošimas

Šią seką atlikite vieną kartą savo Ubuntu kompiuteryje arba asmeninėje VM.
Reikia interneto, veikiančio `systemd` ir `sudo` teisių. Bendrą universiteto
serverį paruošia administratorius; jei neturite `sudo`, diegimo komandos neveiks.
Naudokite savo įprasto vartotojo terminalą, ne `sudo su` ar root sesiją.

Paskaitai pakanka **Docker Engine**, CLI, Buildx ir Compose įskiepių.
Linux aplinkoje Docker Desktop diegti neprivaloma. Docker Hub ar mokamos
Docker paskyros šiam vietiniam pratimui nereikia.

## 1. Patikrinkite aplinką

```bash
cat /etc/os-release
uname -m
docker version
```

Tinka Ubuntu `22.04` arba `24.04`; CPU/ONNX užduotims — `x86_64` ir `aarch64`.
Jei `docker version` jau parodo **Client ir Server**, Docker perinstaliuoti
nereikia: pereikite prie įskiepių patikros 3 skyriuje.
`command not found` reiškia, kad Docker CLI nerastas. Jei Client yra, tačiau
Server nepasiekiamas, pirmiausia tikrinkite tarnybą ir prieigą pagal lentelę apačioje.

Toliau pateiktas diegimas skirtas švariai Ubuntu aplinkai. Jei joje jau yra
`docker.io`, `podman-docker`, atskirai įdiegtas `containerd` / `runc` ar senas
Docker APT šaltinis, pirmiausia vadovaukitės oficialios instrukcijos
[konfliktuojančių paketų skyriumi](https://docs.docker.com/engine/install/ubuntu/#uninstall-old-versions).
Veikiančio bendro serverio paketų aklai nešalinkite.

## 2. Įdiekite Docker

Naudojama [oficiali Docker APT saugykla](https://docs.docker.com/engine/install/ubuntu/).
Komandos įrašytos faile [`scripts/install-docker-ubuntu.sh`](../scripts/install-docker-ubuntu.sh).
Atverkite jį ir kopijuokite eilutes į Bash terminalą arba, būdami
`tutorial/fraud-detection` kataloge, paleiskite visą seką:

```bash
bash scripts/install-docker-ubuntu.sh
```

Jei kurso dar neklonavote, komandų seka taip pat įtraukta į trečios paskaitos
praktikos PDF; diegimo komandas galima vykdyti iš bet kurio katalogo.
Komandas su `\` tęskite kitoje eilutėje. Bloką nuo `sudo tee ... <<EOF` iki
atskiros `EOF` eilutės nukopijuokite visą; vidurys yra APT failo turinys,
ne atskiros terminalo komandos. `sudo` gali paprašyti jūsų Linux slaptažodžio;
vedant terminalas simbolių nerodo.

Skriptas įdiegia Docker Engine, CLI, Buildx, Compose, Git, Python3 ir curl,
paleidžia Docker tarnybą bei vykdo `sudo docker run --rm hello-world`.
Laukiamas pranešimas: **Hello from Docker!** Šis patikrinimas dar naudoja `sudo`.

## 3. Leiskite savo vartotojui naudoti Docker

Kurso `week3.py` kviečia Docker be `sudo`, todėl reikia tinkamos vartotojo prieigos.
Savo kompiuteryje arba asmeninėje VM vykdykite:

```bash
sudo groupadd -f docker
sudo usermod -aG docker "$(id -un)"
```

**Visiškai atsijunkite nuo Ubuntu sesijos ir prisijunkite iš naujo.** SSH atveju
uždarykite ryšį ir prisijunkite iš naujo; grafinėje aplinkoje naudokite Log Out.
Vien naujo terminalo lango gali nepakakti. Jei VM išlaiko seną sesiją,
perkraukite ją. Po prisijungimo, jau be `sudo`, patikrinkite:

```bash
id -nG
docker version
docker buildx version
docker compose version
docker run --rm hello-world
```

Laukiama: grupių sąraše yra `docker`, `docker version` pateikia Client ir Server,
abu įskiepiai išveda versiją, `hello-world` sėkmingas.
Narystė `docker` grupėje suteikia **root lygio prieigą prie kompiuterio**.
Todėl bendrame universiteto serveryje prieigos būdą nustato administratorius;
studentų paskyrų izoliaciją turi užtikrinti pasirinkta aplinka, pvz., atskiros VM.
Žr. [oficialias prieigos instrukcijas](https://docs.docker.com/engine/install/linux-postinstall/).

## 4. Įdiekite paskaitai reikalingą Trivy

Pirmiausia užtikrinkite bendras paskaitos priklausomybes. Šį žingsnį atlikite ir
tada, jei Docker buvo įdiegtas anksčiau ir diegimo skriptą praleidote:

```bash
sudo apt-get update
sudo apt-get install -y ca-certificates curl git python3 gnupg
```

Docker vaizdų saugumui tikrinti dar naudojamas Trivy. Toliau pateikta seka paremta
[oficialia Trivy Ubuntu instrukcija](https://www.trivy.dev/docs/latest/getting-started/installation/).
Jei `trivy --version` jau veikia, tolesnį Trivy diegimo bloką praleiskite.

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://aquasecurity.github.io/trivy-repo/deb/public.key -o /tmp/week3-trivy-key.asc
gpg --batch --yes --dearmor --output /tmp/week3-trivy-key.gpg /tmp/week3-trivy-key.asc
sudo install -m 0644 /tmp/week3-trivy-key.gpg /etc/apt/keyrings/trivy.gpg
echo "deb [signed-by=/etc/apt/keyrings/trivy.gpg] https://aquasecurity.github.io/trivy-repo/deb generic main" | sudo tee /etc/apt/sources.list.d/trivy.list
sudo apt-get update
sudo apt-get install -y trivy
trivy --version
```

Po to grįžkite į [3 paskaitos instrukcijos](week3.md) darbo katalogo ir CPU/ONNX
skyrius. NVIDIA GPU užduočiai papildomai reikia suderinamo NVIDIA driver ir
Container Toolkit; vien Docker įdiegimo jai neužtenka.

## 5. GitHub CLI rankiniam GHCR pratimui

Jei `gh --version` veikia, diegimą praleiskite. Kitu atveju Ubuntu naudokite
[oficialią GitHub CLI APT saugyklą](https://github.com/cli/cli/blob/trunk/docs/install_linux.md):

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
  -o /tmp/week3-githubcli-keyring.gpg
sudo install -m 0644 /tmp/week3-githubcli-keyring.gpg \
  /etc/apt/keyrings/githubcli-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
  | sudo tee /etc/apt/sources.list.d/github-cli.list
sudo apt-get update
sudo apt-get install -y gh
gh --version
```

Prisijungimo komandos yra [GHCR pratime](week3.md). Naršyklės GitHub sesija
neautorizuoja CLI automatiškai; užbaikite `gh auth login` patvirtinimą naršyklėje.

## Jei neveikia

| Pranešimas | Veiksmas |
|---|---|
| `not in the sudoers file` | Aplinką turi paruošti administratorius arba suteikti asmeninę VM. |
| `Cannot connect to the Docker daemon` | `sudo systemctl status docker --no-pager`, tada `sudo systemctl start docker`. |
| `permission denied` prie `/var/run/docker.sock` | Patikrinti `id -nG`, pilnai atsijungti/prisijungti po `usermod`; nekeisti socket teisių į `777`. |
| Per SSH net po prisijungimo vis dar nematyti `docker` grupės | Jei įjungtas SSH ryšio pakartotinis naudojimas (ControlMaster), sukurti tikrai naują ryšį: `ssh -o ControlMaster=no -o ControlPath=none vartotojas@serveris`, pakeitus prisijungimo adresą savuoju. |
| `docker: 'buildx' is not a docker command` | Įdiegti `sudo apt-get install -y docker-buildx-plugin docker-compose-plugin`. |
| `System has not been booted with systemd` | Tai ne šiame vadove numatytas Ubuntu host/VM; paprasto konteinerio viduje šios diegimo sekos nevykdyti. WSL reikia Docker Desktop integracijos arba tinkamai įjungto systemd. |
| APT praneša apie `Signed-By` konfliktą | Patikrinti, ar neliko ankstesnio Docker/Trivy šaltinio su kita rakto vieta; administratorius turi sutvarkyti dubliuotą šaltinį. |

Patikros ribos: instrukcijos sutikrintos su oficialiais šaltiniais ir Bash sintaksė
patikrinta. Pilnas naujo Ubuntu host diegimas šiame macOS kompiuteryje nevykdytas.
