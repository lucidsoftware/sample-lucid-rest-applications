from argparse import Namespace
from datetime import datetime
from os import getenv
from requests import request
from requests.auth import HTTPBasicAuth
from typing import List, Dict, Any
import json
from utils.file_utils import save_raw_issues_to_json, save_parsed_issues_to_csv


def get_jira_issues(email: str, year: int) -> List[Dict[str, Any]]:
  print("Fetching issues from Jira...")
  url = f"https://{getenv('JIRA_SUBDOMAIN')}.atlassian.net/rest/api/3/search"
 
  auth = HTTPBasicAuth(getenv("JIRA_AUTH_EMAIL"), getenv("JIRA_API_KEY"))
 
  headers = {
    "Accept": "application/json"
  }
  
  issues = []
  
  start = 0
  max_results = 50
  total_returned = max_results
  total = -1
  
  while total_returned == max_results and start != total:
  
    query = {
      "jql": f"""assignee = '{email}' 
        AND created >= '{year}-01-01'
        AND created <= '{year}-12-31'
        AND status = Closed""",
      "startAt": f"{start}",
      "maxResults": f"{max_results}"
    }
  
    response = request(
        "GET",
        url,
        headers=headers,
        params=query,
        auth=auth
    )
    response.raise_for_status()
  
    data = json.loads(response.text)
    
    total = data['total']
    total_returned = len(data['issues'])
    start += total_returned
    
    issues += data['issues']
    
    print(f"{start} of {total} issues received from Jira")
  
  return issues

def sort_issues_by_quarter(issues: List[Dict[str, Any]], year: int, email: str, args: Namespace) -> Dict[str, List[Dict[str, Any]]]:
  # sort based on earliest to latest completed
  issues.sort(key = get_updated_or_created_date)
  
  issues_by_quarter = {
  'Q1': [],
  'Q2': [],
  'Q3': [],
  'Q4': []
  }
  
   # Get issues and put them into appropriate Quarter array
  for issue in issues:
    # Assign quarter based on when the issue status was changed to "closed"
    closed_date = get_updated_or_created_date(issue)
    closed_minus_timezone = closed_date[:-5]
    parsed_datetime = datetime.strptime(closed_minus_timezone, '%Y-%m-%dT%H:%M:%S.%f')
    
    if datetime(year, 1, 1) <= parsed_datetime <= datetime(year, 3, 31):
      issues_by_quarter['Q1'].append(issue)
    elif datetime(year, 4, 1) <= parsed_datetime <= datetime(year, 6, 30):
      issues_by_quarter['Q2'].append(issue)
    elif datetime(year, 7, 1) <= parsed_datetime <= datetime(year, 9, 30):
      issues_by_quarter['Q3'].append(issue)
    else:
      issues_by_quarter['Q4'].append(issue)
    
  if args.debug:
    save_raw_issues_to_json(issues, year, email)
    save_parsed_issues_to_csv(issues_by_quarter, year, email)
    
  return issues_by_quarter

def get_updated_or_created_date(issue: Dict[str, Any]) -> str:
  return_var = "1970-01-01T12:00:00.000-0700"
  
  if 'fields' in issue:
    if 'statuscategorychangedate' in issue['fields'] and issue['fields']['statuscategorychangedate'] is not None:
      return_var = issue['fields']['statuscategorychangedate']
    elif 'created' in issue['fields'] and issue['fields']['created'] is not None:
      return_var = issue['fields']['created']

  return return_var