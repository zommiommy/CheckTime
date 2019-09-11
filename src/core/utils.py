# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import re
from time import time
from datetime import datetime

from core.logger import logger


epoch_to_iso = lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%SZ")

iso_to_epoch = lambda x: datetime.fromisoformat(x).timestamp()

rfc3339_pattern = re.compile(r"(.+?)(\.(\d+))?Z")
time_pattern = re.compile(r"(\d+w)?(\d+d)?(\d+h)?(\d+m)?(\d+.?\d*s)?")
    

def parse_time_to_epoch(string):
    if re.match(rfc3339_pattern, string):
        return rfc3339_to_epoch(string)
    if string.isnumeric():
        return int(string)
    if re.match(time_pattern, string):
        return time_to_epoch(string)
    
    logger.error("Can't decode the time format [%s]"%string)
    sys.exit(1)
    
def rfc3339_to_epoch(string):
    founds = re.findall(rfc3339_pattern, string)
    if len(founds) <= 0:
        return string
    date, _, ns = founds[0]
    dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    return dt.timestamp() + float("0." + ns)

def epoch_to_time(epoch):
    if epoch == "inf":
        return "inf"

    weeks,  epoch = divmod(epoch, (7 * 24 * 60 * 60))
    days,   epoch = divmod(epoch, (24 * 60 * 60))
    hours,  epoch = divmod(epoch, (60 * 60))
    mins,   sec   = divmod(epoch, (60))
    
    out = ""
    if weeks:
        out += f"{int(weeks)}w"
    if days:
        out += f"{int(days)}d"
    if hours:
        out += f"{int(hours)}h"
    if mins:
        out += f"{int(mins)}m"
    if sec:
        out += f"{sec:.2f}s"
    return out
    
def time_to_epoch(time):
    weeks, days, hours, minuts, sec = re.findall(time_pattern, time)[0]
    result = 0
    if sec:
        result += float(sec[:-1])
    if minuts:
        result += 60 * int(minuts[:-1])
    if hours:
        result += 60 * 60 * int(hours[:-1])
    if days:
        result += 60 * 60 * 24 * int(days[:-1])
    if weeks:
        result += 60 * 60 * 24 * 7 * int(weeks[:-1])
    return result



def transpose(lista):
    """Transpose a list of dictionaries to a dictionary of lists. 
       It assumes all the dictionaries have the sames keys."""
    _dict = {}
    for x in lista:
        for k, v in x.items():
            _dict.setdefault(k,[])
            _dict[k] += [v]
    return _dict

class Timer:
    def __init__(self, format_):
        self.format_ = format_
    def __enter__(self):
        self.start = time()
    def __exit__(self, type, value, traceback):
        logger.info(self.format_.format(time=(time()-self.start)))