import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from message_details import get_unique_senders

# If modifying these scopes, delete the file token.json.
# https://developers.google.cn/gmail/api/auth/scopes?hl=en#:~:text=Gmail%20API%20scopes%20To%20define%20the%20level%20of,data%20it%20accesses%2C%20and%20the%20level%20of%20access.
SCOPES = [
    "https://www.googleapis.com/auth/gmail.settings.basic",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def main():
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        # Create gmail api client
        service = build("gmail", "v1", credentials=creds)

        messages = (
            service.users().messages().list(userId="me").execute().get("messages")
        )

        # Change filter criteria
        # https://developers.google.com/gmail/api/reference/rest/v1/users.settings.filters#Filter
        filter_content = {
            "criteria": {"from": "example123@gmail.com"},
            "action": {
                "addLabelIds": ["TRASH"],
                "removeLabelIds": ["INBOX"],
            },
        }

        result = (
            service.users()
            .settings()
            .filters()
            .create(userId="me", body=filter_content)
            .execute()
        )

        print(f'Created filter with id: {result.get("id")}')

        print("Unique senders:", get_unique_senders(service, messages))

        # Getting project root directory
        cwd = os.getcwd()
        # Deleting token.json file after successful execution
        os.remove(f"{cwd}/token.json")

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
