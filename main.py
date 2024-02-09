import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/gmail.readonly"]


def get_message_details(service, message_id):
    message = (
        service.users()
        .messages()
        .get(userId="me", id=message_id, format="full")
        .execute()
    )
    headers = message["payload"]["headers"]
    sender = [header["value"] for header in headers if header["name"] == "From"][0]
    subject = [header["value"] for header in headers if header["name"] == "Subject"][0]
    return {"sender": sender, "subject": subject}


def get_unique_senders(service, message):
    unique_senders = set()

    for mess in message:
        message_data = (
            service.users()
            .messages()
            .get(userId="me", id=mess["id"], format="full")
            .execute()
        )
        for header in message_data["payload"]["headers"]:
            if header["name"] == "From":
                if header["value"] not in unique_senders:
                    unique_senders.add(header["value"])

    return unique_senders


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

        message = service.users().messages().list(userId="me").execute().get("messages")

        # messages = []
        # Getting sender and subject of the message
        # for mess in message:
        #     message_id = mess["id"]
        #     message_details = get_message_details(service, message_id)
        #     messages.append(message_details)

        print("Unique senders:", get_unique_senders(service, message))

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
