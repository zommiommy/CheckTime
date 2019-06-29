
import logging
from typing import List

from predict_time import predict
from data_getter import DataGetter

logger = logging.getLogger(__name__)

def analyze_data(measurement : str, host : str, service : str, metrics : List[str] = [], blacklist : List[str] = []) -> List[int]:
    """Predict the seconds left for the disk to fill"""

    dg = DataGetter()

    if not metric:
        logger.debug("Retrieving all the metrics.")
        metrics = dg.get_metrics(host, service)
    
    # Filter the metric that was passed with the  -e param
    filtered_metrics = [m for m in metrics if m not in blacklist]

    logger.debug("Predicting for the metrics [{}]".format(", ".join(filtered_metrics)))

    return [predict(*dg.get_data(host, service, m)) for m in filtered_metrics] 
