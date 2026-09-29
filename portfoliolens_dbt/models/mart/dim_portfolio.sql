select
    PORTFOLIO_ID                  as portfolio_id,
    NAME                          as name,
    RISK_PROFILE                  as risk_profile,
    BENCHMARK_TICKER              as benchmark_ticker,
    INCEPTION_DATE::date          as inception_date,
    INITIAL_VALUE::float          as initial_value
from PORTFOLIOLENS_RAW.PUBLIC.RAW_PORTFOLIOS
