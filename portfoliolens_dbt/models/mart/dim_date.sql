with spine as (
    select dateadd(day, seq4(), '2023-01-01'::date) as full_date
    from table(generator(rowcount => 1095))
    where full_date <= current_date()
)

select
    to_char(full_date, 'YYYYMMDD')::int      as date_id,
    full_date,
    year(full_date)                            as year,
    month(full_date)                           as month,
    day(full_date)                             as day,
    quarter(full_date)                         as quarter,
    dayofweek(full_date)                       as day_of_week,
    dayname(full_date)                         as day_name,
    monthname(full_date)                       as month_name,
    case when dayofweek(full_date) in (0, 6)
         then false else true end              as is_weekday
from spine
