from argparse import ArgumentParser, Namespace

def parse_args() -> Namespace:
  parser = ArgumentParser(description='''This Python script allows you to retrieve issues from Jira associated with a specific user 
                                   and organizes them into a Lucidchart document based on quarterly categorization.'''
                                   )

  parser.add_argument(
    '-d', '--debug',
    action='store_true',
    help='''When this flag is set, two files will be created to assist in debugging. One will be a .csv file of the issues
            sorted by quarter, and the other will be a raw dump of all the JSON issues received from Jira.'''
  )

  # Parse the arguments
  return parser.parse_args()