# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.


import numpy as np
from typing import Tuple
from sklearn.linear_model import RANSACRegressor


def RANSAC(x : np.ndarray, y : np.ndarray) -> Tuple[int, int]:
    ransac = RANSACRegressor()
    ransac.fit(x, y)
    m = ransac.estimator_.coef_[0]
    q = ransac.estimator_.intercept_
    return m, q, 1