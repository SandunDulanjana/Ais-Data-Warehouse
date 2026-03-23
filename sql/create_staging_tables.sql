USE AIS_Staging;
GO

CREATE TABLE dbo.StgVesselTracking (
    MMSI                BIGINT NULL,
    Timestamp           DATETIME NULL,
    Latitude            DECIMAL(9,6) NULL,
    Longitude           DECIMAL(9,6) NULL,
    SOG                 DECIMAL(5,2) NULL,
    COG                 DECIMAL(5,2) NULL,
    Heading             INT NULL,
    NavigationStatus    NVARCHAR(50) NULL,
    Draught             DECIMAL(5,2) NULL,
    Destination         NVARCHAR(100) NULL,
    ETA                 NVARCHAR(50) NULL
);
GO



CREATE TABLE dbo.StgVesselInfo (
    MMSI                BIGINT NULL,
    VesselName          NVARCHAR(100) NULL,
    IMO                 NVARCHAR(20) NULL,
    CallSign            NVARCHAR(20) NULL,
    Flag                NVARCHAR(100) NULL,
    ShipType            NVARCHAR(100) NULL,
    ShipTypeGroup       NVARCHAR(100) NULL
);
GO


--used to check all tables are created
/*
USE AIS_Staging;
SELECT TABLE_NAME 
FROM INFORMATION_SCHEMA.TABLES 
WHERE TABLE_TYPE = 'BASE TABLE'
ORDER BY TABLE_NAME;
*/