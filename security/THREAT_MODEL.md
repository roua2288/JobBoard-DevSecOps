# Modèle de menace STRIDE · JobBoard

Les visiteurs, candidats, recruteurs et administrateurs accèdent à Flask depuis un navigateur. Flask consulte SQLite et un dossier privé contenant les CV PDF. Les principales frontières de confiance sont le navigateur vers le serveur, la séparation entre comptes et rôles, puis les accès du serveur au stockage. Les actifs sont les identités, cookies, CV, offres en attente, candidatures et journaux.

Les parades ci-dessous servent à l’analyse des risques comme dans le Lab 7.

| STRIDE | Menace concrète | Parade envisagée |
|---|---|---|
| S · Usurpation | Un visiteur récupère la clé via une route de démonstration et signe un cookie administrateur (F8). | Restreindre la visibilité des secrets et renouveler les clés exposées. |
| T · Altération | Un site externe fait envoyer une modification de profil au nom d’un candidat connecté (F5). | Valider côté serveur un jeton CSRF lié à la session. |
| R · Répudiation | Un administrateur conteste une décision de modération dont la trace peut être altérée. | Journaliser l’acteur, la date, l’action et l’identifiant d’offre dans un journal protégé en écriture. |
| I · Divulgation | Un recruteur devine l’identifiant d’un CV associé à une autre candidature (F3). | Vérifier la propriété et la relation avec la candidature sur chaque téléchargement. |
| D · Déni de service | Un compte répète les téléversements de fichiers pour saturer le stockage (F7 illustre un contrôle de contenu incomplet). | Limiter le débit, la taille et le quota de stockage. |
| E · Élévation de privilèges | Un visiteur modifie le rôle envoyé lors de l’inscription (F4, Broken Access Control · A01:2025). | Limiter les rôles attribuables lors de l’inscription et séparer leur attribution administrative. |

Voir [les huit constats et les preuves](VULNERABILITIES.md).
