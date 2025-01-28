# gmail-api-client

A generic emailing system that use GMail Workspace API to send emails.

It listens to a Redis queue of emails to send and sends them using the Gmail API. It also takes into account whatever Workspace plan rate limits for sending emails are in place.

The expected format of queued emails is a JSON object with the following fields:

- `to`: the email address to send the email to
- `subject`: the subject of the email
- `message`: the body of the email

## pre requisites

We'll assume you run Ubuntu 24 and Python 3.12.

- have Google Workspace enabled
- have a GCP project with the Gmail API, the Google Cloud Logging, and the Error Reporting APIs enabled
- be the administrator of both the Google Workspace and the GCP project
- Redis installed

## setup

- create a service account following [these instructions](https://developers.google.com/workspace/guides/create-credentials?authuser=1#service-account); however do not assign it any role yet
- add yourself the role of Organization Policy Administrator in the GCP (in the IAM, at organization level)
- allow for the creation of service accounts JSON keys within project GCP Console IAM -> Organization policies -> search for `iam.disableServiceAccountKeyCreation` and disable it
- create the [JSON key for the service account](https://developers.google.com/workspace/guides/create-credentials?authuser=1#create_credentials_for_a_service_account) and download the JSON key and save it in the root of this project with the name `gcp-creds.json` (gitignored)
- add the service account [domain wide delegation](https://developers.google.com/workspace/guides/create-credentials?authuser=1#optional_set_up_domain-wide_delegation_for_a_service_account) with the scope `https://mail.google.com/`
- the service account also needs to have the following permissions for error reporting and logging:

  - `errorreporting.errorEvents.create`
  - `logging.logEntries.create`

- create a virtual environment with `python3 -m venv venv` and activate it with `source venv/bin/activate`
- install the dependencies with `pip install -r requirements.txt`
- `cp .env.example .env` and fill in the environment variables with the relevant values
- run the app with `python3 app.py`

Now that everything is working, you'll want to create a service for the app, so that it can run in the background and restart automatically in case of a crash:

- `sudo nano /etc/systemd/system/gmail_api_client.service` and add the following content:

```
[Unit]
Description=GMail API Client
After=network.target

[Service]
User=$USER
WorkingDirectory=/gmail_api_client/path
ExecStart=/gmail_api_client/path/venv/bin/python3 /gmail_api_client/path/app.py
Restart=always
RestartSec=5
Environment="PATH=/gmail_api_client/path/venv/bin"

# system fully booted and network is up
[Install]
WantedBy=multi-user.target
```

(replace user and paths with your own)

After that, let's start the service and check that everything works as expected:

```bash
sudo systemctl daemon-reload
sudo systemctl start gmail_api_client
sudo systemctl enable gmail_api_client
sudo systemctl status gmail_api_client
```

... you can of course rename the service `gmail_api_client` to whatever you want.