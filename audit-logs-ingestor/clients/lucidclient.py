from datetime import datetime, timedelta, timezone
import logging

from requests import get

logger = logging.getLogger("log")
AUDIT_LOG_WINDOW = timedelta(minutes=10)


def get_audit_logs(token, connectors):
    logger.info("Sending request to retrieve Lucid audit logs...")
    request_url = "https://api.lucid.co/v1/auditLogs"

    request_params = {
        "from": (datetime.now(timezone.utc) - AUDIT_LOG_WINDOW).isoformat(),
    }

    headers = {
        "Authorization": f"Bearer {token}",
        "Lucid-Api-Version": f"{1}",
    }

    # Set a loop counter to prevent infinite loops (shouldn't happen unless bug or system error)
    loop_counter = 1000

    while loop_counter > 0:
        loop_counter -= 1
        response = get(url=request_url, headers=headers, params=request_params)
        response.raise_for_status()
        # Pagination links contain the complete query, so only send these parameters
        # with the initial request.
        request_params = None

        # Convert response to JSON
        json_data = response.json()

        # Count the number of items in the response
        json_count = len(json_data)

        # Get the pagination link supplied by the API, if there is another page.
        new_url = response.links.get("next", {}).get("url")


        # Stop when the time range is exhausted or the API does not advance its token.
        if json_count == 0 or not new_url or new_url == request_url:
            logger.info(
                "Audit log query complete. Stopping requests..."
            )
            break
        else:
            logger.info(
                f"{json_count} new audit log events found. Contining to next page..."
            )
            for connector in connectors:
                connector.store_events(json_data)
            request_url = new_url
