-- Vue d'ensemble de la saison : moyennes de la ligue et faits marquants
-- (blocs F3 et F4 sans équipe sélectionnée). Une ligne par saison.

with matches as (

    select * from {{ ref('fct_matches') }}

),

played as (

    select * from matches where is_played

),

seasons as (

    select distinct season from matches

),

totals as (

    select
        season,
        count(*)                                                            as matches_played,
        sum(home_goals + away_goals)                                        as goals,
        round(avg(home_goals + away_goals), 2)                              as goals_per_match,
        round(avg(home_goals), 2)                                           as home_goals_per_match,
        round(avg(away_goals), 2)                                           as away_goals_per_match,
        round(100.0 * count(*) filter (where outcome = 'home') / count(*), 1) as home_win_pct,
        round(100.0 * count(*) filter (where outcome = 'draw') / count(*), 1) as draw_pct,
        round(100.0 * count(*) filter (where outcome = 'away') / count(*), 1) as away_win_pct,
        max(matchday)                                                       as last_played_matchday
    from played
    group by season

),

next_matchday as (

    -- Journée du prochain match programmé (les matchs reportés sans date sont ignorés).
    select season, arg_min(matchday, kickoff_at) as next_matchday
    from matches
    where status in ('SCHEDULED', 'TIMED')
    group by season

),

biggest_win as (

    select season, match_id as biggest_win_match_id
    from played
    where outcome <> 'draw'
    qualify row_number() over (
        partition by season
        order by abs(home_goals - away_goals) desc, home_goals + away_goals desc, kickoff_at
    ) = 1

),

highest_scoring as (

    select season, match_id as highest_scoring_match_id
    from played
    qualify row_number() over (
        partition by season
        order by home_goals + away_goals desc, kickoff_at
    ) = 1

),

freshness as (

    select season, max(extracted_on) as data_as_of
    from {{ ref('stg_matches') }}
    group by season

)

select
    seasons.season,
    coalesce(totals.matches_played, 0) as matches_played,
    coalesce(totals.goals, 0)          as goals,
    totals.goals_per_match,
    totals.home_goals_per_match,
    totals.away_goals_per_match,
    totals.home_win_pct,
    totals.draw_pct,
    totals.away_win_pct,
    totals.last_played_matchday,
    next_matchday.next_matchday,
    biggest_win.biggest_win_match_id,
    highest_scoring.highest_scoring_match_id,
    freshness.data_as_of
from seasons
left join totals          on seasons.season = totals.season
left join next_matchday   on seasons.season = next_matchday.season
left join biggest_win     on seasons.season = biggest_win.season
left join highest_scoring on seasons.season = highest_scoring.season
left join freshness       on seasons.season = freshness.season
