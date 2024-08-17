#!/usr/bin/env python3

import base64
from dotenv import load_dotenv
from email.message import EmailMessage
from google.oauth2 import service_account
from googleapiclient.discovery import build
import json
import os.path
import redis
import time
from ylogging.lib import get_gcp_error_reporting_logging_clients, get_structured_log_msg

abs_path = os.path.dirname(os.path.abspath(__file__))


def send_email(to: str, subject: str, message: str):
    creds = None
    path_to_sa_key = "gcp-creds.json"
    if os.path.exists(path_to_sa_key):
        creds = service_account.Credentials.from_service_account_file(
            path_to_sa_key, scopes=["https://mail.google.com/"]
        ).with_subject(os.environ.get("EMAIL_FROM_ADDRESS"))
    else:
        raise Exception("no Google credentials found")

    service = build("gmail", "v1", credentials=creds)
    message_obj = EmailMessage()

    message_obj.set_content(message)

    message_obj["To"] = to
    message_obj["From"] = os.environ.get("EMAIL_FROM_ADDRESS")
    message_obj["Subject"] = subject

    # encoded message
    encoded_message = base64.urlsafe_b64encode(message_obj.as_bytes()).decode()

    create_message = {"raw": encoded_message}
    send_message = (
        service.users().messages().send(userId="me", body=create_message).execute()
    )
    return send_message


if __name__ == "__main__":
    load_dotenv(f"{abs_path}/.env")

    email_queue_name = "email_queue"
    service_name = "gmail-api-client"

    error_reporting_client, logger = get_gcp_error_reporting_logging_clients(
        service_name
    )

    logger.log_struct(
        get_structured_log_msg(service_name, "starting emailing service", None),
        severity="INFO",
    )

    email_queue_day_counter_key = "email_queue_day_counter"

    while True:
        try:
            # connect to redis
            redis_client = redis.Redis(
                host=os.environ.get("REDIS_HOST"),
                port=int(os.environ.get("REDIS_PORT")),
                db=int(os.environ.get("REDIS_DATABASE")),
            )

            emails = redis_client.lrange(email_queue_name, 0, -1)

            for email_data in emails:
                email = json.loads(email_data)
                sent = send_email(email["to"], email["subject"], email["message"])
                logger.log_struct(
                    get_structured_log_msg(
                        service_name, "email sent with id", sent["id"]
                    ),
                    severity="INFO",
                )
                # removing the email from the queue
                redis_client.lpop(email_queue_name)
                # increment the day counter
                num_emails_sent = redis_client.incr(email_queue_day_counter_key)
                # get the number of seconds before the end of the day
                SECONDS_IN_A_DAY = 86400
                seconds_until_end_of_day = (
                    SECONDS_IN_A_DAY - time.time() % SECONDS_IN_A_DAY
                )
                # handle the midnight edge case + reset the counter
                if seconds_until_end_of_day == SECONDS_IN_A_DAY:
                    seconds_until_end_of_day = 0
                    redis_client.set(email_queue_day_counter_key, 0)
                wait_time = round(
                    seconds_until_end_of_day
                    / (
                        int(os.environ.get("WORKSPACE_PLAN_GMAIL_DAILY_LIMIT"))
                        - num_emails_sent
                    )
                )
                logger.log_struct(
                    get_structured_log_msg(
                        service_name,
                        "waiting for next email",
                        json.dumps(
                            {
                                "seconds_until_end_of_day": seconds_until_end_of_day,
                                "num_emails_sent": num_emails_sent,
                                "wait_time": wait_time,
                                "workspace_plan_gmail_daily_limit": int(
                                    os.environ.get("WORKSPACE_PLAN_GMAIL_DAILY_LIMIT")
                                ),
                            }
                        ),
                    ),
                    severity="INFO",
                )
                if wait_time == 0:
                    # minimum wait time is 0.1 seconds (to not overload Redis)
                    wait_time = 0.1
                # wait x seconds before sending the next email
                time.sleep(wait_time)

        except Exception as e:
            logger.log_struct(
                get_structured_log_msg(service_name, "error sending email", str(e)),
                severity="ERROR",
            )
            error_reporting_client.report_exception()
