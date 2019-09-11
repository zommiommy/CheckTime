# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.


import numpy as np
from typing import Tuple
from sklearn.linear_model import BayesianRidge

def BAYESIAN(x : np.ndarray, y : np.ndarray) -> Tuple[int, int]:
    clf = BayesianRidge()
    clf.fit(x, y)
    m, q = clf.coef_[0], clf.intercept_
    mean, std = clf.predict(y.reshape(-1, 1), return_std=True)
    return m, q, np.mean(std)