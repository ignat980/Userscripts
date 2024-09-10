from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import StaleElementReferenceException
import datetime
import time
import csv
from concurrent.futures import ThreadPoolExecutor

# Function to handle scraping a range of pages
def scrape_pages(start_page, end_page, file_suffix):
    # Initialize WebDriver for each thread
    driver = webdriver.Chrome()

    # Wait for the page to load
    wait = WebDriverWait(driver, 10)

    # Open the Cypriot Lawyers page
    driver.get('https://www.cyprusbar.org/CypriotAdvocateMembersPage')

    filename = f'lawyers_data_{file_suffix}.csv'
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Full Name', 'Alternative Name', 'Greek Name', 'Phone', 'Fax', 'Court Deposit Box', 'Province', 
            'Address', 'Postal Code', 'Email', 'URL', 'Mobile'
        ])

    def extract_lawyer_data():
        """
        Extracts the lawyer's alternative name, address, postal code, email, URL, and mobile from the details page.
        """
        alternative_name = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_TxtName_I').get_attribute('value')
        address = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_TxtAddress_I').get_attribute('value')
        postal_code = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_TxtPostalCode_I').get_attribute('value')
        email = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_TxtEmail_I').get_attribute('value')
        url = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_TxtUrl_I').get_attribute('value')
        mobile = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_txtMobile_I').get_attribute('value')

        return {
            'alternative_name': alternative_name,
            'address': address,
            'postal_code': postal_code,
            'email': email,
            'url': url,
            'mobile': mobile
        }

    def extract_table_row_data(row):
        """
        Extracts data from the table row (without clicking into the details).
        """
        columns = row.find_elements(By.TAG_NAME, 'td')
        full_name = columns[1].text
        greek_name = columns[2].text
        phone = columns[3].text
        fax = columns[4].text
        court_box = columns[5].text
        province = columns[6].text
        
        return {
            'full_name': full_name,
            'greek_name': greek_name,
            'phone': phone,
            'fax': fax,
            'court_box': court_box,
            'province': province
        }
    
    def select_page_size(size="80"):
        """
        Selects the page size (default to 80) from the dropdown in the table pagination controls.
        """
        try:
            # Click the dropdown to change page size
            dropdown = driver.find_element(By.ID, 'ctl00_ContentPlaceHolder1_LawyersGrid_DXPagerBottom_PSB')
            driver.execute_script("arguments[0].click();", dropdown)

            # Wait for the dropdown options to appear and select 80
            wait.until(EC.presence_of_element_located((By.XPATH, f"//span[text()='{size}']")))
            size_option = driver.find_element(By.XPATH, f"//span[text()='{size}']")
            driver.execute_script("arguments[0].click();", size_option)

            # Wait for the 80th row to confirm the table size has been updated
            wait.until(EC.presence_of_element_located((By.ID, "ctl00_ContentPlaceHolder1_LawyersGrid_DXDataRow79")))

            print(f"Page size set to {size} and table loaded.")

        except Exception as e:
            print(f"Exception raised on line: {str(e.__traceback__.tb_lineno)}")
            print(f"Failed to set page size to 80: {str(e)}")
            return False
        return True
    
    def go_back_to_main_table_at_page(current_page):
        """
        Navigate back to the main table after extracting details and go to the correct page.
        """
        driver.back()  # Go back to the main table
        wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable')))  # Wait for the table to load
        print("Setting size after navigation back to the main table...")
        select_page_size("80")
        # Navigate back to the current page
        return click_to_page(current_page)
    
    def click_to_page(target_page):
        """
        Continuously clicks the highest visible page link until the target page is reached,
        while excluding the last three pages until necessary.
        """
        print(f"Navigating to page {target_page}...")
        if target_page == 1:
            return True
        if target_page > 55:
            print("Target page exceeds the maximum page count.")
            return False

        max_retries = 3
        retries = 0

        try:
            # Ensure page size is set to 80 after going back to the main table
            while True:
                try:
                    # Get all visible page numbers excluding the last three
                    visible_pages = driver.find_elements(By.XPATH, "//a[contains(@class, 'dxp-num')]")
                    highest_visible_page = int(visible_pages[-4].text)

                    # If the target page is within the visible range
                    if target_page <= highest_visible_page or target_page >= 53:
                        target_page_element = driver.find_element(By.XPATH, f"//a[contains(@onclick, 'PN{target_page - 1}') and contains(@class, 'dxp-num')]")
                        print(f"Found page {target_page}...")
                        target_page_element.click()

                        # Wait for the target page number to appear as the current one
                        wait.until(EC.presence_of_element_located((By.XPATH, f"//b[contains(@class, 'dxp-current') and contains(., '{target_page}')]")))
                        break
                    else:
                        # Check for presence of highest visible page + 1
                        if driver.find_elements(By.XPATH, f"//a[contains(@class, 'dxp-num') and contains(., '{highest_visible_page + 1}')]"):
                            print(f"Page {highest_visible_page + 1} found before click.")
                        
                        print(f"Clicking page {highest_visible_page}...")
                        # Click the highest visible page to reveal more pages, wait until the new highest page appears
                        visible_pages[-4].click()

                        # Wait for the new highest page to load
                        wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@class, 'dxp-num') and contains(., '{highest_visible_page + 1}')]")))
                        print(f"Page {highest_visible_page + 1} found.")
                        
                        # time.sleep(0.4)  # Short delay for the page to fully load

                except StaleElementReferenceException:
                    # If a stale reference occurs, refresh the visible elements and retry
                    if retries < max_retries:
                        retries += 1
                        print(f"Stale element reference detected. Retrying... ({retries}/{max_retries})")
                        continue
                    else:
                        print(f"Max retries reached while trying to navigate to page {target_page} when looking for {highest_visible_page}.")
                        return False

        except Exception as e:
            print(f"Exception raised on line: {str(e.__traceback__.tb_lineno)}")
            print(f"Failed to navigate to page {target_page}: {str(e)}")
            return False
        return True
    
    def click_details_button(details_button):
        """
        Scrolls to the details button and clicks it.
        """
        try:
            # Scroll the element into view using JavaScript
            driver.execute_script("arguments[0].scrollIntoView(true);", details_button)
            
            # Adjust scroll to ensure the header doesn't overlap
            driver.execute_script("window.scrollBy(0, -150);")  # Scroll up a bit to avoid the header

            # Optionally, add a small delay to ensure the page has scrolled
            time.sleep(0.2)

            # Now click the details button
            details_button.click()

        except Exception as e:
            print(f"Failed to click on details button: {str(e)}")
            
    def iterate_through_table(start_page, end_page):
        """
        Iterates through all rows on each table page, scraping data and moving to the next page.
        """
        select_page_size("80")
        current_page = start_page
        while current_page <= end_page:
            # if the page navigation fails, break the loop
            if not click_to_page(current_page):
                break

            # Re-fetch the rows on each iteration after page navigation
            rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable']/tbody/tr[contains(@id, 'DXDataRow')]")))
            
            for i in range(len(rows)):
                try:
                    # print(f"Processing row {i} on page {current_page}...")
                    # Re-fetch the rows inside the loop to avoid stale element error
                    rows = driver.find_elements(By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable']/tbody/tr[contains(@id, 'DXDataRow')]")
                    
                    # Extract row data (name, greek name, phone, fax, court box, province)
                    row_data = extract_table_row_data(rows[i])
                    
                    # Find the ">>" details button for additional data
                    details_button = rows[i].find_element(By.XPATH, ".//a[contains(@id, 'btnPrintLicense')]")
                    
                    # Scroll into view and click the details button
                    click_details_button(details_button)
                    
                    # Wait for the details page to load
                    wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_TxtName_I')))
                    
                    # Extract detailed lawyer data (alternative name, address, postal code, email, URL, mobile)
                    details_data = extract_lawyer_data()
                    
                    # Merge table row data and details data
                    full_data = {**row_data, **details_data}

                    print(full_data)  # You can remove this print statement later

                    # Save the extracted data into a CSV file
                    with open(filename, mode='a', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow([
                            full_data['full_name'], full_data['alternative_name'], full_data['greek_name'], full_data['phone'], 
                            full_data['fax'], full_data['court_box'], full_data['province'], full_data['address'], 
                            full_data['postal_code'], full_data['email'], full_data['url'], full_data['mobile']
                        ])
                    
                    if not go_back_to_main_table_at_page(current_page):
                        break

                except Exception as e:
                    print(f"Error processing row {i} on page {current_page}: {str(e)}")
                    continue # If there's an error with one row, continue to the next row

            current_page += 1

    try:
        iterate_through_table(start_page, end_page)
    finally:
        driver.quit()

# Parallelization using ThreadPoolExecutor or ProcessPoolExecutor
def run_parallel_scraping(start_page, end_page, chunk_size=5):
    """
    Runs the scraper in parallel for a range of pages, starting from start_page.

    Args:
    - start_page (int): The starting page for the scraping process.
    - end_page (int): The last page to scrape.
    - chunk_size (int): The number of pages each driver instance handles.
    """
    total_pages = end_page - start_page + 1
    num_threads = total_pages // chunk_size + 1
    # num_threads = 1  # Set the number of threads to run concurrently
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i in range(start_page - 1, end_page, chunk_size):
            page_start = i + 1
            page_end = min(i + chunk_size, end_page)
            file_suffix = f"{timestamp}_{page_start}_{page_end}"
            futures.append(executor.submit(scrape_pages, page_start, page_end, file_suffix))

        # Wait for all threads to finish
        for future in futures:
            future.result()

# Running the parallel scraper for pages 100 to 109
start_page = 1
end_page = 55
run_parallel_scraping(start_page, end_page)


