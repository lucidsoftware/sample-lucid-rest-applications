from requests import get
import logging
import dataaccess

logger = logging.getLogger("log")


def get_audit_logs(token, connectors):
    logger.info("Sending request to retrieve Lucid audit logs...")
    request_url = "https://api.lucid.co/auditLogs"

    headers = {
        "Authorization": f"Bearer {token}",
        "Lucid-Api-Version": f"{1}",
    }

    # Read the existing data
    link = dataaccess.get("link")
    if link:
        request_url = link

    # Set a loop counter to prevent infinite loops (shouldn't happen unless bug or system error)
    loop_counter = 1000

    while loop_counter > 0:
        loop_counter -= 1
        response = get(url=request_url, headers=headers)
        response.raise_for_status()

        # Convert response to JSON
        json_data = response.json()

        # Count the number of items in the response
        json_count = len(json_data)

        # Get the pagination link.
        link = response.headers["Link"]
        start_index = link.find("<") + 1
        end_index = link.find(">")
        new_url = link[start_index:end_index]

        # If there are no new events or the pagination token is the same as the current URL, stop looping
        if json_count == 0 or new_url == request_url:
            logger.info(
                f"{json_count} new audit log events found or identical pagination token. Stopping requests..."
            )
            loop_counter = 0
            dataaccess.set("link", new_url)
        else:
            logger.info(
                f"{json_count} new audit log events found. Contining to next page..."
            )
            for connector in connectors:
                connector.store_events(json_data)
            request_url = new_url
