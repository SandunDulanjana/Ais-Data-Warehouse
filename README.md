# AIS Ship Tracking — Data Warehouse & Business Intelligence

> **IT3021 · Data Warehousing and Business Intelligence**  
> Year 3 Semester 1/2 · 2026 · Assignment 1  
> Sri Lanka Institute of Information Technology

---

## Table of Contents

- [Project Overview](#project-overview)
- [Dataset](#dataset)
- [Repository Structure](#repository-structure)
- [Architecture](#architecture)
- [Data Sources](#data-sources)
- [Data Warehouse Design](#data-warehouse-design)
- [ETL Pipeline](#etl-pipeline)
- [Accumulating Fact Table](#accumulating-fact-table)
- [Getting Started](#getting-started)
- [Tools & Technologies](#tools--technologies)
- [Assignment Tasks](#assignment-tasks)

---

## Project Overview

This project implements a full **Data Warehouse and Business Intelligence solution** for AIS (Automatic Identification System) ship tracking data. The solution enables maritime analysts to answer business questions about vessel movement, speed patterns, destination traffic, and ETA performance — across time, vessel type, and geography.

The pipeline covers:
- Multi-source data preparation (SQL Server database + CSV flat file)
- Staging database design
- Star schema dimensional model
- SSIS ETL packages (Source → Staging → Data Warehouse)
- Accumulating snapshot fact table with a separate update package
- SSAS cube and SSRS reports (Assignment 2)

---

## Dataset

| Property | Value |
|---|---|
| Source | [Kaggle — AIS Ship Tracking: Vessel Dynamics & ETA Data](https://www.kaggle.com/datasets/satyamrajput7913/ais-ship-tracking-vessel-dynamics-and-eta-data) |
| Original rows | 1,098,966 |
| Original columns | 28 |
| Time span | > 1 year of AIS position reports |
| Grain | One AIS ping per vessel per timestamp |

### Column map (original → renamed)

| Original | Renamed | Table |
|---|---|---|
| `mmsi` | `mmsi` | Vessel + VesselTracking |
| `vesselname` | `vessel_name` | Vessel |
| `imo` | `imo` | Vessel |
| `callsign` | `call_sign` | Vessel |
| `vesseltype` | `vessel_type` | Vessel |
| `length` | `length` | Vessel |
| `width` | `width` | Vessel |
| `draft` | `draft` | Vessel |
| `cargo` | `cargo` | Vessel |
| `transceiverclass` | `transceiver_class` | Vessel |
| `basedatetime` | `base_date_time` | VesselTracking |
| `lat` | `latitude` | VesselTracking |
| `lon` | `longitude` | VesselTracking |
| `sog` | `sog` | VesselTracking |
| `cog` | `cog` | VesselTracking |
| `heading` | `heading` | VesselTracking |
| `status` | `nav_status` | VesselTracking |
| `dest_cluster` | `dest_cluster` | VesselTracking |
| `dest_lat` | `dest_latitude` | VesselTracking |
| `dest_lon` | `dest_longitude` | VesselTracking |
| `dist_km` | `dist_km` | VesselTracking |
| `sog_kmh` | `sog_kmh` | VesselTracking |
| `eta_min` | `eta_minutes` | VesselTracking |
| `vesseltype_enc` | `vessel_type_enc` | VesselTracking |
| `status_enc` | `nav_status_enc` | VesselTracking |
| `cargo_enc` | `cargo_enc` | VesselTracking |
| `eta_hours` | `eta_hours` | VesselTracking |
| `speed_category` | `speed_category` | VesselTracking |

---

## Repository Structure

```
ais-data-warehouse/
│
├── README.md
│
├── data-preparation/
│   └── split_ais_dataset.py          # Splits raw CSV → 3 output files (60/40)
│
├── source-db/
│   └── create_source_db.sql          # Creates AIS_SourceDB with Vessel + VesselTracking tables
│
├── data-warehouse/
│   └── create_dw_schema.sql          # Creates AIS_DW star schema tables
│
├── etl/
│   ├── AIS_Load_Staging.dtsx         # SSIS Package 1: Source → Staging
│   ├── AIS_Load_DW.dtsx              # SSIS Package 2: Staging → Data Warehouse
│   ├── AIS_Update_AccumFact.dtsx     # SSIS Package 3: Accumulating fact update
│   └── stored-procedures/
│       ├── UpdateDimVesselType.sql
│       ├── UpdateDimDestination.sql
│       └── UpdateDimVessel.sql
│
├── source-files/
│   ├── vessel_table.csv              # Unique vessels → imported into SQL Server
│   ├── tracking_db_60pct.csv         # 60% of pings → SQL Server VesselTracking table
│   └── tracking_source_40pct.csv     # 40% of pings → source flat file for SSIS
│
├── accumulating-fact/
│   └── completion_updates.csv        # txn_id + accm_txn_complete_time for Task 6
│
├── docs/
│   ├── architecture-diagram.png      # DW/BI solution architecture
│   ├── er-diagram.png                # Source data ER diagram
│   ├── star-schema.png               # Data warehouse dimensional model
│   └── AIS_DW_Business_Questions.pdf # Business questions + Viva Q&A reference
│
└── reports/
    └── Assignment1_Report.pdf        # Final submission report
```

---

## Architecture

```
┌─────────────────┐        ┌──────────────────┐        ┌──────────────────┐
│   Source DB      │        │   Staging DB      │        │  Data Warehouse  │
│  AIS_SourceDB    │──ETL──▶│  AIS_Staging      │──ETL──▶│  AIS_DW          │
│  · Vessel        │  Pkg1  │  · StgVessel      │  Pkg2  │  · DimVessel     │
│  · VesselTracking│        │  · StgTracking_DB │        │  · DimVesselType │
├─────────────────┤        │  · StgTracking_CSV│        │  · DimDestination│
│   Source CSV     │        │  · StgDestination │        │  · DimDate       │
│  tracking_       │──ETL──▶│                   │        │  · FactVessel    │
│  source_40pct.csv│  Pkg1  └──────────────────┘        │    Tracking      │
└─────────────────┘                                      └────────┬─────────┘
                                                                  │ Process
┌─────────────────┐        ┌──────────────────┐                  ▼
│  Completion CSV  │        │  Accum. Fact      │         ┌──────────────┐
│  completion_     │──ETL──▶│  Update           │         │  SSAS Cube   │
│  updates.csv     │  Pkg3  │  (Task 6)         │         └──────┬───────┘
└─────────────────┘        └──────────────────┘                  │
                                                                  ▼
                                                         ┌──────────────┐
                                                         │ SSRS Reports │
                                                         └──────────────┘
```

---

## Data Sources

The original dataset is split **row-wise** into two source types to demonstrate multi-source ETL:

| Source | Type | File / Table | Rows | Used for |
|---|---|---|---|---|
| Source 1 | SQL Server DB | `AIS_SourceDB.dbo.Vessel` | ~unique MMSIs | Vessel dimension |
| Source 1 | SQL Server DB | `AIS_SourceDB.dbo.VesselTracking` | ~659,000 (60%) | Tracking facts |
| Source 2 | CSV flat file | `tracking_source_40pct.csv` | ~440,000 (40%) | Tracking facts |

Run `data-preparation/split_ais_dataset.py` to generate all source files from the raw Kaggle CSV.

---

## Data Warehouse Design

**Schema type:** Star Schema

### Dimensions

| Table | Type | Business key | Hierarchy |
|---|---|---|---|
| `DimVessel` | SCD Type 2 | `mmsi` | — |
| `DimVesselType` | SCD Type 1 | `vessel_type_code` | VesselTypeGroup → VesselTypeName |
| `DimDestination` | SCD Type 1 | `dest_cluster` | Region → Country → PortName |
| `DimDate` | Static | `full_date` | Year → Quarter → Month → Day |

### Fact table

| Table | Grain | Measures |
|---|---|---|
| `FactVesselTracking` | One AIS ping per vessel | `sog`, `cog`, `dist_km`, `sog_kmh`, `eta_minutes`, `eta_hours`, `txn_process_time_hours` (computed) |

### Slowly Changing Dimension — DimVessel (Type 2)

`draft` and `vessel_name` are tracked historically. When either changes in the source, a new row is inserted with a new `StartDate` and the old row's `EndDate` is set. The current record always has `EndDate IS NULL`.

---

## ETL Pipeline

### Package 1 — `AIS_Load_Staging.dtsx`

Extracts from both sources into the staging database. All staging tables are truncated before each run via `OnPreExecute` event handlers.

| Step | Source | Destination |
|---|---|---|
| 1 | `AIS_SourceDB.dbo.Vessel` | `AIS_Staging.dbo.StgVessel` |
| 2 | `AIS_SourceDB.dbo.VesselTracking` | `AIS_Staging.dbo.StgTracking_DB` |
| 3 | `tracking_source_40pct.csv` (Flat File) | `AIS_Staging.dbo.StgTracking_CSV` |

### Package 2 — `AIS_Load_DW.dtsx`

Transforms staging data and loads the dimensional model. **Load order must be respected** due to foreign key constraints.

| Step | Task | SSIS components used |
|---|---|---|
| 1 | Load `DimVesselType` | OLE DB Source → OLE DB Command (stored proc) |
| 2 | Load `DimDestination` | OLE DB Source → OLE DB Command (stored proc) |
| 3 | Load `DimVessel` | OLE DB Source → **Slowly Changing Dimension** (SCD2) |
| 4 | Load `FactVesselTracking` | OLE DB Source × 2 → Union All → Lookup (×3) → Derived Column → OLE DB Destination |

Surrogate key lookups are performed for `VesselSK`, `VesselTypeSK`, `DestinationSK`, and `DateSK` before inserting into the fact table.

---

## Accumulating Fact Table

Task 6 extends `FactVesselTracking` with three columns:

| Column | Type | Description |
|---|---|---|
| `accm_txn_create_time` | `DATETIME` | Set to `GETDATE()` when the fact row is first loaded |
| `accm_txn_complete_time` | `DATETIME` | Updated later by Package 3 |
| `txn_process_time_hours` | Computed | `DATEDIFF(HOUR, accm_txn_create_time, accm_txn_complete_time)` — auto-calculated |

### Package 3 — `AIS_Update_AccumFact.dtsx`

Reads `accumulating-fact/completion_updates.csv` and updates the corresponding fact rows:

```
completion_updates.csv
───────────────────────────────
txn_id  │  accm_txn_complete_time
────────┼──────────────────────────
1001    │  2026-03-10 14:30:00
1002    │  2026-03-11 09:15:00
...
```

---

## Getting Started

### Prerequisites

- SQL Server 2016 or higher
- SQL Server Management Studio (SSMS)
- SQL Server Data Tools (SSDT) with SSIS
- Python 3.8+ with `pandas` installed
- Microsoft Office (Excel)

### Step 1 — Prepare source files

```bash
# Place the raw Kaggle CSV in the same folder as the script
# Change the filename inside the script if needed
python data-preparation/split_ais_dataset.py
```

This creates `source-files/` with three CSVs.

### Step 2 — Create source database

```sql
-- In SSMS: create database AIS_SourceDB, then run:
source-db/create_source_db.sql
```

Import `vessel_table.csv` into `dbo.Vessel` first, then `tracking_db_60pct.csv` into `dbo.VesselTracking` using the **Import Flat File** wizard.

### Step 3 — Create staging and DW databases

```sql
-- In SSMS, create two empty databases:
--   AIS_Staging
--   AIS_DW
-- Then run:
data-warehouse/create_dw_schema.sql
```

### Step 4 — Run SSIS packages in order

```
1. AIS_Load_Staging.dtsx      (Source → Staging)
2. AIS_Load_DW.dtsx           (Staging → Data Warehouse)
3. AIS_Update_AccumFact.dtsx  (Update accumulating fact columns)
```

### Step 5 — Verify data loaded

```sql
USE AIS_DW;
SELECT 'DimVessel'        AS tbl, COUNT(*) AS rows FROM dbo.DimVessel
UNION ALL
SELECT 'DimVesselType',          COUNT(*)          FROM dbo.DimVesselType
UNION ALL
SELECT 'DimDestination',         COUNT(*)          FROM dbo.DimDestination
UNION ALL
SELECT 'DimDate',                COUNT(*)          FROM dbo.DimDate
UNION ALL
SELECT 'FactVesselTracking',     COUNT(*)          FROM dbo.FactVesselTracking;
```

---

## Tools & Technologies

| Tool | Purpose |
|---|---|
| SQL Server 2016+ | Source DB, Staging DB, Data Warehouse |
| SSMS | Database management and query execution |
| SSIS (SQL Server Data Tools) | ETL package development |
| Python + pandas | Dataset preparation and splitting |
| ReportLab | PDF documentation generation |
| SSAS | OLAP cube (Assignment 2) |
| SSRS | BI reports (Assignment 2) |

---

## Assignment Tasks

| Task | Marks | Status |
|---|---|---|
| Task 1 — Dataset selection & ERD | 2.5 | ✅ |
| Task 2 — Data source preparation | 2.5 | ✅ |
| Task 3 — Solution architecture | 5 | ✅ |
| Task 4 — DW design & SQL implementation | 25 | ✅ |
| Task 5 — ETL development (SSIS) | 25 | ✅ |
| Task 6 — Accumulating fact table | 20 | ✅ |
| Documentation & report | 5 | ✅ |
| Viva | 15 | — |
| **Total** | **100** | |

---

> **Note:** The raw dataset CSV is not committed to this repository due to its size (~1 GB).  
> Download it from [Kaggle](https://www.kaggle.com/datasets/satyamrajput7913/ais-ship-tracking-vessel-dynamics-and-eta-data) and place it in the project root before running the preparation script.