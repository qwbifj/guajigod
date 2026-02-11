import urllib.request
import urllib.error
import json
import os
import sys

class NetworkManager:
    BASE_URL = "http://localhost:5000"
    LOCAL_MODE = True # Enable local mode by default
    LOCAL_ACCOUNTS_FILE = "local_accounts.json"
    
    def __init__(self):
        self.user_id = None
        self.username = None
        self.is_connected = False
        
        # In Web/Emscripten, file system might be ephemeral or read-only.
        # Use memory storage for accounts in Web mode to avoid crashes.
        self.is_web = sys.platform == 'emscripten'
        self.web_accounts = {} 
        
    def _post(self, endpoint, data):
        url = f"{self.BASE_URL}{endpoint}"
        headers = {'Content-Type': 'application/json'}
        try:
            req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers)
            with urllib.request.urlopen(req) as response:
                return json.loads(response.read().decode('utf-8')), response.getcode()
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode('utf-8')), e.code
            except:
                return {"error": str(e)}, e.code
        except urllib.error.URLError:
            return {"error": "Connection failed. Is the server running?"}, 503
        except Exception as e:
            return {"error": str(e)}, 500

    def _get(self, endpoint):
        url = f"{self.BASE_URL}{endpoint}"
        try:
            with urllib.request.urlopen(url) as response:
                return json.loads(response.read().decode('utf-8')), response.getcode()
        except urllib.error.HTTPError as e:
            try:
                return json.loads(e.read().decode('utf-8')), e.code
            except:
                return {"error": str(e)}, e.code
        except urllib.error.URLError:
            return {"error": "Connection failed. Is the server running?"}, 503
        except Exception as e:
            return {"error": str(e)}, 500

    def register(self, username, password):
        if self.LOCAL_MODE or self.is_web:
            if self.is_web:
                if username in self.web_accounts:
                    return False, "Username already exists (Web)"
                self.web_accounts[username] = password
                return True, "Registration successful (Web)"

            accounts = {}
            if os.path.exists(self.LOCAL_ACCOUNTS_FILE):
                try:
                    with open(self.LOCAL_ACCOUNTS_FILE, 'r') as f:
                        accounts = json.load(f)
                except:
                    pass
            
            if username in accounts:
                return False, "Username already exists (Local)"
            
            accounts[username] = password
            try:
                with open(self.LOCAL_ACCOUNTS_FILE, 'w') as f:
                    json.dump(accounts, f)
                return True, "Registration successful (Local)"
            except Exception as e:
                return False, f"Local registration failed: {e}"

        data = {"username": username, "password": password}
        resp, code = self._post("/register", data)
        if code == 201:
            return True, resp.get("message")
        return False, resp.get("error")

    def login(self, username, password):
        if self.LOCAL_MODE or self.is_web:
            if self.is_web:
                if username in self.web_accounts and self.web_accounts[username] == password:
                    self.user_id = username
                    self.username = username
                    self.is_connected = True
                    return True, "Login successful (Web)"
                # Also check hardcoded admin/admin for convenience
                if username == "admin" and password == "admin":
                     self.user_id = "admin"
                     self.username = "admin"
                     self.is_connected = True
                     return True, "Login successful (Admin)"
                return False, "Invalid credentials (Web)"

            accounts = {}
            if os.path.exists(self.LOCAL_ACCOUNTS_FILE):
                try:
                    with open(self.LOCAL_ACCOUNTS_FILE, 'r') as f:
                        accounts = json.load(f)
                except:
                    pass
            
            if username in accounts and accounts[username] == password:
                self.user_id = username # Use username as ID
                self.username = username
                self.is_connected = True
                return True, "Login successful (Local)"
            return False, "Invalid credentials (Local)"

        data = {"username": username, "password": password}
        resp, code = self._post("/login", data)
        if code == 200:
            self.user_id = resp.get("user_id")
            self.username = username
            self.is_connected = True
            return True, resp.get("message")
        return False, resp.get("error")

    def save_game(self, game_data):
        if self.LOCAL_MODE:
            # In local mode, we rely on the engine's local save mechanism.
            # We return True to simulate a successful "network" save event without error.
            return True, "Local mode: Cloud save skipped"

        if not self.user_id:
            return False, "Not logged in"
            
        data = {
            "user_id": self.user_id,
            "game_data": game_data
        }
        resp, code = self._post("/save", data)
        if code == 200:
            return True, resp.get("message")
        return False, resp.get("error")

    def load_game(self):
        if self.LOCAL_MODE:
            # Return None to trigger fallback to local save file in GameEngine
            return None, "Local mode"

        if not self.user_id:
            return None, "Not logged in"
            
        resp, code = self._get(f"/load/{self.user_id}")
        if code == 200:
            return resp.get("game_data"), "Success"
        return None, resp.get("error")

    def logout(self):
        self.user_id = None
        self.username = None
        self.is_connected = False
