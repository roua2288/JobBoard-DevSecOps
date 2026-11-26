# JobBoard · Rapport 4.1 et 4.2 avant correction

Méthode adaptée du **Lab 7 – Analyse d’une application vulnérable**, TEK-UP University. La cible est JobBoard sur localhost avec des données fictives. Les constats suivent la démarche du TP : emplacement, cause, impact, reproduction et preuve.

## 4.1 · Lancement de l’application

JobBoard utilise Flask, SQLite et trois rôles (candidat, recruteur et administrateur). Les CV, les candidatures et les données de compte représentent les actifs sensibles.

Le Dockerfile construit les dépendances en amont ; le code vulnérable est copié tel quel. L’image finale `jobboard:lab` repose sur `python:3.12-slim` et exécute le service sous l’UID et le GID 10001. Le mot de passe fictif et la clé de session sont générés au démarrage. La clé est exposée volontairement à l’exécution dans le scénario F8. Le dépôt Git, la base et les fichiers de démonstration ne sont pas copiés dans l’image.

Depuis le sous-dossier `jobboard`, dans PowerShell :

```powershell
docker build --target lab -t jobboard:lab .
docker run --rm -it -p 127.0.0.1:8001:8001 --name jobboard-lab jobboard:lab
```

Dans un deuxième terminal :

```powershell
docker ps --filter name=jobboard-lab
docker exec jobboard-lab id
curl.exe -i http://127.0.0.1:8001/health
```

Preuves à relever sur Docker Desktop : port publié sur 127.0.0.1, UID 10001, réponse HTTP 200, absence de secrets dans le résultat du scan. Pour lancer la vérification complète sous Windows avec Git Bash et Python accessibles :

```powershell
$env:MSYS_NO_PATHCONV = "1"
& "$env:ProgramFiles\Git\bin\bash.exe" scripts/verify_container.sh jobboard:lab 8001
```

Le contrôle Docker et Trivy reste à exécuter sur une machine équipée de Docker. Les preuves HTTP ci-dessous proviennent d’une exécution locale sur des instances temporaires.

## 4.2 · Constats initiaux et preuves

| ID | Où et cause | Impact | Manipulation et preuve observée | Classement |
|---|---|---|---|---|
| F1 · Injection SQL | GET `/?q=…`. La recherche concatène le texte saisi dans la requête. | Lecture d’une offre privée. | Dans la recherche, saisir `' OR 1=1 -- ` avec l’espace final. HTTP 200 et affichage de `OFFRE_FICTIVE_NON_PUBLIEE`. | OWASP A05:2025 · CWE-89 |
| F2 · XSS réfléchie | GET `/?q=…`. La saisie est ajoutée au HTML brut et la CSP manque sur cette route. | Un lien piégé peut exécuter du JavaScript dans l’origine de JobBoard. | Rechercher `<script>alert("XSS JobBoard")</script>` dans le navigateur. Le test automatisé a observé une balise brute et l’absence de CSP. L’alerte est à observer dans le navigateur. | OWASP A05:2025 · CWE-79 |
| F3 · IDOR | GET `/cv/<id>`. Le serveur vérifie la connexion sans vérifier les droits sur le CV. | Lecture du CV d’un autre utilisateur. | Déposer un CV fictif en candidat puis ouvrir son lien avec le compte recruteur tiers. HTTP 200 et retour du PDF. | OWASP A01:2025 · CWE-639 |
| F4 · Contrôle d’accès défaillant (Broken Access Control) : élévation de privilèges | POST `/register`. Le serveur accepte la valeur `admin` envoyée dans le rôle. | Création d’un compte administrateur par un visiteur. | Remplacer la valeur du champ rôle par `admin` dans les outils développeur et soumettre le formulaire. Inscription HTTP 302, métriques HTTP 200 après connexion. | OWASP A01:2025 · CWE-269 |
| F5 · CSRF | POST `/profile`. La route omet le contrôle du jeton. | Modification du profil au nom d’une victime connectée. | Le test envoie une requête de profil avec le cookie, sans jeton et avec un en-tête `Origin` distinct. HTTP 302 et profil modifié. | OWASP A01:2025 · CWE-352 |
| F6 · Tentatives non limitées | POST `/login`. Le compteur d’essais ne bloque aucune requête. | Répétition des essais de mot de passe. | Envoyer cinq mauvais mots de passe puis le bon sur le même compte. Le sixième essai est accepté (HTTP 302). | OWASP A07:2025 · CWE-307 |
| F7 · Faux PDF | POST `/cv/upload`. La validation accepte le fichier sur la seule extension. | Stockage d’un contenu arbitraire dans l’espace des CV. | Créer un fichier texte nommé `faux.pdf` et l’envoyer depuis l’espace candidat. HTTP 302 et un fichier enregistré. | CWE-434 · complément OWASP hors Top 10 |
| F8 · Exposition de la clé de session | GET `/lab/session-key`. Une route de démonstration divulgue la clé générée au démarrage. | Falsification d’une session administrateur. | Le test récupère la clé via la route et signe un cookie de démonstration pour le compte admin fictif. HTTP 200 sur la route puis sur `/metrics` sans connexion. | OWASP A01:2025 · CWE-200 |

Dans JobBoard, la charge SQL générique s’applique à la recherche d’offres. Elle rend le filtre vrai pour tous les résultats et révèle ainsi le brouillon fictif. Dans le Lab 7, la charge s’applique à la connexion de Juice Shop, où le premier compte retourné peut être un compte différent de l’administrateur. Les deux résultats s’expliquent par la requête et la manière dont l’application utilise les lignes retournées.

Pour reproduire les preuves initiales sur des instances jetables, avec Python 3.12 et Git installés :

```powershell
py -3.12 -m pip install -r requirements.txt requests
py -3.12 scripts/compare_lab_live.py 
```

Voir [la sortie HTTP réelle](../evidence/lab07-4.2.txt) et [le modèle STRIDE](THREAT_MODEL.md). Un build réussi ne détecte pas ces failles métier. Cette remise couvre les constats et la démonstration avant correction. La correction finale demandée par le cahier des charges est hors du périmètre de cette remise.

## Surface de dépendances

Le manifeste Python verrouille **13 paquets**, dont **6 utilisés directement par le projet** : Flask, Werkzeug, PyMySQL, pypdf, ReportLab et Gunicorn (serveur de l’image de référence). Les 7 autres sont des dépendances transitives verrouillées. Le comptage repose sur le manifeste et les imports ou lanceurs du projet. Il illustre le risque de chaîne d’approvisionnement **OWASP A03:2025** sans conclure qu’un paquet précis est vulnérable.

Références : Lab 7, parties A à C. [OWASP Top 10:2025](https://top10.owasp.org/2025/), [complément pour CWE-434](https://top10.owasp.org/2025/X01_2025-Next_Steps/).
