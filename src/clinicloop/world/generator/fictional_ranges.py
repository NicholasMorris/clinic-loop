"""Fictional identifier ranges for SimClinic.

These ranges define the boundaries for synthetically generated identifiers
such as phone numbers, email domains, and health identifiers. Using fictional
ranges ensures that synthetic data cannot be confused with real data.
"""

# Fictional phone number ranges (national significant numbers)
# Australian fictional range: 0400-0499 (declared fictional)
PHONE_AREA_CODE_FICTIONAL = "0400"
PHONE_AREA_CODE_FICTIONAL_RANGE = range(0, 100)  # 0400-0499

# Fictional email domain
# Using .test TLD which is reserved for testing per RFC 6761
EMAIL_DOMAIN_FICTIONAL = "test.example.com"
EMAIL_LOCAL_CHARS = "abcdefghijklmnopqrstuvwxyz0123456789._"

# Fictional health identifier prefixes
# Using high-number ranges unlikely to conflict with real identifiers
HEALTH_ID_PREFIX_FICTIONAL = "99"
HEALTH_ID_FICTIONAL_RANGE = range(0, 100000)

# Fictional date ranges
# Using dates far in the future to avoid any chance of collision with real data
PATIENT_DOB_YEAR_MIN = 1960
PATIENT_DOB_YEAR_MAX = 2015

# Fictional given and family names
FICTIONAL_GIVEN_NAMES = [
    "Alex", "Blake", "Casey", "Dana", "Evan", "Fiona", "Grayson", "Hannah",
    "Isaac", "Jordan", "Kaylee", "Logan", "Morgan", "Noah", "Olivia", "Parker",
    "Quinn", "Riley", "Sydney", "Taylor", "Upton", "Violet", "Wesley", "Ximena",
]

FICTIONAL_FAMILY_NAMES = [
    "Adams", "Baker", "Clarke", "Davis", "Evans", "Foster", "Graham", "Harris",
    "Ingram", "Jackson", "Kelly", "Lewis", "Martin", "Nelson", "Oliver", "Parker",
    "Quinn", "Roberts", "Smith", "Taylor", "Underwood", "Vaughn", "Wagner", "Young",
]

# Fictional postcodes (Australian format: 4 digits)
FICTIONAL_POSTCODES = [
    "2000", "2010", "2015", "2020", "2025", "3000", "3010", "3015", "3020", "3025",
    "4000", "4010", "4015", "4020", "4025", "5000", "5010", "5015", "5020", "5025",
    "6000", "6010", "6015", "6020", "6025", "7000", "7010", "7015", "7020", "7025",
]

# Fictional street addresses
FICTIONAL_STREETS = [
    "Main Street", "Oak Avenue", "Maple Road", "Elm Lane", "Pine Drive",
    "Birch Court", "Cedar Way", "Willow Path", "Ash Circle", "Walnut Close",
]

# Clinician IDs (C01..C06)
CLINICIAN_IDS = [f"C{i:02d}" for i in range(1, 7)]
