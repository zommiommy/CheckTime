# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.

import logging
import numpy as np 

from core.utils import Timer
from core.logger import logger
from core.predictors import *

def predict_time_left(x : np.ndarray, y : np.ndarray, name : str, mode : str = "OLS") -> int:
    functions = {
        "OLS":OLS,
        "RANSAC":RANSAC,
        "BAYESIAN":BAYESIAN
    }

    # Reshape the array as a single feature array for the predictors
    x = x.reshape(-1, 1)

    if mode in functions.keys():
        logger.info("Predicting using the mode [%s]"%mode)
        with Timer("The prediction took {time}s"):
            m, q =  functions[mode](x, y)
        logger.info("The coefficents predicted are m [{m}] q[{q}]".format(**locals()))
        if m <= 0:
            logger.info("The predicted line is not growing so it will never reach the max")
            return "inf"
        time_predicted = (1 - q)/m
        delta = time_predicted - x[-1]
        return delta[0]
    logger.error("Mode [%s] not found, the available ones are %s"%(mode, functions.keys()))
    return None

