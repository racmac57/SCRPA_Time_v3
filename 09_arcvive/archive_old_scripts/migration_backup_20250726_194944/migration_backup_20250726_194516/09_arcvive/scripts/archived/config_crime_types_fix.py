# Add this section to your config.py file right after the CRIME_FOLDER_MAPPING section:

# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

# For existing main.py compatibility
CRIME_TYPES = list(CRIME_FOLDER_MAPPING.keys())

# This creates: ["MV Theft", "Burglary - Auto", "Burglary - Comm & Res", "Robbery", "Sexual Offenses"]