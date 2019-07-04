from typing import Tuple
from sklearn.linear_model import LinearRegression


def OLS(x : np.ndarray, y : np.ndarray) -> Tuple[int, int]:
    reg = LinearRegression()
    reg.fit(x, y)
    LinearRegression(fit_intercept=True, n_jobs=None, normalize=False)
    return reg.coef_