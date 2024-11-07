from flask import Flask, redirect, request, session
import requests
import json
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your-secret-key"  # Change this to a secure secret key

# Instagram API Configuration
CLIENT_ID = "your-client-id"
CLIENT_SECRET = "your-client-secret"
REDIRECT_URI = "http://your-domain.com/auth/instagram/callback"
INSTAGRAM_GRAPH_URL = "https://graph.instagram.com/v12.0"


@app.route("/auth/instagram")
def instagram_auth():
    """Initiate Instagram OAuth flow"""
    auth_url = f"https://api.instagram.com/oauth/authorize?client_id={CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=instagram_manage_messages&response_type=code"
    return redirect(auth_url)


@app.route("/auth/instagram/callback")
def instagram_callback():
    """Handle Instagram OAuth callback"""
    code = request.args.get("code")

    # Exchange code for access token
    token_url = "https://api.instagram.com/oauth/access_token"
    response = requests.post(
        token_url,
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI,
            "code": code,
        },
    )

    token_data = response.json()
    session["instagram_access_token"] = token_data["access_token"]
    return "Authentication successful!"


def send_message(recipient_id, message_text):
    """Send a message to an Instagram user"""
    url = f"{INSTAGRAM_GRAPH_URL}/me/messages"

    response = requests.post(
        url,
        params={"access_token": session["instagram_access_token"]},
        json={"recipient": {"id": recipient_id}, "message": {"text": message_text}},
    )

    return response.json()


def get_messages():
    """Retrieve recent messages from Instagram inbox"""
    url = f"{INSTAGRAM_GRAPH_URL}/me/conversations"

    response = requests.get(
        url,
        params={
            "access_token": session["instagram_access_token"],
            "fields": "participants,messages{from,message,created_time}",
        },
    )

    return response.json()


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handle incoming messages webhook"""
    data = request.json

    # Verify webhook signature here

    # Process incoming message
    if "entry" in data:
        for entry in data["entry"]:
            for messaging in entry.get("messaging", []):
                sender_id = messaging["sender"]["id"]
                message_text = messaging.get("message", {}).get("text")

                if message_text:
                    # Auto-reply example
                    send_message(sender_id, f"Thanks for your message: {message_text}")

    return "OK", 200


if __name__ == "__main__":
    app.run(debug=True)
