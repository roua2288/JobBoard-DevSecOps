# Gestion des secrets et rotation

`SECRET_KEY` est obligatoire et fourni à l’exécution. `init-db` crée `admin@gmail.com` quand `ADMIN_PASSWORD` est fourni, puis enregistre le hachage. La commande `seed` initialise les comptes de démonstration avec `DEMO_PASSWORD`. Elle utilise `ADMIN_PASSWORD` pour le compte administrateur si la variable est présente.

Le lanceur de développement génère une clé locale aléatoire dans instance/session.key (ignoré par Git). Ne pas partager ce répertoire.

## Exercice de fuite
Utiliser un dépôt jetable et une clé de test reconnue par l’outil choisi. Conserver uniquement une capture caviardée.
1. Introduire volontairement le secret de test et démontrer le blocage du job Gitleaks.
2. Révoquer/remplacer d’abord le secret dans son système d’utilisation. Pour SECRET_KEY, remplacement puis redémarrage invalident les anciennes sessions.
3. Purger ensuite l’historique du dépôt jetable avec git-filter-repo et coordonner les clones.
4. Relancer Gitleaks avec historique complet et caviardage.
Ne pas inventer des résultats : joindre les sorties réelles à la soutenance.

## Kubernetes
Créer le Secret avec kubectl à partir d’un fichier temporaire à droits restreints, jamais un manifeste contenant la valeur.
Les Secrets Kubernetes sont encodés, pas chiffrés par le seul format Secret. Pour un cluster partagé, activer le chiffrement au repos, restreindre le RBAC d’administration et utiliser un coffre si disponible.
