# Security NFR — įrašai į `docs/requirements.md`

> M3 (13 sav.). Kiekvienas reikalavimas turi būti **patikrinamas** (yra KPI ir kaip tikrinama)
> ir **traceable** (nuoroda į threat'ą iš `docs/threat-model.md`).
> Pridėkite bent 3 eilutes ir naują versiją į pakeitimų istoriją.

```markdown
## Security ir privacy NFR (v1.x)

| ID      | Reikalavimas                                  | KPI / riba                         | Kaip tikrinama                          | Threat |
|---------|-----------------------------------------------|------------------------------------|-----------------------------------------|--------|
| NFR-S1  | Klasteris atmeta nesaugius deploy'us          | 100 % deploy'ų praeina 4 policies  | Gatekeeper deny + `check.sh`            | T1     |
| NFR-S2  | Vidiniai servisai nepasiekiami iš kitų pod'ų  | tik API -> MLflow leidžiamas       | NetworkPolicy + `check.sh` M2           | T2     |
| NFR-S3  | Production'e nėra CRITICAL CVE                | 0 CRITICAL                         | Trivy CI gate (3 sav.)                  | T?     |
| NFR-S4  | Prediction loguose nėra PII                   | 0 PII laukų                        | input validation + audit log peržiūra   | T?     |
| NFR-S5  | Secrets ne Git'e                              | 0 secret'ų repozitorijoje          | K8s Secret / Sealed Secrets; scanner'is | T?     |

| Versija | Data       | Autorius | Pakeitimas                         |
|---------|------------|----------|------------------------------------|
| 1.x     | YYYY-MM-DD | ...      | Security NFR po threat modeling    |
```
