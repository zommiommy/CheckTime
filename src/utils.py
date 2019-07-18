# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import re
import logging
from time import time
from datetime import datetime

logger = logging.getLogger(__name__)

epoch_to_iso = lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%dT%H:%M:%SZ")

iso_to_epoch = lambda x: datetime.fromisoformat(x).timestamp()

rfc3339_pattern = re.compile(r"(.+?)\.(\d+)Z")
time_pattern = re.compile(r"(\d+w)?(\d+d)?(\d+h)?(\d+m)?(\d+.?\d*s)?")
    
    
def rfc3339_to_epoch(string) -> float:
    date, ns = re.findall(rfc3339_pattern, string)[0]
    dt = datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
    return dt.timestamp() + float("0." + ns)

def epoch_to_time(epoch):
    weeks,  epoch = divmod(epoch, (7 * 24 * 60 * 60))
    days,   epoch = divmod(epoch, (24 * 60 * 60))
    hours,  epoch = divmod(epoch, (60 * 60))
    mins,   sec   = divmod(epoch, (60))
    
    out = ""
    if weeks:
        out += "{weeks}w".format(**locals())
    if days:
        out += "{days}d".format(**locals())
    if hours:
        out += "{hours}h".format(**locals())
    if mins:
        out += "{mins}m".format(**locals())
    if sec:
        out += "{sec:6f}s".format(**locals())
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