#!./check_disk_venv/bin/python

import sys
import logging
import argparse

from analyze_data import analyze_data

# Create a custom parser to ensure that the exit code on error is 1
# and that the error messages are print on the stderr so that the 
# stdout is only for sucessfull data analysis

class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help(file=sys.stderr)
        sys.exit(1)


# Define the possible settings

parser = MyParser()

query_settings_r = parser.add_argument_group('query settings (required)')
query_settings_r.add_argument("-M", "--measurement",    help="measurement where the data will be queried.", type=str, required=True)
query_settings_r.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
query_settings_r.add_argument("-s", "--service", help="service to be checked.",            type=str, required=True)

query_settings_o = parser.add_argument_group('query settings (optional)')
query_settings_o.add_argument("-m", "--metric", help="metric to be checked.", type=str, action="append", default=[])
query_settings_o.add_argument("-e", "--exclude", help="metric to be excluded from the analysis.", type=str, action="append", default=[])

thresholds_settings = parser.add_argument_group('thresholds settings')
thresholds_settings.add_argument("-n", "--window", help="the range of time to consider in the analysis.", type=str, required=True)
thresholds_settings.add_argument("-w", "--warning-threshold", help="the time that if the predicted time is lower the script will exit(1).", type=str, required=True)
thresholds_settings.add_argument("-c", "--critical-threshold", help="the time that if the predicted time is lower the script will exit(2).", type=str, required=True)

verbosity_settings= parser.add_argument_group('verbosity settings (optional)')
verbosity_settings.add_argument("-v", "--verbosity", help="set the logging verbosity, 0 == ERROR, 1 == DEBUG, it defaults to ERROR.",  type=int, choices=[0,1], default=0)
args = parser.parse_args()

# Set the verbosity

if args.verbosity == 0:
    logging.basicConfig(level=logging.ERROR)
else:
    logging.basicConfig(level=logging.DEBUG)

# Validate the settings

if args.warning_threshold > args.critical_threshold:
    logger.error("The warning time ({}) should be bigger than the critical time ({})\n".format(args.warning_threshold,args.critical_threshold))
    os.exit(-1)


# Analyze the data

predicted_time = analyze_data(args.host, args.service, args.metric, args.exclude)

# Return the correct exit code

# Critical case
if any(t < args.critical_threshold for t in predicted_time):
    sys.exit(2)
# Warning case
elif any(t < args.warning_threshold for t in predicted_time):
    sys.exit(1)
# Metric no found
elif any(t == None for t in predicted_time):
    sys.exit(1)
# Normal case
else:
    sys.exit(0)