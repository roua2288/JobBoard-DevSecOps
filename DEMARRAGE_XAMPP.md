# JobBoard avec XAMPP

XAMPP fournit Apache, PHP, phpMyAdmin et le serveur MySQL/MariaDB. JobBoard utilise Flask pour l’application et le serveur de base de données de XAMPP pour ses tables.

1. Dans XAMPP Control Panel, démarrer MySQL et Apache.
2. Ouvrir http://localhost/phpmyadmin et choisir Importer.
3. Importer database/jobboard_xampp.sql. La base jobboard et ses tables sont créées.
4. Ouvrir PowerShell dans le dossier jobboard extrait de l’archive, puis exécuter :

    py -3.12 -m venv .venv
    .\.venv\Scripts\python.exe -m pip install -r requirements.txt
    $env:ADMIN_PASSWORD = Read-Host "Mot de passe du compte admin JobBoard"
    .\.venv\Scripts\python.exe -m scripts.start_xampp

5. Ouvrir http://127.0.0.1:8000/login.
6. Se connecter avec `admin@gmail.com` et le mot de passe saisi. Si le compte existe déjà, utiliser son mot de passe actuel.
7. Pour un candidat/recruteur, ouvrir http://127.0.0.1:8000/register.

Configuration locale par défaut :
- DB_ENGINE=mysql
- DB_HOST=127.0.0.1
- DB_PORT=3306
- DB_NAME=jobboard
- DB_USER=root
- DB_PASSWORD vide

Si votre compte MySQL a un mot de passe ou utilise un autre port, définir les variables avant le lancement :

    $env:DB_PASSWORD = Read-Host "Mot de passe MySQL"
    $env:DB_PORT = "3306"
    .\.venv\Scripts\python.exe -m scripts.start_xampp

Ne pas déplacer ce projet dans htdocs : Apache sert phpMyAdmin, Flask sert JobBoard sur le port 8000.
Le compte root sans mot de passe est la configuration locale habituelle de XAMPP ; si vous l’avez modifiée, utilisez vos paramètres réels.
Les comptes, offres, candidatures et événements sont conservés dans MySQL/MariaDB. Les CV restent dans instance/cvs, et leurs références sont en base.
Le site en ligne conserve sa base hébergée D1. La version XAMPP se lance sur votre ordinateur avec ces instructions.
