# dates
Headache-free datetime in python - mini module


""" Datetime mini lib ----------------------------------------------------------
(c) 2022 BCT

GOAL: Headache free datetime & time arithmetic

PURPOSE:
- Standardize on pd.Timestamps (works well with pd.Timedelta for time arithmetic)
- Meant to work with dataframe but can be used as standalone
- Parse from any datetime format
- Cast to different string foramts  (e.g. iso)

-> NOTE: avoid mixing with other datetime: datetime.datetime or np.datetime64 (parse all)

##
##  KEEP THIS MODULE SMALL - designed for an from import * 
##

KEY FUNCTIONS:
    - dt_parse          parse any datetime & strings; takes in a df, np, string, datetime, etc
    - dt_set_tz         convert time to different timezone
    - dt_now            current time
    - dt_str            returns shortest string (e.g. removes seconds if 0); option to return iso
    - dt_delta_to_res   cast timedelta into float
Use with:
    - datetime.timedelta
    - subtract 2 dates, after adding a tz (dt_parse(d, tz=<pick tz>) and/or dt_set_tz)

EXAMPLE:
    import dates as dt
    # Parse a df index (most of the functions work with a df, string, datetime, other; demonstrating for a df)
        df = pd.DataFrame(index=['2022-07-22 11:33:22.872903-0400'])
        df = dt.dt_parse(df)                        # parse the df index - no tz added
        print(df.index.tzinfo)                      # prints None (no timezone info)
    # Cast into a string
        ts = dt.dt_now()
        ts_iso = dt.dt_str(ts, tz=None, keep_ms=True, isoformat=True) + "Z" # return current time in RFC-3339 format (for Alpaca API)
        print(ts_iso)
    # Readily use time arithmetic
        ts = dt.dt_now(tz=None)
        ts2 = dt.dt_now(tz=None) - pd.Timedelta(minutes=1)
        print(ts < ts2)                             # return False
    # Convert to a date only, but keeps it as pd.Timestamp so arithmetic still works and timezones can be applied so as to safely compare or bucket finer timeframes.
        ts = dt.dt_now()
        date_dt = dt.dt_date_only(ts)               # keep only the date and return a pd.Timestamp
    # Add a timezone when none is available
        ts = dt.dt_now(tz=None)                     # return current time in UTC without tz info
        df = pd.DataFrame(index=[ts])
        df = dt.dt_set_tz(df, "localtz", "utc")     # convert to local tz, assuming anything without tz is UTC
        print(df.index)
    # Convert to tz
        df = dt.dt_set_tz(df, dt.TZ.NYC.st)         # convert time to NYC tz
        print(df.index)
    # Remove tz (converting back to utc when removing)
        df = dt.dt_set_tz(df, None)                 # remove tz info, after converting to UTC - same as dt_clear_tz(df)
        print(df.index)
    # Override timezone (overwrite existing tz without changing time) - NOT RECOMMENDED UNLESS IT IS KNOWN WHY THIS OPERATION IS CONDUCTED
        df = dt.dt_overwrite_tz(df, dt.TZ.LON.st)   # change tz, without converting the time
        print(df.index)
