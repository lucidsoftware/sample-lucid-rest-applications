#!/usr/bin/python
from clients import lucidclient
import configuration
import dataaccess
import oauth2
import os
import logging

logger = logging.getLogger("log")
logger.setLevel(logging.INFO)
main_handler = logging.StreamHandler()
main_formatter = logging.Formatter(
    "%(asctime)s: %(module)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
main_handler.setFormatter(main_formatter)
logger.addHandler(main_handler)
log_filepath = configuration.get_value("FILES", "LOG_FILEPATH", allow_none=True)

if log_filepath is not None:
    file_handler = logging.FileHandler(configuration.get_value("FILES", "LOG_FILEPATH"))
    file_handler.setFormatter(main_formatter)
    logger.addHandler(file_handler)


def _get_connectors():
    connectors = []
    if configuration.has_section("FILE_CONNECTOR"):
        from connectors import fileconnector

        connectors.append(fileconnector)
    if configuration.has_section("SPLUNK_CONNECTOR"):
        from connectors import splunkconnector

        connectors.append(splunkconnector)

    if len(connectors) == 0:
        logger.warning(
            "No connectors found, aborting early to avoid pulling logs without a destination."
        )
        exit(1)
    else:
        logger.info(
            f"Using {len(connectors)} connectors: {', '.join([conn.__name__ for conn in connectors])}"
        )

    return connectors


if __name__ == "__main__":
    logger.info("Starting Lucid Audit Log Importer. Working directory: " + os.getcwd())

    # Handle arguments
    dataaccess.handle_args()

    # Get an oauth2 token. This will go through the generate token flow if none is found, otherwise it use or refresh the existing token.
    token = oauth2.authenticate()

    # Determine the connectors to use
    connectors = _get_connectors()

    # Pull new audit logs from Lucid and push them to the selected connector
    events = lucidclient.get_audit_logs(token, connectors)
