-- Sharpe ratio = (annualised return - risk_free_rate) / annual_volatility
-- risk_free_rate = 0.04 (4%, approximate for current environment)

with base as (
    select distinct
        portfolio_id,
        price_date,
        total_portfolio_value,
        daily_return,
        cumulative_return
    from {{ ref('fact_portfolio_positions') }}
),

stats as (
    select
        portfolio_id,
        min(price_date)                                                                  as start_date,
        max(price_date)                                                                  as end_date,
        avg(daily_return)                                                                as avg_daily_return,
        stddev(daily_return)                                                             as daily_volatility,
        stddev(daily_return) * sqrt(252)                                                 as annual_volatility,
        (avg(daily_return) * 252 - 0.04) / nullif(stddev(daily_return) * sqrt(252), 0) as sharpe_ratio
    from base
    group by portfolio_id
),

latest as (
    select
        portfolio_id,
        total_portfolio_value  as current_value,
        cumulative_return      as total_return
    from base
    qualify row_number() over (partition by portfolio_id order by price_date desc) = 1
)

select
    s.portfolio_id,
    dp.name             as portfolio_name,
    dp.risk_profile,
    dp.benchmark_ticker,
    s.start_date,
    s.end_date,
    l.current_value,
    l.total_return,
    s.avg_daily_return,
    s.daily_volatility,
    s.annual_volatility,
    s.sharpe_ratio
from stats                          s
left join latest                    l  using (portfolio_id)
left join {{ ref('dim_portfolio') }} dp using (portfolio_id)
