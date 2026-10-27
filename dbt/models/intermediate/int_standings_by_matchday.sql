-- Classement recalculé après chaque journée, à partir des seuls résultats.
--
-- Une ligne par équipe et par journée jouée. Les cumuls incluent tous les matchs
-- terminés dont la journée est <= à la journée courante (un match reporté puis
-- joué compte dans sa journée d'origine).
--
-- Départage (règlement LFP 2025-26, voir docs/adr/0002-departage.md) :
--   points, différence de buts générale, points puis différence de buts en
--   confrontations directes entre équipes à égalité, buts marqués, victoires,
--   victoires à l'extérieur. Le critère fair-play n'est pas disponible en
--   gratuit ; l'identifiant d'équipe sert de dernier critère déterministe.

with played_matches as (

    select * from {{ ref('int_team_matches') }}
    where is_played

),

matchdays as (

    select distinct season, matchday from played_matches

),

teams as (

    select distinct season, team_id from {{ ref('int_team_matches') }}

),

-- Toutes les équipes à toutes les journées, même sans match ce jour-là.
grid as (

    select teams.season, teams.team_id, matchdays.matchday
    from teams
    inner join matchdays on teams.season = matchdays.season

),

per_matchday as (

    select
        grid.season,
        grid.team_id,
        grid.matchday,
        count(played_matches.match_id)                                         as played,
        count(*) filter (where played_matches.result = 'W')                    as won,
        count(*) filter (where played_matches.result = 'D')                    as drawn,
        count(*) filter (where played_matches.result = 'L')                    as lost,
        count(*) filter (
            where played_matches.result = 'W' and played_matches.venue = 'away'
        )                                                                      as away_won,
        coalesce(sum(played_matches.goals_for), 0)                             as goals_for,
        coalesce(sum(played_matches.goals_against), 0)                         as goals_against,
        coalesce(sum(played_matches.points), 0)                                as points
    from grid
    left join played_matches
        on  grid.season = played_matches.season
        and grid.team_id = played_matches.team_id
        and grid.matchday = played_matches.matchday
    group by grid.season, grid.team_id, grid.matchday

),

cumulative as (

    select
        season,
        team_id,
        matchday,
        (sum(played) over w)::integer        as played,
        (sum(won) over w)::integer           as won,
        (sum(drawn) over w)::integer         as drawn,
        (sum(lost) over w)::integer          as lost,
        (sum(away_won) over w)::integer      as away_won,
        (sum(goals_for) over w)::integer     as goals_for,
        (sum(goals_against) over w)::integer as goals_against,
        (sum(points) over w)::integer        as points
    from per_matchday
    window w as (
        partition by season, team_id
        order by matchday
        rows between unbounded preceding and current row
    )

),

with_difference as (

    select *, goals_for - goals_against as goal_difference
    from cumulative

),

-- Paires d'équipes à égalité de points ET de différence de buts à une journée.
tied_pairs as (

    select
        a.season,
        a.matchday,
        a.team_id,
        b.team_id as rival_id
    from with_difference as a
    inner join with_difference as b
        on  a.season = b.season
        and a.matchday = b.matchday
        and a.points = b.points
        and a.goal_difference = b.goal_difference
        and a.team_id <> b.team_id

),

-- Mini-classement des confrontations directes entre équipes à égalité.
head_to_head as (

    select
        tied_pairs.season,
        tied_pairs.matchday,
        tied_pairs.team_id,
        sum(played_matches.points)::integer                                  as h2h_points,
        sum(played_matches.goals_for - played_matches.goals_against)::integer as h2h_goal_difference
    from tied_pairs
    inner join played_matches
        on  tied_pairs.season = played_matches.season
        and tied_pairs.team_id = played_matches.team_id
        and tied_pairs.rival_id = played_matches.opponent_id
        and played_matches.matchday <= tied_pairs.matchday
    group by tied_pairs.season, tied_pairs.matchday, tied_pairs.team_id

),

ranked as (

    select
        with_difference.*,
        coalesce(head_to_head.h2h_points, 0)          as h2h_points,
        coalesce(head_to_head.h2h_goal_difference, 0) as h2h_goal_difference
    from with_difference
    left join head_to_head
        on  with_difference.season = head_to_head.season
        and with_difference.matchday = head_to_head.matchday
        and with_difference.team_id = head_to_head.team_id

)

select
    season || '-' || matchday || '-' || team_id as standing_key,
    season,
    matchday,
    team_id,
    row_number() over (
        partition by season, matchday
        order by
            points desc,
            goal_difference desc,
            h2h_points desc,
            h2h_goal_difference desc,
            goals_for desc,
            won desc,
            away_won desc,
            team_id
    )::integer as position,
    played,
    won,
    drawn,
    lost,
    goals_for,
    goals_against,
    goal_difference,
    points,
    away_won,
    h2h_points,
    h2h_goal_difference
from ranked
