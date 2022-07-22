# dates
Headache-free datetime in python - mini module


Datetime mini lib ----------------------------------------------------------

(c) 2022 BCT

GOAL: Headache free datetime & time arithmetic

PURPOSE:
- Standardize on pd.Timestamps (works well with pd.Timedelta for time arithmetic)
- Meant to work with dataframe but can be used as standalone
- Parse from any datetime format
- Cast to different string foramts  (e.g. iso)

-> NOTE: avoid mixing with other datetime: datetime.datetime or np.datetime64 (parse all)

KEY FUNCTIONS:
- dt_parse          parse any datetime & strings; takes in a df, np, string, datetime, etc
- dt_set_tz         convert time to different timezone
- dt_now            current time
- dt_str            returns shortest string (e.g. removes seconds if 0); option to return iso
- dt_delta_to_res   cast timedelta into float
