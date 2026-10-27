-- Le classement recalculé doit coïncider avec le classement officiel du dernier
-- snapshot sur tout ce qui découle des seuls résultats : matchs joués, V/N/D,
-- buts pour et contre. Bloquant : un écart signifie une donnée manquante ou fausse.
--
-- Les points et le rang sont comparés à part, en avertissement
-- (assert_points_and_positions_match_official), car une sanction de la LFP
-- (retrait de points) les fait légitimement diverger.

with recalculated as (

    select * from {{ ref('mart_standings_current') }}

),

official as (

    select * from {{ ref('stg_standings') }}
    where standing_type = 'total'

)

select
    coalesce(recalculated.team_id, official.team_id) as team_id,
    recalculated.played        as recalculated_played,
    official.played            as official_played,
    recalculated.won           as recalculated_won,
    official.won               as official_won,
    recalculated.drawn         as recalculated_drawn,
    official.drawn             as official_drawn,
    recalculated.goals_for     as recalculated_goals_for,
    official.goals_for         as official_goals_for,
    recalculated.goals_against as recalculated_goals_against,
    official.goals_against     as official_goals_against
from recalculated
full outer join official
    on  recalculated.season = official.season
    and recalculated.team_id = official.team_id
where recalculated.team_id is null
   or official.team_id is null
   or recalculated.played        <> official.played
   or recalculated.won           <> official.won
   or recalculated.drawn         <> official.drawn
   or recalculated.lost          <> official.lost
   or recalculated.goals_for     <> official.goals_for
   or recalculated.goals_against <> official.goals_against
