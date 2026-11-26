# JobBoard — VERSION VOLONTAIREMENT VULNÉRABLE (état initial 4.2)

> **Cette version contient 8 failles volontaires (F1 à F8) et AUCUN des 8 correctifs.**
> Usage strictement local, données fictives, ne jamais exposer sur Internet. Détail, cause, impact et reproduction : `security/VULNERABILITIES.md`.

| ID | Faille | Où |
|---|---|---|
| F1 | Injection SQL | `GET /?q=` |
| F2 | XSS réfléchie (CSP retirée) | `GET /?q=` |
| F3 | IDOR sur les CV | `GET /cv/<id>` |
| F4 | **Broken Access Control** : élévation de privilèges (`role=admin` à l'inscription) · A01:2025 · CWE-269 | `POST /register` |
| F5 | CSRF | `POST /profile` |
| F6 | Pas de limitation des tentatives | `POST /login` |
| F7 | Faux PDF accepté (extension seule) | `POST /cv/upload` |
| F8 | Clé de session exposée | `GET /lab/session-key` |

Lancer : `DEMARRER_JOBBOARD.bat` (Windows) ou `python -m scripts.start_vulnerable` → http://127.0.0.1:8001.
Rejouer les 8 attaques : `python scripts/compare_lab_live.py` · Tests : `python -m pytest -q`.
Le dossier `app/lab.py` (4 exercices bonus) reste inactif sauf `LAB_MODE=1`.

---

# JobBoard — Portail de recrutement DevSecOps

Pour utiliser la base MySQL/MariaDB de XAMPP : suivre DEMARRAGE_XAMPP.md et importer database/jobboard_xampp.sql dans phpMyAdmin.

Projet pédagogique d’Ahmed Lakti et Roua Ben Amor — TEK-UP, 5 SSIR J E.
Application serveur Flask, templates HTML/CSS, base SQLite persistante et stockage privé des CV.
Trois rôles : candidat, recruteur et administrateur.

**Livrable 4.1 et 4.2 avant correction** · [Rapport adapté du Lab 7](security/VULNERABILITIES.md).

## Démarrage rapide

Sous Windows, extraire l’archive puis double-cliquer sur `DEMARRER_JOBBOARD.bat`. Le lanceur utilise Python 3.12 et Git. Il ouvre **la version volontairement vulnérable** sur [http://127.0.0.1:8001](http://127.0.0.1:8001). Le terminal affiche les comptes fictifs et leur mot de passe. Garder la fenêtre ouverte et utiliser uniquement des données de test. La base SQLite et les fichiers du laboratoire sont temporaires. Chaque lancement repart de zéro.

Pour voir une première faille, saisir `' OR 1=1 -- ` dans la recherche du laboratoire. L’offre fictive non publiée devient visible. Pour parcourir les huit scénarios automatiquement, installer `requests` et exécuter `python scripts/compare_lab_live.py`.

### Laboratoire vulnérable avec Docker Desktop

Ouvrir PowerShell dans le sous-dossier `jobboard` qui contient le Dockerfile. Si le lanceur Windows utilise déjà le port 8001, l’arrêter avec Ctrl+C avant de démarrer le conteneur.

```powershell
docker build --target lab -t jobboard:lab .
docker run --rm -it -p 127.0.0.1:8001:8001 jobboard:lab
```

Ouvrir [http://127.0.0.1:8001](http://127.0.0.1:8001). Le mot de passe de démonstration s’affiche dans le terminal. Utiliser des données fictives. L’image de référence pour le contrôle 4.1 se construit avec `docker build -t jobboard:41 .`.

### Démarrage de la version de référence

Prérequis : Python 3.12, terminal ouvert dans ce dossier.

### Windows PowerShell
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
$env:DEMO_PASSWORD = Read-Host "Mot de passe des comptes fictifs (12 caractères minimum)"
python -m scripts.start_local
```
Si votre politique PowerShell empêche l’activation, utilisez directement .\.venv\Scripts\python.exe à la place de python.

### Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
read -rsp 'Mot de passe des comptes fictifs (12 caractères minimum) : ' DEMO_PASSWORD
export DEMO_PASSWORD
python -m scripts.start_local
```

Ouvrir http://127.0.0.1:8000.
La première exécution initialise la base. Si DEMO_PASSWORD est défini, les comptes fictifs sont créés :
- roua@example.test : candidat ;
- ahmed@example.test : recruteur ;
- admin@gmail.com : administrateur ;
- other@example.test : autre recruteur, utile pour tester l’isolation.

Les comptes fictifs utilisent `DEMO_PASSWORD`. Pour créer uniquement `admin@gmail.com`, définir `ADMIN_PASSWORD` avant le premier lancement. Si les deux variables sont définies, l’administrateur utilise `ADMIN_PASSWORD`. Une base existante conserve ses mots de passe.

## Fonctions
Candidat : inscription, connexion, profil, recherche, détail d’offre, dépôt de CV PDF, candidature avec un fichier joint ou un CV enregistré, suivi et retrait des candidatures.
Recruteur : création d’offre soumise à validation, clôture, consultation de ses candidatures, téléchargement des CV associés et changement de statut.
Administrateur : validation/rejet des offres, suspension/réactivation des comptes non administrateurs et journal d’activité.
Les contrôles d’accès sont exécutés côté serveur. Un sélecteur de rôle n’existe que dans l’aperçu visuel autonome, jamais dans cette authentification.

## Docker
```bash
python -c "import secrets; print('SECRET_KEY='+secrets.token_hex(32))" > .env
docker compose up --build -d
docker compose exec -e DEMO_PASSWORD jobboard flask --app app seed
```
Exporter DEMO_PASSWORD avant la commande seed. Le service écoute uniquement sur 127.0.0.1:8000.
Les données sont dans le volume jobboard-data. Ne jamais ajouter .env ou des données réelles au dépôt.
COOKIE_SECURE=0 est réservé à HTTP localhost. Activer COOKIE_SECURE=1 derrière un accès HTTPS.

## Kubernetes local
Prérequis : cluster local, kubectl, stockage dynamique. Pour que les NetworkPolicy soient effectives, utiliser un CNI compatible (par exemple Calico). Le réseau par défaut de certains clusters kind ne les applique pas.
```bash
docker build -t jobboard:local .
kind load docker-image jobboard:local
kubectl apply -f k8s/app.yaml
```
La création du Deployment précède volontairement celle du Secret : les pods attendent ce Secret.
Créer un fichier temporaire pour SECRET_KEY avec droits restreints, puis :
```bash
umask 077
python -c "import secrets; print(secrets.token_hex(32))" > /tmp/jobboard-session-key
kubectl -n jobboard create secret generic jobboard-runtime --from-file=SECRET_KEY=/tmp/jobboard-session-key
rm /tmp/jobboard-session-key
kubectl -n jobboard rollout status deployment/jobboard
kubectl apply -f k8s/network.yaml
kubectl -n jobboard port-forward service/jobboard 8000:8000
```
Le port-forward est réservé à la démonstration opérateur ; il ne constitue pas une preuve de filtrage du trafic inter-pods.
Pour un Ingress, installer ingress-nginx et appliquer k8s/ingress.yaml ; configurer jobboard.local dans votre résolution locale. Pour une exposition partagée, ajouter un nom réel, TLS et cookies Secure.
Initialiser les comptes de test via un kubectl exec avec DEMO_PASSWORD fourni temporairement dans l’environnement du processus seed, sans le committer ni le laisser dans un manifeste.
Tester le refus d’un pod non conforme : sh scripts/admission-test.sh. Lire le motif réel du refus.
Une seule réplique : SQLite et PVC ReadWriteOnce. Migration PostgreSQL et réplication restent des extensions possibles.

## Tests et sécurité
```bash
pip install -r requirements-dev.txt
python -m pytest -q
python scripts/run_dynamic_check.py
semgrep --config security/semgrep.yaml --exclude '*lab.py' --error app
pip-audit -r requirements.txt
```
Le script dynamique crée sa base éphémère, démarre un vrai serveur local, s’authentifie et l’arrête après vérification.
La CI .github/workflows/security.yml ajoute SAST, scans de dépendances/image, historique des secrets et IaC.
Le DAST livré est un test dynamique ciblé authentifié ; ce n’est pas une couverture générale OWASP ZAP.
Consulter security/VULNERABILITIES.md pour les huit failles locales et les correctifs.
Consulter security/THREAT_MODEL.md, GATE_POLICY.md, SECRETS.md et INCIDENT_RESPONSE.md.

## Observabilité
Les événements de sécurité sont structurés en JSON, avec acteur et corrélation, sans mot de passe ni contenu du CV.
```bash
docker compose logs -f --no-log-prefix jobboard | python scripts/detect.py
```
Ce détecteur écrit les alertes sur stdout. Aucun Slack/email ni SIEM n’est configuré.
Pour l’exercice : accès interdit à un CV → événement access_denied → alerte → suspension du compte → vérification du confinement.

## Connexion inscription et base de données

Ouvrir /login pour se connecter et /register pour s’inscrire. Le rôle est lu depuis la base après vérification du mot de passe ; il ne peut pas être choisi à la connexion.
Inscription : candidat ou recruteur uniquement, email unique, mot de passe confirmé. Les mots de passe sont hachés avec scrypt par Werkzeug, jamais stockés en clair.
La base SQLite persistante se trouve dans instance/jobboard.db (ou /data/jobboard.db avec Docker). Son schéma est fourni dans database/schema.sql.
Le compte administrateur initial utilise l’adresse `admin@gmail.com`. Son mot de passe est fourni lors de la première initialisation via `ADMIN_PASSWORD`, ou via `DEMO_PASSWORD` pour les données de démonstration.

Le site hébergé utilise une base D1 persistante et un stockage privé R2 des CV, avec authentification côté serveur et cookie de session HttpOnly. Le code du site est synchronisé dans son dépôt Sites.
La version Python fournie ici utilise SQLite, avec les mêmes rôles et pages séparées.

## État des validations
Voir VALIDATION.md : résultats réellement exécutés et contrôles restant à lancer.
Docker, Kubernetes, Gitleaks et Trivy ne sont pas présentés comme déjà validés si l’environnement d’exécution ne les fournit pas.
Le rapport de soutenance, les captures du pipeline, les résultats du cluster et les fiches individuelles doivent refléter votre travail réel.

## Usage d’IA
Base de code, interfaces, tests et documentation générés avec l’assistance de ChatGPT/Codex.
L’équipe doit relire, comprendre, adapter et valider ces éléments, et déclarer cette assistance dans le rapport.
Aucune contribution personnelle de l’un des membres n’est affirmée par ces fichiers.

## Références
- Flask : https://flask.palletsprojects.com/
- Kubernetes security : https://kubernetes.io/docs/concepts/security/
- Pod Security Admission : https://kubernetes.io/docs/concepts/security/pod-security-admission/
- NetworkPolicy : https://kubernetes.io/docs/concepts/services-networking/network-policies/
- Semgrep : https://semgrep.dev/docs/
- Trivy : https://trivy.dev/
- Gitleaks : https://github.com/gitleaks/gitleaks
- OWASP ZAP : https://www.zaproxy.org/docs/
- pypdf : https://pypdf.readthedocs.io/

Ces liens sont des références à consulter ; aucune capture ni preuve externe n’est fabriquée.

## Métriques et comparaison avant après
GET /metrics, accessible uniquement après connexion administrateur, expose jobboard_security_events_total par type d’événement. Pour un collecteur Prometheus autonome, prévoir une authentification de service distincte ; aucun accès public aux métriques n’est livré.
```bash
python scripts/compare_lab_live.py
```
Ce script compare les routes normales de JobBoard sur deux instances locales jetables. Il vérifie l’injection SQL, la XSS réfléchie, l’IDOR et le contrôle d’accès défaillant (F4). Voir [la procédure de vérification des exigences 4.1 et 4.2](security/VERIFICATION_4_1_4_2.md).

## Créer son CV

Depuis l’espace candidat, cliquer sur Créer mon CV (/cv/create). Le formulaire permet de sauvegarder un brouillon privé, télécharger un PDF, ou enregistrer le CV dans ses documents pour postuler. Les champs disponibles sont identité, titre, coordonnées, profil, expériences, formation, projets, compétences, langues et certifications.
Le brouillon est conservé dans la table cv_profiles ; les PDF restent privés et suivent les mêmes droits d’accès que les CV téléversés. Chaque génération enregistrée crée une nouvelle version du CV, sans modifier les fichiers déjà associés à une candidature.
Après mise à jour, réinstaller requirements.txt et redémarrer avec python -m scripts.start_xampp : init-db ajoute automatiquement cv_profiles sans supprimer les données existantes. Ne pas réimporter ou supprimer la base jobboard.
