from email_sender import send_gmail
from enphase.production import get_envoy_production
import configparser

config = configparser.ConfigParser()
config.read('config.ini')

ENVOY_IP1 = config['envoy1']['ip']
TOKEN1 = config['envoy1']['token']
ENVOY_IP2 = config['envoy2']['ip']
TOKEN2 = config['envoy2']['token']
UNIT_COST = float(config['settings']['unit_cost'])

def send_daily_production_email(total, unit_cost):
    dollar_value = unit_cost * total

    send_gmail("c.a.singh@hotmail.com", "Enphase Production", f"""
    
    Total Prodduction {total}
    Dollar Value $ {dollar_value}
               
    """)

    send_gmail("madavie.singh1@gmail.com", "Enphase Production", f"""
    
    Total Prodduction {total}
    Dollar Value $ {dollar_value}
               
    """)

if __name__ == "__main__":
    total = 0
    total += get_envoy_production("first", ENVOY_IP1, TOKEN1)
    total += get_envoy_production("second", ENVOY_IP2, TOKEN2)
    print(total)

    send_daily_production_email(total, UNIT_COST)
    