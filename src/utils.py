from datetime import datetime

date_to_epoch = lambda x: datetime.fromisoformat(x).timestamp()
epoch_to_date = lambda x: datetime.fromtimestamp(x).strftime("%Y-%m-%d")