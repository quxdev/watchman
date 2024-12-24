import logging
import os

import boto3
import requests
from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from mail import AWSEmail

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
service_name = os.getenv("SERVICE_NAME", "Watchman")
sender_email = os.environ.get("SENDER_EMAIL")
recipient_emails = os.environ.get("RECIPIENT_EMAILS", "").split(",")
regions = os.getenv("REGIONS_TO_CHECK", "us-east-1,ap-south-1").split(",")


def get_running_instances(region):
    """Retrieve running instances and their 'known_as' tag values in a specified region."""
    ec2 = boto3.client("ec2", region_name=region)
    try:
        response = ec2.describe_instances(
            Filters=[{"Name": "instance-state-name", "Values": ["running"]}]
        )
        instances = response["Reservations"]
        instance_info = []
        for reservation in instances:
            for instance in reservation["Instances"]:
                instance_id = instance["InstanceId"]
                public_dns = instance.get("PublicDnsName", "")
                known_as_tag = next(
                    (
                        tag["Value"]
                        for tag in instance.get("Tags", [])
                        if tag["Key"] == "known_as"
                    ),
                    "",
                )
                instance_info.append(
                    {
                        "instance_id": instance_id,
                        "public_dns": public_dns,
                        "known_as": known_as_tag,
                    }
                )
        return instance_info
    except Exception as e:
        logger.error("Error retrieving instances in region %s: %s", region, e)
        return []


def check_url_status(url):
    """Check the status of the URL and return the HTTP status code."""
    try:
        response = requests.get(url, timeout=10)
        logger.info("Response from %s: %s", url, response.status_code)
        return response.status_code
    except requests.RequestException as e:
        logger.error("Error checking URL %s: %s", url, e)
        return None


def check_instances():
    """Check the running status of instances across specified regions and gather tag data."""
    success = []
    failure = []
    unknown = []
    servers = []
    for region in regions:
        instances = get_running_instances(region)
        for instance in instances:
            servers.append(instance)

    for server in os.getenv("SERVERS", "").split(","):
        servers.append({"known_as": server})

    for server in servers:
        hostname = server.get("known_as", "")
        parts = hostname.split(".")
        if len(parts) == 2:
            server["domain"] = hostname
            server["subdomain"] = ""
        else:
            server["domain"] = ".".join(parts[-2:])
            server["subdomain"] = ".".join(parts[:-2])

    # Sort the servers list
    sorted_list = sorted(servers, key=lambda x: (x["domain"], x["subdomain"]))

    for server in sorted_list:
        hostname = server["known_as"]

        if hostname:
            url = f"https://{hostname}/"
            status_code = check_url_status(url)
            if status_code == 200:
                linestr = f"<dd>[200] {hostname}</dd>"
                success.append(linestr)
            else:
                status_code = status_code if status_code else "???"
                linestr = f"<dd>[{status_code}] {hostname}</dd>"
                failure.append(linestr)
        else:
            linestr = f"<dd>[???] {hostname}</dd>"
            unknown.append(linestr)

    report = ""
    if success:
        report += "<dt><b>RUNNING!</b></dt>" + "".join(success)

    if failure:
        style = "color: red;"
        if report:
            style += " margin-top: 1rem;"
        report += f'<dt style="{style}"><b>!FAILURE</b></dt>' + "".join(failure)

    if unknown:
        style = "color: orange;"
        if report:
            style += " margin-top: 1rem;"
        report += f'<dt style="{style}"><b>!UNKNOWN</b></dt>' + "".join(unknown)

    if report:
        report = f"<div><dl>{report}</dl></div>"

    return report


def send_email(to_email, subject, body):
    """Send an email using SES."""
    try:
        awsmail = AWSEmail()
        awsmail.sender = sender_email
        awsmail.to = to_email
        awsmail.subject = subject
        awsmail.message = body
        response = awsmail.send()
        logger.info("Email sent successfully to %s: %s", to_email, response)
        return response
    except Exception as e:
        logger.error("Error sending email to %s: %s", to_email, e)
        return None


def lambda_handler(event, context):
    _ = event, context  # Unused
    if not sender_email:
        logger.error("SENDER_EMAIL is not set")
        return {"statusCode": 500, "body": "SENDER_EMAIL is not set"}
    if not recipient_emails:
        logger.error("RECIPIENT_EMAILS is not set")
        return {"statusCode": 500, "body": "RECIPIENT_EMAILS is not set"}
    try:
        report = check_instances()
        subject = f"{service_name}: Services Status Report"
        body = f"""
        <html>
        <body>
          <div>
            {report}
          </div>
        </body>
        </html>
        """

        for recipient in recipient_emails:
            send_email(recipient, subject, body)

        return {"statusCode": 200, "body": "Emails processed successfully"}
    except (NoCredentialsError, PartialCredentialsError) as e:
        logger.error("Error in accessing AWS services: %s", e)
        return {"statusCode": 500, "body": "Error in accessing AWS services"}
    except Exception as e:
        logger.error("Error in Lambda function: %s", e)
        return {"statusCode": 500, "body": "An error occurred"}
