import requests
import urllib3
import json

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_envoy_production(name, ip_address, auth_token):
    """Fetches the daily production data from the Enphase Envoy."""
    
    headers = {}
    
    if auth_token:
        print("Attempting to connect via HTTPS with Authorization Token...")
        url = f"https://{ip_address}/production.json"
        headers["Authorization"] = f"Bearer {auth_token}"
        verify_ssl = False 
    else:
        print("Attempting to connect via HTTP (Older Firmware)...")
        url = f"http://{ip_address}/production.json"
        verify_ssl = True

    try:
        response = requests.get(url, headers=headers, verify=verify_ssl, timeout=10)
        
        if response.status_code == 401:
            print("❌ Error 401: Unauthorized. Your Envoy requires a Token.")
            print("Generate one at https://entrez.enphaseenergy.com/ and add it to the script.")
            return
            
        response.raise_for_status() 
        data = response.json()

        with open(f"{name}.json", "w") as f:
            f.write(json.dumps(data))
        
        for item in data.get('production', []):
            if item.get('type') in ['eim']:
                print(item)
                wh_today = item.get('whToday', 0)
                w_now = item.get('wNow', 0)
                
                kwh_today = wh_today / 1000.0
                
                print("-" * 30)
                print(f"🌞 Enphase Envoy Production 🌞")
                print("-" * 30)
                print(f"Daily Production:  {kwh_today:.2f} kWh")
                print(f"Current Output:    {w_now} W")
                print("-" * 30)
                return kwh_today
                
        print("❌ Connected, but could not find production data in the expected format.")
        
    except requests.exceptions.Timeout:
        print(f"❌ Error: Connection timed out. Ensure {ip_address} is correct and online.")
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Failed to connect. Check your Envoy IP address.")
    except Exception as e:
        print(f"❌ An unexpected error occurred: {e}")
