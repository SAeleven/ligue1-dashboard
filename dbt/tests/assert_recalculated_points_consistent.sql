-- Classement recalculé : points = 3 × victoires + nuls, joués = V + N + D,
-- et les rangs d'une journée vont de 1 au nombre d'équipes sans trou.

with checks as (

    select
        season,
        matchday,
        count(*)                       as n_teams,
        max(position)                  as max_position,
        count(distinct position)       as n_positions,
        count(*) filter (
            where points <> 3 * won + drawn or played <> won + drawn + lost
        )                              as n_inconsistent
    from {{ ref('int_standings_by_matchday') }}
    group by season, matchday

)

select *
from checks
where n_inconsistent > 0
   or max_position <> n_teams
   or n_positions <> n_teams
