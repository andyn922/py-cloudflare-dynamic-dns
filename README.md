# Cloudflare Dynamic DNS Client.
Update a single record on cloudflare with the ip address if where this script is run. **Tested on python 3.9** may or may not work on earlier versions.

# Setup

## Required python modules
 - requiests
 - arrow

## Cloudflare API token
Create one here: https://dash.cloudflare.com/profile/api-tokens

The minimum required permissions are:  
Zone - Zone - Read  
Zone - DNS  - Edit

## Edit config
 - Remove '-TEMPLATE' suffix.
 - Update all items in the 'CLOUDFLARE_CONFIG' section.
    - When adding api_token - do not include the "BEARER" part.