# Gmail Integration Setup Guide

This guide explains how to set up Gmail integration for the Claims Triage System to automatically fetch and process claim-related emails.

## Overview

The Gmail integration allows the system to:
- Scan your primary Gmail inbox for claim-related emails
- Identify emails using keywords like "claim," "insurance," "accident," "injury," etc.
- Convert email content and attachments into PDFs
- Process them through the automated claims triage pipeline
- Mark processed emails as read and add a "CLAIM_PROCESSED" label

## Prerequisites

- Google Cloud Console account
- MongoDB running locally or remotely
- Python 3.9+ with all backend dependencies installed
- Backend server running

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Select a project" → "New Project"
3. Enter project name: `Claims Triage Gmail`
4. Click "Create"

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API" and click "Enable"

## Step 3: Configure OAuth Consent Screen

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select "External" (or "Internal" if using Google Workspace)
3. Click "Create"

### App Information
- **App name**: `Claims Triage System`
- **User support email**: Your email
- **Developer contact email**: Your email

### Scopes
Click "Add or Remove Scopes" and add:
- `https://www.googleapis.com/auth/gmail.readonly`
- `https://www.googleapis.com/auth/gmail.modify`

Click "Save and Continue"

### Test Users (for External apps)
Add your email address as a test user during development

Click "Save and Continue"

## Step 4: Create OAuth 2.0 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Select "Web application"

### Configuration
- **Name**: `Claims Triage Gmail Client`
- **Authorized JavaScript origins**:
  - `http://localhost:8080`
  - `http://localhost:3030`
- **Authorized redirect URIs**:
  - `http://localhost:8080/api/gmail/callback`

4. Click "Create"
5. Copy the **Client ID** and **Client Secret**

## Step 5: Configure Environment Variables

1. Open your `.env` file in the backend directory
2. Add the following variables:

```bash
# Gmail API Configuration
GMAIL_CLIENT_ID=your_client_id_from_google_cloud_console
GMAIL_CLIENT_SECRET=your_client_secret_from_google_cloud_console
GMAIL_REDIRECT_URI=http://localhost:8080/api/gmail/callback
```

Replace the placeholder values with your actual credentials from Step 4.

## Step 6: Install Dependencies

If you haven't already, install the Gmail integration dependencies:

```bash
cd backend
pip install -r requirements.txt
```

This will install:
- `google-auth` - Google authentication library
- `google-auth-oauthlib` - OAuth 2.0 support
- `google-auth-httplib2` - HTTP client
- `google-api-python-client` - Gmail API client
- `reportlab` - PDF generation
- `weasyprint` - HTML to PDF conversion
- `beautifulsoup4` - HTML parsing
- `Pillow` - Image processing

## Step 7: Start the Backend Server

```bash
cd backend
python app.py
```

The server should start on `http://localhost:8080`

## Step 8: Test the Integration

### Via Frontend UI

1. Open the frontend at `http://localhost:3030`
2. Navigate to the "Upload Claim" section
3. Click the "Connect Gmail" button in the top-right
4. Complete the OAuth flow in the popup window
5. Grant the required permissions
6. Once connected, the button will change to "Fetch from Gmail"
7. Click "Fetch from Gmail" to preview claim emails
8. Select emails to process

### Via API

#### Check Connection Status
```bash
curl http://localhost:8080/api/gmail/status
```

#### Get Authorization URL
```bash
curl http://localhost:8080/api/gmail/auth-url
```

#### Preview Emails
```bash
curl http://localhost:8080/api/gmail/preview?max_results=10
```

#### Fetch and Process Emails
```bash
curl -X POST http://localhost:8080/api/gmail/fetch
```

#### Disconnect Gmail
```bash
curl -X DELETE http://localhost:8080/api/gmail/disconnect
```

## OAuth Flow

The OAuth flow works as follows:

1. **User clicks "Connect Gmail"** → Frontend requests auth URL from backend
2. **Backend generates auth URL** → Returns URL with OAuth parameters
3. **Popup opens** → User authenticates with Google
4. **User grants permissions** → Google redirects to callback URL
5. **Backend receives code** → Exchanges code for access/refresh tokens
6. **Tokens stored in MongoDB** → In `gmail_tokens` collection
7. **User email retrieved** → Stored with tokens for reference
8. **Frontend notified** → Connection status updated

## Email Detection Keywords

