"""
WordPress post update module for solar monitoring data.
Uploads images and updates post content with production/consumption data.
"""

import os
import json
import requests
from datetime import datetime
from utils.config import WP_POST_URL, WP_USERNAME, WP_APP_PASSWORD, WP_POST_ID


def upload_image_to_wordpress(image_path, site_url, username, app_password):
    """
    Upload an image to WordPress media library.

    Args:
        image_path: Path to the image file
        site_url: WordPress site URL
        username: WordPress username
        app_password: WordPress application password

    Returns:
        dict: WordPress media response with id, url, etc.
    """
    media_url = f"{site_url}/wp-json/wp/v2/media"

    filename = os.path.basename(image_path)

    with open(image_path, 'rb') as img_file:
        files = {'file': (filename, img_file, 'image/png')}
        headers = {'Content-Disposition': f'attachment; filename={filename}'}

        response = requests.post(
            media_url,
            files=files,
            headers=headers,
            auth=(username, app_password)
        )

    if response.status_code in [200, 201]:
        return response.json()
    else:
        print(f"Failed to upload image {filename}. Status: {response.status_code}")
        print(response.text)
        return None


def load_production_data():
    """
    Load latest production and consumption data from JSON files.

    Returns:
        dict: Combined data from enphase, hqst, and consumption sources
    """
    data = {
        'enphase': {},
        'hqst': {},
        'consumption': {},
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    # Load Enphase data
    enphase_json = 'production/data/enphase.json'
    if os.path.exists(enphase_json):
        try:
            with open(enphase_json, 'r') as f:
                data['enphase'] = json.load(f)
        except Exception as e:
            print(f"Error loading enphase data: {e}")

    # Load HQST data
    hqst_json = 'production/data/hqst.json'
    if os.path.exists(hqst_json):
        try:
            with open(hqst_json, 'r') as f:
                data['hqst'] = json.load(f)
        except Exception as e:
            print(f"Error loading hqst data: {e}")

    # Load consumption data
    consumption_json = 'production/data/consumption.json'
    if os.path.exists(consumption_json):
        try:
            with open(consumption_json, 'r') as f:
                data['consumption'] = json.load(f)
        except Exception as e:
            print(f"Error loading consumption data: {e}")

    return data


def generate_solar_html_content(data, house_image_url=None, shed_image_url=None, comparison_image_url=None):
    """
    Generate HTML content for the WordPress post with solar data and images.

    Args:
        data: Production/consumption data dict
        house_image_url: URL of uploaded house production graph
        shed_image_url: URL of uploaded shed production graph
        comparison_image_url: URL of uploaded comparison graph

    Returns:
        str: HTML content for the post
    """
    today_str = datetime.now().strftime('%B %d, %Y')

    # Extract values with fallbacks
    enphase_w = data['enphase'].get('wNow', 0)
    enphase_wh = data['enphase'].get('whToday', 0)
    enphase_wh_total = data['enphase'].get('whLifetime', 0)

    hqst_power = data['hqst'].get('pv_power', 0)
    hqst_today = data['hqst'].get('power_generation_today', 0)
    hqst_total = data['hqst'].get('power_generation_total', 0)

    consumption_w = data['consumption'].get('total_consumption_w', 0)
    consumption_wh = data['consumption'].get('total_consumption_wh_today', 0)
    net_grid_w = data['consumption'].get('net_consumption_wh_today', 0)

    # Calculate totals
    total_solar_w = enphase_w + hqst_power
    total_solar_wh = enphase_wh + hqst_today

    html = f"""
    <h2>☀️ Solar Production & Consumption Dashboard - {today_str}</h2>

    <p><em>Last updated: {data['timestamp']}</em></p>

    <h3>🏠 House Solar (Enphase)</h3>
    <ul>
        <li><strong>Current Power:</strong> {enphase_w:,.0f} W</li>
        <li><strong>Today's Production:</strong> {enphase_wh:,.0f} Wh ({enphase_wh/1000:.2f} kWh)</li>
        <li><strong>Lifetime Production:</strong> {enphase_wh_total/1000:,.1f} kWh</li>
    </ul>

    <h3>🔋 Shed Solar (HQST)</h3>
    <ul>
        <li><strong>Current Power:</strong> {hqst_power} W</li>
        <li><strong>Today's Production:</strong> {hqst_today} Wh ({hqst_today/1000:.2f} kWh)</li>
        <li><strong>Lifetime Production:</strong> {hqst_total/1000:,.1f} kWh</li>
    </ul>

    <h3>📊 Combined Solar</h3>
    <ul>
        <li><strong>Total Current Power:</strong> {total_solar_w:,.0f} W</li>
        <li><strong>Total Today's Production:</strong> {total_solar_wh:,.0f} Wh ({total_solar_wh/1000:.2f} kWh)</li>
    </ul>

    <h3>⚡ Home Consumption</h3>
    <ul>
        <li><strong>Current House Load:</strong> {consumption_w:,.0f} W</li>
        <li><strong>Today's Consumption:</strong> {consumption_wh:,.0f} Wh ({consumption_wh/1000:.2f} kWh)</li>
        <li><strong>Net Grid State:</strong> {net_grid_w:,.0f} W ({'Exporting' if net_grid_w < 0 else 'Importing'})</li>
    </ul>
    """

    # Add images if uploaded
    if house_image_url:
        html += f"""

    <h3>📈 House Production Graph</h3>
    <img src="{house_image_url}" alt="House Solar Production" style="max-width: 100%; height: auto;" />
    """

    if comparison_image_url:
        html += f"""

    <h3>� Production vs. Consumption Graph</h3>
    <img src="{comparison_image_url}" alt="Solar Production vs Home Consumption" style="max-width: 100%; height: auto;" />
    """

    if shed_image_url:
        html += f"""

    <h3>📈 Shed Production Graph</h3>
    <img src="{shed_image_url}" alt="Shed Solar Production" style="max-width: 100%; height: auto;" />
    """
   
    return html


def update_wordpress_post(html_content, site_url, post_id, username, app_password):
    """
    Update a WordPress post with new content.

    Args:
        html_content: HTML content for the post
        site_url: WordPress site URL
        post_id: Post ID to update
        username: WordPress username
        app_password: WordPress application password

    Returns:
        bool: True if successful, False otherwise
    """
    url = f"{site_url}/wp-json/wp/v2/posts/{post_id}"

    updated_data = {
        "content": html_content,
        "status": "publish"
    }

    response = requests.post(
        url,
        json=updated_data,
        auth=(username, app_password)
    )

    if response.status_code == 200:
        print("Post updated successfully!")
        return True
    else:
        print(f"Failed to update post. Status code: {response.status_code}")
        print(response.text)
        return False


def post_solar_update(include_images=True):
    """
    Main function to post solar production and consumption update to WordPress.
    Uploads images and updates post content.

    Args:
        include_images: Whether to upload and include images in the post

    Returns:
        bool: True if successful, False otherwise
    """
    # Check if config is loaded
    if not WP_POST_URL or not WP_USERNAME or not WP_APP_PASSWORD or not WP_POST_ID:
        print("WordPress configuration not complete. Please check config.ini [post] section.")
        return False

    # Extract site URL from post URL (remove /wp-json/wp/v2/posts/... part)
    site_url = WP_POST_URL.split('/wp-json')[0]

    print(f"Updating WordPress post {WP_POST_ID} at {site_url}...")

    # Load production data
    data = load_production_data()
    print(f"Loaded data - Enphase: {data['enphase'].get('wNow', 0)}W, "
          f"HQST: {data['hqst'].get('pv_power', 0)}W")

    # Upload images if requested
    house_image_url = None
    shed_image_url = None
    comparison_image_url = None

    if include_images:
        today_str = datetime.now().strftime('%Y%m%d')

        # House production graph
        house_image_path = f"production/images/house/{today_str}.png"
        if os.path.exists(house_image_path):
            print(f"Uploading house graph: {house_image_path}")
            result = upload_image_to_wordpress(house_image_path, site_url, WP_USERNAME, WP_APP_PASSWORD)
            if result:
                house_image_url = result.get('source_url')
                print(f"House graph uploaded: {house_image_url}")

        # Shed production graph
        shed_image_path = f"production/images/shed/{today_str}.png"
        if os.path.exists(shed_image_path):
            print(f"Uploading shed graph: {shed_image_path}")
            result = upload_image_to_wordpress(shed_image_path, site_url, WP_USERNAME, WP_APP_PASSWORD)
            if result:
                shed_image_url = result.get('source_url')
                print(f"Shed graph uploaded: {shed_image_url}")

        # Comparison graph
        comparison_image_path = f"production/images/house/comparison_{today_str}.png"
        if os.path.exists(comparison_image_path):
            print(f"Uploading comparison graph: {comparison_image_path}")
            result = upload_image_to_wordpress(comparison_image_path, site_url, WP_USERNAME, WP_APP_PASSWORD)
            if result:
                comparison_image_url = result.get('source_url')
                print(f"Comparison graph uploaded: {comparison_image_url}")

    # Generate HTML content
    html_content = generate_solar_html_content(
        data,
        house_image_url=house_image_url,
        shed_image_url=shed_image_url,
        comparison_image_url=comparison_image_url
    )

    # Update WordPress post
    return update_wordpress_post(
        html_content,
        site_url,
        WP_POST_ID,
        WP_USERNAME,
        WP_APP_PASSWORD
    )


if __name__ == "__main__":
    post_solar_update(include_images=True)