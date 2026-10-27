-- Rang et points cumulés de chaque équipe après chaque journée (bloc F2).

select
    standings.standing_key,
    standings.season,
    standings.matchday,
    standings.team_id,
    teams.short_name,
    teams.tla,
    standings.position,
    standings.points,
    standings.goal_difference,
    standings.played
from {{ ref('int_standings_by_matchday') }} as standings
inner join {{ ref('dim_teams') }} as teams on standings.team_id = teams.team_id
