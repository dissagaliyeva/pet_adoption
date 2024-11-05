from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import pandas as pd
import os
import re

FILENAME = 'data/scraped_data.csv'
CLEAN_FILENAME = 'data/clean_data.csv'

PETS_OPTIONS = ['cat', 'dog', 'rabbit', 'horse', 'bird', 'fish', 'chinchila', 'degu', 'ferret', 'gerbil', 'guinea pig',
                'hamster', 'hedgehog', 'mouse', 'prairie dog', 'rat', 'skunk', 'sugar glider', 'alpaca', 'cow', 'goat', 'llama',
                'pig', 'pot bellied', 'sheep', 'amphibian', 'fish', 'other animal', 'reptile', 'salamander', 'snake', 'toad', 
                'tortoise', 'turtle']

URL = 'https://www.petfinder.com/'

def setup():
    
    # set the chrome options to run in headless mode
    options = webdriver.Options()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
        
    # initiate a webdriver
    driver = webdriver.Chrome(options=options)
    driver.get(URL)                 # open the url
    time.sleep(5)                   # wait to load the page 
    
    return driver


def scrape_data(pet, location, n_pets):
    driver = setup()
    
    # initialize an explicit wait with a longer timeout
    wait = WebDriverWait(driver, 15)

    # wait for the pet type field to be clickable, then enter the pet type
    search_field_pet = wait.until(EC.element_to_be_clickable((By.ID, 'simpleSearchAnimalType')))
    search_field_pet.click()
    search_field_pet.send_keys(pet)
    time.sleep(1)  

    # wait for the value to be entered in the pet field
    wait.until(lambda driver: driver.find_element(By.ID, 'simpleSearchAnimalType').get_attribute('value') == pet)

    # wait for the location field, click, and enter the location
    search_field_location = wait.until(EC.element_to_be_clickable((By.ID, 'simpleSearchLocation')))
    search_field_location.click()
    search_field_location.send_keys(location)
    time.sleep(1)  

    # wait for the value to be entered in the location field
    wait.until(lambda driver: driver.find_element(By.ID, 'simpleSearchLocation').get_attribute('value') == location)

    # wait for the search button to be clickable, then click it
    search_button = wait.until(EC.element_to_be_clickable((By.ID, 'petSearchBarSearchButton')))
    search_button.click()

    # wait for the redirection to complete and the results container to be visible
    wait.until(EC.visibility_of_element_located((By.XPATH, '//*[@id="Site"]/div/div/div[2]/pfdc-animal-search/div/div/div[2]/div[2]/div[2]/pfdc-animal-search-results/div')))

    counter = 0

    while True:
        
        if isinstance(n_pets, int):
            if n_pets > counter:
                print(f'Scraped {n_pets} pets, aborting...')
                break
        
        # find the animal cards container
        animal_cards_container = driver.find_element(By.XPATH, '//*[@id="Site"]/div/div/div[2]/pfdc-animal-search/div/div/div[2]/div[2]/div[2]/pfdc-animal-search-results/div')

        # find all individual animal cards
        animal_cards = animal_cards_container.find_elements(By.CLASS_NAME, 'petCard')

        for card in animal_cards:
            # get the link to the animal's profile
            profile_link = card.find_element(By.CSS_SELECTOR, 'a.petCard-link').get_attribute('href')

            # open the profile link in a new window
            driver.execute_script("window.open(arguments[0]);", profile_link)
            driver.switch_to.window(driver.window_handles[-1])

            # wait for the profile page to load
            WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))

            try:
                pet_name_element = WebDriverWait(driver, 15).until(
                    EC.visibility_of_element_located((By.XPATH, '//*[@data-test="Pet_Name"]'))
                )
                pet_name = pet_name_element.text
            except:
                pet_name = None
            
            # extract pet details with safer handling
            try:
                pet_age = driver.find_element(By.XPATH, '//*[@data-test="Pet_Age"]').text
            except:
                pet_age = None

            try:
                pet_sex = driver.find_element(By.XPATH, '//*[@data-test="Pet_Sex"]').text
            except:
                pet_sex = None

            try:
                pet_size = driver.find_element(By.XPATH, '//*[@data-test="Pet_Full_Grown_Size"]').text
            except:
                pet_size = None

            try:
                pet_color = driver.find_element(By.XPATH, '//*[@data-test="Pet_Primary_Color"]').text
            except:
                pet_color = None
                
            try:
                characteristics = driver.find_element(By.XPATH, '//dt[text()="Characteristics"]/following-sibling::dd').text
            except:
                characteristics = None

            try:
                coat_length = driver.find_element(By.XPATH, '//dt[text()="Coat length"]/following-sibling::dd').text
            except:
                coat_length = None

            try:
                house_trained = driver.find_element(By.XPATH, '//dt[text()="House-trained"]/following-sibling::dd').text
            except:
                house_trained = None

            try:
                health = driver.find_element(By.XPATH, '//dt[text()="Health"]/following-sibling::dd').text
            except:
                health = None

            try:
                address_city = driver.find_element(By.XPATH, '//span[@itemprop="addressLocality"]').text
            except:
                address_city = None

            try:
                address_region = driver.find_element(By.XPATH, '//span[@itemprop="addressRegion"]').text
            except:
                address_region = None

            full_address = f"{address_city}, {address_region}" if address_city and address_region else None

            # Contact details
            try:
                email = driver.find_element(By.XPATH, '//*[@id="Site"]/div/div/div[1]/div/div[2]/div[3]/div[3]/ul/li[2]/div[2]/pf-ensighten/a').text
            except:
                email = None

            try:
                phone = driver.find_element(By.XPATH, '//a[@data-test="Shelter_Telephone_Link"]/span[@itemprop="telephone"]').text
            except:
                phone = None

            # save data to CSV
            pd.DataFrame({
                'Name': [pet_name],
                'Age': [pet_age],
                'Sex': [pet_sex],
                'Size': [pet_size],
                'Color': [pet_color],
                'Characteristics': [characteristics],
                'Coat Length': [coat_length],
                'House Trained': [house_trained],
                'Health': [health],
                'City': [address_city],
                'Region': [address_region],
                'Full Address': [full_address],
                'Email': [email],
                'Phone': [phone],
                'Profile': [profile_link]
            }).to_csv(FILENAME, mode='a', index=False, header=not os.path.exists(FILENAME))

            # close the new window and switch back to the main window
            driver.close()
            driver.switch_to.window(driver.window_handles[0])
            
        try:
            # wait for the "Next" button to be present and visible
            next_button = wait.until(EC.presence_of_element_located(
                (By.XPATH, '//button[contains(@class, "fieldBtn") and .//span[text()="Next"]]'))
            )
            
            driver.execute_script("arguments[0].click();", next_button)
            time.sleep(2)
        except Exception as e:
            print("No more pages to scrape or unable to locate 'Next' button.")
            break

    # close the driver after finishing
    driver.quit()
    
    
