"""Constants for the JUDO integration."""
from __future__ import annotations

DOMAIN = "judo"
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "Connectivity"
DEFAULT_SCAN_INTERVAL = 300  # seconds
MIN_API_GAP = 11.0  # seconds between API calls (firmware rate-limit)
REQUEST_TIMEOUT = 15  # seconds

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
REG_LEAKAGE_PROTECTION_ON = "3C00"
REG_LEAKAGE_PROTECTION_OFF = "3C01"
REG_VACATION_MODE_ON = "4100"
REG_VACATION_MODE_OFF = "4200"

# Known device types (FF00 value -> human-readable name)
DEVICE_TYPES = {
    0x33: "Softwell P",
    0x34: "Softwell K",
    0x42: "Softwell S",
    0x43: "Softwell KS",
    0x44: "Softwell C",
    0x67: "i-soft K",
    0x68: "i-soft K SAFE+",
    0x69: "i-soft TGA",
    0x72: "i-soft Pro",
    0x73: "i-soft Pro SAFE+",
}
