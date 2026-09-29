select distinct
    ticker       as asset_id,
    asset_name   as name,
    asset_type,
    sector,
    country
from {{ ref('stg_prices') }}
