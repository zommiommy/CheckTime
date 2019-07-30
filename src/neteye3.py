# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import numpy as np
from core import logger
from core import MainClass

class WinScript(MainClass):

    def __init__(self):
        super(WinScript, self).__init__()
        os_depenat_required = self.parser.add_argument_group('os dependant settings (required) Windows')
        os_depenat_required.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
        os_depenat_required.add_argument("-s", "--service", help="service to be checked.",            type=str, required=True)
        os_depenat_optional = self.parser.add_argument_group('os dependant settings (optional) Windows')
        os_depenat_optional.add_argument("-pl", "--performance-label", help="performance-label to be checked.", type=str, action="append", default=[])
        os_depenat_optional.add_argument("-e", "--exclude", help="metric to be excluded from the analysis.", type=str, action="append", default=[])

    def construct_query(self):
        return {
            "measurement":self.args.measurement,
            "selectors":{
                "host":self.args.host,
                "service":self.args.service
                },
            "optionals":{
                "performanceLabel":{
                    "values":self.args.metric,
                    "blacklist":self.args.exclude
                    }
                },
            "fields":["time", "value", "max"]
        }


    def parse_data(self, data):
        x = np.array(data["time"])
        value = np.array(data["value"])
        _max = np.array(data["max"])
        y = value / _max
        return x, y



if __name__ == "__main__":
    w = WinScript()
    w.run()