import os.path
import re

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.discovery import Resource
from googleapiclient.errors import HttpError


# If modifying these scopes, delete the file token.json.
# https://developers.google.cn/gmail/api/auth/scopes?hl=en#:~:text=Gmail%20API%20scopes%20To%20define%20the%20level%20of,data%20it%20accesses%2C%20and%20the%20level%20of%20access.
SCOPES = [
    "https://mail.google.com/",
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/gmail.modify",
]


def get_messages_id_list(service: Resource, messages_list: list) -> list[str]:
    """Extracts a list of message IDs from a provided list of messages.

    Args:
        service: An authorized Gmail API service instance
        messages_list: A list of message dictionaries obtained from the API.

    Returns:
        A list of message IDs corresponding to the provided messages.
    """
    messages_id = []

    for message in messages_list:
        messages_id.append(message["id"])

    return messages_id


def trash_msgs_except_star_label(service: Resource, message_ids: list[str]) -> None:
    """Send to trash messages from Gmail except those with the STARRED label.

    Args:
        service: An authorized Gmail API service instance.
        message_ids: A list of message IDs to send to trash.
    """
    for message_id in message_ids:
        message = service.users().messages().get(userId="me", id=message_id).execute()
        if "STARRED" not in message["labelIds"]:
            service.users().messages().trash(userId="me", id=message_id).execute()
            print(f"Message {message_id} send to trash successfully.")
        else:
            print(f"Skipping message {message_id} as it is starred.")


def extract_emails(senders: set[str]) -> list[str]:
    """
    Extracts email addresses from a set of strings.

    Args:
        senders: A set of strings containing sender name and addresses.

    Returns:
        A list containing the extracted email addresses.
    """
    emails = []
    for text in senders:
        email_match = re.search(r"<(.*?)>", text)  # Extract email within angle brackets
        if email_match:
            email = email_match.group(1)
            emails.append(email)
    return emails


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
        page_token = None

        while True:
            messages = (
                service.users()
                .messages()
                .list(userId="me", maxResults=500, pageToken=page_token)
                .execute()
                .get("messages")
            )

            trash_msgs_except_star_label(
                service, get_messages_id_list(service, messages)
            )

            # Check for the presence of a next page token
            # lastest message on a page contains information does next page exists
            # if page_token does not exist, sets token to 'None'
            page_token = messages[-1].get("nextPageToken", None)

            if not page_token:
                break

        # Getting project root directory
        cwd = os.getcwd()
        # Deleting token.json file after successful execution
        os.remove(f"{cwd}/token.json")

    except HttpError as error:
        print(f"An error occurred: {error}")


if __name__ == "__main__":
    main()
