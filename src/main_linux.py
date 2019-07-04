

import numpy as np
from main import MainClass

class LinuxScript(MainClass):

    def __init__(self):
        super(LinuxScript, self).__init__()
        os_depenat_required = self.parser.add_argument_group('os dependant settings (required) Linux')
        os_depenat_optional = self.parser.add_argument_group('os dependant settings (optional) Linux')
        os_depenat_required.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
        os_depenat_required.add_argument("-d", "--device",  help="service to be checked.",            type=str, required=True)
        os_depenat_optional.add_argument("-p", "--path",    help="path to be checked.", type=str, action="append", default=[])
        os_depenat_optional.add_argument("-e", "--exclude", help="path to be excluded from the analysis.", type=str, action="append", default=[])

    def construct_query(self):
        return {
            "measurement":self.args.measurement,
            "selectors":{
                "host":self.args.host,
                "device":self.args.device
                },
            "optional":{
                "path":{
                    "values":self.args.path,
                    "blacklist":self.args.exclude
                    }
                },
            "fields":["time", "free", "total"]
        }

    def predict(self, data):
        x = data["time"]
        free = np.array(data["free"])
        total = np.arrya(data["total"])
        y = 1 - (free / total)
        return = self._predict(x, y)




if __name__ == "__main__":
    l = LinuxScript()
    l.run()


