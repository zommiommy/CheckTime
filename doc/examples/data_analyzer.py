

import numpy as np
import pandas as pd
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.linear_model import RANSACRegressor
from statsmodels.tsa.holtwinters import ExponentialSmoothing

# Helper functions to convert epoch to date
date_to_epoch = lambda x: datetime.fromisoformat(x).timestamp()
epoch_to_date = lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d")


def plot_esitmate(x, y, ransac, time_predicted, inlier_mask, outlier_mask):
    # Predict data of estimated models
    px1 = np.linspace(x.min(), x.max(), 100)[:, np.newaxis]
    py1 = ransac.predict(px1)

    px2 = np.linspace(x.max(), time_predicted, 100)[:, np.newaxis]
    py2 = ransac.predict(px2)

    # Set the figure size
    plt.figure(figsize=(20,5))

    # Print in yellow the data ignored and in green the data used
    plt.scatter(x[inlier_mask], y[inlier_mask], color='yellowgreen', marker='.', label='Inliers')
    plt.scatter(x[outlier_mask], y[outlier_mask], color='gold', marker='.', label='Outliers')

    # Print the prediction
    plt.plot(px1, py1, color='blue')
    plt.plot(px2, py2, color='blue', dashes=[5,3])

    # Print the axes
    plt.plot([x.min(),time_predicted], [1,1], color='red', dashes=[5,3])

    # Setup the limits
    plt.xlim([x.min() ,time_predicted])

    plt.show()
        

def get_estimated_time(df : pd.DataFrame, x_col_name: str, y_col_name : str, window : int = None, *, smooth : bool = True, debug : bool = False):

    # Get the columns as numpy arrays to be able to fit them
    x = df[x_col_name].array.to_numpy()
    y = df[y_col_name].array.to_numpy()

    # Apply the window
    if window != None:
        x = x[-window:]
        y = y[-window:]

    # reshape the x to (n, 1) so the RANSAC can accept it
    x = x[:, np.newaxis]

    if smooth:
        model = ExponentialSmoothing(y, trend='add', seasonal=None)
        fit = model.fit()
        y = fit.fittedvalues

    # Fit the Line
    ransac = RANSACRegressor()
    ransac.fit(x, y)

    # Get the value ignored and the one actually used for the fit
    inlier_mask = ransac.inlier_mask_
    outlier_mask = np.logical_not(inlier_mask)

    # Get the coefficents
    m = ransac.estimator_.coef_[0]
    q = ransac.estimator_.intercept_
    if debug:
        print("y = {m} * x + {q}".format(**locals()))

    # Predict the intercept time
    time_predicted = (1 - q)/m

    # Print a lot of debugs info
    if debug:
        delta = time_predicted - x[-1]
        print("Date esitmated : %s"%epoch_to_date(time_predicted))
        print("Days left: %d"%(delta/(60*60*24)))
        plot_esitmate(x, y, ransac, time_predicted, inlier_mask, outlier_mask)


    # If the angular coefficent is 0 or negative then there will be no intercept
    if m  <= 0:
        print("The line is never going to intercept the max")
        return -1


    return time_predicted

