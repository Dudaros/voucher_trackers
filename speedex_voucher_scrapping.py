import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os


def track_speedex(voucher_numbers, delay=1):
    # Lists to store all tracking data
    all_tracking_data = []

    # Headers to mimic a browser
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5'
    }

    session = requests.Session()

    for voucher in voucher_numbers:
        try:
            # URL for the tracking page
            url = f'https://speedex.gr/speedex/NewTrackAndTrace.aspx?number={voucher}'

            # Make request
            response = session.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Extract tracking events
            timeline_items = soup.find_all('li', class_='timeline-item')

            for item in timeline_items:
                # Get the status
                title = item.find('h4', class_='card-title')
                status = title.text.strip() if title else None

                # Get the location and timestamp
                subtitle = item.find('span', class_='font-small-3')
                details = subtitle.text.strip() if subtitle else None

                if status and details:
                    # Split location and timestamp
                    try:
                        location, timestamp = details.split(', ')
                    except ValueError:
                        location = ""
                        timestamp = details

                    all_tracking_data.append({
                        'voucher_number': voucher,
                        'status': status,
                        'location': location,
                        'timestamp': timestamp,
                    })

            # Check for delivery confirmation
            delivery_card = soup.find('div', class_='delivered-speedex')
            if delivery_card:
                delivered_title = delivery_card.find('h4', class_='delivered-title')
                delivered_details = delivery_card.find('span', class_='font-small-3')
                if delivered_title and delivered_details:
                    location, timestamp = delivered_details.text.strip().split(', ')
                    all_tracking_data.append({
                        'voucher_number': voucher,
                        'status': 'ΠΑΡΑΔΟΣΗ',
                        'location': location,
                        'timestamp': timestamp,
                        'additional_info': delivered_title.text.strip()
                    })

            print(f"Successfully tracked voucher: {voucher}")

            # Add delay between requests to be nice to the server
            time.sleep(delay)

        except Exception as e:
            print(f"Error tracking voucher {voucher}: {str(e)}")
            continue

    return all_tracking_data


def save_tracking_data(tracking_data, base_filename):
    # Create a DataFrame
    df = pd.DataFrame(tracking_data)

    # Create timestamp for filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Save as CSV
    csv_filename = f"{base_filename}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # utf-8-sig for proper Greek character encoding
    print(f"Data saved to CSV: {csv_filename}")

    # Save as Excel
    excel_filename = f"{base_filename}_{timestamp}.xlsx"
    df.to_excel(excel_filename, index=False)
    print(f"Data saved to Excel: {excel_filename}")


# Example usage
def main():
    # You can input voucher numbers in several ways:

    # 1. Direct list
    voucher_numbers = [
        "700036338271",
        "700036338272",  # Add more numbers as neede
    ]

    # 2. From a text file
    # with open('vouchers.txt', 'r') as f:
    #     voucher_numbers = [line.strip() for line in f if line.strip()]

    # Track all vouchers
    tracking_data = track_speedex(voucher_numbers)

    # Save the results
    save_tracking_data(tracking_data, "speedex_tracking")


if __name__ == "__main__":
    main()