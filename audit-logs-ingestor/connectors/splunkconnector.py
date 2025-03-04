import configuration
import logging
import splunklib.client as client

logger = logging.getLogger("log")

HOST = configuration.get_value("SPLUNK_CONNECTOR", "HOST")
PORT = configuration.get_value("SPLUNK_CONNECTOR", "PORT")
TOKEN = configuration.get_value("SPLUNK_CONNECTOR", "TOKEN", allow_none=True)
INDEX = configuration.get_value("SPLUNK_CONNECTOR", "INDEX")
USERNAME = configuration.get_value("SPLUNK_CONNECTOR", "USERNAME", allow_none=True)
PASSWORD = configuration.get_value("SPLUNK_CONNECTOR", "PASSWORD", allow_none=True)


def store_events(events):
    try:
        # Create a Service instance using token
        if TOKEN is not None:
            logger.info("Attempting to connect to Splunk with token")
            service = client.connect(host=HOST, port=PORT, token=TOKEN, autologin=True)
        else:
            logger.info("Attempting to connect to Splunk with username and password")
            service = client.connect(
                host=HOST,
                port=PORT,
                username=USERNAME,
                password=PASSWORD,
                autologin=True,
            )
        _send_events_to_splunk(service, INDEX, events)
    except Exception as e:
        logger.error(f"Failed to connect to Splunk with Exception: {e}")
        logger.error(
            "Failed to store Lucid pulled audit logs. After resolving the authentication issue, consider rerunning the import script with the --clear_link flag to re-pull the lost events."
        )


# Send events to Splunk
def _send_events_to_splunk(service, index_name, event_data):
    # Look up the index
    index = service.indexes[index_name]

    for event in event_data:
        # Submit the event
        index.submit(
            event=event,
            sourcetype="json",
        )

    return
