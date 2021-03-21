import configparser
import logging
import socket
import sys
import time
from pathlib import Path, PurePath

import arrow
import requests

# Init

# setup logging
logs_dir = Path(f"{Path.cwd()}/logs")
# make logs dir if it does not exist
logs_dir.mkdir(parents=True, exist_ok=True)
logs_fullpath = Path(
    f"{logs_dir}/{time.strftime('%Y%m%d')}-cloudlare-dyndns.log")
if not logs_fullpath.is_file():  # make daily logs file if it does not exist
    with open(logs_fullpath, 'w'):
        pass
logging.basicConfig(
    filename=logs_fullpath,
    level="INFO",
    format='%(asctime)s :: %(levelname)s :: %(message)s')

# config file
config_fullpath = f"{Path.cwd()}/config.ini"
config = configparser.ConfigParser(allow_no_value=True)
config.read(config_fullpath)

# check forced_update mode
if len(sys.argv) > 1 and sys.argv[1] == "--force-update":
    force_update_mode = True
    print("FORCED UPDATE MODE")
    print("")
else:
    force_update_mode = False

# funct


def prlog(message: str, isError=False):
    if isError:
        print(f"ERROR: {message}")
        logging.error(message)
    else:
        print(message)
        logging.info(message)

# Main
logging.info(" - Started new session. ---")

# get ips addresses
local_ip = requests.get("http://ipv4.icanhazip.com").text.rstrip('\n')
remote_ip = socket.gethostbyname(config['CLOUDFLARE_CONFIG']['record_name'])
prlog(f"Local IP: {local_ip}, Remote IP: {remote_ip}")

# compare ips, if force_update we'll update cloudflare regardless
if local_ip == remote_ip and not force_update_mode:
    prlog("Local IP is the same as Remote IP, NO CHANGE required")

else:

    if not force_update_mode:
        prlog("Local IP is different to Remote IP, WILL UPDATE Cloudflare")
    else:
        prlog("FORCED UPDATE MODE ACTIVE - Updating Cloudflare regardless.")

    # get base info for cloudflare api requests
    zone_name = config['CLOUDFLARE_CONFIG']['zone_name']
    record_name = config['CLOUDFLARE_CONFIG']['record_name']
    base_headers = {'Content-Type': 'application/json',
                    "Authorization": f"Bearer {config['CLOUDFLARE_CONFIG']['api_token']}"}

    # Notice for anyone running script interactiviely!
    print("")
    print("========")
    print("About to start the API requests, these can take some time.")
    print("(Not sure why, probably because i'm free tier ?!)")
    print("Anyway, there's 3 requests and a print statement before each.")
    print("I've found they can can between 30 - 120 secs, please be patient.")
    print("========")
    print("")

    # api request for zone id
    prlog("Starting GET request for Zone ID")
    zone_id_request = requests.get(
        f"https://api.cloudflare.com/client/v4/zones?name={zone_name}", headers=base_headers)
    if zone_id_request.ok == False:  # terminating exception if failed
        err_msg = f"Unable to retreive Zone ID from cloudflare api, message: {zone_id_request.text}"
        logging.error(err_msg)
        raise SystemExit(err_msg)
    zone_id = (zone_id_request.json())['result'][0]['id']

    # api request for record id
    prlog("Starting GET request for Record ID")
    record_id_request = requests.get(
        f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records?name={record_name}", headers=base_headers)
    if zone_id_request.ok == False:  # terminating exception if failed
        err_msg = f"Unable to retreive Record ID from cloudflare api, message: {record_id_request.text}"
        logging.error(err_msg)
        raise SystemExit(err_msg)
    record_id = (record_id_request.json())['result'][0]['id']

    # api request to update dns record
    prlog("Starting PUT request to update DNS record")
    update_record_request = requests.put(
        url=f"https://api.cloudflare.com/client/v4/zones/{zone_id}/dns_records/{record_id}", headers=base_headers,
        json={
            'id': zone_id,
            'type': 'A',
            'name': record_name,
            'content': local_ip
        }
    )

    # log status, if it failed, dump cloudflare response.
    if update_record_request.ok:
        prlog(
            f"Successfully updated cloudflare DNS record '{record_name}' with '{local_ip}'")
    else:
        prlog(
            isError=True,
            message=f"Cannot update cloudflare DNS record '{record_name}', message: {update_record_request.text}"
        )

# Housekeeping
retention_time = config['LOG_RETENTION']['days']
cutoff_date = arrow.now().shift(days=int(f"-{retention_time}"))

# itterate all files in logs dir
print("")
prlog("Starting housekeeping")
housekeeping_remove_count = 0
for item in Path(logs_dir).glob('*'):
    if item.is_file():
        # get file last modified, delete if older than set retention period
        file_time = arrow.get(item.stat().st_mtime)
        if file_time < cutoff_date:
            logging.info(f"Removing old log file: {item.name}")
            item.unlink()
            housekeeping_remove_count += 1
if housekeeping_remove_count == 0:
    prlog("No old log files to remove")

# Goodbye
logging.info(" --- End of session. -")
