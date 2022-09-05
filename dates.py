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

"""
from enum import Enum
import pandas as pd
import numpy as np
import unittest
from datetime import datetime, timedelta


class TZ(Enum):
    """
    Helper Enum with standard timezone names
    Example:
        TZ.USEAST.st    # return the string used to identify US Eastern timezone
    """
    UTC = "utc"                 # appears to have same results as "gmt"
    NYC = "America/New_York"
    USEAST = "US/Eastern"
    #EST - purposefully excluding as these create confusion with seasonal time changes - use USEAST instead
    #EDT - purposefully excluding as these create confusion with seasonal time changes - use USEAST instead
    LON = "Europe/London"
    @property
    def st(self): return self.value

# Daytime mini lib ----------------------------------------------------------
# PURPOSE: 1/ focus on pandas, and commit to its datetime management 
#          2/ offer flexibility to replace the pd datetime backend later if it fails
# warning: pandas uses pytz tz info, different than datetime https://stackoverflow.com/questions/62382814/tzinfo-in-pandas-and-datetime-seems-to-be-different-is-there-a-workaround
# https://stackoverflow.com/questions/2720319/python-figure-out-local-timezone
# timezones (use tzinfo): 'America/New_York' 'EST' 'US/Eastern'
from tzlocal import get_localzone
def dt_local_tz() -> str:
    """local timezone"""
    # LOCAL_TIMEZONE = datetime.now(timezone.utc).astimezone().tzinfo
    return str(get_localzone())

def dt_now(force_tz="localtz", tz=None, clear_tz=False) -> pd.Timestamp:
    """current local date/time w/ force_tz attached
    force_tz = "localtz"  -> append local tz
    force_tz = None       -> local time, no tz appended
    force_tz = other      -> SET (force) to other tz (keep time as is, no conversion)
    tz       = convert to <tz> IF NOT NONE
    clear_tz = True       -> override all params, remove tz and convert to UTC

    Sample output (not for doctest):
    >>>> [dt.dt_now(),                      # use local tz, and use machine time
          dt.dt_now(force_tz="UTC"),        # force UTC tz, with machine time
          dt.dt_now(tz="UTC")]              # convert to UTC
    [Timestamp('2022-07-15 16:23:35.128231-0400', tz='America/New_York'),
     Timestamp('2022-07-15 16:23:35.128425+0000', tz='UTC'),
     Timestamp('2022-07-15 20:23:35.128445+0000', tz='UTC')]
    """
    d = pd.Timestamp.now()
    if force_tz == "localtz":
        d = d.tz_localize(dt_local_tz())    # applies tz so can be subtracted
    else:
        d = d.tz_localize(force_tz)#dt_set_tz(d, tz)
    if tz is not None:
        d = dt_convert_tz(d, tz)
    if clear_tz:
        d = dt_clear_tz(d)
    return d

def dt_now_iswithin(min_time, max_time) -> bool:
    return min_time < dt_now() < max_time

def dt_convert_tz(d, tz):
    """converts timestamp(s) to <tz>
    assumes a UTC timestamp if none is provided in the timestamp.
    Use dt_set_tz for conversions from non UTC timestamps with no timestamp provided.
    -   type(d) is pd.DataFrame -> apply to d.index
    -   type(d) is pd.Series -> apply to the series individual items (not the index!)
    -   type(d) is pd.Timestamp -> apply to item
    """
    return dt_set_tz(d, tz, "utc")

def dt_overwrite_tz(d, tz):
    """set/overwrite tz ignoring prior tz"""
    if not isinstance(d, (pd.Timestamp, pd.core.series.Series, pd.DataFrame, pd.core.indexes.datetimes.DatetimeIndex)):
        print(f"[BCT Warning] using dt_overwrite_tz on a type '{type(d)}' other than designed for")

    if tz == "localtz":
        tz = dt_local_tz()

    if isinstance(d, pd.DataFrame):
        assert isinstance(d.index, pd.core.indexes.datetimes.DatetimeIndex), "[BCT Error] dt_set_tz() index is not a DatetimeIndex. use pd.to_datetime to convert first."
        d.index = dt_overwrite_tz(d.index, tz)            # apply to the index
    elif isinstance(d, pd.core.series.Series):
        d = d.apply(lambda x: dt_overwrite_tz(x, tz=tz))  # apply to the column
    else:                       # timestamps & pd index, other non df & series
        d = d.tz_localize(tz)   # overwrite tz
    return d

def dt_set_tz(d, tz=None,
              when_notz="utc") -> pd.Timestamp:
    """convert to <tz> timezone
    if no tz, assume timestamp is set to tz = <when_notz> (then convert to <tz>)

    PARAM
    tz: convert to tz
    -   tz=None -> convert to UTC AND remove the tz info
    -   tz="utc" -> convert to utc
    -   tz="localtz" -> convert to local tz
    when_notz: fills inexistnet tz with when_notz
    -   when_notz="utc" -> sets no tz to "utc" [**DEFAULT** - Leave as is unless it is _known_ that the timestamp is in a different tz that is not reported]
    -   when_notz="localtz" -> sets no tz to local tz
    d
    -   IF NO TZ FOUND, APPLY TZ (NOT UTC)
    -   type(d) is pd.DataFrame -> apply to d.index
    -   type(d) is pd.Series -> apply to the series individual items
    -   type(d) is pd.Timestamp -> apply to item
    """
    if not isinstance(d, (pd.Timestamp, pd.core.series.Series, pd.DataFrame, pd.core.indexes.datetimes.DatetimeIndex)):
        print(f"[BCT Warning] using dt_set_tz on a type '{type(d)}' other than designed for")

    if tz == "localtz":
        tz = dt_local_tz()
    if when_notz == "localtz":
        when_notz = dt_local_tz()

    if isinstance(d, pd.DataFrame):
        assert isinstance(d.index, pd.core.indexes.datetimes.DatetimeIndex), "[BCT Error] dt_set_tz() index is not a DatetimeIndex. use pd.to_datetime to convert first."
        d.index = dt_set_tz(d.index, tz, when_notz)          # apply to the index
    elif isinstance(d, pd.core.series.Series):
        d = d.apply(lambda x: dt_set_tz(x, tz, when_notz))   # apply to the column
    else:                       # timestamps & pd index, other non df & series
        if d.tzinfo is None:
            d = d.tz_localize(when_notz)
        d = d.tz_convert(tz)
    return d

def dt_set_tz_local(d) -> pd.Timestamp:
    return dt_set_tz(d, dt_local_tz())

def dt_clear_tz(d) -> pd.Timestamp:
    """remove tz and converts back to UTC"""
    return dt_set_tz(d, tz=None, when_notz="utc")

def dt_parse(date_pd_or_str, tz=None, when_notz="utc") -> pd.Timestamp:
    """parse string, df's index, series
    1/ if a TZ in timestamp, ignore when_notz argument
    2/ if no TZ in timestamp, assume <when_notz> timezone
    3/ convert to <tz> timezone
    
    tz=None      -> convert to UTC [default]
    tz="localtz" -> converted to local tz
    
    e.g. to convert a time described in local hour without specification in the timestamp:
    dt_parse("2022-01-01 08:00:01", when_notz="localtz")
    
    30M rows dataframe processed in 6.5s
    NOTE: if parsing just a time, will append today's date. Subtractions can then be conducted.
    """
    if isinstance(date_pd_or_str, pd.DataFrame):    # for Df, apply to the index
        d = date_pd_or_str.copy()
        d.index = pd.to_datetime(date_pd_or_str.index)
    else:
        d = pd.to_datetime(date_pd_or_str)          # other: just apply to_datetime
    d = dt_set_tz(d, tz, when_notz)
    return d

def dt_date_only(d) -> pd.Timestamp:
    """Keep date only - remove all h, m, s, ms from Timestamp, remove tz"""
    return dt_parse(d.date(), tz=None)

def dt_str(d: pd.Timestamp, tz="utc", keep_ms=False, isoformat=False) -> str:
    """ tranform to shortest str without losing generality
    by default, convert to utc, remove tz, convert to date if h:m:s == 0"""
    assert isinstance(d, pd.Timestamp), "[BCT Error] dt_str() only takes timestamps"
    if tz == "utc":
        tz=None
    d = dt_set_tz(d, tz)
    if not isoformat and d.hour + d.minute + d.second == 0:
        d=d.date()
        return str(d)                   # stop; rest of fun expects Timestamp not datetime.date
    if not keep_ms:
        d=d.replace(microsecond=0)
    if isoformat:
        return d.isoformat()            # note: isoformat() does NOT append Z for UTC
    return str(d)

def dt_delta_to_res(tdelta: pd.Timedelta, res="m") -> float:
    """ cast a timedelta into a float
    res: 
        - "ms" milliseconds
        - "s" seconds
        - "m" minutes
        - "h" hours
        - "D" (capitalized) days
        - "W" (capitalized) weeks
        - "Y" (capitalized) years"""
    return tdelta/np.timedelta64(1, res)



# -----------------------------------------------------------------------
# Basic unit tests
class test(unittest.TestCase):
    def time_test(self):
        T0 = dt_now()
        T1 = T0 + timedelta(hours=2)
        T2 = T0 + timedelta(hours=-2)
        self.assertTrue(dt_now_iswithin(T0,T1))
        self.assertTrue(not dt_now_iswithin(T1,T0))
        
    def test_dt_set_tz(self):
        ts1 = pd.to_datetime("23:55Z")  # w/ UTC tz
        ts2 = pd.to_datetime("23:55")   # no tz
        c1 = str(dt_set_tz(ts1, TZ.USEAST.st)), str(dt_set_tz(ts2, TZ.USEAST.st)) == \
            ("(Timestamp('2022-06-19 19:55:00-0400', tz='US/Eastern')",
             "Timestamp('2022-06-19 23:55:00-0400', tz='US/Eastern'))")
        c2 = str((dt_set_tz(ts1, None), dt_set_tz(ts2, None))) == \
            ("(Timestamp('2022-06-19 23:55:00'), "
             "Timestamp('2022-06-19 23:55:00'))")
        c3 = str((dt_clear_tz(ts1), dt_clear_tz(ts2))) == \
            ("(Timestamp('2022-06-19 23:55:00'), "
             "Timestamp('2022-06-19 23:55:00'))")
        self.assertTrue(c1)
        # self.assertTrue(c2)
        # self.assertTrue(c3)


if __name__ == '__main__':
    unittest.main()




