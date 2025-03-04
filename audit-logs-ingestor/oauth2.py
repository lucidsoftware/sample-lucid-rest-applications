#!/usr/bin/python
import json
import requests
import logging
import dataaccess
import configuration

from datetime import datetime, timedelta

logger = logging.getLogger("log")
CLIENT_ID = configuration.get_value("OAUTH2", "CLIENT_ID")
CLIENT_SECRET = configuration.get_value("OAUTH2", "CLIENT_SECRET")
REDIRECT_URI = configuration.get_value("OAUTH2", "REDIRECT_URI", allow_none=True)
if REDIRECT_URI is None:
    REDIRECT_URI = "https://lucid.app/oauth2/clients/{0}/redirect".format(CLIENT_ID)
    logger.info("No Redirect found. Using default redirect URI: " + REDIRECT_URI)


# 1) Return our current token, or generate a new one if its expired.
#    If this is the first execution, walk the user through the oauth2 grant flow
def _retrieve_access_token():
    token_data = dataaccess.get("token")
    if token_data is None:
        return generate_initial_token()
    return _retrieve_token_info(json.loads(token_data))


# 2) Retrieve the current token and refresh if its expired or about to
def _retrieve_token_info(data):
    if datetime.fromisoformat(data["expiration"]) > datetime.now() - timedelta(
        minutes=5
    ):
        logger.info(f"Current token valid until {data['expiration']}")
        return data["access_token"]
    logger.info("Token expired, refreshing...")
    return _refresh_token(data["refresh_token"])


# 3) Refresh my token and save for future use
def _refresh_token(refresh_token):
    url = "https://api.lucid.co/oauth2/token"
    body = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }
    request = requests.post(url, json=body)
    request.raise_for_status()
    response = json.loads(request.content)

    _save_token_info(response)
    return response["access_token"]


# 4) Set the expiration and save the token for next time
def _save_token_info(token):
    expiration = datetime.now() + timedelta(seconds=token.get("expires_in"))
    token["expiration"] = expiration.isoformat()
    dataaccess.set("token", json.dumps(token))


# --------------------------------------------------------------------------------------------------
# Generate initial access/refresh tokens if not generated
# --------------------------------------------------------------------------------------------------
def generate_initial_token():
    logger.info("Generating initial OAuth2 token")

    authorize_url = "https://lucid.app/oauth2/authorizeAccount"
    token_url = "https://api.lucid.co/oauth2/token"

    authorization_redirect_url = (
        authorize_url
        + "?response_type=code&client_id="
        + CLIENT_ID
        + "&redirect_uri="
        + REDIRECT_URI
        + "&scope=account.audit.logs+offline_access"
    )

    print(
        "go to the following url on the browser and enter the code from the returned url: "
    )
    print("---\n" + authorization_redirect_url + "\n---")
    authorization_code = input("code: ")

    data = {
        "grant_type": "authorization_code",
        "code": authorization_code,
        "client_secret": CLIENT_SECRET,
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
    }

    logger.info("Sending OAuth2 access request to Lucid")
    response = requests.post(token_url, json=data)
    response.raise_for_status()

    # we can now use the access_token as much as we want to access protected resources.
    tokens = json.loads(response.content)
    _save_token_info(tokens)
    access_token = tokens["access_token"]

    return access_token


# --------------------------------------------------------------------------------------------------
# Generate initial access/refresh tokens if not generated
# --------------------------------------------------------------------------------------------------
def authenticate():
    return _retrieve_access_token()
