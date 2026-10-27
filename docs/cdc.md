# Ligue 1 Dashboard — Cahier des charges

27 octobre 2026 · Noah

## 1. Contexte et objectifs

Le projet livre un dashboard public sur la Ligue 1, alimenté chaque jour par un pipeline de données automatisé. C'est un projet personnel de portfolio : sa valeur tient autant à la qualité d'ingénierie qu'au dashboard lui-même.

Objectifs :

1. **Produit** : suivre la saison de Ligue 1 en cours (classement, forme, performances des équipes, buteurs), lisible en moins d'une minute.
2. **Technique** : mettre en œuvre une chaîne data complète et réaliste — ingestion, entrepôt, transformations SQL testées, orchestration, CI.
3. **Carrière** : constituer un repo GitHub présentable en entretien et support d'un post LinkedIn de fin de projet.

## 2. Périmètre

Le périmètre se limite à ce que l'offre gratuite de football-data.org fournit : la saison de Ligue 1 en cours, au niveau équipes et matchs.

| Inclus (V1) | Exclu (V1) |
| --- | --- |
| Saison de Ligue 1 en cours | Saisons passées (historique payant) |
| Matchs : calendrier, scores, journée, domicile / extérieur | Scores en direct (différés en gratuit) |
| Classement et son évolution journée par journée | Statistiques de match (tirs, possession, xG) |
| Équipes (nom, logo) | Données joueurs détaillées (compositions, cartons) |
| Meilleurs buteurs, si l'endpoint est disponible en gratuit | Autres compétitions |

L'historique s'accumule au fil de la saison grâce à des snapshots quotidiens stockés par le pipeline. Une V2 pourra élargir le périmètre (autres championnats, source payante).

## 3. Besoins fonctionnels

Le dashboard comporte une seule page, organisée en quatre blocs qui répondent chacun à une question. Un clic sur une équipe dans le classement filtre les trois autres blocs sur cette équipe ; sans sélection, ils montrent la vue d'ensemble de la Ligue 1. La page affiche la date de dernière mise à jour des données.

| ID | Bloc | Question | Sans sélection | Équipe sélectionnée |
| --- | --- | --- | --- | --- |
| F1 | Classement | Où en est la saison ? | Classement complet (Pts, J, G-N-P, BP, BC, Diff), forme sur 5 matchs, zones européennes et de relégation | Ligne de l'équipe mise en évidence ; un nouveau clic annule la sélection |
| F2 | Évolution | Comment la saison s'est-elle construite ? | Position de toutes les équipes journée par journée | Courbe de l'équipe en avant, les autres estompées ; points cumulés |
| F3 | Profil | Comment joue l'équipe ? | Moyennes de la ligue (buts par match, bilan domicile / extérieur) | Bilan domicile / extérieur, buts marqués et encaissés par match, séries en cours |
| F4 | Matchs | Que s'est-il passé, que reste-t-il ? | Résultats de la dernière journée, prochaine journée, faits marquants | Résultats récents et prochains matchs de l'équipe |

Le filtrage se fait dans l'application, sur les marts déjà chargés, sans nouvel appel à l'API. Besoin optionnel F5 : un cinquième bloc Buteurs, selon disponibilité des données.

## 4. Exigences non fonctionnelles

| ID | Exigence | Cible |
| --- | --- | --- |
| NF1 | Fraîcheur | Données mises à jour une fois par jour, automatiquement |
| NF2 | Coût | 0 € de fonctionnement |
| NF3 | Respect de l'API | Jamais plus de 10 appels par minute ; aucun appel API depuis le dashboard |
| NF4 | Qualité des données | Tests dbt sur clés, unicité, valeurs non nulles et cohérence (ex. points = 3×G + N) ; un test en échec bloque la publication |
| NF5 | Reproductibilité | Projet installable et lançable en local en moins de 10 minutes via le README |
| NF6 | Idempotence | Relancer le pipeline le même jour ne crée pas de doublons |
| NF7 | Sécurité | Token API stocké en secret, jamais dans le code |
| NF8 | Performance | La page s'affiche en moins de 3 secondes ; les blocs se mettent à jour en moins d'1 seconde après la sélection d'une équipe |
| NF9 | Maintenabilité | Code typé, linté, testé (pytest), CI verte sur chaque push |

