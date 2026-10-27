-- Sur une saison, les buts marqués par toutes les équipes égalent les buts encaissés.

select
    season,
    sum(goals_for)     as goals_for,
    sum(goals_against) as goals_against
from {{ ref('int_team_matches') }}
where is_played
group by season
having sum(goals_for) <> sum(goals_against)
