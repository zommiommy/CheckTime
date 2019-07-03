
import os
import sys
import json
import logging
import numpy as np
from typing import List, Tuple, Dict
from influxdb import InfluxDBClient

logger = logging.getLogger(__name__)

class DataGetter:
    setting_file = "/db_settings.json"

    def __init__(self, query):
        """Load the settings file and connect to the DB"""
        self.query = query

        # Get the current folder
        current_script_dir = "/".join(__file__.split("/")[:-1])
        
        path = current_script_dir + self.setting_file
        logger.debug("Loading the DB settings from [%s]"%path)

        # Load the settings
        with open(path, "r") as f:
            self.settings = json.load(f)

        # Create the client passing the settings as kwargs
        self.client = InfluxDBClient(**self.settings)

    def __del__(self):
        """On exit / delation close the client connetion"""
        self.client.close()

    def exec_query(self, query : str):
        # Construct the query to workaround the tags distinct constraint
        logger.debug("Executing query [%s]"%query)
        return self.client.query(query).get_points()


    def get_distinct_values(self, name : str, args : Dict[str,str] = {}) -> List:
        """
        Select all the distinct values.
        It use a query in the form of "SELECT distinct("{name}") FROM (SELECT * FROM "{measurement}")
        because the "name" could be both a tag and a field.
        While a query SELECT distinct({name})  FROM {measurement} works on fields, on tags it return empty.
        So this workaround works on both tags and fields."""
        
        where = ""
        if args != {}:
            where = """WHERE """
            where += " AND ".join("{} = '{}'".format(name,value) for name, value in args.items())

        # Construct the query to workaround the tags distinct constraint
        query = """SELECT distinct("{name}") FROM (SELECT * FROM "{measurement}" {where})""".format(**locals())
        r = self.exec_query(query)
        return [x["distinct"] for x in list(r)]

    def get_measurements(self) -> List[str]:
        """Get all the measurements sul DB"""
        return [x["name"] for x in self.exec_query("""SHOW MEASUREMENTS""")]

    def get_available(self, name : str):
        """For a field it returns all the distinct values once the filter is applied
         to the previous fields in order of insertion in the dictionary"""
        if name == "measurements":
            return self.get_measurements()
        index = list(self.query["selectors"].keys()).index(name)
        selectors_before_name = dict(list(self.query["selectors"].items())[:index])
        return self.get_distinct_values(name, selectors_before_name)

    def check_existance(self, name : str, value : str):
        available = self.get_available(name)
        if value not in available:
            logger.error("The {name} [{value}] do not exist. The available one are [{available}]".format(**locals()))
            self.__del__()
            sys.exit(1)

    def get_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Read the data from the DB and return it as (x, y) where x is the time and y is the percentual disk usage"""
        
        self.check_existance("measurements", self.query["measurements"])

        for name, value in self.query["selectors"].items():
            self.check_existance(name, value)


        metrics = self.get_metrics()
        name = next(self.query["optional"].keys())
        if metric not in metrics:
            logger.error("The {name} [{metric}] do not exist. The available one are [{metrics}]".format(**locals()))
            return None

        fields = ", ".join(self.query["fields"])
        query = """SELECT {fields} FROM "{measurement}" {where})""".format(**locals())
        return self.exec_query(query)
