import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

# URL of the page
url = "https://groww.in/indices/nifty-total-market-index"

# Adding a User-Agent header to mimic a standard browser request
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

try:
    # Fetch the page content
    response = requests.get(url, headers=headers)
    response.raise_for_status()

    # Parse the HTML content
    soup = BeautifulSoup(response.text, "html.parser")

    # Locate the table using a regular expression to match the class starting with "tb10"
    table = soup.find("table", class_=re.compile(r"^tb10"))

    if table:
        # Extract headers
        headers_list = [th.text.strip() for th in table.find_all("th")]

        # Fallback headers if <th> tags aren't explicitly structured
        if not headers_list:
            headers_list = ["Company", "Market Cap", "Market Price", "Sector"]

        # Extract rows
        rows_data = []
        tbody = table.find("tbody")
        rows = tbody.find_all("tr") if tbody else table.find_all("tr")[1:]

        for row in rows:
            cells = [cb.text.strip() for cb in row.find_all("td")]
            if cells:
                rows_data.append(cells)

        # Create a Pandas DataFrame
        df = pd.DataFrame(rows_data, columns=headers_list[: len(rows_data[0])])

        # Display the scraped data
        print("Successfully scraped data from class 'tb10...':")
        print(df.to_string(index=False))

        # Optional: Save to a CSV file
        # df.to_csv("nifty_total_market_companies.csv", index=False)

    else:
        print("Could not find a table matching class 'tb10...' on the page.")

except requests.exceptions.RequestException as e:
    print(f"An error occurred while fetching the page: {e}")