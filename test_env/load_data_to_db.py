import influxdb
import pandas as pd

c = influxdb.DataFrameClient()

c.create_database("windows")
windows = pd.read_excel("DiskSpace.xlsx")
c.write_points(windows,"windows")

c.create_database("linux")
linux = pd.read_excel("DiskSpace.xlsx", sheet_name=1)
c.write_points(linux,"linux")
