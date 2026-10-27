# ADR 0002 — Recalcul du classement et départage

- Statut : accepté
- Date : 2026-10-27

## Contexte

L'offre gratuite de football-data.org ne fournit que le classement du jour. Le bloc F2
(évolution journée par journée) exige donc de recalculer le classement à partir des
résultats, ce qui impose d'appliquer les mêmes critères de départage que la LFP.

Le règlement de la Ligue 1 a été revu pour 2025-26 (critères liés aux buts à
l'extérieur supprimés, victoires ajoutées). En cas d'égalité de points :

1. différence de buts générale ;
2. points en confrontations directes ;
3. différence de buts en confrontations directes ;
4. buts marqués ;
5. nombre de victoires ;
6. nombre de victoires à l'extérieur ;
7. classement du fair-play (avertissement = 1 point, exclusion = 3 points) ;
8. tirage au sort.

## Décision

- `int_standings_by_matchday` applique les critères 1 à 6. Les confrontations directes
  sont calculées entre toutes les équipes à égalité de points **et** de différence de
  buts (mini-classement), sur les matchs joués jusqu'à la journée considérée.
- Le critère 7 n'est pas disponible en gratuit (pas de cartons) ; il est remplacé par
  l'identifiant d'équipe, pour un classement déterministe.
- Un match reporté puis joué compte dans sa journée d'origine.
- Le règlement 2025-26 est supposé reconduit en 2026-27 (à vérifier à chaque saison).
- Contrôle : le classement recalculé est comparé au classement officiel du jour.
  Les écarts sur matchs joués, V/N/D et buts **bloquent** la publication ; les écarts
  de points ou de rang ne sont qu'un **avertissement**, car un retrait de points par
  la LFP ou le critère fair-play peuvent les expliquer.
- Un test unitaire dbt vérifie que la confrontation directe passe avant les buts marqués.

## Conséquences

- Les rangs historiques de F2 sont fidèles au règlement, sauf égalité parfaite
  jusqu'au critère 6 (rarissime).
- Une sanction en points n'est pas reflétée dans le classement recalculé ; elle
  apparaît en avertissement dans `dbt build`.

## Sources

- [Ligue 1 — critères de départage 2025/2026](https://ligue1.com/fr/articles/l1_article_2830-)
