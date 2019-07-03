
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

    def __init__(self):
        """Load the settings file and connect to the DB"""
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
        query = """SHOW MEASUREMENTS"""
        logger.debug("Executing query [%s]"%query)
        r = self.exec_query(query)
        return [x["name"] for x in r]


    def get_available(self, name : str):
        if name == "measurements":
            return self.get_measurements()


    def check_existance(self, name : str, value : str):
        available = self.get_available()
        if value not in available:
            logger.error("The {name} [{value}] do not exist. The available one are [{available}]".format(**locals()))
            self.__del__()
            sys.exit(1)

    def get_data(self, measurement : str, host : str, service : str, metric : str) -> Tuple[np.ndarray, np.ndarray]:
        """Read the data from the DB and return it as (x, y) where x is the time and y is the percentual disk usage"""
        
        measurements = self.get_measurements()
        if measurement not in measurements:
            logger.error("The measurment [{measurement}] do not exist. The available one are [{measurements}]".format(**locals()))
            sys.exit(1)

        hosts = self.get_hosts(measurement)
        if host not in hosts:
            logger.error("The host [{host}] do not exist. The available one are [{hosts}]".format(**locals()))
            sys.exit(1)

        services = self.get_services(measurement, host)
        if service not in services:
            logger.error("The service [{service}] do not exist. The available one are [{services}]".format(**locals()))
            sys.exit(1)

        metrics = self.get_metrics(measurement, host, service)
        if metric not in metrics:
            logger.error("The metric [{metric}] do not exist. The available one are [{metrics}]".format(**locals()))
            return None


        query = """SELECT  FROM "{measurement}" {where})""".format(**locals())
        # Execute the query and return the unique results
        r = self.exec_query(query)


        return (0,0)
