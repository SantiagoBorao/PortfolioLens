select
    md5(p.price_date::string || '-' || p.portfolio_id || '-' || p.ticker) as position_id,
    d.date_id,
    p.price_date,
    p.portfolio_id,
    p.ticker            as asset_id,
    p.quantity,
    p.price,
    p.market_value,
    p.total_portfolio_value,
    p.weight_pct,
    p.daily_return,
    p.cumulative_return
from {{ ref('stg_portfolio_positions') }} p
left join {{ ref('dim_date') }} d on p.price_date = d.full_date
