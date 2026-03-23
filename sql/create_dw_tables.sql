USE AIS_DW;
GO

-- Create DimDate table
CREATE TABLE dbo.DimDate (
    DateSK          INT NOT NULL PRIMARY KEY,
    FullDate        DATE NOT NULL,
    DayOfMonth      INT NOT NULL,
    DayName         NVARCHAR(10) NOT NULL,
    WeekOfYear      INT NOT NULL,
    Month           INT NOT NULL,
    MonthName       NVARCHAR(10) NOT NULL,
    Quarter         INT NOT NULL,
    QuarterName     NVARCHAR(10) NOT NULL,
    Year            INT NOT NULL,
    IsWeekend       BIT NOT NULL,
    InsertDate      DATETIME DEFAULT GETDATE()
);
GO

-- Populate DimDate (2023 to 2026)
DECLARE @StartDate DATE = '2023-01-01';
DECLARE @EndDate   DATE = '2026-12-31';
DECLARE @Date      DATE = @StartDate;

WHILE @Date <= @EndDate
BEGIN
    INSERT INTO dbo.DimDate (
        DateSK, FullDate, DayOfMonth, DayName,
        WeekOfYear, Month, MonthName,
        Quarter, QuarterName, Year, IsWeekend
    )
    VALUES (
        CONVERT(INT, CONVERT(VARCHAR, @Date, 112)),
        @Date,
        DAY(@Date),
        DATENAME(WEEKDAY, @Date),
        DATEPART(WEEK, @Date),
        MONTH(@Date),
        DATENAME(MONTH, @Date),
        DATEPART(QUARTER, @Date),
        'Q' + CAST(DATEPART(QUARTER, @Date) AS VARCHAR),
        YEAR(@Date),
        CASE WHEN DATEPART(WEEKDAY, @Date) IN (1,7) THEN 1 ELSE 0 END
    );
    SET @Date = DATEADD(DAY, 1, @Date);
END
GO

CREATE TABLE dbo.DimVesselType (
    VesselTypeSK            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    AlternateVesselTypeID   INT NOT NULL,
    VesselTypeCode          NVARCHAR(20) NOT NULL,
    VesselTypeName          NVARCHAR(100) NOT NULL,  -- Hierarchy Level 2
    VesselTypeGroup         NVARCHAR(100) NOT NULL,  -- Hierarchy Level 1
    InsertDate              DATETIME DEFAULT GETDATE(),
    ModifiedDate            DATETIME DEFAULT GETDATE()
);
GO

CREATE TABLE dbo.DimDestination (
    DestinationSK           INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    AlternateDestinationID  INT NOT NULL,
    DestinationName         NVARCHAR(100) NOT NULL,
    PortName                NVARCHAR(100) NOT NULL,  -- Hierarchy Level 3
    Country                 NVARCHAR(100) NOT NULL,  -- Hierarchy Level 2
    Region                  NVARCHAR(100) NOT NULL,  -- Hierarchy Level 1
    InsertDate              DATETIME DEFAULT GETDATE(),
    ModifiedDate            DATETIME DEFAULT GETDATE()
);
GO


CREATE TABLE dbo.DimVessel (
    VesselSK            INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    AlternateMMSI       BIGINT NOT NULL,
    VesselName          NVARCHAR(100) NOT NULL,
    IMO                 NVARCHAR(20) NULL,
    Flag                NVARCHAR(100) NULL,
    CallSign            NVARCHAR(20) NULL,          -- SCD Type 1 (Changing)
    Draught             DECIMAL(5,2) NULL,           -- SCD Type 2 (Historical)
    VesselTypeSK        INT NOT NULL,
    StartDate           DATETIME NOT NULL,
    EndDate             DATETIME NULL,               -- NULL means current record
    InsertDate          DATETIME DEFAULT GETDATE(),
    ModifiedDate        DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (VesselTypeSK) REFERENCES dbo.DimVesselType(VesselTypeSK)
);
GO


CREATE TABLE dbo.FactVesselTracking (
    TrackingSK              INT IDENTITY(1,1) NOT NULL PRIMARY KEY,
    TrackingNaturalKey      BIGINT NOT NULL,          -- txn_id (natural key)
    VesselSK                INT NOT NULL,
    DateSK                  INT NOT NULL,
    DestinationSK           INT NOT NULL,
    VesselTypeSK            INT NOT NULL,
    Latitude                DECIMAL(9,6) NOT NULL,
    Longitude               DECIMAL(9,6) NOT NULL,
    SOG                     DECIMAL(5,2) NULL,        -- Speed Over Ground
    COG                     DECIMAL(5,2) NULL,        -- Course Over Ground
    Heading                 INT NULL,
    NavigationStatus        NVARCHAR(50) NULL,
    accm_txn_create_time    DATETIME NULL,
    accm_txn_complete_time  DATETIME NULL,
    txn_process_time_hours  AS (
        CASE 
            WHEN accm_txn_complete_time IS NOT NULL 
            AND accm_txn_create_time IS NOT NULL
            THEN DATEDIFF(HOUR, accm_txn_create_time, accm_txn_complete_time)
            ELSE NULL 
        END
    ),
    FOREIGN KEY (VesselSK)      REFERENCES dbo.DimVessel(VesselSK),
    FOREIGN KEY (DateSK)        REFERENCES dbo.DimDate(DateSK),
    FOREIGN KEY (DestinationSK) REFERENCES dbo.DimDestination(DestinationSK),
    FOREIGN KEY (VesselTypeSK)  REFERENCES dbo.DimVesselType(VesselTypeSK)
);
GO

--used to check all tables are created
/*
USE AIS_DW;
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
*/