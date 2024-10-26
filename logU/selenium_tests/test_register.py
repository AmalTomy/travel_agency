from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import logging
import easygui

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def wait_and_fill(driver, by, value, text):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((by, value))
        )
        element.clear()
        element.send_keys(text)
    except TimeoutException:
        logger.error(f"Element {value} not found or not visible")
        raise

try:
    driver = webdriver.Chrome()
    driver.maximize_window()
    logger.info("Chrome driver initialized")

    url = "http://localhost:8000/signup"  # Changed from "/logU/signup/"
    driver.get(url)
    logger.info(f"Attempting to open URL: {url}")

    # Wait for the page to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )
    logger.info(f"Page loaded. Current URL: {driver.current_url}")

    # Log page title and source
    logger.info(f"Page title: {driver.title}")
    logger.info("Page source:")
    logger.info(driver.page_source)

    # Attempt to find the first form element
    try:
        fname_element = WebDriverWait(driver, 10).until(
            EC.visibility_of_element_located((By.ID, 'fname'))
        )
        logger.info("Found 'fname' element")
    except TimeoutException:
        logger.error("Could not find 'fname' element")
        raise

    # Fill out form fields
    wait_and_fill(driver, By.ID, 'fname', 'Aleena')
    wait_and_fill(driver, By.ID, 'lname', 'Ginu')
    wait_and_fill(driver, By.ID, 'phone', '9876543210')
    wait_and_fill(driver, By.ID, 'email', 'aleenaginu@gmail.com')
    wait_and_fill(driver, By.ID, 'address', 'Anster')
    wait_and_fill(driver, By.ID, 'city', 'Anytown')
    wait_and_fill(driver, By.ID, 'district', 'Central')
    wait_and_fill(driver, By.ID, 'postal_code', '123456')
    wait_and_fill(driver, By.ID, 'password', 'Aleena@123')
    wait_and_fill(driver, By.ID, 're-password', 'Aleena@1123')

    logger.info("Filled out all form fields")

    # Submit the form
    submit_button = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@type='submit' and @value='Register']"))
    )
    submit_button.click()
    logger.info("Clicked submit button")

    # Wait for URL change or any error message
    try:
        WebDriverWait(driver, 20).until(
            lambda d: d.current_url != "http://localhost:8000/signup"
        )
        logger.info(f"URL changed to: {driver.current_url}")
    except TimeoutException:
        logger.warning("URL did not change after form submission")
        # Check for any error messages on the page
        try:
            error_message = driver.find_element(By.CLASS_NAME, "error-message").text
            logger.error(f"Error message found: {error_message}")
        except NoSuchElementException:
            logger.warning("No error message found on the page")

    # Check the current URL
    current_url = driver.current_url
    if current_url in ["http://localhost:8000/login/", "http://localhost:8000/login"]:
        logger.info("Registration successful")
        easygui.msgbox("Testing Successful! User successfully registered!")
    elif current_url == "http://localhost:8000/signup":
        logger.info("Registration failed or invalid details")
        easygui.msgbox("Testing with Invalid details Successful!")
    else:
        logger.error(f"Unexpected URL after registration: {current_url}")
        easygui.msgbox("Testing Failed: Unexpected result")

except Exception as e:
    logger.error(f"An error occurred: {str(e)}")
    logger.error(f"Error type: {type(e).__name__}")
    logger.exception("Exception traceback:")
    easygui.msgbox(f"Testing Failed: {str(e)}")

finally:
    if 'driver' in locals():
        driver.quit()
    logger.info("Test completed, browser closed")