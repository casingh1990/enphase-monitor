from datetime import datetime
from email_sender import send_gmail_with_images
from enphase.production import get_envoy_production
from utils.config import ENVOY_IP1, TOKEN1, ENVOY_IP2, TOKEN2, UNIT_COST

def send_daily_production_email(total, unit_cost):
    dollar_value = unit_cost * total
    today_str = datetime.now().strftime("%Y%m%d")
    
    # Paths to the current daily graphs
    image_paths = {
        "house_graph": f"production/images/house/{today_str}.png",
        "consumption_graph": f"production/images/house/consumption_{today_str}.png",
        "shed_graph": f"production/images/shed/{today_str}.png"
    }

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #1f2937; max-width: 600px; margin: 0 auto; padding: 20px;">
        <h2 style="color: #0284c7; border-bottom: 2px solid #e5e7eb; padding-bottom: 10px; text-align: center;">🌞 Daily Solar Production Update 🌞</h2>
        
        <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 15px; margin: 20px 0; text-align: center;">
          <p style="font-size: 18px; margin: 5px 0;"><strong>Total Enphase Production:</strong> <span style="color: #0284c7; font-weight: bold;">{total:.2f} kWh</span></p>
          <p style="font-size: 18px; margin: 5px 0;"><strong>Estimated Dollar Value:</strong> <span style="color: #16a34a; font-weight: bold;">$ {dollar_value:.2f}</span></p>
        </div>

        <div style="margin-top: 30px;">
          <h3 style="color: #0369a1; border-left: 4px solid #0284c7; padding-left: 8px;">🏡 House Solar Generation Graph</h3>
          <img src="cid:house_graph" alt="House Solar Production Graph" style="width: 100%; max-width: 600px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" />
        </div>

        <div style="margin-top: 30px; margin-bottom: 30px;">
          <h3 style="color: #b45309; border-left: 4px solid #d97706; padding-left: 8px;">☀️ Consumption Graph</h3>
          <img src="cid:consumption_graph" alt="Consumption Graph" style="width: 100%; max-width: 600px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" />
        </div>

        <div style="margin-top: 30px; margin-bottom: 30px;">
          <h3 style="color: #b45309; border-left: 4px solid #d97706; padding-left: 8px;">☀️ Shed Solar Generation Graph</h3>
          <img src="cid:shed_graph" alt="Shed Solar Production Graph" style="width: 100%; max-width: 600px; border-radius: 8px; border: 1px solid #e5e7eb; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1);" />
        </div>

        <p style="font-size: 11px; color: #9ca3af; margin-top: 40px; text-align: center; border-top: 1px solid #e5e7eb; padding-top: 20px;">
          This is an automated report from your home solar monitoring system.
        </p>
      </body>
    </html>
    """

    send_gmail_with_images("c.a.singh@hotmail.com", "Daily Enphase Solar Production", html_body, image_paths)
    send_gmail_with_images("madavie.singh1@gmail.com", "Daily Enphase Solar Production", html_body, image_paths)

if __name__ == "__main__":
    total = 0
    total += get_envoy_production("first", ENVOY_IP1, TOKEN1)
    total += get_envoy_production("second", ENVOY_IP2, TOKEN2)
    print(total)

    send_daily_production_email(total, UNIT_COST)
    