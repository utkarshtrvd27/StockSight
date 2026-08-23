import os
import time
from urllib.parse import unquote, urlparse
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_latest_udiff_bhavcopy():
    # landing_dir = os.path.join(os.path.dirname(__file__), "landing")
    landing_dir = os.path.abspath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "landing")
    )
    os.makedirs(landing_dir, exist_ok=True)

    # 1. Setup Chrome options
    options = webdriver.ChromeOptions()
    options.add_argument("--headless=new")  # Runs silently in the background
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

    prefs = {
        "download.default_directory": landing_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)

    print(f"Downloads will be saved to: {landing_dir}")

    # Initialize the browser driver
    driver = webdriver.Chrome(options=options)
    
    try:
        print("Opening NSE All Reports page...")
        driver.get("https://www.nseindia.com/all-reports")
        
        print("Waiting for dynamic content to load...")
        # 2. Wait up to 15 seconds for the table links to appear in the DOM
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.TAG_NAME, "a"))
        )
        
        # Give JS an extra second to render everything completely
        time.sleep(2)
        
        # 3. Read URLs from the current DOM to avoid stale WebElement references
        hrefs = driver.execute_script(
            "return Array.from(document.querySelectorAll('a')).map(link => link.href);"
        )
        target_href = next(
            (
                href
                for href in hrefs
                if "BhavCopy_NSE_CM_0_0_0_" in href and href.endswith(".zip")
            ),
            None,
        )

        if target_href:
            file_name = os.path.basename(unquote(urlparse(target_href).path))
            target_file_path = os.path.join(landing_dir, file_name)

            if os.path.isfile(target_file_path):
                print(f"File already exists: {target_file_path}. Skipping download.")
                return

            print("Triggering download...")
            driver.get(target_href)
            
            # Keep script alive for a few seconds to let the download finish
            time.sleep(5)
            print("✅ Download triggered successfully! Check your default Downloads folder.")
        else:
            print("❌ Could not find the UDiFF Bhavcopy link on the loaded page.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    download_latest_udiff_bhavcopy()