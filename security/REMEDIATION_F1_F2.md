# Contribution individuelle - F1 et F2

**Auteur :** Roua Ben Amor
**Projet :** JobBoard - DevSecOps
**Branche :** roua

## 1. Objectif

Identifier, analyser et corriger deux vulnerabilites
de JobBoard, puis automatiser leur validation dans
un pipeline CI/CD securise.

## 2. F1 - SQL Injection

- Fichier : app/__init__.py
- Fonction : index()
- Route : GET /
- Parametre : q
- OWASP : A05:2025 - Injection
- CWE : CWE-89
- STRIDE : Information Disclosure / Tampering

### Cause

Concatenation directe de la saisie utilisateur
dans une requete SQL.

### Impact

Risque de modification de la logique SQL et
de divulgation des offres non publiees.

### Correction

Utilisation de requetes parametrees afin de
separer les donnees utilisateur des instructions SQL.

### Validation

- Semgrep : aucune detection F1 apres correction.
- Pytest : 3 tests F1 reussis.
- Controles HTTP authentifies : reussis.
- Commit : d94331e.

## 3. F2 - Cross-Site Scripting

- Fichier : app/__init__.py
- Fonctions : index() et headers()
- Parametre : q
- OWASP : A05:2025 - Injection
- CWE : CWE-79
- STRIDE : Tampering

### Cause

Concatenation directe de la saisie utilisateur
dans la reponse HTML et absence de CSP sur la recherche.

### Impact

Risque d'execution de JavaScript non autorise
dans le navigateur utilisateur.

### Correction

- Suppression de la concatenation HTML non echappee.
- Utilisation du rendu securise Jinja2.
- Retablissement de Content Security Policy.

### Validation

- Semgrep : aucune detection F2 apres correction.
- Pytest : 2 tests F2 reussis.
- Verification dynamique de l'echappement HTML.
- Verification de la politique CSP.
- Commit : 9d5262b.

## 4. Pipeline DevSecOps

Outils utilises :

- GitHub Actions : automatisation CI/CD.
- Semgrep : analyse statique SAST.
- Pytest : tests de non-regression.
- OWASP ZAP : analyse DAST passive.
- Python Requests : controles HTTP authentifies.
- SQLite : base temporaire de test.

## 5. Evolution des pipelines

| Pipeline | Objectif | Resultat |
|----------|----------|----------|
| 1 | Detection initiale F1 et F2 | Failure |
| 2 | Correction F1 | Failure - F2 restante |
| 3 | Correction F2 | Success |
| 4 | Integration OWASP ZAP | Success |
| 5 | Controles HTTP authentifies | Success |
| 6 | Renforcement des controles bloquants | Success |

## 6. Resultats avant et apres correction

| Indicateur | Avant | Apres |
|------------|-------|-------|
| Detections SAST ciblees | 2 | 0 |
| Tests Pytest reussis | 2/5 | 5/5 |
| Tests Pytest echoues | 3 | 0 |
| Pipeline | Failure | Success |

## 7. Resultats OWASP ZAP

Resultats du pipeline 4 :

- 13 URL analysees.
- 61 controles PASS.
- 0 FAIL bloquant.
- 7 categories WARN.

L'alerte 10031 concerne la reflexion du parametre
q dans un attribut HTML. Elle est informative et
ne confirme pas une exploitation XSS.

Les tests confirment l'echappement HTML et la
presence de CSP pour les entrees testees.

## 8. Securisation du pipeline

- Controles SAST bloquants.
- Tests de securite bloquants.
- Mot de passe temporaire genere aleatoirement.
- Masquage du mot de passe dans les journaux.
- Base de donnees temporaire et donnees fictives.
- Utilisation de pipefail pour propager les erreurs.
- Publication automatique des rapports de securite.

## 9. Limites

Les controles sont cibles sur F1 et F2.
Le scan ZAP est passif et non authentifie.
Les controles HTTP authentifies sont complementaires.
Un scan DAST actif reste a realiser.
Les autres vulnerabilites sont hors du perimetre
de cette contribution individuelle.

## 10. Conclusion

Les corrections F1 et F2 ont ete implementees
et validees par les controles automatises.
Le passage du pipeline rouge au pipeline vert
demontre l'efficacite des correctifs pour
les scenarios testes.
