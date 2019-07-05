
import os
import sys
import json
import logging
import numpy as np
from cacher import cacher
from typing import List, Tuple, Dict, Union
from influxdb import InfluxDBClient

logger = logging.getLogger(__name__)

class DataGetter:
    setting_file = "/db_settings.json"

    def __init__(self, query):
        """Load the settings file and connect to the DB"""
        self.query = query
        self.measurement = query["measurement"]

        # Get the current folder
        current_script_dir = "/".join(__file__.split("/")[:-2])
        
        path = current_script_dir + self.setting_file
        logger.info("Loading the DB settings from [%s]"%path)

        # Load the settings
        with open(path, "r") as f:
            self.settings = json.load(f)

        # Create the client passing the settings as kwargs
        self.client = InfluxDBClient(**self.settings)

    def __del__(self):
        """On exit / delation close the client connetion"""
        self.client.close()

    @cacher
    def exec_query(self, query : str):
        # Construct the query to workaround the tags distinct constraint
        logger.info("Executing query [%s]"%query)
        return list(self.client.query(query).get_points())

    def construct_selection(self, args: Union[Dict[str,str], Dict[str,List[str]]]):
        """Create a WHERE selection in normal disjoint form (AND of ORS) and prepare for the final time selection"""

        logger.info("Constructing a selection where query part with [%s]"%args)
        if not args:
            return """ WHERE """
        # Normalize to lists all the values in the dictionary
        converted = {k : [v] for k, v in args.items() if type(v) != list }
        query = {**args, **converted}
        # constrct all the equivalences
        query = [["{} = '{}'".format(k, x) for x in v] for k, v in query.items()]
        # Construct the ORs
        query = ["(%s)"%(" OR ".join(v)) for v in query]
        # Construct the AND
        query = " AND ".join(query)
        # Add the final And for the time selection
        query += " AND "
        return """ WHERE %s"""%query

    def get_distinct_values(self, name : str, args : Dict[str,str] = {}) -> List:
        """
        Select all the distinct values.
        It use a query in the form of "SELECT distinct("{name}") FROM (SELECT * FROM "{measurement}")
        because the "name" could be both a tag and a field.
        While a query SELECT distinct({name})  FROM {measurement} works on fields, on tags it return empty.
        So this workaround works on both tags and fields."""
        
        where = self.construct_selection(args)
        
        # Construct the query to workaround the tags distinct constraint
        time = self.query["time"]
        query = """SELECT distinct("{name}") FROM (SELECT * FROM {self.measurement} {where} {time})""".format(**locals())
        r = self.exec_query(query)
        return [x["distinct"] for x in list(r)]

    @cacher
    def get_measurements(self) -> List[str]:
        """Get all the measurements sul DB"""
        result =  [x["name"] for x in self.exec_query("""SHOW MEASUREMENTS""")]
        logger.info("Found the measurements %s"%result)
        return result

    @cacher
    def get_available(self, name : str):
        """For a field it returns all the distinct values once the filter is applied
         to the previous fields in order of insertion in the dictionary"""
        # If it's measuremnets it's a special case because it's a different kind of query
        if name == "measurement":
            return self.get_measurements()
        # Selectors must be valid and they have an order
        elif name in self.query["selectors"].keys():
            index = list(self.query["selectors"].keys()).index(name)
            selectors_before_name = dict(list(self.query["selectors"].items())[:index])
            return self.get_distinct_values(name, selectors_before_name)
        # Optionals do not have an order and only need the selectors on the WHERE
        elif name in self.query["optionals"].keys():
            return self.get_distinct_values(name, self.query["selectors"])
        else:
            logger.info("%s not found"%name)
            
    @cacher
    def check_existance(self, name : str, value : str):
        available = self.get_available(name)
        if value not in available:
            logger.error("The {name} [{value}] do not exist. The available one are [{available}]".format(**locals()))
            self.__del__()
            sys.exit(1)

    @cacher
    def check_existance_optionals(self, name : str, value : str):
        available = self.get_available(name)
        if value not in available:
            logger.error("The {name} [{metric}] do not exist. The available one are [{metrics}]".format(**locals()))
            return False
        return True

    def validate_query(self):
        self.check_existance("measurement", self.query["measurement"])

        for name, value in self.query["selectors"].items():
            self.check_existance(name, value)

        for name, values in self.query["optionals"].items():
            for value in values:
                if not self.check_existance_optionals(name, value):
                    return False
        return True

    def set_query(self, query):
        self.query = query

    def get_data(self):
        """Read the data from the DB and return it as (x, y) where x is the time and y is the percentual disk usage"""
        if not self.validate_query():
            return None

        optionals =[v for v in self.query["optionals"].keys()]
        fields = ", ".join(self.query["fields"] + optionals)
        where = self.construct_selection({**self.query["selectors"], **self.query["optionals"]})
        time = self.query["time"]
        # Do the query and filter only the useful fields
        measurement = self.measurement
        query = """SELECT {fields} FROM (SELECT * FROM "{measurement}" {where} {time})""".format(**locals())
        results = self.exec_query(query)
        return results
