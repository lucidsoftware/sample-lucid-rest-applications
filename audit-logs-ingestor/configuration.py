import argparse
import configparser
import logging
import sys

logger = logging.getLogger("log")
parser = argparse.ArgumentParser()
parser.add_argument(
    "--clear_all",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Clear all stored information to force re-authentication and reset audit log pagination.",
)
parser.add_argument(
    "--clear_token",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Clear stored token to force re-authentication. Useful if token is expired or invalid.",
)
parser.add_argument(
    "--clear_link",
    default=False,
    action=argparse.BooleanOptionalAction,
    help="Clear stored audit log link to force re-fetching of audit logs.",
)
parser.add_argument(
    "-c",
    "--conf_file",
    help="Specify config file",
    metavar="FILE",
    default="config.ini",
)
args, _ = parser.parse_known_args()
config = configparser.ConfigParser()
config.read(args.conf_file)


def has_section(section):
    return config.has_section(section)


def get_value(section, key, allow_none=False):
    value = config.get(section, key, fallback=None)
    if value is None and allow_none is False:
        logger.error(
            f"Could not find value for {key} in section {section}. Exiting early."
        )
        sys.exit(1)

    return config.get(section, key, fallback=None)


def get_args():
    return args
