import json
import logging

import requests
import yaml

import config as c

LASM_ADDRESS = "http://localhost:5000"
INCIDENT_PATH = "/analysis-service/gralaf-report"
METRICS_PATH = "/analysis-service/gralaf-metrics"

session = requests.Session()
logger = logging.getLogger(__name__)


def send_metrics(last_metrics, lasm_addresses):
    last_metrics = last_metrics.to_dict()

    # data_to_send = {"violations": [],
    #                 "metrics": last_metrics}

    with open("sample_metrics_data.json", "w+") as outfile:
        json.dump(last_metrics, outfile, indent=2)
    for lasm_address in lasm_addresses:
        url = f"{lasm_address}{METRICS_PATH}"
        post_data(last_metrics, url, "metrics")


def post_data(data, url, data_name):
    try:
        response = session.post(url, json=data, timeout=5)
    except Exception as e:
        logger.error(f"Unable to sent {data_name} to {url} :\n{e}")
        return
    if response.status_code == 200:
        logger.info(f"Successfully sent {data_name} to LASM at {url}")
    else:
        logger.error(
            f"Unable to sent {data_name} to {response.request.url}. Response: {response.status_code} - {response.text}")


# curl -X POST http://127.0.0.1:8000/analysis-service/gralafreport/
def send_incident(data, lasm_addresses):
    for lasm_address in lasm_addresses:
        url = f"{lasm_address}{METRICS_PATH}"
        post_data(data, url, "incident")


if __name__ == '__main__':
    logging.basicConfig(level=getattr(logging, c.LOG_LEVEL),
                        format=c.LOGGING_FORMAT, datefmt=c.TIME_FORMAT)
    with open('config.yaml') as f:
        app_config = yaml.load(f, Loader=yaml.FullLoader)
    send_metrics({}, app_config['lasm_server_urls'])
