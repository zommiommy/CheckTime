# CheckTime
CheckTime it's a plugin for Icinga to predict the time left until a certain metric reach the max.
It's under GPL2 license and it was developed for Würth Phoenix S.r.l.

## Description

Often, on monitoring softwares, the warning threshold of several metrics are expressed as a percentage.

This approch have the major flaw that it doesn't consider the rate of change.
Therefore a disk with 99% of the space used create a warning even if it's has been years that nothing written on it.

To solve this problem this script was made.

This script will read the metric from the DB (InfluxDB) and try to predict the expected time left before the metric reach it's max.

![](https://github.com/zommiommy/CheckTime/raw/master/doc/example.png)



The software specification and more informations (only in Italian for now) can be found [here](https://github.com/zommiommy/CheckTime/raw/master/doc/WP_time_prediction_V0_3.pdf).

## Installation
In order to execute the script, there must be a python 3 environment with the followings modules installed:
```
Python 3.7.3
Package         Version 
--------------- --------
asn1crypto      0.24.0  
certifi         2019.3.9
cffi            1.12.2  
chardet         3.0.4   
conda           4.6.14  
cryptography    2.6.1   
idna            2.8     
influxdb        5.2.2   
joblib          0.13.2  
numpy           1.16.4  
pandas          0.24.2  
pip             19.0.3  
pycosat         0.6.3   
pycparser       2.19    
pyOpenSSL       19.0.0  
PySocks         1.6.8   
python-dateutil 2.8.0   
pytz            2019.1  
requests        2.21.0  
ruamel-yaml     0.15.46 
scikit-learn    0.21.2  
scipy           1.3.0   
setuptools      41.0.0  
six             1.12.0  
sklearn         0.0     
urllib3         1.24.1  
wheel           0.33.1 
```
This can be achieved in 3 ways:

- Have python 3 installed on the system and use pip to install all the needed modules if not already presents.
- Have python 3 installed and create a Virtual-Environment where the modules will be installed.
- Use the preconfigured python in ```check_time_env``` which is miniconda.

The last option allows the script to be installed without modifying anything in the system, this convinence is paid by the size of the folder which is ~500Mb.

## Update
Since the script do not have any dependancies beside his folder, in order to update the script a pull must be performed.
```
git pull
```

## Database configuration
The database configurations are in the file ```db_settings.json``` in the root of the folder.
```json
{
    "database": "my_db",
    "host": "localhost",
    "port": 8086,
    "username": "root",
    "password": "root",
    "ssl": false,
    "verify_ssl": false,
    "timeout": 60,
    "retries": 3,
    "use_udp": false,
    "udp_port": 4444,
    "proxies": {},
    "path": ""
}
```

If a more flexible approch is needed, open an issue or modify the ```__init__``` function of the class ```DataGetter``` in the file ```src/core/data_getter.py```,

## Usage

To get more information about the script it can just be called with the ```-h / --help``` argument:
```
$ checktime-win -h
usage: win.py [-h] [-vq {0,1}] -M MEASUREMENT -n WINDOW -w WARNING_THRESHOLD
              -c CRITICAL_THRESHOLD [-v {0,1}] -H HOST -s SERVICE [-m MATRIC]
              [-e EXCLUDE]

CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix
S.r.l. under GPL-2 License.

optional arguments:
  -h, --help            show this help message and exit

query settings (required):
  -vq {0,1}, --validate-queries {0,1}
                        Before executing the query, check that each single
                        field of the query exists on the DB, 0 == do not
                        check, 1 == check, by defaults it check.
  -M MEASUREMENT, --measurement MEASUREMENT
                        measurement where the data will be queried.

thresholds settings:
  -n WINDOW, --window WINDOW
                        the range of time to consider in the analysis.
  -w WARNING_THRESHOLD, --warning-threshold WARNING_THRESHOLD
                        the time that if the predicted time is lower the
                        script will exit(1).
  -c CRITICAL_THRESHOLD, --critical-threshold CRITICAL_THRESHOLD
                        the time that if the predicted time is lower the
                        script will exit(2).

verbosity settings (optional):
  -v {0,1}, --verbosity {0,1}
                        set the logging verbosity, 0 == CRITICAL, 1 == INFO,
                        it defaults to ERROR.

os dependant settings (required) Windows:
  -H HOST, --host HOST  host which disks will be checked.
  -s SERVICE, --service SERVICE
                        service to be checked.

os dependant settings (optional) Windows:
  -m MATRIC, --matric MATRIC
                        metric to be checked.
  -e EXCLUDE, --exclude EXCLUDE
                        metric to be excluded from the analysis.
```

Therefore an example of usage might be:
```
checktime-win -v 1 -M disk -n 10000w -w 10w -c 5w -H my.host.com -s Diskspace -m Win
```

The output will be like:
```
CRITICAL: 1s /etc
WARNING: 1m /var
OK: 1d4s /tmp
```

And the exit code is 0 if everything is OK, 1 if there are WARNINGs and finally 2 if there are CRITICALs.

### Frontends
The script have a core class which is extended by a few frontends which job is to handle the difference in the schemas of the various measurements.

The default frontends are:
```
name            Schema expected
----            ---------------
linux           time, hostname, device, path, free, total
win             time, hostname, service, metric, value, max
win_percentage  time, hostname, service, metric, value, max
net_eye3        time, host, service, performanceLabel, value, max
net_eye4        time, hostname, service, metric, value, max
```

### Executable
In order to execute the script it must follow the syntax:
```
python frontend.py 
```
And then adding the arguments after.

If the installation must be contained in the folder an useful trick is an executable bash script which find his current path (saved in the DIR variable) and then call the correct environment an script from there. 

e.g.
```Bash
#!/bin/bash
DIR=$(dirname "$(python -c "import os,sys; print(os.path.realpath(sys.argv[1]))" $0)")
$DIR/../check_time_env/bin/python $DIR/../src/linux.py "$@"
```

### Custom Frontend
A frontend is just a class that extend ```MainClass``` from the package core.

The frontend will have to to 4 things:

Create a constructor where the schema-specific argument will be passed to the script. Once called constructor of the father class there will be the attribute ```self.parser``` which is the parser from the module ```ArgParse```.

e.g.
```python
    def __init__(self):
        super(WinScript, self).__init__()
        os_depenat_required = self.parser.add_argument_group('os dependant settings (required) Windows')
        os_depenat_required.add_argument("-H", "--host",    help="host which disks will be checked.", type=str, required=True)
        os_depenat_required.add_argument("-s", "--service", help="service to be checked.",            type=str, required=True)
        os_depenat_optional = self.parser.add_argument_group('os dependant settings (optional) Windows')
        os_depenat_optional.add_argument("-m", "--metric", help="metric to be checked.", type=str, action="append", default=[])
        os_depenat_optional.add_argument("-e", "--exclude", help="metric to be excluded from the analysis.", type=str, action="append", default=[])
```

Then it must override the method ```construct_query``` that must return a dictionary:

e.g.
```python
    def construct_query(self):
        return {
            "measurement":self.args.measurement,
            "selectors":{
                "hostname":self.args.host,
                "service":self.args.service
                },
            "optionals":{
                "metric":{
                    "values":self.args.metric,
                    "blacklist":self.args.exclude
                    }
                },
            "fields":["time", "value", "max"]
        }
```
This dictionary will make the script read the measurement passed by argument.
Selectors is a dictionary of the fields that must be matched.
So in the example only the data with hostname and service equals to the ones passed as argument will be considered.
Optionals are the data that can have multiple values.
Each field in optionals have a "selection" dictionary where values must be the list of the only values that must be considered, if empty all the values are used.
Moreover blacklist is the list of values that must NOT be considered.
And then the data for the analysis will be time, value, max.

Then the frontend must also override the method ```parse_data``` which will receive a dictionary in the form {"field":list_of_values}.

The result have to be the x and y numpy array to pass to the analysis.

e.g.
```python
    def parse_data(self, data):
        x = np.array(data["time"])
        y = np.array(data["value"]) / 100
        return x, y
```

Finally to run the script must execute the run method of the class.

e.g.
```python
if __name__ == "__main__":
    w = WinScript()
    w.run()
```
