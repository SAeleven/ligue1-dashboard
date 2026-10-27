-- Classement officiel du dernier snapshot : une ligne par équipe et par type
-- de classement (total, home, away).

with latest_snapshot as (

    select season, extracted_on, payload
    from {{ source('raw', 'standings') }}
    qualify row_number() over (partition by season order by extracted_on desc) = 1

),

standings as (

    select
        season,
        extracted_on,
        unnest(json_extract(payload, '$.standings[*]')) as standing_json
    from latest_snapshot

),

table_rows as (

    select
        season,
        extracted_on,
        lower(standing_json ->> '$.type') as standing_type,
        unnest(json_extract(standing_json, '$.table[*]')) as row_json
    from standings

),

renamed as (

    select
        standing_type || '-' || (row_json ->> '$.team.id')   as standing_id,
        season,
        standing_type,
        (row_json ->> '$.team.id')::integer                  as team_id,
        (row_json ->> '$.position')::integer                 as position,
        (row_json ->> '$.playedGames')::integer              as played,
        (row_json ->> '$.won')::integer                      as won,
        (row_json ->> '$.draw')::integer                     as drawn,
        (row_json ->> '$.lost')::integer                     as lost,
        (row_json ->> '$.points')::integer                   as points,
        (row_json ->> '$.goalsFor')::integer                 as goals_for,
        (row_json ->> '$.goalsAgainst')::integer             as goals_against,
        (row_json ->> '$.goalDifference')::integer           as goal_difference,
        row_json ->> '$.form'                                as form,
        extracted_on
    from table_rows

)

select * from renamed
