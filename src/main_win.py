from main import MainClass

class WinScript(MainClass):

    def __init__(self):
        super(WinScript, self).__init__()
        self.os_depenat_required = self.parser.add_argument_group('os dependant settings (required) Windows')
        self.os_depenat_optional = self.parser.add_argument_group('os dependant settings (optional) Windows')
        self.os_depenat_required.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
        self.os_depenat_required.add_argument("-s", "--service", help="service to be checked.",            type=str, required=True)
        self.os_depenat_optional.add_argument("-m", "--metric", help="metric to be checked.", type=str, action="append", default=[])
        self.os_depenat_optional.add_argument("-e", "--exclude", help="metric to be excluded from the analysis.", type=str, action="append", default=[])

    def construct_query(self):
        return {
            "measurement":self.args.measurement,
            "selectors":{
                "host":self.args.host,
                "service":self.args.service
                },
            "optional":{
                "matric":self.args.metric
                }, 
            "blacklist":self.args.exclude,
            "fields":["time", "value", "max"]
        }

    def predict(self):
        x = self.data.get("time")
        y = self.data.get("value") / self.data.get("max") 
        return self._predict(x, y)



if __name__ == "__main__":
    w = WinScript()
    w.run()