# arg_config.py
import argparse

def get_cli_args():
    parser = argparse.ArgumentParser(
        description="Use any of the commands below for a more unqiue experience:",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("-rc", "--result-count", type=int, help="max number of results to return", default=5)
    parser.add_argument("-s", "--search", help="search term",  default="OpenAI")
    parser.add_argument("-c", "--clean", action="store_true", help="clear existing log file")
    
    return parser.parse_args()