def clean_data():
    data = pd.read_csv(FILENAME)
    data['Full Address'] = data['Full Address'].apply(lambda x: x.replace(',,', ','))
    data.drop(columns=['City', 'Region'], inplace=True)
    data.rename(columns={'Full Address': 'State'}, inplace=True)
    data['Phone'] = data['Phone'].apply(lambda x: '+1' + re.sub(r'\D', '', x))
    data.to_csv(CLEAN_FILENAME, index=False)
    

if __name__ == "__main__":    
    import argparse
    
    arg_parser = argparse.ArgumentParser(description="Set animal and location to search")
    arg_parser.add_argument('--pet', type=str, help='Pet species', required=True, default='Cat')
    arg_parser.add_argument('--location', type=str, help='Location', required=True, default='Washington DC')
    arg_parser.add_argument('--n_pets', type=str, help='Number of pets to scrape', required=True, default='all')
    
    args = arg_parser.parse_args()

    # extract arguments
    pet = args.pet
    location = args.location
    n_pets = args.n_pets
    
    assert pet.lower() in PETS_OPTIONS, f'The selected species `{pet}` does not exist. Please select one of the following: {", ".join(PETS_OPTIONS)}'
    
    # delete previous entries
    if os.path.exists(FILENAME):
        os.remove(FILENAME)
        os.remove(CLEAN_FILENAME)
    
    # preprocess number of animals
    try:
        n_pets = int(n_pets) if n_pets != 'all' else n_pets
        
        print('Starting the scraper...')
        scrape_data(pet, location, n_pets)
        clean_data()
        
    except:
        print("Can't process the argument. Please select digits or `all` option...")
    
    