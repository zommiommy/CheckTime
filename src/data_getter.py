
import os
import sys
import json
import logging
import numpy as np
from cacher import cacher
from typing import List, Tuple, Dict
from influxdb import InfluxDBClient

logger = logging.getLogger(__name__)

def transpose(lista):
    """Transpose a list of dictionaries to a dictionary of lists. 
       It assumes all the dictionaries have the sames keys."""
    _dict = {}
    for x in lista:
        for k, v in x.items():
            _dict.setdefault(k,[])
            _dict[k] += [v]
    return _dict

class DataGetter:
    setting_file = "/db_settings.json"

    def __init__(self, query):
        """Load the settings file and connect to the DB"""
        self.query = query

        # Get the current folder
        current_script_dir = "/".join(__file__.split("/")[:-2])
        
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

    @cacher
    def exec_query(self, query : str):
        # Construct the query to workaround the tags distinct constraint
        logger.debug("Executing query [%s]"%query)
        return self.client.query(query).get_points()

    def construct_selection(self, args: Union[Dict[str,str], Dict[str,List[str]]]):
        """Create a WHERE selection in normal disjoint form (AND of ORS) and prepare for the final time selection"""
        if not args:
            return """ WHERE """
        # Normalize to lists all the values in the dictionary
        converted = {k : list(v) for k, v in args.items() if type(v) != list }
        query = {**query, **converted}
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
        
        where = ""
        if args != {}:
            where = self.construct_selection(args)

        # Construct the query to workaround the tags distinct constraint
        query = """SELECT distinct("{name}") FROM (SELECT * FROM "{measurement}" {where})""".format(**locals())
        r = self.exec_query(query)
        return [x["distinct"] for x in list(r)]

    @cacher
    def get_measurements(self) -> List[str]:
        """Get all the measurements sul DB"""
        return [x["name"] for x in self.exec_query("""SHOW MEASUREMENTS""")]

    @cacher
    def get_available(self, name : str):
        """For a field it returns all the distinct values once the filter is applied
         to the previous fields in order of insertion in the dictionary"""
        # If it's measuremnets it's a special case because it's a different kind of query
        if name == "measurements":
            return self.get_measurements()
        # Selectors must be valid and they have an order
        elif name in self.query["selectors"].keys():
            index = list(self.query["selectors"].keys()).index(name)
            selectors_before_name = dict(list(self.query["selectors"].items())[:index])
            return self.get_distinct_values(name, selectors_before_name)
        # Optionals do not have an order and only need the selectors on the WHERE
        elif name in self.query["optionals"].keys():
            return self.get_distinct_values(name, self.query["selectors"])
            
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
        self.check_existance("measurements", self.query["measurements"])

        for name, value in self.query["selectors"].items():
            self.check_existance(name, value)

        for name, values in self.query["optionals"].items():
            for value in values:
                if not self.check_existance_optionals(name, value):
                    return False
        return True

    def get_data(self) -> Tuple[np.ndarray, np.ndarray]:
        """Read the data from the DB and return it as (x, y) where x is the time and y is the percentual disk usage"""
        if not self.validate_query():
            return None

        fields = ", ".join(self.query["fields"] + self.query["optionals"])
        where = self.construct_selection({**self.query["selectors"], **self.query["optionals"]})
        time = self.query["time"]
        # Do the query and filter only the useful fields
        query = """SELECT {fields} FROM (SELECT * FROM "{measurement}" {where} {time})""".format(**locals())
        results = transpose(self.exec_query(query))
        return results
