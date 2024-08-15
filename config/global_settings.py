# Copyright 2023 Jen-Hung Wang, IDUN Section, Department of Health Technology, Technical University of Denmark (DTU)
"""System module."""
import configparser
import json


def create_config_dict(config):
    """Create config dict"""
    dict = {}
    for section in config.sections():
        dict[section] = {}
        for key, val in config.items(section):
            dict[section][key] = val
    return dict


def import_config_dict():
    """Import config dict"""
    config = configparser.ConfigParser()
    config.read('config/path.ini')
    config_dict = create_config_dict(config)

    return config_dict


def str2bool(string):
    """string to boolean"""
    return string.lower() in ("yes", "true", "t", "1")
