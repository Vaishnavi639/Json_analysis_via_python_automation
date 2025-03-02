import json
from datetime import datetime
from collections import defaultdict

# Load the JSON file
with open("buckets.json", "r") as file:
    data = json.load(file)

# Ensure the JSON structure is correct
if not isinstance(data, dict) or "buckets" not in data:
    raise ValueError("Invalid JSON format! Ensure the JSON file contains a 'buckets' key.")

buckets = data["buckets"]  # Extract the list of buckets

# Constants
COST_PER_GB = 0.023  # Example S3 standard storage cost per GB
ARCHIVE_THRESHOLD = 50
DELETE_THRESHOLD = 100
DAYS_UNUSED_DELETE = 20
DAYS_UNUSED_LARGE_BUCKETS = 90

# Get today's date
today = datetime.today()

# Generate a timestamped report file
timestamp = today.strftime("%Y-%m-%d_%H-%M-%S")
report_filename = f"s3_report_{timestamp}.txt"

# Initialize cost reports
cost_by_region = defaultdict(float)
cost_by_team = defaultdict(float)

# Lists for recommendations
cleanup_recommendations = []
deletion_queue = []
archive_candidates = []

# Helper function to calculate days unused
def days_unused(created_on):
    created_date = datetime.strptime(created_on, "%Y-%m-%d")
    return (today - created_date).days

# Writing report to file
with open(report_filename, "w") as report_file:
    def log(message):
        """Write message to file and print to console."""
        print(message)
        report_file.write(message + "\n")

    log("\n=== S3 Bucket Analysis Report ===\n")

    # Print bucket summaries
    log("\n--- Bucket Summary ---")
    for bucket in buckets:
        if not isinstance(bucket, dict):
            log(f"ERROR: Invalid bucket format -> {bucket}")
            continue

        name = bucket.get("name", "Unknown")
        region = bucket.get("region", "Unknown")
        size = bucket.get("sizeGB", 0)  # Fix: Use "sizeGB" instead of "size_gb"
        versioning = "Enabled" if bucket.get("versioning", False) else "Disabled"
        created_on = bucket.get("createdOn", "Unknown")
        team = bucket.get("tags", {}).get("team", "Unknown")  # Extract team from tags

        log(f"Name: {name}, Region: {region}, Size: {size}GB, Versioning: {versioning}, Created On: {created_on}")

        # Track costs
        cost_by_region[region] += size * COST_PER_GB
        cost_by_team[team] += size * COST_PER_GB

        # Identify large, unused buckets
        if size > 80 and days_unused(created_on) > DAYS_UNUSED_LARGE_BUCKETS:
            log(f"  ⚠️ {name} is unused for 90+ days and >80GB. Consider deletion.")

        # Recommendations
        if size > ARCHIVE_THRESHOLD:
            cleanup_recommendations.append(name)

        if size > DELETE_THRESHOLD and days_unused(created_on) > DAYS_UNUSED_DELETE:
            deletion_queue.append(name)

        if size > DELETE_THRESHOLD and days_unused(created_on) > DAYS_UNUSED_LARGE_BUCKETS:
            archive_candidates.append(name)

    # Print cost report
    log("\n--- Cost Report by Region ---")
    for region, cost in cost_by_region.items():
        log(f"Region: {region}, Total Cost: ${cost:.2f}")

    log("\n--- Cost Report by Team ---")
    for team, cost in cost_by_team.items():
        log(f"Team: {team}, Total Cost: ${cost:.2f}")

    # Print cleanup recommendations
    log("\n--- Cleanup Recommendations ---")
    for bucket in cleanup_recommendations:
        log(f"Bucket: {bucket} (Consider cleanup)")

    # Print deletion queue
    log("\n--- Deletion Queue ---")
    for bucket in deletion_queue:
        log(f"Bucket: {bucket} (Flagged for deletion)")

    # Print final deletion list and archival recommendations
    log("\n--- Final Deletion List ---")
    for bucket in deletion_queue:
        log(f"Delete: {bucket}")

    log("\n--- Archival Recommendations (Move to Glacier) ---")
    for bucket in archive_candidates:
        log(f"Archive: {bucket}")

# Notify user about report creation
print(f"\n✅ Report saved as: {report_filename}")