The system searches for emails containing these keywords in the subject line:
- claim
- insurance
- accident
- injury
- policy
- collision
- damage
- incident
- loss
- acord

## Email Processing Flow

1. **Fetch emails** → Gmail API searches primary inbox for matching keywords
2. **Extract content** → Email metadata, body (HTML/text), and attachments
3. **Generate PDF** → Email content + attachments merged into single PDF
4. **Save to uploads/** → PDF saved with timestamp and subject in filename
5. **Pathway watches** → Detects new PDF and triggers processing pipeline
6. **Mark as read** → Email marked as read in Gmail
7. **Add label** → "CLAIM_PROCESSED" label added to email

## Troubleshooting

### Error: "Gmail not connected"
- Ensure you've completed the OAuth flow
- Check that tokens are stored in MongoDB (`gmail_tokens` collection)
- Try disconnecting and reconnecting

### Error: "Invalid credentials"
- Verify `GMAIL_CLIENT_ID` and `GMAIL_CLIENT_SECRET` in `.env`
- Ensure credentials match those in Google Cloud Console
- Check that OAuth 2.0 client is enabled

### Error: "Access denied"
- Ensure Gmail API is enabled in Google Cloud Console
- Check that required scopes are configured
- For External apps, ensure your email is added as a test user

### Error: "Redirect URI mismatch"
- Verify `GMAIL_REDIRECT_URI` matches authorized redirect URI in Google Cloud Console
- Default should be `http://localhost:8080/api/gmail/callback`

### No emails found
- Check that you have unread emails in your primary inbox
- Verify emails contain claim-related keywords in subject
- Try using broader search terms (modify `CLAIM_KEYWORDS` in `gmail_service.py`)

### PDF generation fails
- Ensure `reportlab` and `weasyprint` are installed
- Check that attachments are in supported formats (JPG, PNG, PDF)
- Review backend logs for specific errors

## Security Considerations

- **Tokens are stored encrypted** in MongoDB
- **Read-only access** to emails (except for labels)
- **No email deletion** - System only reads and modifies labels
- **OAuth 2.0** - Industry-standard authentication
- **Refresh tokens** - Automatic token renewal
- **Scoped permissions** - Only Gmail access, no other Google services

## Production Deployment

For production deployment:

1. **Update OAuth Consent Screen** to "Published" status
2. **Update Authorized Origins/Redirect URIs** with production URLs
3. **Use environment variables** for all sensitive data
4. **Enable HTTPS** for all endpoints
5. **Implement rate limiting** on Gmail API calls
6. **Set up monitoring** for failed OAuth flows
7. **Configure token rotation** for security
8. **Add audit logging** for email processing

## MongoDB Collections

### `gmail_tokens`
Stores OAuth tokens for Gmail integration:
- `user_email` - Email address of connected account
- `token` - Access token
- `refresh_token` - Refresh token
- `token_uri` - Token endpoint URI
- `client_id` - OAuth client ID
- `client_secret` - OAuth client secret
- `scopes` - Granted scopes
- `expiry` - Token expiration timestamp
- `created_at` - Connection timestamp
- `updated_at` - Last update timestamp

## API Endpoints

### `GET /api/gmail/auth-url`
Generate OAuth authorization URL
- **Returns**: `{ auth_url, state }`

### `GET /api/gmail/callback?code=<code>`
Handle OAuth callback
- **Query Params**: `code` (required), `state` (optional)
- **Returns**: `{ message, user_email, redirect }`

### `GET /api/gmail/status`
Check Gmail connection status
- **Returns**: `{ connected, user_email?, connected_at? }`

### `GET /api/gmail/preview?max_results=10`
Preview claim emails without processing
- **Query Params**: `max_results` (default: 10)
- **Returns**: `{ emails[], total }`

### `POST /api/gmail/fetch`
Fetch and process claim emails
- **Query Params**: `max_results` (default: 10), `unread_only` (default: true)
- **Returns**: `{ message, emails_found, emails_processed, claim_ids[], emails[] }`

### `DELETE /api/gmail/disconnect`
Disconnect Gmail account
- **Returns**: `{ message }`

## Support

For issues or questions:
1. Check backend logs for detailed error messages
2. Verify all environment variables are set correctly
3. Ensure MongoDB is running and accessible
4. Review Google Cloud Console for API quota/errors
5. Check that all dependencies are installed correctly
