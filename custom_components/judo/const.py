"""Constants for the JUDO integration."""
from __future__ import annotations

DOMAIN = "judo"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Connectivity"
DEFAULT_SCAN_INTERVAL = 300  # seconds
MIN_API_GAP = 11.0  # seconds between API calls (firmware rate-limit)
REQUEST_TIMEOUT = 15  # seconds

# Optional cloud relay (myjudo.eu). Used to surface live values that the
# local connectivity-module API does not expose (live flow, battery backup,
# regeneration count). Disabled unless the user provides credentials.
CONF_CLOUD_USER = "cloud_user"
CONF_CLOUD_PASSWORD = "cloud_password"
CLOUD_BASE_URL = "https://www.myjudo.eu"

# REST registers (hex strings without leading 0x)
REG_DEVICE_TYPE = "FF00"
REG_DEVICE_NUMBER = "0600"
REG_SW_VERSION = "0100"
REG_INSTALLATION_DATE = "0E00"
REG_OPERATING_HOURS = "2500"
REG_TARGET_HARDNESS = "5100"
REG_SALT_LEVEL = "5600"
REG_TOTAL_WATER = "2800"
REG_SOFT_WATER = "2900"
REG_DAILY_STATS = "FB00"
REG_WEEKLY_STATS = "FC00"
REG_MONTHLY_STATS = "FD00"
REG_YEARLY_STATS = "FE00"

REG_REGENERATION_START = "350000"
REG_LEAKAGE_CLOSE = "3C00"  # close valve = leakage protection active
REG_LEAKAGE_OPEN = "3D00"   # open valve = leakage protection inactive
REG_VACATION_MODE_ON = "4100"
REG_VACATION_MODE_OFF = "4200"
REG_SALT_WARNING_DAYS = "5700"
REG_SERVICE_CONTACT = "5800"

# Known device types (FF00 value -> human-readable name).
# Compiled from OStrama/judo_rest_api which has the most extensive mapping
# verified across multiple devices.
DEVICE_TYPES = {
    0x32: "i-soft",
    0x33: "i-soft SAFE+",
    0x34: "Softwell P",
    0x35: "Softwell S",
    0x36: "Softwell K",
    0x37: "i-soft TGA",
    0x38: "QuickSoft M",
    0x39: "QuickSoft P",
    0x3C: "i-fill",
    0x3D: "i-dos eco",
    0x41: "i-dos eco",
    0x42: "i-soft K SAFE+",
    0x43: "i-soft K",
    0x44: "ZEWA / PROM-i-SAFE",
    0x46: "QuickSoft CD",
    0x47: "Softwell KP",
    0x48: "Softwell KS",
    0x49: "OptiLine Z",
    0x4A: "OptiLine E",
    0x4B: "i-soft Pro S",
    0x4C: "i-soft Pro L",
    0x4D: "QuickSoft MP",
    0x4E: "i-soft C SAFE",
    0x4F: "i-soft C",
    0x50: "i-soft K",
    0x51: "i-soft K SAFE+",
    0x52: "Softwell KP",
    0x53: "i-soft",
    0x54: "i-soft K",
    0x55: "i-soft TGA",
    0x56: "i-soft SAFE",
    0x57: "i-soft SAFE+",
    0x58: "i-soft Pro",
    0x59: "Softwell P",
    0x5A: "Softwell K",
    0x5B: "QuickSoft M",
    0x5C: "QuickSoft P",
    0x5D: "ScanSoft M",
    0x5E: "ScanSoft P",
    0x5F: "FineSky WHS C",
    0x60: "FineSky WHS P",
    0x61: "QuickSoft CD",
    0x62: "Softwell KP",
    0x63: "Softwell S",
    0x64: "Softwell KS",
    0x65: "OptiLine Z",
    0x66: "OptiLine E",
    0x67: "i-soft K SAFE+",
    0x68: "ZEWA / PROM-i-SAFE",
    0x6A: "Aqua Tenera E",
    0x6B: "Aqua Tenera D",
}
