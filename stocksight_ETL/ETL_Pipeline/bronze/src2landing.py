import os
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def download_latest_udiff_bhavcopy():
    landing_dir = os.path.join(os.path.dirname(__file__), "landing")
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
        
        # 3. Find all links on the rendered page
        links = driver.find_elements(By.TAG_NAME, "a")
        target_link_element = None
        
        for link in links:
            href = link.get_attribute("href") or ""
            if "BhavCopy_NSE_CM_0_0_0_" in href and href.endswith(".zip"):
                target_link_element = link
                print(f"Found latest file link: {href.split('/')[-1]}")
                break
                
        if target_link_element:
            print("Triggering download...")
            # 4. Use JavaScript click to bypass any overlay blocking
            driver.execute_script("arguments[0].click();", target_link_element)
            
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