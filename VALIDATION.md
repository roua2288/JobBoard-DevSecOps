# Validation de la version vulnérable

Exécuté : `python scripts/compare_lab_live.py` → F1 à F8 reproduites (HTTP 200/302 attendus) ; `pytest` → 1 test réussi (les 8 failles sont exploitables).
Non exécuté ici : Docker, Trivy, Gitleaks, Kubernetes.
