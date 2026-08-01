# Constants for Chicago Geo-Mocking Utility
# These values are tied to the trained model distribution and must not be placed in .env
# as they shouldn't change across environments unless the model is retrained.

ANCHOR_LAT = 41.8781
ANCHOR_LON = -87.6298

# Bounding box of Chicago data used in the model
BBOX_MIN_LAT = 41.6445
BBOX_MAX_LAT = 42.0230
BBOX_MIN_LON = -87.9401
BBOX_MAX_LON = -87.5240

# Risk thresholds mapping (0-100 scale)
RISK_THRESHOLD_LOW_MAX = 70
RISK_THRESHOLD_MEDIUM_MAX = 82      # >82 = HIGH
REROUTE_TRIGGER_THRESHOLD = 83      # Threshold that triggers a reroute alert for active trips
