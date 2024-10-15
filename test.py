import os
import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException, TimeoutException, ElementClickInterceptedException
)
import lyricsgenius
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()

# Configuration from environment variables
GENIUS_API_TOKEN = os.getenv('GENIUS_API_TOKEN')
GENIUS_EMAIL = os.getenv('GENIUS_EMAIL')
GENIUS_PASSWORD = os.getenv('GENIUS_PASSWORD')
CHROMEDRIVER_PATH = os.getenv('CHROMEDRIVER_PATH')  # e.g., '/path/to/chromedriver'

# Validate environment variables
if not all([GENIUS_API_TOKEN, GENIUS_EMAIL, GENIUS_PASSWORD, CHROMEDRIVER_PATH]):
    raise EnvironmentError("Please ensure all required environment variables are set in the .env file.")

# Initialize Genius API client
genius = lyricsgenius.Genius(
    GENIUS_API_TOKEN,
    skip_non_songs=True,
    excluded_terms=["(Remix)", "(Live)"],
    timeout=15,
    retries=3
)

def search_song_genius(song_name, artist_name=None):
    """
    Search for a song using lyricsgenius and return the song object.
    """
    try:
        song = genius.search_song(title=song_name, artist=artist_name)
        if song:
            print(f"Found song: {song.full_title}")
            return song
        else:
            print("Song not found using lyricsgenius.")
            return None
    except Exception as e:
        print(f"Error searching for song: {e}")
        return None

def setup_selenium_driver():
    """
    Setup Selenium WebDriver with headless Chrome.
    """
    chrome_options = Options()
    #chrome_options.add_argument("--headless")  # Run in headless mode
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-dev-shm-usage")  # Overcome limited resource problems
    service = Service(executable_path=CHROMEDRIVER_PATH)
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def login_to_genius(driver, email, password):
    try:
        driver.get("https://genius.com/J-cole-she-knows-lyrics/")

        # Use WebDriverWait for more robust element detection
        try:  # Check if already logged in (e.g., profile icon)
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='UserAvatar__BaseUserAvatar-sc-1jly10v-0 ...]")) # Replace ... with the actual class(es)
            )
            print("Already logged in.")
            return True
        except TimeoutException:
            pass  # Not logged in, proceed with login

        # Check for the "Sign Up" element and initiate the process. Wait up to 10 seconds.
        signup_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign Up')]"))
        )
        signup_button.click()

        signin_link = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Sign in here')]"))
        )
        signin_link.click()


        email_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.NAME, "email")) # Or By.ID
        )

        password_field = driver.find_element(By.NAME, "password")  # Or By.ID

        email_field.send_keys(email)
        password_field.send_keys(password)


        submit_button = WebDriverWait(driver, 10).until(
           EC.element_to_be_clickable((By.XPATH, "//button[@type='submit' and contains(., 'Sign in')]")) # More flexible text match
        )
        submit_button.click()


        # Verify login more robustly (e.g., checking a profile element that only appears when logged in)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[@class='UserAvatar__BaseUserAvatar-sc-1jly10v-0 ...]")) # Replace ... with actual class name(s)
            )
            print("Logged in successfully!")
            return True
        except TimeoutException:
            print("Login failed. Could not find logged-in element.")
            return False

    except (NoSuchElementException, TimeoutException, ElementClickInterceptedException) as e: # Catch specific exceptions
        print(f"Login error: {e}")
        return False


def get_song_writers(driver, song_url):
    try:
        driver.get(song_url)

        # Wait for the writers section to load (more robust)
        writers_div = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(@class,'ContributorsCreditMetadataItem__Artists')]")) # Correct class
        )


        writer_links = writers_div.find_elements(By.TAG_NAME, "a")  # More direct
        writers = [link.text for link in writer_links if link.text]  # Handle potential empty links

        if writers:
            return writers
        else:
            print("No writers found or writer links have no text content.")
            return []  # Return empty list rather than None to avoid issues later

    except Exception as e: # Include TimeoutException if WebDriverWait is used
         print(f"Error getting writers: {e}")
         return None

def main():
    # Initialize Selenium WebDriver
    driver = setup_selenium_driver()

    # Log into Genius
    logged_in = login_to_genius(driver, GENIUS_EMAIL, GENIUS_PASSWORD)
    if not logged_in:
        print("Failed to log in to Genius. Exiting script.")
        driver.quit()
        return

    # Search for the song using lyricsgenius
    song_name = "Just Dance"
    artist_name = "Lady Gaga"  # Optional: specify the artist for more accurate results
    song = search_song_genius(song_name, artist_name)

    if song:
        print(f"Song URL: {song.url}")

        # Scrape the song page to find the writers
        writers = get_song_writers(driver, song.url)
        if writers:
            print("Writers of the song:", ', '.join(writers))
        else:
            print("Could not retrieve the writers.")
    else:
        print("Song not found.")

    # Close the Selenium WebDriver
    driver.quit()

if __name__ == "__main__":
    main()
