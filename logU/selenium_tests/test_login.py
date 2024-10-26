from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import easygui
import time

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    # Set up the WebDriver
    options = webdriver.ChromeOptions()
    options.add_argument('--log-level=3')  # This will suppress info/warning/error logs
    driver = webdriver.Chrome(options=options)
    driver.maximize_window()
    logger.info("Chrome driver initialized")

    # Navigate to the login page
    url = "http://localhost:8000/login"  # No trailing slash
    driver.get(url)
    logger.info(f"Navigating to: {url}")

    # Wait for the page to load
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    logger.info(f"Page loaded. Current URL: {driver.current_url}")

    # Find and fill the email and password fields
    email_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Type your email']")))
    password_field = WebDriverWait(driver, 10).until(EC.visibility_of_element_located((By.XPATH, "//input[@placeholder='Type your password']")))

    email_field.send_keys('aleenaginu@gmail.com')
    password_field.send_keys('Aleena@1123')
    logger.info("Filled login credentials")

    # Find and click the login button
    login_button = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//button[text()='Login']")))
    login_button.click()
    logger.info("Clicked login button")

    # Wait for URL change
    try:
        WebDriverWait(driver, 10).until(EC.url_changes(url))
        logger.info(f"URL changed to: {driver.current_url}")
    except TimeoutException:
        logger.error("URL did not change after clicking login button")

    # Check if login was successful
    if driver.current_url == "http://localhost:8000/welcome/":  # Note the trailing slash
        logger.info("Login successful")
        easygui.msgbox("Testing Successful! Login successful!")
    elif driver.current_url == url:
        logger.error("Login failed. URL did not change.")
        # Try to find any error message on the page
        try:
            error_message = driver.find_element(By.XPATH, "//*[contains(text(), 'error') or contains(text(), 'invalid')]").text
            logger.error(f"Error message found: {error_message}")
            easygui.msgbox(f"Testing Failed: {error_message}")
        except NoSuchElementException:
            logger.error("No error message found on the page.")
            easygui.msgbox("Testing Failed: Login unsuccessful and no error message found")
    else:
        logger.error(f"Unexpected URL after login attempt: {driver.current_url}")
        easygui.msgbox(f"Testing Failed: Unexpected URL after login - {driver.current_url}")

    # Print page source for debugging
    logger.info("Page source after login attempt:")
    logger.info(driver.page_source)

except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    easygui.msgbox(f"Testing Failed: {str(e)}")

finally:
    # Close the browser
    if 'driver' in locals():
        driver.quit()
    logger.info("Test completed, browser closed")
