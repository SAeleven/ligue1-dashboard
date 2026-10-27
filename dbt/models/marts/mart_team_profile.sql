-- Profil de chaque équipe : bilans domicile / extérieur, moyennes, séries (bloc F3).

with played as (

    select * from {{ ref('int_team_matches') }}
    where is_played

),

totals as (

    select
        season,
        team_id,
        count(*)                                                        as played,
        count(*) filter (where venue = 'home')                          as home_played,
        count(*) filter (where venue = 'home' and result = 'W')         as home_won,
        count(*) filter (where venue = 'home' and result = 'D')         as home_drawn,
        count(*) filter (where venue = 'home' and result = 'L')         as home_lost,
        coalesce(sum(goals_for) filter (where venue = 'home'), 0)       as home_goals_for,
        coalesce(sum(goals_against) filter (where venue = 'home'), 0)   as home_goals_against,
        count(*) filter (where venue = 'away')                          as away_played,
        count(*) filter (where venue = 'away' and result = 'W')         as away_won,
        count(*) filter (where venue = 'away' and result = 'D')         as away_drawn,
        count(*) filter (where venue = 'away' and result = 'L')         as away_lost,
        coalesce(sum(goals_for) filter (where venue = 'away'), 0)       as away_goals_for,
        coalesce(sum(goals_against) filter (where venue = 'away'), 0)   as away_goals_against,
        sum(goals_for)                                                  as goals_for,
        sum(goals_against)                                              as goals_against,
        count(*) filter (where goals_against = 0)                       as clean_sheets,
        count(*) filter (where goals_for = 0)                           as failed_to_score
    from played
    group by season, team_id

),

ordered as (

    select
        season,
        team_id,
        result,
        row_number() over latest_first     as recency,
        first_value(result) over latest_first as last_result
    from played
    window latest_first as (partition by season, team_id order by kickoff_at desc)

),

streaks as (

    -- Une série s'arrête au premier match (en remontant le temps) qui la brise.
    select
        season,
        team_id,
        any_value(last_result)                                                     as current_streak_result,
        coalesce(min(recency) filter (where result <> last_result) - 1, count(*))  as current_streak_length,
        coalesce(min(recency) filter (where result = 'L') - 1, count(*))           as unbeaten_run,
        coalesce(min(recency) filter (where result = 'W') - 1, count(*))           as winless_run
    from ordered
    group by season, team_id

)

select
    teams.team_id,
    teams.season,
    teams.short_name,
    teams.crest_url,
    coalesce(totals.played, 0)                                       as played,
    coalesce(totals.home_played, 0)                                  as home_played,
    coalesce(totals.home_won, 0)                                     as home_won,
    coalesce(totals.home_drawn, 0)                                   as home_drawn,
    coalesce(totals.home_lost, 0)                                    as home_lost,
    coalesce(totals.home_goals_for, 0)                               as home_goals_for,
    coalesce(totals.home_goals_against, 0)                           as home_goals_against,
    coalesce(totals.away_played, 0)                                  as away_played,
    coalesce(totals.away_won, 0)                                     as away_won,
    coalesce(totals.away_drawn, 0)                                   as away_drawn,
    coalesce(totals.away_lost, 0)                                    as away_lost,
    coalesce(totals.away_goals_for, 0)                               as away_goals_for,
    coalesce(totals.away_goals_against, 0)                           as away_goals_against,
    round(totals.goals_for / nullif(totals.played, 0), 2)            as goals_for_per_match,
    round(totals.goals_against / nullif(totals.played, 0), 2)        as goals_against_per_match,
    coalesce(totals.clean_sheets, 0)                                 as clean_sheets,
    coalesce(totals.failed_to_score, 0)                              as failed_to_score,
    streaks.current_streak_result,
    coalesce(streaks.current_streak_length, 0)                       as current_streak_length,
    coalesce(streaks.unbeaten_run, 0)                                as unbeaten_run,
    coalesce(streaks.winless_run, 0)                                 as winless_run
from {{ ref('dim_teams') }} as teams
left join totals
    on  teams.season = totals.season
    and teams.team_id = totals.team_id
left join streaks
    on  teams.season = streaks.season
    and teams.team_id = streaks.team_id
