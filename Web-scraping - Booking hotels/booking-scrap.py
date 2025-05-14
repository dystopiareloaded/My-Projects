from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException, TimeoutException
from tqdm import tqdm
import time
from bs4 import BeautifulSoup
import re
import pandas as pd

url = 'https://www.booking.com/searchresults.html?label=gen173nr-1FCAEoggI46AdIM1gEaGyIAQGYATG4ARfIAQzYAQHoAQH4AQKIAgGoAgO4AtSmksEGwAIB0gIkMGM2NTE2ZjgtMWIyYi00MzgxLWExNTMtODhkOTIzMTIxZGE52AIF4AIB&aid=304142&ss=Kolkata&ssne=Kolkata&ssne_untouched=Kolkata&lang=en-us&src=index&dest_id=-2092511&dest_type=city&checkin=2025-05-14&checkout=2025-05-15&group_adults=2&no_rooms=1&auth_success=1&account_created=1'

# Setup
driver = webdriver.Chrome()
driver.get(url)
wait = WebDriverWait(driver, 10)

# 1. Grid view selection
try:
    grid_switch = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="bodyconstraint-inner"]/div/div/div[2]/div[3]/div[2]/div[1]/div/span/label[2]')))
    grid_switch.click()
    print("✅ Grid view selected.")
    time.sleep(2)
except Exception as e:
    print("⚠️ Grid switch not found or clickable:", e)

# 2. Apply filter
try:
    filter_xpath = '//div[contains(@id, "filter_group_popular")]/div[6]/label'
    filter_element = wait.until(EC.element_to_be_clickable((By.XPATH, filter_xpath)))
    filter_element.click()
    print("✅ Filter applied.")
    time.sleep(2)
except Exception as e:
    print("⚠️ Filter not found or not clickable:", e)

# 3. Infinite scroll with Load More if available
print("🔄 Starting infinite scroll...")
scroll_pause = 2
last_height = driver.execute_script("return document.body.scrollHeight")
pbar = tqdm(desc="Scrolling", unit="scroll")

while True:
    # Try clicking 'Load More' if it exists
    try:
        load_more = WebDriverWait(driver, 3).until(
            EC.element_to_be_clickable((By.XPATH, '//*[@id="bodyconstraint-inner"]/div/div/div[2]/div[3]/div[2]/div[2]/div[3]/div[3]/button'))
        )
        driver.execute_script("arguments[0].click();", load_more)
        print("🟢 Clicked 'Load more'")
        time.sleep(2)
    except (TimeoutException, NoSuchElementException):
        pass  # It's okay if there's no button

    # Scroll to bottom
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(scroll_pause)

    # Check for new content
    new_height = driver.execute_script("return document.body.scrollHeight")
    pbar.update(1)

    if new_height == last_height:
        print("🛑 No more content to load.")
        break

    last_height = new_height

# Done scrolling — get page source
print("✅ Scrolling complete.")

# Scrape

html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')

hotels = soup.find_all('div', class_='afd3558156 ac28d37f07')

name, location, price, ratings, reviews, reviews_score = [], [], [], [], [], []

for hotel in hotels:
    name_tag = hotel.find('div', class_= 'e7addce19e a3e0b4ffd1').text.strip()
    #print(name_tag)
    name.append(name_tag)

    location_tag = hotel.find('span', class_='d823fbbeed f9b3563dd4').text.strip()
    #print(location_tag)
    location.append(location_tag)

    price_tag = hotel.find('span', {'data-testid': 'price-and-discounted-price'})

    if price_tag:
        price_text = price_tag.get_text(strip=True)
        price_number = re.sub(r'[^\d]', '', price_text)  # Keep only digits
        #print(price_number)  # Output: 1363
    else:
        price_number = None
    #print(price_number)    
    price.append(price_number)

    reviews_tag = hotel.find('span', class_='fff1944c52 f546354b44 becbee2f63')
    if reviews_tag is not None:
        reviews_tag = reviews_tag.text.strip()
    else:
        reviews_tag = 'No Reviews'
    #print(reviews_tag)
    reviews.append(reviews_tag)

    reviews_score_tag = hotel.find('span', class_='fff1944c52 fb14de7f14 eaa8455879')
    if reviews_score_tag is not None:
        reviews_score_text = reviews_score_tag.text.strip()
        reviews_count = int(re.sub(r'[^\d]', '', reviews_score_text))
        #print(reviews_count)  # ✅ This will print just: 6
    else:
        reviews_count = 'Not Available'
    #print(reviews_count)
    reviews_score.append(reviews_count)


    ratings_tag = hotel.find('div', class_='fff1944c52 dff2e52086')
    if ratings_tag is not None:
        ratings_tag = ratings_tag.text.strip()
    else:
        ratings_tag = 'No Ratings'
    #print(ratings_tag)
    ratings.append(reviews_tag)

    #print('------------')
    #break

# Create Datasets

df = pd.DataFrame({
    'Name': name,
    'Location': location,
    'Price': price,
    'Ratings': ratings,
    'Reviews': reviews,
    'Reviews Score': reviews_score
})

# Save to csv file
df.to_csv('Hotels_of_Kolkata.csv', index= False)

# Option to keep the browser open for debugging
input("Press Enter to close the browser...")

# Close browser
driver.quit()