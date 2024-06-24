# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import os
import sys
import logging
import argparse
import numpy as np
from typing import Dict, Union, List

import warnings
warnings.filterwarnings("ignore")

from core.logger import logger, setLevel
from core.data_getter import DataGetter
from core.predict_time import predict_time_left
from core.utils import transpose, rfc3339_to_epoch, parse_time_to_epoch, time_to_epoch, epoch_to_time, Timer

classification_order = {
    "OK":0,
    "WARNING":1,
    "CRITICAL":2
}

class MyParser(argparse.ArgumentParser):
    """Custom parser to ensure that the exit code on error is 1
        and that the error messages are printed on the stderr 
        so that the stdout is only for sucessfull data analysis"""

    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)

def check_overflow(epoch, _max = 2**32 - 1):
    """ IF the epoch overflow, influx wants a INF"""
    if epoch > _max:
        logger.info(f"The value {epoch} is bigger than {_max} so it was capped to it to prevent Influx duration Overflow Error")
        return _max
    return epoch

class MainClass:

    copyrights = """CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License."""

    def __init__(self):
        # Define the possible settings

        self.parser = MyParser(description=self.copyrights)

        query_settings_r = self.parser.add_argument_group('query settings (required)')
        query_settings_r.add_argument("-vq", '--validate-queries', type=int, choices=[0,1], default=1, help="Before executing the query, check that each single field of the query exists on the DB, 0 == do not check, 1 == check,  by defaults it check.")
        query_settings_r.add_argument("-M", "--measurement",    help="measurement where the data will be queried.", type=str, required=True)

        thresholds_settings = self.parser.add_argument_group('thresholds settings')
        thresholds_settings.add_argument("-n", "--window", help="the range of time to consider in the analysis.", type=str, required=True)
        thresholds_settings.add_argument("-w", "--warning-threshold", help="the time that if the predicted time is lower the script will exit(1).", type=str, required=True)
        thresholds_settings.add_argument("-c", "--critical-threshold", help="the time that if the predicted time is lower the script will exit(2).", type=str, required=True)

        verbosity_settings= self.parser.add_argument_group('verbosity settings (optional)')
        verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == CRITICAL, 1 == INFO, it defaults to ERROR.",  type=int, choices=[0,1], default=0)

    
    def parse_arguments(self):
        self.args = self.parser.parse_args()
        self.warning_threshold  = check_overflow(time_to_epoch(self.args.warning_threshold))
        self.critical_threshold = check_overflow(time_to_epoch(self.args.critical_threshold))
        

    def set_verbosity(self):
        if self.args.verbosity == 1:
            setLevel(logging.INFO)
        else:
            setLevel(logging.CRITICAL)

    def validate_args(self):
        if self.warning_threshold < self.critical_threshold:
            logger.error("The warning time ({}) should be bigger than the critical time ({})\n".format(self.warning_threshold,self.critical_threshold))
            sys.exit(-1)

    def render_optionals(self, dg):
        for name, dictionary in self.query["optionals"].items():
            values = dictionary["values"]
            blacklist = dictionary["blacklist"]
            
            if not values:
                values = dg.get_available(name)
                logger.info(f"The metrics available are  [{values}]")
                
            filtered_values = [v for v in values if v not in blacklist]
            
            logger.info("Rendered for the metrics [{}]".format(", ".join(filtered_values)))
            self.query["optionals"][name] = filtered_values


    def get_data(self):
        dg = DataGetter(self.query)
        self.render_optionals(dg)
        dg.set_query(self.query)
        last_optional = list(self.query["optionals"].values())[-1]
        return dg.get_data()

    def construct_query(self):
        raise  NotImplemnetedError("This method is ment to be overwritten by subclasses")

    def convert_types(self, data):
        data["time"] = [parse_time_to_epoch(x) for x in data["time"]]
        for field in self.query["fields"]:
            data[field] = [float(x) if type(x) == str and x.isnumeric() else x for x in data[field] ]
        return data

    def normalize_data(self, x, y, _max):
        if None not in _max:
            logger.info("Normalizing data by divinding value by max")
            return x, y / _max
        else:
            logger.info("The max values contains at least one None")
            if (0 <= y).all() and (y <= 1).all():
                logger.info("Assuming the values are already percentages since they are in the range [0,1]")
                return x, y
            elif (0 <= y).all() and (y <= 100).all():
                logger.info("Assuming the values are already percentages since they are in the range [0,1]")
                return x, y / 100
        logger.error("The max field contains Nones and the values are non interpretable as percentages")
        os.exit(1)

    def predict(self, option, subvalue):
        logger.info(f"Analyzing the metric: [{option}] with value [{subvalue}]")
        data = transpose([x for x in self.data if x[option] == subvalue])
        data = self.convert_types(data)
        x, y, _max = self.parse_data(data)
        x, y = self.normalize_data(x, y, _max)
        delta, p = predict_time_left(x, y, subvalue)
        delta_formatted = epoch_to_time(delta)

        if delta not in [None,"inf"] and delta < self.critical_threshold:
            classification = "CRITICAL"
        elif delta not in [None,"inf"] and  delta < self.warning_threshold:
            classification = "WARNING"
        else:
            classification = "OK"
        
        return delta, p, classification, subvalue, delta_formatted

    def parse_data(self, x, y, name):
        raise  NotImplemnetedError("This method is ment to be overwritten by subclasses")
        # This just save the need to import files on the two frontends

    def add_time_to_query(self):
        """ Add the time selector to the query json"""
        time = """time > now() - {}s""".format(check_overflow(time_to_epoch(self.args.window)))
        self.query.update({"time":time})

    def print_results(self):
        self.predicted_times.sort(key=lambda x: classification_order[x[2]], reverse=True)

        for time, p, classification, sub_value, delta_formatted in self.predicted_times:
            if np.isnan(p):
                print(f"{classification}: {sub_value} {delta_formatted}")
            else:
                print(f"{classification}: {sub_value} {delta_formatted} ({100*p:.2f}%)")

    def exit(self):
        logger.info(f"Warning threshold [{self.warning_threshold}]")
        logger.info(f"Critical threshold [{self.critical_threshold}]")
        times = [t[0] for t in self.predicted_times]

        # Critical case
        if any(t < self.critical_threshold for t in times if t != "inf"):
            logger.critical("Critical theshold failed!")
            sys.exit(2)
        # Warning case
        elif any(t < self.warning_threshold for t in times if t != "inf"):
            logger.warning("Warning theshold failed!")
            sys.exit(1)
        # Metric no found
        elif any(t == None for t in times):
            logger.warning("Some metrics were not found!")
            sys.exit(1)
        # Normal case
        else:
            logger.info("Sucessfull exit")
            sys.exit(0)

    def run(self):
        with Timer("The total runtime was {time}s"):
            # Parsing
            self.parse_arguments()
            # Check the args
            self.set_verbosity()
            self.validate_args()
            # Create the Query
                # OS specific part
            self.query = self.construct_query()
                # General part
            self.add_time_to_query()
            self.query["validate_queries"] = self.args.validate_queries == 1
            # Get the data
            self.data = self.get_data()
            # Predict
            self.predicted_times = [self.predict(option, subvalue) for option, values in self.query["optionals"].items() for subvalue in values]
            self.print_results()
            # Exit accordingly
            self.exit()
