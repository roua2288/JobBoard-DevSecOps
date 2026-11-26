# Réponse à incident — accès illégitime à un CV

## Détecter
Déclencheur : événement access_denied sur une route de CV ou brute_force_detected.
Lancer : docker compose logs -f --no-log-prefix jobboard | python scripts/detect.py
Le détecteur produit une alerte JSON sur stdout. Il faut brancher ce flux sur le canal d’alerte choisi ; aucun message externe n’est envoyé par ce projet.
Conserver l’heure, l’identifiant de corrélation et le compte concerné. Ne jamais copier le contenu d’un CV dans les logs.

## Contenir
Suspendre le compte suspect depuis l’espace administrateur. Les sessions de ce compte perdent immédiatement leur accès à la requête suivante.
En cas de compromission de SECRET_KEY : remplacer la clé à l’exécution puis redémarrer, ce qui invalide toutes les sessions. Sur un système à plusieurs réplicas, coordonner le remplacement.

## Éradiquer
Reproduire dans un environnement isolé avec données fictives, corriger l’autorisation et ajouter un test croisé entre utilisateurs. Révoquer d’abord toute clé exposée, puis purger son historique.

## Rétablir
Rejouer les tests, redéployer l’image contrôlée et vérifier /health ainsi que les téléchargements autorisés et interdits. Réactiver le compte après investigation.

## Apprendre
Documenter la chronologie, la cause, le correctif, les personnes responsables et les améliorations de détection. Ajouter les preuves réelles de la séance.

## Exercice à réaliser
1. Candidat : charger un CV.
2. Recruteur sans candidature associée : appeler /cv/1 → 403.
3. Observer access_denied et l’alerte JSON.
4. Administrateur : suspendre ce compte.
5. Recruteur : rafraîchir son tableau de bord → redirection vers connexion.
6. Noter le temps de détection et de confinement, puis vérifier le rétablissement.
