from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials, firestore

from .settings import settings

firebase_app: Optional[firebase_admin.App] = None
firestore_client = None


def initialize_firebase() -> Optional[firebase_admin.App]:
    global firebase_app
    
    # Return existing app if already initialized
    if firebase_app:
        return firebase_app

    # Check if any apps already exist
    existing = firebase_admin._apps
    if existing:
        firebase_app = firebase_admin.get_app()
        return firebase_app

    options = {}
    if settings.firebase_project_id:
        options["projectId"] = settings.firebase_project_id

    credentials_json = getattr(settings, "firebase_credentials_json", None)
    try:
        # If a JSON string is provided (useful when stored in secrets), prefer it
        if credentials_json:
            try:
                import json

                cred_dict = json.loads(credentials_json)
                print("Initializing Firebase with credentials from JSON string")
                cred = credentials.Certificate(cred_dict)
                firebase_app = firebase_admin.initialize_app(cred, options or None)
            except Exception as e:
                print(f"Failed to initialize from JSON credentials: {e}")
                # fall through to try file path or default
        if not firebase_app:
            print("Initializing Firebase with default credentials")
            firebase_app = firebase_admin.initialize_app(options=options or None)
        
        print(f"Firebase initialized successfully: {firebase_app.project_id}")
    except Exception as e:
        print(f"Firebase initialization failed: {e}")
        firebase_app = None
    
    return firebase_app


def get_firestore_client():
    global firestore_client
    
    if firestore_client:
        return firestore_client

    app = initialize_firebase()
    if not app:
        print("Firebase app not available, Firestore client will be None")
        return None

    try:
        firestore_client = firestore.client(app)
        print("Firestore client created successfully")
    except Exception as e:
        print(f"Failed to create Firestore client: {e}")
        firestore_client = None
    
    return firestore_client


async def verify_firebase_token(token: str) -> Optional[dict]:
    app = initialize_firebase()
    if not app:
        print("Firebase app not available for token verification")
        return None

    try:
        decoded_token = auth.verify_id_token(token, app=app)
        print("Firebase token verified successfully")
        return decoded_token
    except Exception as e:
        print(f"Firebase token verification failed: {e}")
        return None
