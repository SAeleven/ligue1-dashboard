-- Classement actuel recalculé, avec la forme sur 5 matchs et la zone (bloc F1).

with standings as (

    select * from {{ ref('int_standings_by_matchday') }}
    qualify matchday = max(matchday) over (partition by season)

),

recent_results as (

    select
        season,
        team_id,
        result,
        row_number() over (partition by season, team_id order by kickoff_at desc) as recency
    from {{ ref('int_team_matches') }}
    where is_played

),

form as (

    -- Du plus ancien au plus récent : "WWDLW" se lit de gauche à droite.
    select
        season,
        team_id,
        string_agg(result, '' order by recency desc) as form
    from recent_results
    where recency <= 5
    group by season, team_id

),

teams as (

    select * from {{ ref('dim_teams') }}

)

select
    standings.team_id,
    standings.season,
    standings.matchday                as last_matchday,
    standings.position,
    teams.team_name,
    teams.short_name,
    teams.tla,
    teams.crest_url,
    standings.played,
    standings.won,
    standings.drawn,
    standings.lost,
    standings.goals_for,
    standings.goals_against,
    standings.goal_difference,
    standings.points,
    form.form,
    case
        when standings.position <= {{ var('ucl_last_position') }}  then 'Ligue des champions'
        when standings.position <= {{ var('uel_last_position') }}  then 'Ligue Europa'
        when standings.position <= {{ var('uecl_last_position') }} then 'Ligue Conférence'
        when standings.position =  {{ var('relegation_playoff_position') }} then 'Barrage'
        when standings.position >= {{ var('relegation_first_position') }}   then 'Relégation'
    end                               as zone
from standings
inner join teams on standings.team_id = teams.team_id
left join form
    on  standings.season = form.season
    and standings.team_id = form.team_id
