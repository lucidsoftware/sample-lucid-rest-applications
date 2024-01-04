# Jira Issues to Lucid Document Generator
This Python script allows you to retrieve completed issues from Jira associated with a specific user and organizes them into a Lucid document based on quarterly categorization.
This script can be used to view completed work by an individual in a calendar year. Also, each shape representing a Jira issue has a link back to the source issue on Jira.

## Example Lucid Document Screenshot
![image](https://github.com/jakechr/jira-to-lucid-doc/assets/73912850/57aa7755-ce09-4a0f-84ac-9dddc836217a)

## Prerequisites
* Python 3.x installed on your system

### Required Python Modules

Before running the script, ensure you have the following Python modules installed:
* `dotenv`: Use `pip` to install the `dotenv` package
* `requests`: Use `pip` to install`requests` package
```
pip install python-dotenv
pip install requests
```

## Setup
### 1. Jira Authentication:
* Ensure you have appropriate access to the Jira instance.
* Provide the necessary authentication details (email, domain, and API token) in the `.env` file. You should be able to see your current Jira API tokens [here](https://id.atlassian.com/manage-profile/security/api-tokens).

### 2. Lucid API Setup:
* [Obtain API credentials](https://developer.lucid.co/rest-api/v1/#using-oauth2) (OAuth 2.0 token) from the [Lucid Developer Console](https://developer.lucid.co/guides/#unlocking-developer-tools).
* Put your valid OAuth 2.0 token in the `.env` file to authenticate and access Lucid.
* Note: The API credential is the generated OAuth 2.0 token that is valid for 1 hour from generation. You will need to generate a new token each time you use this script.

## Usage
### 1. Run the Script:
* Execute the Python script jira_to_lucid_doc.py.
* Provide the Jira email (doesn't have to be the same as the auth email), year for which you want to fetch issues, and Lucid product you want to import the document into (`lucidchart` or `lucidspark`).

### 2. Process Overview:
* The script will connect to Jira using the provided credentials and fetch all issues associated with the specified user.
* It categorizes these issues by the quarter they were updated or created.
* It creates a Lucid document with separate containers for each quarter, organizing the issues within them.

### 3. View the Lucid Document:
* Access the generated Lucid document through the generated link to visualize the categorized issues based on quarters.
* Use the Lucid interface to further analyze and manage these issues conveniently.

## Configuration and Environment Variables
This script requires specific environment variables to be set in a `.env` file within the project directory. Note that the `.env` file must be in the same directory as `jira_to_lucid_doc.py` 
Create a .env file with the following variables:

* #### JIRA_API_KEY: API key or token for Jira authentication.
* #### JIRA_AUTH_EMAIL: Email associated with the Jira account.
* #### LUCID_OAUTH2_TOKEN: OAuth2 token for Lucid API access.
* #### JIRA_SUBDOMAIN: Subdomain of your Jira instance URL.

### Obtaining Required Credentials:
#### Jira API Key:
* Generate an API token or key from your Jira [account settings](https://id.atlassian.com/manage-profile/security/api-tokens). This token will be used as the `JIRA_API_KEY`.
#### Jira Authentication Email:
* Use the email address associated with your Jira account as the `JIRA_AUTH_EMAIL`.
#### Lucid OAuth2 Token:
* Obtain an OAuth 2.0 token by creating an OAuth 2.0 app in your [Lucid Developer Console](https://developer.lucid.co/guides/#oauth-2-0-client-creation). Use the generated token as `LUCID_OAUTH2_TOKEN`.
#### Jira Subdomain:
* Identify and specify the subdomain of your Jira instance's URL. For instance, if your Jira URL is `https://yourcompany.atlassian.net`, the subdomain is `yourcompany`. Use the subdomain as `JIRA_SUBDOMAIN`.

### Example .env file:
```
JIRA_API_KEY="your_jira_api_key"
JIRA_AUTH_EMAIL="your_email@example.com"
LUCID_OAUTH2_TOKEN="your_lucid_oauth2_token"
JIRA_SUBDOMAIN="your_jira_subdomain"
```
### Command Line Flags
The script includes the following flags:

* #### -d or --debug: 
    * When this flag is set, two files will be created to assist in debugging. One will be a .csv file of the issues sorted by quarter, and the other will be a raw dump of all the JSON issues received from Jira.

* #### -h or --help: 
     * Display the help message explaining how to use the script and its flags.

## Example
```
python jira_to_lucid_doc.py
```
## Notes
* Ensure proper permissions and access levels for Jira and Lucid accounts to avoid authentication or data access issues.
* Ensure the .env file remains secure and isn't shared or committed to version control systems as it contains sensitive information.
