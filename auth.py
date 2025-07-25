import http.server
import socketserver
import webbrowser
import requests
from urllib.parse import urlparse, parse_qs
from utils import save_config, load_config, print_success, print_error


def exchange_code_for_token(code, client_id, client_secret, redirect_uri):
    token_url = "https://launchpad.37signals.com/authorization/token"
    payload = {
        "type": "web_server",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "client_secret": client_secret,
        "code": code
    }
    try:
        res = requests.post(token_url, data=payload)
        if res.status_code == 200:
            return res.json()
        else:
            print_error(f"[Token Exchange] Failed: {res.status_code} {res.text}")
    except Exception as e:
        print_error(f"[Token Exchange] Exception: {e}")
    return None


def get_account_id(access_token):
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        res = requests.get("https://launchpad.37signals.com/authorization.json", headers=headers)
        if res.status_code == 200:
            return res.json().get("accounts", [{}])[0].get("id")
        else:
            print_error(f"[Account ID Fetch] Failed: {res.status_code} {res.text}")
    except Exception as e:
        print_error(f"[Account ID Fetch] Exception: {e}")
    return None


def get_token():
    config = load_config()

    client_id = config.get("client_id")
    client_secret = config.get("client_secret")
    redirect_uri = config.get("redirect_uri", "http://localhost:8888/callback")

    if not client_id or not client_secret:
        print_error("Missing client_id or client_secret in config.json")
        return

    auth_url = (
        f"https://launchpad.37signals.com/authorization/new"
        f"?type=web_server&client_id={client_id}&redirect_uri={redirect_uri}"
    )

    print(f"Opening browser for authorization...\nIf it doesn't open, manually visit:\n{auth_url}")
    try:
        webbrowser.open(auth_url)
    except:
        import subprocess
        subprocess.run(["start", auth_url], shell=True)

    class OAuthHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            parsed = urlparse(self.path)
            code = parse_qs(parsed.query).get("code", [None])[0]

            if not code:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Missing code in redirect URL.")
                return

            token_data = exchange_code_for_token(code, client_id, client_secret, redirect_uri)
            if not token_data:
                print_error("Failed to retrieve access token.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Token exchange failed.")
                return

            access_token = token_data.get("access_token")
            refresh_token = token_data.get("refresh_token")
            if not access_token:
                print_error("No access_token returned.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"No access token in response.")
                return

            config["access_token"] = access_token
            config["refresh_token"] = refresh_token

            account_id = get_account_id(access_token)
            if account_id:
                config["account_id"] = account_id
                save_config(config)
                print_success("Access token and account ID saved to config.json.")
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"Authentication complete. You may close this window.")
            else:
                print_error("Token received but failed to fetch account_id.")
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"Token received, but failed to retrieve account ID.")

    with socketserver.TCPServer(("localhost", 8888), OAuthHandler) as httpd:
        httpd.handle_request()

def get_auth_headers():
    config = load_config()
    access_token = config.get("access_token")
    account_id = config.get("account_id")

    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "User-Agent": "BasecampTool (you@example.com)",  # optional
        "Account-ID": str(account_id)
    }
