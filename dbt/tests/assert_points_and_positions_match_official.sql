{{ config(severity='warn') }}

-- Points et rang recalculés comparés au classement officiel.
-- Avertissement seulement : un retrait de points par la LFP ou le critère
-- fair-play (absent des données gratuites) peut expliquer un écart.

select
    recalculated.team_id,
    recalculated.points   as recalculated_points,
    official.points       as official_points,
    recalculated.position as recalculated_position,
    official.position     as official_position
from {{ ref('mart_standings_current') }} as recalculated
inner join {{ ref('stg_standings') }} as official
    on  recalculated.season = official.season
    and recalculated.team_id = official.team_id
    and official.standing_type = 'total'
where recalculated.points <> official.points
   or recalculated.position <> official.position
