from main import MainClass

class LinuxScript(MainClass):

    def __init__(self):
        super(LinuxScript, self).__init__()
        self.os_depenat_required = self.parser.add_argument_group('os dependant settings (required) Linux')
        self.os_depenat_optional = self.parser.add_argument_group('os dependant settings (optional) Linux')
        self.os_depenat_required.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
        self.os_depenat_required.add_argument("-d", "--device",  help="service to be checked.",            type=str, required=True)
        self.os_depenat_optional.add_argument("-p", "--path",    help="path to be checked.", type=str, action="append", default=[])
        self.os_depenat_optional.add_argument("-e", "--exclude", help="path to be excluded from the analysis.", type=str, action="append", default=[])

    def construct_query(self):
        return {
            "measurement":self.args.measurement,
            "selectors":{
                "host":self.args.host,
                "device":self.args.device
                },
            "optional":{
                "path":self.args.path
                }, 
            "blacklist":self.args.exclude,
            "fields":["time", "free", "total"]
        }

    def predict(self):
        x = self.data.get("time")
        y = 1 - (self.data.get("free") / self.data.get("total")) 
        return = self._predict(x, y)




if __name__ == "__main__":
    l = LinuxScript()
    l.run()

