#!/bin/bash
echo 'Start last price task and other periodic' && celery -A src.worker call src.worker.last_tickers_task && celery -A src.worker worker --loglevel=INFO