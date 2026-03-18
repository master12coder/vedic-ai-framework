# Google OAuth Setup

## Step 1: Create Google Cloud Project

1. Go to [console.cloud.google.com](https://console.cloud.google.com)
2. Click "Select a project" → "New Project"
3. Name: "Jyotish AI"
4. Click "Create"

## Step 2: OAuth Consent Screen

1. Go to APIs & Services → OAuth consent screen
2. User type: "External"
3. App name: "Jyotish AI"
4. User support email: your email
5. Authorized domains: your domain (e.g., `jyotish.yourdomain.com`)
6. Developer contact: your email
7. Scopes: email, profile, openid (defaults)
8. Test users: add your email + Pandit Ji's email
9. Click "Save and Continue" through all steps

## Step 3: Create OAuth Credentials

1. Go to APIs & Services → Credentials
2. Click "Create Credentials" → "OAuth 2.0 Client ID"
3. Application type: "Web application"
4. Name: "Jyotish Web"
5. Authorized redirect URIs:
   - `https://jyotish.yourdomain.com/auth/callback`
   - `http://localhost:8000/auth/callback` (for local dev)
6. Click "Create"
7. Copy **Client ID** and **Client Secret**

## Step 4: Configure .env

```bash
# On your server:
nano /opt/jyotish/.env

# Add:
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
ALLOWED_EMAILS=manish@email.com,panditji@email.com
```

## Step 5: Restart

```bash
sudo systemctl restart jyotish
```

## Notes

- Google OAuth is free, no billing required
- "External" user type: anyone with Google can sign in
- `ALLOWED_EMAILS` restricts access to specific email addresses
- Leave `ALLOWED_EMAILS` empty to allow anyone
- First user to sign in automatically becomes "owner" role
