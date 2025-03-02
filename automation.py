import json
from datetime import datetime, timedelta
from collections import defaultdict

# Load the JSON file
with open("buckets.json", "r") as file:
    buckets = json.load(file)

# Define cost per GB (example: $0.023 per GB for standard S3)
COST_PER_GB = 0.023
ARCHIVE_THRESHOLD = 50
DELETE_THRESHOLD = 100
DAYS_UNUSED_DELETE = 20
DAYS_UNUSED_LARGE_BUCKETS = 90

# Get today's date
today = datetime.today()

# Initialize cost reports
cost_by_region = defaultdict(float)
cost_by_department = defaultdict(float)

# Lists for different categories
cleanup_recommendations = []
deletion_queue = []
archive_candidates = []

# Helper function to calculate days unused
def days_unused(last_accessed):
    last_accessed_date = datetime.strptime(last_accessed, "%Y-%m-%d")
    return (today - last_accessed_date).days

# Print bucket summaries
print("\n--- Bucket Summary ---")
for bucket in buckets:
    name = bucket["name"]
    region = bucket["region"]
    size = bucket["size_gb"]
    versioning = "Enabled" if bucket["versioning"] else "Disabled"
    last_accessed = bucket["last_accessed"]
    
    print(f"Name: {name}, Region: {region}, Size: {size}GB, Versioning: {versioning}")

    # Track costs
    cost_by_region[region] += size * COST_PER_GB
    cost_by_department[bucket["department"]] += size * COST_PER_GB

    # Identify large, unused buckets
    if size > 80 and days_unused(last_accessed) > DAYS_UNUSED_LARGE_BUCKETS:
        print(f"  ⚠️ {name} is unused for 90+ days and >80GB. Consider deletion.")

    # Recommendations
    if size > ARCHIVE_THRESHOLD:
        cleanup_recommendations.append(name)

    if size > DELETE_THRESHOLD and days_unused(last_accessed) > DAYS_UNUSED_DELETE:
        deletion_queue.append(name)

    if size > DELETE_THRESHOLD and days_unused(last_accessed) > DAYS_UNUSED_LARGE_BUCKETS:
        archive_candidates.append(name)

# Print cost report
print("\n--- Cost Report by Region ---")
for region, cost in cost_by_region.items():
    print(f"Region: {region}, Total Cost: ${cost:.2f}")

print("\n--- Cost Report by Department ---")
for department, cost in cost_by_department.items():
    print(f"Department: {department}, Total Cost: ${cost:.2f}")

# Print cleanup recommendations
print("\n--- Cleanup Recommendations ---")
for bucket in cleanup_recommendations:
    print(f"Bucket: {bucket} (Consider cleanup)")

# Print deletion queue
print("\n--- Deletion Queue ---")
for bucket in deletion_queue:
    print(f"Bucket: {bucket} (Flagged for deletion)")

# Print final deletion list and archival recommendations
print("\n--- Final Deletion List ---")
for bucket in deletion_queue:
    print(f"Delete: {bucket}")

print("\n--- Archival Recommendations (Move to Glacier) ---")
for bucket in archive_candidates:
    print(f"Archive: {bucket}")
