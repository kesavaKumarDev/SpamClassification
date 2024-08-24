import os
import tkinter as tk
from tkinter import messagebox
from googleapiclient.discovery import build
import threading
import time
import re
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow



import joblib
import re
from sklearn.feature_extraction.text import TfidfVectorizer

# Load the trained model
model = joblib.load('model.pkl')

# Load the same vectorizer used during training
vectorizer = joblib.load('tfidf_vectorizer.pkl')  # Example if using Tfidf


# Define the scope for modifying emails
SCOPES = ['https://www.googleapis.com/auth/gmail.modify']


class EmailClassifierApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Automated Email Classifier")

        self.start_button = tk.Button(root, text="Start Classifying", command=self.start_classification)
        self.start_button.pack()

        self.status_label = tk.Label(root, text="Status: Not started")
        self.status_label.pack()

    def start_classification(self):
        self.status_label.config(text="Status: Running")
        threading.Thread(target=self.classify_emails).start()

    def classify_emails(self):
        while True:
            # Connect to Gmail and fetch emails
            service = authenticate_gmail()
            messages = get_unread_emails(service)

            for msg in messages:
                content = get_email_content(service, msg['id'])  # Extract the 'id' key
                label = classify_email(content)
                update_email_label(service, msg['id'], label)


            time.sleep(60)  # Wait for a minute before checking again

# Placeholder functions (you'd replace these with your actual functions)
def authenticate_gmail():
    creds = None
    # Load credentials from file if they exist
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If no valid credentials, let the user log in
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for future use
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('gmail', 'v1', credentials=creds)

service = authenticate_gmail()
    

def get_unread_emails(service):
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q="is:unread").execute()
    messages = results.get('messages', [])
    return messages

def get_email_content(service, message_id):
    message = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    content = ''
    if 'payload' in message and 'parts' in message['payload']:
        for part in message['payload']['parts']:
            if part['mimeType'] == 'text/plain':
                content = part['body']['data']
    return content

def preprocess_content(content):
    # Example preprocessing steps
    content = re.sub(r'\W', ' ', content)  # Remove special characters
    content = content.lower()  # Convert to lowercase
    return content

def classify_email(content):
    # Preprocess the email content
    processed_content = preprocess_content(content)
    
    # Convert content to vector (if using a vectorizer like Tfidf)
    content_vector = vectorizer.transform([processed_content])
    
    # Predict using the trained model
    prediction = model.predict(content_vector)
    
    # Map the boolean prediction to "Spam" or "Ham"
    if prediction[0]:
        return "Spam"
    else:
        return "Ham"

def update_email_label(service, message_id, label):
    if label == "Spam":
        label_id = 'SPAM'
    else:
        label_id = 'INBOX'  # Keep it in Inbox or add a custom label
    service.users().messages().modify(
        userId='me', id=message_id, body={'addLabelIds': [label_id]}).execute()


if __name__ == "__main__":
    root = tk.Tk()
    app = EmailClassifierApp(root)
    root.mainloop()
    
    


