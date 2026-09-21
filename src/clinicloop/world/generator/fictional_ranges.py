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

# Fictional health identifier prefixes
# Using high-number ranges unlikely to conflict with real identifiers
HEALTH_ID_PREFIX_FICTIONAL = "99"
HEALTH_ID_FICTIONAL_RANGE = range(0, 100000)

# Fictional date ranges
# Using dates far in the future to avoid any chance of collision with real data
PATIENT_DOB_YEAR_MIN = 1960
PATIENT_DOB_YEAR_MAX = 2015
