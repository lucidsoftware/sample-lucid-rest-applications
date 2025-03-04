#!/usr/bin/python
import configuration
import json
import os
import logging

logger = logging.getLogger("log")
STORAGE_FILE = configuration.get_value("FILES", "STORAGE_FILEPATH")


def set(key, value):
    existing = _retrieve_storage()
    if existing.get(key) != value:
        existing.update({key: value})
        _write_to_file(STORAGE_FILE, existing)


def get(key):
    existing = _retrieve_storage()
    return existing.get(key)


def _retrieve_storage():
    if os.path.exists(STORAGE_FILE):
        return _read_from_file(STORAGE_FILE)
    else:
        _write_to_file(STORAGE_FILE, {})
        return {}


def _write_to_file(file_path, data):
    with open(file_path, "w") as file:
        json.dump(data, file, indent=4)


def _read_from_file(file_path):
    with open(file_path, "r") as file:
        data = json.load(file)
    return data


def _clear_storage():
    if os.path.exists(STORAGE_FILE):
        os.remove(STORAGE_FILE)


def handle_args():
    args = configuration.get_args()
    if args.clear_token:
        set("token", None)
    if args.clear_link:
        set("link", None)
    if args.clear_all:
        _clear_storage()
