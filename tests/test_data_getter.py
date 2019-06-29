
import logging
from ..data_getter import DataGetter


logging.basicConfig(level=logging.DEBUG)

dg = DataGetter()

measuremnts = dg.get_measurements()
print(measuremnts)

hosts = dg.get_hosts(measuremnts[0])
print(hosts)

services = dg.get_services(measuremnts[0], hosts[1])
print(services)

metrics = dg.get_metrics(measuremnts[0], hosts[1], services[0])
print(metrics)