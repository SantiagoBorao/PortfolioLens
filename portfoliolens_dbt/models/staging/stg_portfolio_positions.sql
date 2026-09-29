with source as (
    select * from PORTFOLIOLENS_RAW.PUBLIC.RAW_POSITIONS
)

select
    PRICE_DATE::date              as price_date,
    PORTFOLIO_ID                  as portfolio_id,
    PORTFOLIO_NAME                as portfolio_name,
    RISK_PROFILE                  as risk_profile,
    BENCHMARK_TICKER              as benchmark_ticker,
    TICKER                        as ticker,
    QUANTITY::float               as quantity,
    PRICE::float                  as price,
    MARKET_VALUE::float           as market_value,
    TOTAL_PORTFOLIO_VALUE::float  as total_portfolio_value,
    WEIGHT_PCT::float             as weight_pct,
    DAILY_RETURN::float           as daily_return,
    CUMULATIVE_RETURN::float      as cumulative_return
from source
