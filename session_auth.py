import requests
import os
from bs4 import BeautifulSoup
from utils.utils import load_config, print_success, print_error

class BasecampSessionAuth:
    """Handle direct email/password authentication to Basecamp without OAuth."""
    
    def __init__(self):
        self.session = requests.Session()
        self.authenticated = False
        self.account_id = None
        
    def login(self):
        """Login using email and password from config.json."""
        config = load_config()
        username = config.get('username')
        password = config.get('password')
        self.account_id = config.get('account_id')
        
        if not username or not password:
            print_error("Missing username or password in config.json")
            return False
            
        if not self.account_id:
            print_error("Missing account_id in config.json")
            return False
            
        try:
            print_success("Starting direct Basecamp login...")
            
            # Step 1: Get the main Basecamp login page
            login_url = "https://launchpad.37signals.com/signin"
            print(f"Getting login page: {login_url}")
            
            response = self.session.get(login_url)
            response.raise_for_status()
            
            # Parse the login form
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Debug: save login page to see structure
            with open("debug_login_page.html", "w", encoding='utf-8') as f:
                f.write(response.text)
            print(f"Login page saved to debug_login_page.html for inspection")
            
            # Look for the email/username field and next button approach
            email_field = soup.find('input', {'type': 'email'}) or soup.find('input', attrs={'name': lambda x: x and 'email' in x.lower()})
            
            # Also look for text inputs that might be email fields
            if not email_field:
                text_inputs = soup.find_all('input', {'type': 'text'})
                for inp in text_inputs:
                    if any(keyword in str(inp).lower() for keyword in ['email', 'user', 'login']):
                        email_field = inp
                        break
            
            if not email_field:
                print_error("Could not find email field on login page")
                print("Available input fields:")
                for inp in soup.find_all('input'):
                    print(f"  {inp.get('type', 'unknown')} - {inp.get('name', 'no-name')} - {inp.get('placeholder', 'no-placeholder')}")
                return False
                
            print_success("Found email field, proceeding with direct login")
            
            # Step 2: This is a JavaScript-driven form, but we can submit directly
            form = email_field.find_parent('form')
            if not form:
                print_error("Could not find login form")
                return False
            
            print_success(f"Found form with action: {form.get('action')}")
                
            # Extract form data - this form expects username and password together
            form_data = {'username': username, 'password': password}
            
            # Add any hidden fields (including CSRF tokens)
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    form_data[name] = value
                    print(f"Added hidden field: {name}")
            
            # Get form action
            form_action = form.get('action') or '/signin'
            if form_action.startswith('/'):
                form_submit_url = f"https://launchpad.37signals.com{form_action}"
            else:
                form_submit_url = form_action
                
            print(f"Submitting credentials to: {form_submit_url}")
            print(f"Form data keys: {list(form_data.keys())}")
            
            # Submit the form with both username and password
            login_response = self.session.post(form_submit_url, data=form_data, allow_redirects=True)
            
            print_success(f"Login response status: {login_response.status_code}")
            print_success(f"Final URL: {login_response.url}")
            
            # The response should be the login result
            password_response = login_response
            
            # Step 4: Verify login success
            final_url = password_response.url
            final_content = password_response.text.lower()
            
            # Check for successful login indicators
            success_indicators = [
                'dashboard',
                'projects', 
                'sign_out',
                str(self.account_id)
            ]
            
            # Check URL and content separately to avoid type errors
            url_success = any(indicator in final_url for indicator in success_indicators)
            content_success = any(indicator in final_content for indicator in success_indicators)
            
            login_successful = url_success or content_success
            
            if login_successful:
                print_success("Successfully logged into Basecamp!")
                print_success(f"Final URL: {final_url}")
                self.authenticated = True
                
                # Navigate to the specific account to ensure session context
                account_url = f"https://3.basecamp.com/{self.account_id}"
                account_response = self.session.get(account_url)
                
                if account_response.status_code == 200:
                    print_success(f"Successfully navigated to account {self.account_id}")
                    return True
                else:
                    print_error(f"Could not access account {self.account_id}")
                    return False
                    
            else:
                print_error("Login may have failed")
                print(f"Final URL: {final_url}")
                print(f"Response contains sign_in: {'sign_in' in final_content}")
                return False
                
        except Exception as e:
            print_error(f"Login failed: {str(e)}")
            return False
    
    def get_session(self):
        """Get the authenticated session for making requests."""
        if not self.authenticated:
            print_error("Not authenticated. Call login() first.")
            return None
        return self.session
    
    def download_file(self, url, local_path):
        """Download a file using the authenticated session."""
        if not self.authenticated:
            print_error("Not authenticated. Call login() first.")
            return False
            
        try:
            print(f"Downloading: {url}")
            print(f"Saving to: {local_path}")
            
            response = self.session.get(url, stream=True)
            response.raise_for_status()
            
            # Create directory if needed - handle Windows path issues
            dir_path = os.path.dirname(local_path)
            if dir_path:  # Only create directory if there is a directory component
                print(f"Creating directory: {dir_path}")
                os.makedirs(dir_path, exist_ok=True)
            
            with open(local_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            print_success(f"Downloaded: {local_path}")
            return True
            
        except Exception as e:
            print_error(f"Download failed for {url}: {str(e)}")
            print_error(f"Local path was: {local_path}")
            return False

def test_session_login():
    """Test the session-based login."""
    auth = BasecampSessionAuth()
    
    if auth.login():
        print_success("✅ Session login successful!")
        
        # Test downloading a file (using the attachment URL from our previous test)
        test_url = "https://storage.3.basecamp.com/4146522/blobs/c01303aa-dc88-11ef-a1ff-44a842377e52/download/image.png"
        test_path = "test_downloads/session_test_image.png"
        
        if auth.download_file(test_url, test_path):
            print_success("✅ File download successful!")
        else:
            print_error("❌ File download failed")
    else:
        print_error("❌ Session login failed")

if __name__ == "__main__":
    test_session_login()