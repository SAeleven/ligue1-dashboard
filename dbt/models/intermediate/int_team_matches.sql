-- Chaque match vu par chacune des deux équipes : deux lignes par match.
-- Base de tous les calculs par équipe (classement, profil, forme).

with matches as (

    select * from {{ ref('stg_matches') }}

),

sides as (

    select
        match_id,
        season,
        matchday,
        kickoff_at,
        status,
        is_played,
        home_team_id as team_id,
        away_team_id as opponent_id,
        'home'       as venue,
        home_goals   as goals_for,
        away_goals   as goals_against
    from matches

    union all

    select
        match_id,
        season,
        matchday,
        kickoff_at,
        status,
        is_played,
        away_team_id as team_id,
        home_team_id as opponent_id,
        'away'       as venue,
        away_goals   as goals_for,
        home_goals   as goals_against
    from matches

),

with_result as (

    select
        *,
        case
            when not is_played then null
            when goals_for > goals_against then 'W'
            when goals_for = goals_against then 'D'
            else 'L'
        end as result
    from sides

)

select
    match_id || '-' || team_id as team_match_id,
    match_id,
    season,
    matchday,
    kickoff_at,
    status,
    is_played,
    team_id,
    opponent_id,
    venue,
    goals_for,
    goals_against,
    result,
    case result when 'W' then 3 when 'D' then 1 when 'L' then 0 end as points
from with_result
