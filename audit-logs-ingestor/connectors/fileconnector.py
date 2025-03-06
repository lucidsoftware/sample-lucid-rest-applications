#!/usr/bin/python
import configuration
import logging

logger = logging.getLogger("log")
FILE_NAME = configuration.get_value("FILE_CONNECTOR", "FILEPATH")
filelogger = logging.getLogger("auditlogs")
filelogger.setLevel(logging.INFO)
filelogger.addHandler(logging.FileHandler(FILE_NAME))


def store_events(events):
    logger.info(f"Storing Lucid audit logs via file connector. File: {FILE_NAME}")
    for event in events:
        filelogger.info(event)
