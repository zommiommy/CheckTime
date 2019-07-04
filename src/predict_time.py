
import logging
import numpy as np
from predictors import *

logger = logging.getLogger(__name__)

def predict_time_left(x : np.ndarray, y : np.ndarray, name : str, mode : str = "OLS") -> int:
    functions = {
        "OLS":OLS,
        "RANSAC":RANSAC,
        "BAYESIAN":BAYESIAN
    }
    
    if mode in functions.keys():
        logger.debug("Predicting using the mode [%s]"%mode)
        m, q =  functions[mode](x, y)
        time_predicted = (1 - q)/m
        delta = time_predicted - x[-1]
        print("{name} {delta}".format(**locals()))
        return delta
    logger.error("Mode [%s] not found, the available ones are %s"%(mode, functions.keys()))
    return None

