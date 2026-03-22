import pandas as pd
import os

# ─────────────────────────────────────────────────────────────────
# STEP 1 — Load raw dataset
# ─────────────────────────────────────────────────────────────────
df = pd.read_csv(r'C:\DWBI_Project\processed_AIS_dataset.csv')         # <── change to your filename

# Normalise all column names
df.columns = df.columns.str.strip().str.lower()

print("=== Raw columns ===")
print(df.columns.tolist())
print(f"Total rows   : {len(df)}")
print(f"Total columns: {len(df.columns)}")

# ─────────────────────────────────────────────────────────────────
# STEP 2 — Rename to clean snake_case
#
# Original 28 columns → clean names
# ─────────────────────────────────────────────────────────────────
rename_map = {
    'mmsi'            : 'mmsi',
    'basedatetime'    : 'base_date_time',       # timestamp of the AIS ping
    'lat'             : 'latitude',
    'lon'             : 'longitude',
    'sog'             : 'sog',                  # speed over ground (knots)
    'cog'             : 'cog',                  # course over ground (degrees)
    'heading'         : 'heading',
    'vesselname'      : 'vessel_name',
    'imo'             : 'imo',
    'callsign'        : 'call_sign',
    'vesseltype'      : 'vessel_type',          # raw type code
    'status'          : 'nav_status',           # navigation status (text)
    'length'          : 'length',
    'width'           : 'width',
    'draft'           : 'draft',
    'cargo'           : 'cargo',                # cargo type code
    'transceiverclass': 'transceiver_class',    # Class A or B AIS
    'dest_cluster'    : 'dest_cluster',         # clustered destination label
    'dest_lat'        : 'dest_latitude',        # destination latitude
    'dest_lon'        : 'dest_longitude',       # destination longitude
    'dist_km'         : 'dist_km',              # distance to destination (km)
    'sog_kmh'         : 'sog_kmh',              # speed in km/h (derived)
    'eta_min'         : 'eta_minutes',          # ETA in minutes (derived)
    'vesseltype_enc'  : 'vessel_type_enc',      # encoded vessel type (ML)
    'status_enc'      : 'nav_status_enc',       # encoded nav status (ML)
    'cargo_enc'       : 'cargo_enc',            # encoded cargo (ML)
    'eta_hours'       : 'eta_hours',            # ETA in hours (derived)
    'speed_category'  : 'speed_category',       # e.g. slow/medium/fast
}

df = df.rename(columns=rename_map)

print("\n=== Columns after rename ===")
print(df.columns.tolist())

# ─────────────────────────────────────────────────────────────────
# STEP 3 — Separate into logical tables
#
# VESSEL TABLE  — static info, one row per unique MMSI
#   Columns: mmsi, vessel_name, imo, call_sign, vessel_type,
#            length, width, draft, cargo, transceiver_class
#
# TRACKING TABLE — dynamic ping data, one row per AIS message
#   Columns: mmsi, base_date_time, latitude, longitude,
#            sog, cog, heading, nav_status,
#            dest_cluster, dest_latitude, dest_longitude,
#            dist_km, sog_kmh, eta_minutes, eta_hours,
#            vessel_type_enc, nav_status_enc, cargo_enc,
#            speed_category
#
# Why this split?
#   Vessel info is fixed per ship → dimension table in DW (SCD2)
#   Tracking info changes every ping → fact table in DW
# ─────────────────────────────────────────────────────────────────

VESSEL_COLS = [
    'mmsi',
    'vessel_name',
    'imo',
    'call_sign',
    'vessel_type',          # raw numeric code
    'length',
    'width',
    'draft',                # SCD2 candidate (changes when ship loads/unloads)
    'cargo',
    'transceiver_class',
]

TRACKING_COLS = [
    'mmsi',                 # FK back to Vessel
    'base_date_time',
    'latitude',
    'longitude',
    'sog',
    'cog',
    'heading',
    'nav_status',
    'dest_cluster',
    'dest_latitude',
    'dest_longitude',
    'dist_km',
    'sog_kmh',
    'eta_minutes',
    'eta_hours',
    'vessel_type_enc',
    'nav_status_enc',
    'cargo_enc',
    'speed_category',
]

# Guard: keep only cols that actually exist after rename
VESSEL_COLS   = [c for c in VESSEL_COLS   if c in df.columns]
TRACKING_COLS = [c for c in TRACKING_COLS if c in df.columns]

print(f"\n=== Vessel columns   ({len(VESSEL_COLS)}) ===")
print(VESSEL_COLS)
print(f"\n=== Tracking columns ({len(TRACKING_COLS)}) ===")
print(TRACKING_COLS)

# ─────────────────────────────────────────────────────────────────
# STEP 4 — Build Vessel dimension (deduplicated, one row per MMSI)
# ─────────────────────────────────────────────────────────────────
vessel_df = (
    df[VESSEL_COLS]
    .drop_duplicates(subset=['mmsi'])
    .sort_values('mmsi')
    .reset_index(drop=True)
)
print(f"\nUnique vessels (Vessel table rows): {len(vessel_df)}")

# ─────────────────────────────────────────────────────────────────
# STEP 5 — Build Tracking table and split 60 / 40
# ─────────────────────────────────────────────────────────────────
tracking_df = df[TRACKING_COLS].reset_index(drop=True)

split_at  = int(len(tracking_df) * 0.60)
db_rows   = tracking_df.iloc[:split_at].reset_index(drop=True)   # → SQL Server
csv_rows  = tracking_df.iloc[split_at:].reset_index(drop=True)   # → Flat file

print(f"Tracking rows → SQL Server DB (60%): {len(db_rows)}")
print(f"Tracking rows → CSV flat file (40%): {len(csv_rows)}")

# ─────────────────────────────────────────────────────────────────
# STEP 6 — Write the three output files
# ─────────────────────────────────────────────────────────────────
os.makedirs('asset', exist_ok=True)
os.makedirs('source-file', exist_ok=True)


# Vessel table — imported into SQL Server
vessel_df.to_csv('asset/vessel_table.csv', index=False)

# Tracking 60% — imported into SQL Server VesselTracking table
db_rows.to_csv('asset/tracking_db_60pct.csv', index=False)

# Tracking 40% — kept as SOURCE flat file (SSIS reads this directly)
csv_rows.to_csv('source-file/tracking_source_40pct.csv', index=False)

print("\n=== Output files written to ./ais_source_files/ ===")
print(f"  vessel_table.csv           {len(vessel_df):>8,} rows   Vessel table in SQL Server")
print(f"  tracking_db_60pct.csv      {len(db_rows):>8,} rows   VesselTracking table in SQL Server")
print(f"  tracking_source_40pct.csv  {len(csv_rows):>8,} rows   Source flat file (CSV)")
print("\nAll done!")