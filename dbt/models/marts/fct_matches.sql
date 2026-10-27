-- Matchs joués et à venir, prêts à afficher (bloc F4).

with matches as (

    select * from {{ ref('stg_matches') }}

),

teams as (

    select * from {{ ref('dim_teams') }}

)

select
    matches.match_id,
    matches.season,
    matches.matchday,
    matches.kickoff_at,
    matches.status,
    matches.is_played,
    matches.home_team_id,
    home.short_name                as home_team,
    home.crest_url                 as home_crest_url,
    matches.away_team_id,
    away.short_name                as away_team,
    away.crest_url                 as away_crest_url,
    matches.home_goals,
    matches.away_goals,
    matches.home_goals_half_time,
    matches.away_goals_half_time,
    case
        when not matches.is_played then null
        when matches.home_goals > matches.away_goals then 'home'
        when matches.home_goals < matches.away_goals then 'away'
        else 'draw'
    end                            as outcome
from matches
inner join teams as home on matches.home_team_id = home.team_id
inner join teams as away on matches.away_team_id = away.team_id