## 5. Contraintes et choix techniques

La stack reprend en miniature celle d'une équipe data moderne, uniquement avec des outils gratuits.

| Couche | Choix | Raison |
| --- | --- | --- |
| Source | API football-data.org v4 (offre gratuite) | Gratuite, Ligue 1 incluse, JSON propre |
| Ingestion | Python 3.12, httpx, Pydantic | Client API typé, gestion du rate limit et des erreurs |
| Stockage brut | Fichiers JSON horodatés (couche raw) | Rejouer les transformations sans rappeler l'API |
| Entrepôt | DuckDB | SQL analytique rapide, zéro serveur |
| Transformations | dbt-core + dbt-duckdb | Standard du marché ; couches staging → intermediate → marts, tests et doc intégrés |
| Dashboard | Streamlit, hébergé sur Streamlit Community Cloud | Python, gratuit, lien public |
| Orchestration | GitHub Actions (cron quotidien) | Gratuit, couplé à la CI |
| Qualité | uv, ruff, mypy, pytest, pre-commit | Outillage Python moderne |

Contraintes : 10 appels par minute, saison en cours uniquement, budget d'environ 1 h par jour. Le mode de livraison des données au dashboard hébergé est arrêté dans la spécification technique.

Les données ne remontent jamais de l'API vers le dashboard en direct : tout passe par la couche raw puis par les marts dbt.

## 6. Livrables et jalons

Le projet avance en sept jalons ; chacun se termine par un livrable vérifiable, mergé sur la branche main.

| Jalon | Livrable | Terminé quand |
| --- | --- | --- |
| J1 Cadrage | Cahier des charges + spécification technique | Les deux documents sont validés |
| J2 Setup | Repo GitHub structuré, environnement uv, pre-commit, CI de base | `uv sync` puis `pytest` passent en local et en CI |
| J3 Ingestion | Client API + extraction vers la couche raw | Une commande récupère matchs, classement et équipes sans dépasser le rate limit |
| J4 Modélisation | Projet dbt (staging, intermediate, marts) + tests | `dbt build` passe et produit les tables des blocs F1 à F4 |
| J5 Dashboard | Application Streamlit (F1 à F4) | La page s'affiche en local et la sélection d'une équipe filtre les blocs F2 à F4 |
| J6 Automatisation | Workflow GitHub Actions quotidien + mise en ligne | Le dashboard public se met à jour seul pendant 7 jours d'affilée |
| J7 Finalisation | README, schéma d'architecture, post LinkedIn | Un inconnu peut lancer le projet avec le seul README |

## 7. Critères d'acceptation

- [ ] Le dashboard public affiche les blocs F1 à F4, filtrables par équipe, avec des données de moins de 24 h
- [ ] Le classement affiché correspond au classement officiel de la Ligue 1 à la même date
- [ ] Le pipeline tourne chaque jour sans intervention pendant 7 jours consécutifs
- [ ] Tous les tests dbt et pytest passent ; la CI est verte sur main
- [ ] Relancer le pipeline deux fois le même jour ne crée aucun doublon
- [ ] Aucun secret n'apparaît dans l'historique Git
- [ ] Le README permet d'installer et de lancer le projet en moins de 10 minutes
- [ ] La documentation dbt (lineage, description des modèles) est générée

## 8. Risques

| Risque | Impact | Parade |
| --- | --- | --- |
| L'offre gratuite de l'API change ou est coupée | Pipeline bloqué | Couche raw conservée ; client API isolé derrière une interface pour changer de source |
| Données utiles absentes en gratuit (buteurs, minute des buts) | Page en moins | F5 optionnelle ; vérification des endpoints dès J3 |
| Fichier de données trop lourd pour le dépôt Git | Déploiement compliqué | Ne versionner que les marts, en Parquet compressé |
| Mise en veille de l'app Streamlit gratuite | Premier affichage lent | Accepté pour un projet portfolio |
| Manque de temps (1 h par jour) | Projet qui s'étire | Jalons courts, chacun livrable seul ; V1 volontairement réduite |
