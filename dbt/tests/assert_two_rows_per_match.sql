-- Chaque match doit apparaître exactement deux fois dans int_team_matches
-- (une fois par équipe), l'une à domicile et l'autre à l'extérieur.

select
    match_id,
    count(*)                                 as n_rows,
    count(*) filter (where venue = 'home')   as n_home
from {{ ref('int_team_matches') }}
group by match_id
having count(*) <> 2 or count(*) filter (where venue = 'home') <> 1
