# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import os
import sys
import json
import logging
from functools import lru_cache

from logger import logger

# TODO make a good cacher decorator to cache the queries
# TODO add cache persistency
#   TODO Add cache expiration

cacher = lambda x: lru_cache()(x)