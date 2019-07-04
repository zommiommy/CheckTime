

import sys
import logging
import argparse

from predict_time import predict_time_left

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
        verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == ERROR, 1 == DEBUG, it defaults to ERROR.",  type=int, choices=[0,1], default=0)
       

    def set_verbosity(self):
        if self.args.verbosity == 0:
            logging.basicConfig(level=logging.ERROR)
        else:
            logging.basicConfig(level=logging.DEBUG)

    def validate_args(self):
        if self.args.warning_threshold > self.args.critical_threshold:
            logger.error("The warning time ({}) should be bigger than the critical time ({})\n".format(self.args.warning_threshold,self.args.critical_threshold))
            os.exit(-1)

    def render_optionals(self, dg):
        for name, dictionary in self.query["optionals"].items():
            values = dictionary["values"]
            blacklist = dictionary["blacklist"]
            
            if not values:
                values = dg.get_available(name)
                
            filtered_values = [v for v in values if m not in blacklist]
            
            logger.debug("Rendered for the metrics [{}]".format(", ".join(filtered_values)))
            self.query["optionals"][name] = filtered_values


    def get_data(self):
        dg = DataGetter(self.query)
        self.render_optionals(dg)
        last_optional = list(self.query["optionals"].values())[-1]
        return [dg.get_data(m) for m in last_optional] 

    def construct_query(self):
        raise  NotImplemnetedError("This metod is ment to be overwritten by subclasses")

    def predict(self):
        raise  NotImplemnetedError("This metod is ment to be overwritten by subclasses")

    def _predict(self, x , y):
        # This just save the need to import files on the two frontends
        return predict_time_left(x, y)

    def add_time_to_query(self):
        """ Add the time selector to the query json"""
        time = """time > now() - {}""".format(self.args.window)
        self.query.update({"time":time})

    def exit(self):
        # Critical case
        if any(t < self.args.critical_threshold for t in self.predicted_times):
            sys.exit(2)
        # Warning case
        elif any(t < self.args.warning_threshold for t in self.predicted_times):
            sys.exit(1)
        # Metric no found
        elif any(t == None for t in self.predicted_times):
            sys.exit(1)
        # Normal case
        else:
            sys.exit(0)

    def run(self):
        self.args = self.parser.parse_args()
        self.set_verbosity()
        self.validate_args()
        self.query = self.construct_query()
        self.add_time_to_query()
        self.data = self.get_data()
        self.predicted_times = [self.predict(*data) for data in self.data]
        self.exit()
