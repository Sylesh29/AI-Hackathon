{{ config(
    materialized='table',
    meta={
        "dimension": {
            "id": {"type": "number"},
            "message": {"type": "string"}
        }
    }
) }}

select 1 as id, 'hello_lightdash' as message
