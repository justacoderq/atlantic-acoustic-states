import argparse, json
from pathlib import Path
import pandas as pd

ROOT=Path(__file__).resolve().parents[1]
ap=argparse.ArgumentParser(description="Build hourly ship_minutes and buoy weather tables.")
ap.add_argument("--raw",type=Path,default=ROOT/"data/raw",help="folder holding vessel/ships/ and env/")
ap.add_argument("--out",type=Path,default=ROOT/"data/processed",help="where the CSVs are written")
args=ap.parse_args()
RAW,OUT=args.raw,args.out
OUT.mkdir(parents=True,exist_ok=True)

DEPS=[f"{i:02d}" for i in range(1,19)]
sent={"WDIR":999,"WSPD":99,"GST":99,"WVHT":99,"DPD":99,"APD":99,"PRES":9999,"ATMP":999,"WTMP":999,"DEWP":999}

# 1. raw events, all 18 deployments in one file
ev=[]; cov=[]
for d in DEPS:
    e=pd.read_csv(RAW/f"vessel/ships/SanctSound_SB01_{d}_ships.csv"); e["deployment"]=d; ev.append(e)
    m=json.load(open(RAW/f"vessel/ships/SanctSound_SB01_{d}_ships-metadata.json"))
    cov.append((d,pd.Timestamp(m["START_TIME"],tz="UTC"),pd.Timestamp(m["END_TIME"],tz="UTC")))
ev=pd.concat(ev)[["deployment","ISOStartTime","ISOEndTime","Labels"]]
ev.to_csv(OUT/"ships_events_SB01_01-18.csv",index=False)

# 2. hourly table: ship_minutes + buoy weather, full range
s=pd.to_datetime(ev.ISOStartTime,utc=True); e=pd.to_datetime(ev.ISOEndTime,utc=True)
hours=pd.date_range(cov[0][1].floor("1h"),cov[-1][2].floor("1h"),freq="1h",inclusive="left")
mins=pd.Series(0.0,index=hours); dep=pd.Series(pd.NA,index=hours,dtype=object)
for d,a,b in cov: dep[(hours>=a.floor("1h"))&(hours<b.floor("1h"))]=d
for st,en in zip(s,e):
    for h in pd.date_range(st.floor("1h"),en.floor("1h"),freq="1h"):
        if h in mins.index:
            ov=(min(en,h+pd.Timedelta("1h"))-max(st,h)).total_seconds()/60
            if ov>0: mins[h]+=ov
mins[dep.isna()]=pd.NA
ships=pd.DataFrame({"deployment":dep,"ship_minutes":mins,"ship_present":(mins>0).astype("float").where(mins.notna())})

def buoy(stn,years,cols):
    fr=[]
    for y in years:
        b=pd.read_csv(RAW/f"env/{stn}h{y}.txt",sep=r"\s+",skiprows=[1]); b.columns=[c.lstrip("#") for c in b.columns]; fr.append(b)
    b=pd.concat(fr); b["t"]=pd.to_datetime(dict(year=b.YY,month=b.MM,day=b.DD,hour=b.hh,minute=b.mm),utc=True); b=b.set_index("t")
    for c,v in sent.items():
        if c in b: b[c]=b[c].where(b[c]<v)
    return b[cols].resample("1h").mean()

env=buoy(44013,(2018,2019,2020,2021),["WDIR","WSPD","GST","PRES","ATMP","WTMP","DEWP"])
wave=buoy(44098,(2018,2019,2020,2021),["WVHT","DPD","APD"]).add_suffix("_44098")

# ships-only hourly file
ships_out=ships.copy(); ships_out.index.name="hour_utc"
ships_out.to_csv(OUT/"ships_hourly_SB01_01-18.csv")

# weather-only hourly file (both buoys, trimmed to the ships/acoustic date range)
weather=env.join(wave).reindex(hours); weather.index.name="hour_utc"
weather.to_csv(OUT/"weather_hourly_SB01_01-18.csv")

print("events file:", len(ev), "rows")
print("ships hourly file:", len(ships_out), "rows")
print("weather hourly file:", len(weather), "rows,", weather.index.min(), "to", weather.index.max())
