-- Classement des buteurs (bloc F5).

select
    scorers.player_id,
    scorers.season,
    rank() over (
        partition by scorers.season
        order by scorers.goals desc
    )::integer                           as rank,
    scorers.player_name,
    scorers.team_id,
    teams.short_name                     as team,
    teams.crest_url,
    scorers.goals,
    scorers.assists,
    scorers.penalties,
    scorers.played_matches
from {{ ref('stg_scorers') }} as scorers
inner join {{ ref('dim_teams') }} as teams on scorers.team_id = teams.team_id
