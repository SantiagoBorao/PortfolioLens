with source as (
    select * from PORTFOLIOLENS_RAW.PUBLIC.RAW_PRICES
)

select
    PRICE_DATE::date     as price_date,
    TICKER               as ticker,
    ASSET_NAME           as asset_name,
    ASSET_TYPE           as asset_type,
    SECTOR               as sector,
    COUNTRY              as country,
    OPEN::float          as open,
    HIGH::float          as high,
    LOW::float           as low,
    CLOSE::float         as close,
    ADJ_CLOSE::float     as adj_close,
    VOLUME::bigint       as volume
from source
where CLOSE is not null
  and CLOSE > 0
