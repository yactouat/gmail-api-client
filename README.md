# gmail-api-client

The emailing client using Google Workspace for the Markets Agent project.

## pre requisites

- have Google Workspace enabled
- have a GCP project with the Gmail API enabled
- be the administrator of both the Google Workspace and the GCP project
- Node.js and NPM installed

## setup

- create a service account following [these instructions](https://developers.google.com/workspace/guides/create-credentials?authuser=1#service-account); however do not assign it any role yet
- add yourself the role of Organization Policy Administrator in the GCP (in the IAM, at organization level)
- allow for the creation of service accounts JSON keys within GCP Console IAM -> Organization policies -> search for `iam.disableServiceAccountKeyCreation` and disable it
- create the [JSON key for the service account](https://developers.google.com/workspace/guides/create-credentials?authuser=1#create_credentials_for_a_service_account) and download the JSON key and save it in the root of this project with the name `gmail-api-client-creds.json` (gitignored)
- add the service account [domain wide delegation](https://developers.google.com/workspace/guides/create-credentials?authuser=1#optional_set_up_domain-wide_delegation_for_a_service_account) with the scope `https://mail.google.com/`
- create a virtual environment with `python3 -m venv venv` and activate it with `source venv/bin/activate`
- `cp .env.example .env` and fill in the environment variables