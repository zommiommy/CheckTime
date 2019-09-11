

import numpy as np
from typing import Tuple
from sklearn.linear_model import LinearRegression


def OLS(x : np.ndarray, y : np.ndarray) -> Tuple[int, int]:
    reg = LinearRegression()
    reg.fit(x, y)
    m, q = reg.coef_[0], reg.intercept_
    return m, q, 1