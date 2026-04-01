import pandas as pd

df = pd.read_csv(r'C:\Users\User\Documents\GitHub\Ais-Data-Warehouse\dataset\primary-dataset\processed_AIS_dataset.csv')
print(df.columns)  # <── change to your filename

df = pd.read_csv(r'C:\Users\User\Documents\GitHub\Ais-Data-Warehouse\dataset\asset-dataset\vessel_table.csv')
print(df.columns)  # <── change to your filename

df = pd.read_csv(r'C:\Users\User\Documents\GitHub\Ais-Data-Warehouse\dataset\asset-dataset\tracking_db_60pct.csv')
print(df.columns)  # <── change to your filename


df = pd.read_csv(r'C:\Users\User\Documents\GitHub\Ais-Data-Warehouse\sources\tracking_source_40pct.csv')
print(df.columns)  # <── change to your filename