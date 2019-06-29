
import os
import sys
import json
import logging
import numpy as np
from typing import List, Tuple
from influxdb import InfluxDBClient

logger = logging.getLogger(__name__)

class DataGetter:
     hirerarchy = []
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

    def get_distinct_values(self, value : str, measurement : str, host : str = None, service : str = None, name : str = None) -> List:
        """
        Select all the distinct values.
        It use a query in the form of "SELECT distinct("{name}") FROM (SELECT * FROM "{measurement}")
        because the "name" could be both a tag and a field.
        While a query SELECT distinct({name}) FROM {measurement} works on fields, on tags it return empty.
        So this workaround works on both tags and fields."""
        
        where = ""
        if host:
            where = """WHERE hostname = '{host}' """
            if service:
                where += """ AND service = '{service}' """
                if name:
                    where += """ AND name = '{name}' """

        where = where.format(**locals())

        # Construct the query to workaround the tags distinct constraint
        query = """SELECT distinct("{value}") FROM (SELECT * FROM "{measurement}" {where})""".format(**locals())
        logger.debug("Executing query [%s]"%query)

        # Execute the query and return the unique results
        r = self.client.query(query)
        return [x["distinct"] for x in list(r.get_points())]

    def get_measurements(self) -> List[str]:
        """Get all the measurements sul DB"""
        query = """SHOW MEASUREMENTS"""
        logger.debug("Executing query [%s]"%query)
        query = self.client.query(query).get_points()
        return [x["name"] for x in query]

    def get_hosts(self, measurement : str) -> List[str]:
        """Get all the measurements sul DB"""
        return self.get_distinct_values("hostname", measurement)

    def get_services(self, measurement : str, host : str) -> List[str]:
        """Get all the measurements sul DB"""
        return self.get_distinct_values("service", measurement, host)

    def get_metrics(self, measurement : str, host : str, service : str) -> List[str]:
        """Return the metrics for this host and service (an host might have mutiple disks)"""
        return self.get_distinct_values("matric", measurement, host, service)

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
        logger.debug("Executing query [%s]"%query)

        # Execute the query and return the unique results
        r = self.client.query(query)


        return (0,0)



class WindowGetter(DataGetter):
    hirerarchy = ["host", "service", "matric", ("value", "max")]

class LinuxGetter(DataGetter):
    hirerarchy = ["host", "device",  "path", ("free", "total")]