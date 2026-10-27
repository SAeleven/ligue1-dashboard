-- Le classement officiel doit respecter points = 3 × victoires + nuls
-- et matchs joués = victoires + nuls + défaites. Renvoie les lignes en erreur.

select
    standing_id,
    points,
    won,
    drawn,
    lost,
    played
from {{ ref('stg_standings') }}
where points != 3 * won + drawn
   or played != won + drawn + lost
