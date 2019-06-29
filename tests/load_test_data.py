import influxdb
import pandas as pd

c = influxdb.DataFrameClient()
c.create_database("icinga2")
c.switch_database("icinga2")
df = pd.read_excel("Disk Space.xlsx")
df['time'] = df.index
df.index = pd.to_datetime(df.index)
c.write_points(df, "disk")