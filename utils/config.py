"""
Centralized configuration module for the Enphase solar monitoring system.
Loads all configuration values from config.ini and provides them as module-level constants.
"""

import os
import configparser

# Initialize config parser
config = configparser.ConfigParser()
config_file = 'config.ini'

# Enphase Envoy 1 settings (main system with consumption CTs)
ENVOY_IP1 = None
TOKEN1 = None

# Enphase Envoy 2 settings (secondary system)
ENVOY_IP2 = None
TOKEN2 = None

# General settings
UNIT_COST = 0.26
CT_SCALE_FACTOR = 2.0

# HQST/Renogy Charge Controller settings
HQST_MAC_ADDRESS = None
HQST_DEVICE_NAME = None
HQST_DEVICE_TYPE = 'controller'
HQST_DEVICE_ID = 1
HQST_READ_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
HQST_WRITE_CHAR_UUID = "0000ffe1-0000-1000-8000-00805f9b34fb"
HQST_POWER_MULTIPLIER = 0.5
HQST_GENERATION_MULTIPLIER = 0.05

# WordPress post settings
WP_POST_URL = None
WP_USERNAME = None
WP_APP_PASSWORD = None
WP_POST_ID = None


def load_config():
    """Load configuration from config.ini file."""
    global ENVOY_IP1, TOKEN1, ENVOY_IP2, TOKEN2
    global UNIT_COST, CT_SCALE_FACTOR
    global HQST_MAC_ADDRESS, HQST_DEVICE_NAME, HQST_DEVICE_TYPE, HQST_DEVICE_ID
    global HQST_READ_CHAR_UUID, HQST_WRITE_CHAR_UUID
    global HQST_POWER_MULTIPLIER, HQST_GENERATION_MULTIPLIER
    global WP_POST_URL, WP_USERNAME, WP_APP_PASSWORD, WP_POST_ID

    if not os.path.exists(config_file):
        return

    config.read(config_file)

    # Load Envoy 1 settings
    if 'envoy1' in config:
        ENVOY_IP1 = config['envoy1'].get('ip', None)
        TOKEN1 = config['envoy1'].get('token', None)

    # Load Envoy 2 settings
    if 'envoy2' in config:
        ENVOY_IP2 = config['envoy2'].get('ip', None)
        TOKEN2 = config['envoy2'].get('token', None)

    # Load general settings
    if 'settings' in config:
        UNIT_COST = config['settings'].getfloat('unit_cost', 0.26)
        CT_SCALE_FACTOR = config['settings'].getfloat('ct_scale_factor', 2.0)

    # Load HQST settings
    if 'hqst' in config:
        HQST_MAC_ADDRESS = config['hqst'].get('mac_address', None)
        HQST_DEVICE_NAME = config['hqst'].get('device_name', None)
        HQST_DEVICE_TYPE = config['hqst'].get('device_type', 'controller')
        HQST_DEVICE_ID = config['hqst'].getint('device_id', 1)
        HQST_READ_CHAR_UUID = config['hqst'].get(
            'read_char_uuid', '0000ffe1-0000-1000-8000-00805f9b34fb'
        )
        HQST_WRITE_CHAR_UUID = config['hqst'].get(
            'write_char_uuid', '0000ffe1-0000-1000-8000-00805f9b34fb'
        )
        HQST_POWER_MULTIPLIER = config['hqst'].getfloat('power_multiplier', 0.5)
        HQST_GENERATION_MULTIPLIER = config['hqst'].getfloat(
            'generation_multiplier', 0.05
        )

    # Load WordPress post settings
    if 'post' in config:
        WP_POST_URL = config['post'].get('url', None)
        WP_USERNAME = config['post'].get('username', None)
        WP_APP_PASSWORD = config['post'].get('app_password', None)
        WP_POST_ID = config['post'].get('post_id', None)


# Load config on module import
load_config()