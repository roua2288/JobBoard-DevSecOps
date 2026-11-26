# Politique de blocage

- SAST : toute règle ERROR fait échouer le build. La configuration locale vise injection SQL et rendu non sûr, complétée par les règles Python de Semgrep.
- Dépendances et image : toute vulnérabilité HIGH ou CRITICAL bloque. Le portail manipule des CV ; ces sévérités justifient de différer la livraison même lorsqu’un correctif n’est pas encore disponible. Réviser les dépendances ou documenter un contournement plutôt que prétendre que le pipeline passe.
- Secrets : toute détection bloque ; historique complet, affichage caviardé.
- IaC : toute configuration HIGH ou CRITICAL bloque.
- Tests : tout échec bloque le déploiement de la cible dynamique.
- Exceptions : aucune exception livrée. Toute exception future doit préciser vulnérabilité, exploitabilité, contrôle compensatoire, responsable, approbation et date d’expiration ≤ 7 jours. Les suppressions permanentes et globales sont interdites.
- Images d’outils et actions : versions lisibles dans la CI ; les figer par digest/SHA après validation locale pour une meilleure reproductibilité.
- La cible dynamique est jetable, locale au runner, et contient uniquement les comptes de test.
- La CI de démonstration déploie sur un processus vivant du runner. Le déploiement Kubernetes est une procédure distincte, pas une étape CD déjà vérifiée.
- Un pipeline vert ne garantit ni absence de faille métier ni sécurité complète.
