# Threat model — <jūsų komandinio projekto pavadinimas>

> M3 (13 sav.). Užpildykite **savo komandiniam projektui**, ne fraud pavyzdžiui.
> Išsaugokite kaip `docs/threat-model.md` savo projekto repozitorijoje.

## 1. Architektūros eskizas

Trumpai (3–5 eilutės arba diagrama): kokie komponentai, kur duomenys, kas pasiekiama iš išorės.

```
[vartotojas] -> [API] -> [modelis iš registry] ...
```

## 2. Assets (ką saugome?)

| # | Asset | Kodėl vertingas |
|---|-------|-----------------|
| A1 | pvz. modelio svoriai MLflow registry | konkurentas ar užpuolikas galėtų nukopijuoti |
| A2 | pvz. training duomenys (gali turėti PII) | GDPR |
| A3 | | |

## 3. Threats (bent 5, iš skirtingų atakos sričių)

Atakos sritys iš paskaitos: **1** supply chain · **2** admission · **3** secrets ir network · **4** model attacks · **5** data ir privacy

| # | Atakos sritis | Threat (kaip puola?) | Asset | Impact (L/M/H) | Likelihood (L/M/H) | Mitigation (kas jau yra / ką pridėsime) |
|---|---------------|----------------------|-------|----------------|--------------------|-----------------------------------------|
| T1 | 2 | pvz. root + privileged konteineris patenka į klasterį | visas node'as | H | M | Gatekeeper policies (M1) |
| T2 | 3 | pvz. compromised pod'as skaito MLflow | A1 | H | M | NetworkPolicy default-deny (M2) |
| T3 | | | | | | |
| T4 | | | | | | |
| T5 | | | | | | |

L = low, M = medium, H = high.

## 4. Compliance, 3–5 sakiniai

- Ar sistema apdoroja asmens duomenis (PII)? Kokius? Ar galima apsieiti be jų (data minimization)?
- Kuriai EU AI Act risk kategorijai priskirtumėte sistemą ir kodėl?
- Kas loguojama apie kiekvieną prognozę ir ar loguose nėra PII?
