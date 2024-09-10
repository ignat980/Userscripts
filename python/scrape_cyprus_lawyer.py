from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import datetime
import time
import csv

# Initialize WebDriver
driver = webdriver.Chrome()

# Wait for the page to load
wait = WebDriverWait(driver, 10)

# Open the Cypriot Advocates members page
driver.get('https://www.cyprusbar.org/CypriotAdvocateMembersPage')

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

def go_back_to_main_table(current_page):
    """
    Navigate back to the main table after extracting details and go to the correct page.
    """
    driver.back()  # Go back to the main table
    wait.until(EC.presence_of_element_located((By.ID, 'ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable')))  # Wait for the table to load
    # Navigate back to the current page
    if current_page > 1:
        click_next_page(current_page)

def click_next_page(target_page):
    """
    Clicks the next visible page link or the highest visible page link until the target page is reached,
    while excluding the last three pages until necessary.
    """
    try:
        while True:
            # Get all visible page numbers excluding the last three
            visible_pages = driver.find_elements(By.XPATH, "//a[contains(@class, 'dxp-num')]")
            current_highest_visible_page = int(visible_pages[-4].text)  # Exclude the last three pages

            # If the target page is within the visible range
            if target_page <= current_highest_visible_page:
                target_page_element = driver.find_element(By.XPATH, f"//a[contains(@onclick, 'PN{target_page - 1}') and contains(@class, 'dxp-num')]")
                target_page_element.click()
                wait.until(EC.presence_of_element_located((By.XPATH, f"//b[contains(@class, 'dxp-current') and contains(., '{target_page}')]")))
                break

            # If we are approaching the last three pages (435, 436, 437), include them
            elif target_page >= 435:
                target_page_element = driver.find_element(By.XPATH, f"//a[contains(@onclick, 'PN{target_page - 1}') and contains(@class, 'dxp-num')]")
                target_page_element.click()
                wait.until(EC.presence_of_element_located((By.XPATH, f"//b[contains(@class, 'dxp-current') and contains(., '{target_page}')]")))
                break

            else:
                # Click the highest visible page to reveal more pages, wait until the new highest page appears
                visible_pages[-4].click()
                next_highest_page = str(current_highest_visible_page + 1)

                # Wait until the next set of pages is loaded (wait for the next highest page to be visible)
                wait.until(EC.presence_of_element_located((By.XPATH, f"//a[contains(@class, 'dxp-num') and contains(., '{next_highest_page}')]")))
                time.sleep(0.4)  # Wait for the page to load

    except Exception as e:
        print(f"No more pages to navigate: {str(e)}")
        return False

    return True




def iterate_through_table():
    """
    Iterates through all rows on each table page, scraping data and moving to the next page.
    """
    current_page = 101
    while True:
        # Re-fetch the rows on each iteration after page navigation
        rows = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable']/tbody/tr[contains(@id, 'DXDataRow')]")))
        
        for i in range(len(rows)):
            try:
                # Re-fetch the rows inside the loop to avoid stale element error
                rows = driver.find_elements(By.XPATH, "//table[@id='ctl00_ContentPlaceHolder1_LawyersGrid_DXMainTable']/tbody/tr[contains(@id, 'DXDataRow')]")
                
                # Extract row data (name, greek name, phone, fax, court box, province)
                row_data = extract_table_row_data(rows[i])

                # Click on the "Details" button for additional data
                details_button = rows[i].find_element(By.XPATH, ".//a[contains(@id, 'btnPrintLicense')]")
                details_button.click()

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

                
                # Go back to the main table and return to the current page
                go_back_to_main_table(current_page)

            except Exception as e:
                print(f"Error processing row {i} on page {current_page}: {str(e)}")
                continue  # If there's an error with one row, continue to the next row

        # Move to the next page after processing all rows in the current page
        current_page += 1
        if not click_next_page(current_page):
            break

# Start scraping and navigating through pages
try:
    # Generate filename with timestamp
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'lawyers_data_{timestamp}.csv'
    # Create the CSV and write headers
    with open(filename, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow([
            'Full Name', 'Alternative Name', 'Greek Name', 'Phone', 'Fax', 'Court Deposit Box', 'Province', 
            'Address', 'Postal Code', 'Email', 'URL', 'Mobile'
        ])
    
    iterate_through_table()
finally:
    driver.quit()
