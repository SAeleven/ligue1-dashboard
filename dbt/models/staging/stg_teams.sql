-- Une équipe par ligne, telle que décrite dans le dernier snapshot.

with snapshots as (

    select season, extracted_on, payload
    from {{ source('raw', 'teams') }}

),

exploded as (

    select
        season,
        extracted_on,
        unnest(json_extract(payload, '$.teams[*]')) as team_json
    from snapshots

),

renamed as (

    select
        (team_json ->> '$.id')::integer          as team_id,
        team_json ->> '$.name'                   as team_name,
        team_json ->> '$.shortName'              as short_name,
        team_json ->> '$.tla'                    as tla,
        team_json ->> '$.crest'                  as crest_url,
        (team_json ->> '$.founded')::integer     as founded_year,
        team_json ->> '$.venue'                  as venue,
        season,
        extracted_on
    from exploded

)

select *
from renamed
qualify row_number() over (partition by team_id order by extracted_on desc) = 1
