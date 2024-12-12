import requests
import time
import pandas as pd
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)


def fetch_voucher_data(voucher, max_retries=5, timeout=30):
    url = f'https://www.taxydema.gr/api/track-request/{voucher}'
    for attempt in range(max_retries):
        try:
            response = requests.get(url, timeout=timeout)

            # Handle 500 error specifically
            if response.status_code == 500:
                logging.error(f"Server error for voucher {voucher} (attempt {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {'error': 'Server Error', 'status_code': 500}
                time.sleep(5)  # Longer wait time for server errors
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.Timeout:
            logging.warning(f"Timeout occurred for voucher {voucher} (attempt {attempt + 1}/{max_retries})")
        except requests.exceptions.RequestException as e:
            logging.error(f"Request failed for voucher {voucher}: {str(e)}")

        # Wait before retrying, with increasing delay
        time.sleep(2 * (attempt + 1))

    return {'error': 'Failed after all attempts'}


def extract_vertical_status(voucher_data, voucher_id):
    if not voucher_data:
        logging.warning(f"No data available for voucher {voucher_id}")
        return []

    if "error" in voucher_data:
        logging.error(f"Error processing voucher {voucher_id}: {voucher_data['error']}")
        return [{
            'Voucher': voucher_id,
            'Status': f"Error: {voucher_data.get('error', 'Unknown error')}"
        }]

    status_entries = []
    vertical_status = voucher_data.get('verticalStatus', [])

    if not vertical_status:
        logging.warning(f"No vertical status found for voucher {voucher_id}")
        return [{
            'Voucher': voucher_id,
            'Status': "No status available"
        }]

    for status in vertical_status:
        status_entries.append({
            'Voucher': voucher_id,
            'Status': status.get('tt_status_title', 'Unknown Status')
        })

    return status_entries


def main():
    # List of voucher IDs
    vouchers = ['348600000465', '348600000449']

    # List to store all status entries
    all_status_entries = []

    # Fetch and process data for each voucher
    for voucher in vouchers:
        logging.info(f"Processing voucher {voucher}...")
        voucher_data = fetch_voucher_data(voucher)
        status_entries = extract_vertical_status(voucher_data, voucher)
        all_status_entries.extend(status_entries)

    # Create DataFrame and save to Excel
    df = pd.DataFrame(all_status_entries)
    output_file = 'taxydema_voucher.xlsx'
    df.to_excel(output_file, index=False)
    logging.info(f"Data has been saved to {output_file}")

    # Print summary
    successful = len([entry for entry in all_status_entries if not entry['Status'].startswith('Error')])
    logging.info(f"Processing complete: {successful}/{len(vouchers)} vouchers processed successfully")


if __name__ == "__main__":
    main()