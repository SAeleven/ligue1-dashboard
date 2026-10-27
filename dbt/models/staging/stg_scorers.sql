-- Classement des buteurs du dernier snapshot : une ligne par joueur.

with latest_snapshot as (

    select season, extracted_on, payload
    from {{ source('raw', 'scorers') }}
    qualify row_number() over (partition by season order by extracted_on desc) = 1

),

exploded as (

    select
        season,
        extracted_on,
        unnest(json_extract(payload, '$.scorers[*]')) as scorer_json
    from latest_snapshot

),

renamed as (

    select
        (scorer_json ->> '$.player.id')::integer         as player_id,
        scorer_json ->> '$.player.name'                  as player_name,
        (scorer_json ->> '$.team.id')::integer           as team_id,
        (scorer_json ->> '$.playedMatches')::integer     as played_matches,
        (scorer_json ->> '$.goals')::integer             as goals,
        (scorer_json ->> '$.assists')::integer           as assists,
        (scorer_json ->> '$.penalties')::integer         as penalties,
        season,
        extracted_on
    from exploded

)

select * from renamed
