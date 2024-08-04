import base64
from dotenv import load_dotenv
from email.message import EmailMessage
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os.path


def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    creds = None
    path_to_sa_key = "gmail-api-client-creds.json"
    if os.path.exists(path_to_sa_key):
        creds = service_account.Credentials.from_service_account_file(
            path_to_sa_key, scopes=["https://mail.google.com/"]
        ).with_subject(os.environ.get("EMAIL_SUBJECT"))

    try:
        service = build("gmail", "v1", credentials=creds)
        message = EmailMessage()

        message.set_content("test message body")

        message["To"] = os.environ.get("EMAIL_SUBJECT")
        message["From"] = os.environ.get("EMAIL_SUBJECT")
        message["Subject"] = "test message subject"

        # encoded message
        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {"raw": encoded_message}
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
    except HttpError as error:
        print(f"An error occurred: {error}")
        send_message = None

    return send_message


if __name__ == "__main__":
    load_dotenv()
    main()
