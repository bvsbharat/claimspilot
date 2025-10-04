# Gmail Credentials Setup Guide

This guide explains how to set up Gmail credentials for automatic email fetching using the existing `credentials.json` and `token.json` files.

## Quick Start

The Gmail integration is now using **automatic authentication** with `credentials.json` and `token.json` files. These files have already been copied from the SuperMail project.

### Files Already Configured

- ✅ `backend/credentials.json` - OAuth client credentials
- ✅ `backend/token.json` - Authenticated user token

### How It Works

The system uses **LangChain's GmailToolkit** which automatically:
1. Reads `credentials.json` for OAuth client configuration
2. Reads `token.json` for authenticated user access
3. Connects to Gmail API without requiring popup/manual OAuth flow
4. Automatically refreshes tokens when needed

### Testing the Connection

1. **Start the backend:**
   ```bash
   cd backend
   python app.py
   ```

2. **Check connection status:**
   ```bash
   curl http://localhost:8080/api/gmail/status
   ```

   Expected response if connected:
   ```json
   {
     "connected": true,
     "user_email": "your-email@gmail.com",
     "message": "Gmail connected via credentials.json"
   }
   ```

3. **Test email fetching:**
   ```bash
   curl "http://localhost:8080/api/gmail/preview?max_results=5&days_back=7"
   ```

### Using the Frontend

1. Start the frontend:
   ```bash
   cd frontend
   npm run dev
   ```

2. Open http://localhost:3030

3. Click "Fetch from Gmail" button - it will automatically connect and show emails!

## What Happens When You Fetch Emails

1. **Search**: Looks for emails in primary inbox from last 7 days with claim keywords
2. **Keywords**: claim, insurance, accident, injury, policy, collision, damage, incident, loss, acord
3. **Preview**: Shows list of matching emails
4. **Process**: Converts each email + attachments to PDF
5. **Save**: PDFs saved to `backend/uploads/` directory
6. **Pipeline**: Pathway automatically processes them through claims triage
7. **Label**: Marks emails as read and adds "CLAIM_PROCESSED" label

## Credentials Details

### credentials.json Structure
```json
{
  "installed": {
    "client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "YOUR_CLIENT_SECRET",
    "redirect_uris": ["http://localhost"]
  }
}
```

### token.json Structure
Contains:
- `token`: Access token for Gmail API
- `refresh_token`: Token to get new access tokens
- `token_uri`: OAuth token endpoint
- `client_id`: OAuth client ID
- `client_secret`: OAuth client secret
- `scopes`: Granted permissions (gmail.readonly, gmail.modify)
- `expiry`: Token expiration time

## Regenerating Tokens (if needed)

If the token expires or you need to re-authenticate:

1. **Delete existing token:**
   ```bash
   rm backend/token.json
   ```

2. **Use Google's quickstart script:**
   ```bash
   cd backend
   python -c "
   from langchain_community.agent_toolkits import GmailToolkit
   toolkit = GmailToolkit()
   print('Gmail authenticated successfully!')
   print(f'User: {toolkit.api_resource.users().getProfile(userId=\"me\").execute()[\"emailAddress\"]}')
   "
   ```

3. **Follow the OAuth flow:**
   - Browser will open
   - Sign in with your Google account
   - Grant permissions
   - Token will be saved automatically

## Troubleshooting

### Error: "Gmail not connected"
**Solution:** Check that both files exist:
```bash
ls -la backend/credentials.json backend/token.json
```

### Error: "Token expired"
**Solution:** LangChain automatically refreshes tokens. If this fails, delete `token.json` and re-authenticate.

### Error: "Invalid credentials"
**Solution:** Verify `credentials.json` is valid and from Google Cloud Console with Gmail API enabled.

### No emails found
**Solutions:**
- Check you have emails in primary inbox
- Verify emails contain claim keywords in subject
- Adjust `days_back` parameter (default is 7 days)
- Check Gmail API quotas in Google Cloud Console

## API Endpoints

### Check Connection Status
```bash
GET /api/gmail/status
```

### Preview Emails (without processing)
```bash
GET /api/gmail/preview?max_results=10&days_back=7
```

### Fetch and Process Emails
```bash
POST /api/gmail/fetch?max_results=10&days_back=7
```

## Security Notes

- **credentials.json** contains OAuth client credentials (safe to commit if using installed app type)
- **token.json** contains user-specific access tokens (**DO NOT commit to git**)
- Add `token.json` to `.gitignore`
- Tokens are automatically refreshed by LangChain
- Gmail API has rate limits (check Google Cloud Console)

## Environment Variables (Optional)

You can also use environment variables:
```bash
export GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```

Or set in `.env`:
```
GOOGLE_APPLICATION_CREDENTIALS=./credentials.json
```

## Comparison: OAuth Popup vs Auto-Connect

### Old Method (OAuth Popup) ❌
- Required manual OAuth flow every time
- Popup windows and callbacks
- Stored tokens in MongoDB
- Complex frontend integration

### New Method (Auto-Connect) ✅
- Uses existing credentials.json and token.json
- No popups or manual steps
- LangChain handles everything
- Simple, straightforward integration

## Support

For issues:
1. Check backend logs for detailed errors
2. Verify files exist and are readable
3. Test with curl commands above
4. Check Google Cloud Console for API status
