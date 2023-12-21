from argparse import Namespace
from .jira_client import get_jira_issues, sort_issues_by_quarter
from requests import post
from typing import Dict, Any
from utils.file_utils import cleanup, create_zip_file, generate_json_file
import os

def create_lucid_board(args: Namespace) -> Dict[str, Any]:
  email = input("Enter the email of your Jira user: ")
  year = int(input("Enter the year you want the Jira history for: "))
  product = input("What Lucid product would you like to import this document into? (lucidchart/lucidspark): ")
  
  issues = get_jira_issues(email, year)
  issues_by_quarter = sort_issues_by_quarter(issues, year, email, args)
  generate_json_file(issues_by_quarter)
  create_zip_file()
  return send_lucid_import_request(email, year, product)

def send_lucid_import_request(email: str, year: int, product: str) -> Dict[str, Any]:
  print("Sending request to create Lucid document...")
  url = "https://api.lucid.co/documents"
 
  headers = {
    "Authorization": f'Bearer {os.getenv("LUCID_OAUTH2_TOKEN")}',
    "Lucid-Api-Version": f"{1}"
  }

  files = {
    "file": ('standard.lucid', open('standard.lucid', 'rb'), 'x-application/vnd.lucid.standardImport')
  }
  
  data = {
    "title": f"{email.split('@')[0]} Jira History - {year}",
    "product": product
  }
  
  response = post(url = url, headers = headers, data = data, files = files)
  cleanup()
  response.raise_for_status()
  return response.json()
