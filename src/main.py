# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import sys
import logging
import argparse
from typing import Dict, Union, List

from data_getter import DataGetter
from predict_time import predict_time_left
from utils import transpose, rfc3339_to_epoch, time_to_epoch, epoch_to_time


logger = logging.getLogger(__name__)



class MyParser(argparse.ArgumentParser):
    """Custom parser to ensure that the exit code on error is 1
        and that the error messages are printed on the stderr 
        so that the stdout is only for sucessfull data analysis"""
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)


class MainClass:

    def __init__(self):
        # Define the possible settings

        self.parser = MyParser()

        query_settings_r = self.parser.add_argument_group('query settings (required)')
        query_settings_r.add_argument("-M", "--measurement",    help="measurement where the data will be queried.", type=str, required=True)

        thresholds_settings = self.parser.add_argument_group('thresholds settings')
        thresholds_settings.add_argument("-n", "--window", help="the range of time to consider in the analysis.", type=str, required=True)
        thresholds_settings.add_argument("-w", "--warning-threshold", help="the time that if the predicted time is lower the script will exit(1).", type=str, required=True)
        thresholds_settings.add_argument("-c", "--critical-threshold", help="the time that if the predicted time is lower the script will exit(2).", type=str, required=True)

        verbosity_settings= self.parser.add_argument_group('verbosity settings (optional)')
        verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == ERROR, 1 == info, it defaults to ERROR.",  type=int, choices=[0,1], default=0)
       
    def parse_arguments(self):
        self.args = self.parser.parse_args()
        self.warning_threshold  = time_to_epoch(self.args.warning_threshold)
        self.critical_threshold = time_to_epoch(self.args.critical_threshold)

    def set_verbosity(self):
        if self.args.verbosity == 0:
            logging.basicConfig(level=logging.CRITICAL)
        else:
            logging.basicConfig(level=logging.INFO)

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
        raise  NotImplemnetedError("This metod is ment to be overwritten by subclasses")

    def convert_types(self, data):
        data["time"] = [rfc3339_to_epoch(x) for x in data["time"]]
        for field in self.query["fields"]:
            data[field] = [float(x) if type(x) == str and x.isnumeric() else x for x in data[field] ]
        return data

    def predict(self, option, subvalue):
        logger.info("Analyzing the metric: [{option}] with value [{subvalue}]".format(**locals()))
        data = transpose([x for x in self.data if x[option] == subvalue])
        data = self.convert_types(data)
        x, y = self.parse_data(data)
        delta = predict_time_left(x, y, subvalue)
        delta_formatted = epoch_to_time(delta)
        print("{subvalue} {delta_formatted}".format(**locals()))
        return delta

    def parse_data(self, x, y, name):
        raise  NotImplemnetedError("This metod is ment to be overwritten by subclasses")
        # This just save the need to import files on the two frontends

    def add_time_to_query(self):
        """ Add the time selector to the query json"""
        time = """time > now() - {}""".format(self.args.window)
        self.query.update({"time":time})

    def exit(self):
        # Critical case
        if any(t < self.critical_threshold for t in self.predicted_times):
            logger.error("Critical theshold failed!")
            sys.exit(2)
        # Warning case
        elif any(t < self.warning_threshold for t in self.predicted_times):
            logger.warning("Warning theshold failed!")
            sys.exit(1)
        # Metric no found
        elif any(t == None for t in self.predicted_times):
            logger.warning("Some metrics were not found!")
            sys.exit(1)
        # Normal case
        else:
            logger.info("Sucessfull exit")
            sys.exit(0)

    def run(self):
        self.parse_arguments()
        self.set_verbosity()
        self.validate_args()
        self.query = self.construct_query()
        self.add_time_to_query()
        self.data = self.get_data()
        self.predicted_times = [self.predict(option, subvalue) for option, values in self.query["optionals"].items() for subvalue in values]
        self.exit()
