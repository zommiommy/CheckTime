# CheckTime is a free software developed by Tommaso Fontana for Wurth Phoenix S.r.l. under GPL-2 License.


import numpy as np
from typing import Tuple
from sklearn.linear_model import BayesianRidge
from regressors import stats

def BAYESIAN(x : np.ndarray, y : np.ndarray) -> Tuple[int, int]:
    clf = BayesianRidge()
    clf.fit(x, y)
    m, q = clf.coef_[0], clf.intercept_
    mean = clf.predict(y.reshape(-1, 1))
    # This it's not an actual probability but it should be interpretable as one.
    print(stats.summary(clf, x, y.reshape(y.size)))
    p = 1 - np.nanmean(stats.coef_pval(clf, x, y))
    return m, q, p