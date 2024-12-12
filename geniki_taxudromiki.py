import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import time
import os


def track_geniki_taxydromiki(voucher_numbers, delay=1):
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
            url = f'https://www.taxydromiki.com/track/{voucher}'

            # Make request
            response = session.get(url, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all tracking checkpoints
            checkpoints = soup.find_all('div', class_='tracking-checkpoint')

            # Keep track of the step number for better timeline representation
            total_steps = len(checkpoints)
            current_step = 0

            for checkpoint in checkpoints:
                current_step += 1
                # Extract status
                status_div = checkpoint.find('div', class_='checkpoint-status')
                status = status_div.text.replace('Κατάσταση', '').strip() if status_div else None

                # Extract location
                location_div = checkpoint.find('div', class_='checkpoint-location')
                location = location_div.text.replace('Τοποθεσία', '').strip() if location_div else ''

                # Extract date
                date_div = checkpoint.find('div', class_='checkpoint-date')
                date = date_div.text.replace('Ημερομηνία', '').strip() if date_div else None

                # Extract time
                time_div = checkpoint.find('div', class_='checkpoint-time')
                time = time_div.text.replace('Ώρα', '').strip() if time_div else None

                if status and date:
                    # Check if this is the final delivery status
                    is_delivery = 'tracking-delivery' in checkpoint.get('class', [])

                    # Format timestamp consistently
                    try:
                        # Parse the Greek date format
                        date_parts = date.split(', ')[1].split('/')
                        formatted_date = f"{date_parts[2]}-{date_parts[1]}-{date_parts[0]}"
                        timestamp = f"{formatted_date} {time}"
                    except:
                        timestamp = f"{date} {time}"

                    all_tracking_data.append({
                        'voucher_number': voucher,
                        'step': f"{current_step}/{total_steps}",
                        'status': status,
                        'location': location,
                        'timestamp': timestamp,
                        'date': formatted_date,
                        'time': time,
                        'is_final_status': is_delivery
                    })

            print(f"Successfully tracked voucher: {voucher}")

            # Add delay between requests to be nice to the server
            time.sleep(delay)

        except Exception as e:
            print(f"Error tracking voucher {voucher}: {str(e)}")
            continue

    return all_tracking_data


def get_next_version_filename(base_filename, extension):
    """Generate filename with version number if file exists"""
    version = 1
    while True:
        filename = f"{base_filename}_v{version}{extension}"
        if not os.path.exists(filename):
            return filename
        version += 1


def save_tracking_data(tracking_data, base_filename):
    # Create a DataFrame
    df = pd.DataFrame(tracking_data)

    # Sort the data by timestamp and voucher number
    df['timestamp'] = pd.to_datetime(df['timestamp'], format='%Y-%m-%d %H:%M', errors='coerce')
    df = df.sort_values(['voucher_number', 'timestamp'])

    # Reorder columns for better readability
    columns_order = [
        'voucher_number',
        'step',
        'status',
        'location',
        'date',
        'time',
        'is_final_status'
    ]
    df = df[columns_order]

    # Create date string
    date_str = datetime.now().strftime("%Y%m%d")

    # Base filename with date
    base = f"geniki_taxydromiki_{date_str}"

    # Get versioned filenames
    csv_filename = get_next_version_filename(base, ".csv")
    excel_filename = get_next_version_filename(base, ".xlsx")

    # Save as CSV
    df.to_csv(csv_filename, index=False, encoding='utf-8-sig')  # utf-8-sig for proper Greek character encoding
    print(f"Data saved to CSV: {csv_filename}")

    # Save as Excel with some formatting
    with pd.ExcelWriter(excel_filename, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Tracking Data')

        # Get the workbook and the worksheet
        workbook = writer.book
        worksheet = writer.sheets['Tracking Data']

        # Adjust column widths
        for idx, col in enumerate(df.columns):
            max_length = max(df[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_length

    print(f"Data saved to Excel: {excel_filename}")


# Example usage
def main():
    # You can input voucher numbers in several ways:

    # 1. Direct list
    voucher_numbers = [
        "4952705564", "4952903395"  # Add more numbers as needed
    ]

    # 2. From a text file
    # with open('vouchers.txt', 'r') as f:
    #     voucher_numbers = [line.strip() for line in f if line.strip()]

    # Track all vouchers
    tracking_data = track_geniki_taxydromiki(voucher_numbers)

    # Save the results
    save_tracking_data(tracking_data, "geniki_taxydromiki")


if __name__ == "__main__":
    main()