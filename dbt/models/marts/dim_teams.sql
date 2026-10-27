-- Dimension équipe, utilisée par tous les blocs du dashboard.

select
    team_id,
    season,
    team_name,
    coalesce(short_name, team_name) as short_name,
    tla,
    crest_url,
    venue,
    founded_year
from {{ ref('stg_teams') }}
