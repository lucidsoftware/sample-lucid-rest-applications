from typing import List, Dict, Any
import csv
import json
import os
import zipfile

def cleanup() -> None:
    os.remove("document.json")
    os.remove("standard.lucid")

def save_raw_issues_to_json(issues: List[Dict[str, Any]], year: int, email: str) -> None:
  with open(f"raw_issues_{email.split('@')[0]}_{year}.json", "w") as json_file:
    # Convert the dictionary to a JSON string
    json.dump(issues, json_file, indent=2)  # `indent` for pretty formatting


def save_parsed_issues_to_csv(issues: List[Dict[str, Any]], year: int, email: str) -> None:
  with open(f"jira_history_{email.split('@')[0]}_{year}.csv", "w", newline="") as csvfile:
    fieldnames = ['quarter', 'key', 'summary']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    for key, value in issues.items():
      for issue in value:
        simpIssue = {
          'quarter': f'{key}',
          'key': f'{issue["key"]}',
          'summary': f'{issue["fields"]["summary"]}'
        }
        writer.writerow(simpIssue)

def create_zip_file() -> None:
  with zipfile.ZipFile('standard.zip', 'w') as my_zip:
    # Add files to the zip (replace this with actual file paths)
    my_zip.write('document.json')

  # Rename the zip file to have a .lucid extension
  os.rename('standard.zip', 'standard.lucid')
  
def generate_json_file(issues: Dict[str, List[Dict[str, Any]]]) -> None:
  data = {
    "version": 1,
    "collections": [],
    "pages": [
      {
        "id": "page1",
        "title": "Main Plan",
        "shapes": []
      }
    ]
  }
  
  swimlane = {
    "id": "swimlane1",
    "type": "swimLanes",
    "boundingBox": {
      "x": 0,
      "y": 0,
      "w": 1280,
      "h": 1200 # This will get replaced with the max lane height later
    },
    "style": {
        "fill": {
        "type": "color",
        "color": "#ADD8E6"
      },
        "stroke": {
        "color": "#000000",
        "width": 2,
        "style": "solid"
      }
    },
    "magnetize": True,
    "vertical": True,
    "titleBar": {
      "height": 10,
      "verticalText": False
    },
    "lanes": [
      {
        "title": "Q1",
        "width": 320,
        "headerFill": "#ffffff",
        "laneFill": "#D3D3D3"
      },
      {
        "title": "Q2",
        "width": 320,
        "headerFill": "#ffffff",
        "laneFill": "#D3D3D3"
      },
      {
        "title": "Q3",
        "width": 320,
        "headerFill": "#ffffff",
        "laneFill": "#D3D3D3"
      },
      {
        "title": "Q4",
        "width": 320,
        "headerFill": "#ffffff",
        "laneFill": "#D3D3D3"
      }
    ]
  }

  data["pages"][0]["shapes"].append(swimlane)
  
  i = 0
  max_y = 0
  
  for key, value in issues.items():
    start_x = i * 320
    j = 0
    
    for issue in value:
      x = start_x + ((j % 3) * 105) + 5
      y = 50 + (j // 3) * 105
      
      if y > max_y:
        max_y = y
      
      shape = {
        "id": f"{issue['key']}",
        "type": "stickyNote",
        "boundingBox": {
          "x": x,
          "y": y,
          "w": 100,
          "h": 100
        },
        "style": {
          "fill": {
            "type": "color",
            "color": "#ADD8E6"
          },
          "stroke": {
            "color": "#000000",
            "width": 1,
            "style": "solid"
          }
        },
        "text": f"<a href='https://{os.getenv('JIRA_SUBDOMAIN')}.atlassian.net/browse/{issue['key']}'>{issue['key']}</a>: {issue['fields']['summary']}",
      }
      
      data["pages"][0]["shapes"].append(shape)
      j += 1
    i += 1
  
  data["pages"][0]["shapes"][0]["boundingBox"]["h"] = max_y + 100 # the extra 100 pixels allows room for the title bar and bottom padding
  
  with open('document.json', 'w') as json_file:
    # Convert the dictionary to a JSON string
    json.dump(data, json_file, indent=2)  # `indent` for pretty formatting