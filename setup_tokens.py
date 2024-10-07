import requests

# Prompt user for App credentials from Azure
CLIENT_ID = input("Enter your Azure Client ID: ").strip()
CLIENT_SECRET = input("Enter your Azure Client Secret: ").strip()

# Define constants for OAuth2
REDIRECT_URI = "https://login.microsoftonline.com/common/oauth2/nativeclient"
AUTHORITY_URL = "https://login.microsoftonline.com/common/oauth2/v2.0"
TOKEN_URL = f"{AUTHORITY_URL}/token"
SCOPE = "Tasks.ReadWrite offline_access"
AUTH_URL = f"{AUTHORITY_URL}/authorize"

# Step 1: Generate the authorization URL for first-time login
auth_url = (
    f"{AUTH_URL}?client_id={CLIENT_ID}&response_type=code&redirect_uri={REDIRECT_URI}"
    f"&response_mode=query&scope={SCOPE}&state=12345"
)

print("Go to the following URL and log in to provide consent:")
print(auth_url)

# Step 2: After login, get the authorization code from the redirect URL
auth_code = input("Enter the authorization code from the redirect URL: ").strip()

# Step 3: Exchange authorization code for access and refresh tokens
data = {
    "client_id": CLIENT_ID,
    "scope": SCOPE,
    "code": auth_code,
    "redirect_uri": REDIRECT_URI,
    "grant_type": "authorization_code",
    "client_secret": CLIENT_SECRET,
}

response = requests.post(TOKEN_URL, data=data)
if response.status_code == 200:
    tokens = response.json()
    print("Access Token:", tokens["access_token"])
    print("Refresh Token:", tokens["refresh_token"])
else:
    print(f"Error fetching tokens: {response.status_code}, {response.text}")
