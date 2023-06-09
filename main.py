#!/usr/bin/env python3

import json
import logging
import os
import redis
import requests
import semver
import sys
from prettytable import PrettyTable

# Create a logger
logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("terraform_versions")

# Checks:
try:
    webhook_url = os.environ["SLACK_WEBHOOK_URL"]
except KeyError:
    logger.error("The SLACK_WEBHOOK_URL environment variable is required.")
    logger.error(
        "Please pass it using the '-e' flag when running the Docker container:"
    )
    logger.error(
        "    docker run -e SLACK_WEBHOOK_URL=$SLACK_WEBHOOK_URL your_image_name"
    )
    exit(1)

# Define a list of provider names to check
providers = [
    "hashicorp/archive",
    "hashicorp/aws",
    "hashicorp/helm",
    "hashicorp/http",
    "hashicorp/kubernetes",
    "hashicorp/null",
    "hashicorp/random",
    "hashicorp/tls",
    "netskopeoss/netskope",
    "strongdm/sdm",
]

# Set the webhook URL for your Slack app
webhook_url = os.environ["SLACK_WEBHOOK_URL"]
# Connect to Redis
redis_client = redis.Redis(
    host=os.environ["REDIS_HOSTNAME"], port=os.environ["REDIS_PORT"]
)

# Create a table to store the provider names and versions
table = PrettyTable()
table.field_names = ["Provider", "Previous Version", "Current Version"]

# Create a dictionary to store the current version of all providers
current_versions = {}

# Iterate over the list of providers
updated_providers = []
for provider in providers:
    # Get the current version from the Terraform registry
    url = f"https://registry.terraform.io/v1/providers/{provider}/versions"
    response = requests.get(url)
    if response.status_code == 200:
        data = json.loads(response.content.decode("utf-8"))
        versions = data["versions"]
        latest_version = max(
            versions, key=lambda x: semver.VersionInfo.parse(x["version"])
        )
        current_version = latest_version["version"]

        # Get the previous version from Redis
        previous_version = redis_client.get(provider)
        if previous_version is not None:
            previous_version = previous_version.decode("utf-8")

        # Check if the current version is different from the previous version
        if current_version != previous_version:
            table.add_row([provider, previous_version, current_version])
            updated_providers.append(provider)

            # Update the previous version in Redis
            redis_client.set(provider, current_version)

            # Log the change
            logger.info(f"{provider}: {previous_version} -> {current_version}")
        else:
            logger.info(f"{provider}: {previous_version} is up to date.")

    else:
        logger.error(f"Failed to fetch the URL for {provider}.")

    # Add the current version to the dictionary
    current_versions[provider] = current_version

# Sort the table by provider name
table.sortby = "Provider"

# Construct the message and send it to Slack
message = f"*New version available for the following Terraform providers:*\n```{table}```\n\n*Current versions of all providers:*\n\n"
for provider, version in sorted(current_versions.items()):
    message += f"{provider}: {version}\n"

data = {"text": message}
headers = {"Content-Type": "application/json"}
response = requests.post(webhook_url, data=json.dumps(data), headers=headers)
if response.ok:
    logger.info("Message sent to Slack.")
else:
    logger.error("Error sending message to Slack.")
