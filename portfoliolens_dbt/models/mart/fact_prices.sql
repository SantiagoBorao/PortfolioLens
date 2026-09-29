select
    md5(p.price_date::string || '-' || p.ticker)  as price_id,
    d.date_id,
    p.price_date,
    p.ticker    as asset_id,
    p.open,
    p.high,
    p.low,
    p.close,
    p.adj_close,
    p.volume
from {{ ref('stg_prices') }} p
left join {{ ref('dim_date') }} d on p.price_date = d.full_date
