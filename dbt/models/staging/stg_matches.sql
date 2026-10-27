-- Un match par ligne, dans son état le plus récent (dernier snapshot où il apparaît).

with snapshots as (

    select season, extracted_on, payload
    from {{ source('raw', 'matches') }}

),

exploded as (

    select
        season,
        extracted_on,
        unnest(json_extract(payload, '$.matches[*]')) as match_json
    from snapshots

),

renamed as (

    select
        (match_json ->> '$.id')::integer                     as match_id,
        season,
        (match_json ->> '$.matchday')::integer               as matchday,
        (match_json ->> '$.utcDate')::timestamptz            as kickoff_at,
        match_json ->> '$.status'                            as status,
        match_json ->> '$.stage'                             as stage,
        (match_json ->> '$.homeTeam.id')::integer            as home_team_id,
        (match_json ->> '$.awayTeam.id')::integer            as away_team_id,
        (match_json ->> '$.score.fullTime.home')::integer    as home_goals,
        (match_json ->> '$.score.fullTime.away')::integer    as away_goals,
        (match_json ->> '$.score.halfTime.home')::integer    as home_goals_half_time,
        (match_json ->> '$.score.halfTime.away')::integer    as away_goals_half_time,
        match_json ->> '$.score.winner'                      as winner,
        match_json ->> '$.score.duration'                    as duration,
        (match_json ->> '$.lastUpdated')::timestamptz        as last_updated_at,
        extracted_on
    from exploded

)

select *
from renamed
qualify row_number() over (partition by match_id order by extracted_on desc) = 1
