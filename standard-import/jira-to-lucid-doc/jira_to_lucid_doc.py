from dotenv import load_dotenv
from clients.lucid_client import create_lucid_board
from utils.arg_utils import parse_args
from utils.file_utils import cleanup
    
load_dotenv()

args = parse_args()
response_json = create_lucid_board(args)
cleanup()

print(f"Access the new document at: {response_json['editUrl']}")