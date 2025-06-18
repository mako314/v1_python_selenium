from logger import logger, clear_log_file
from arg_config import get_cli_args
import os
import sys
import platform
from datetime import datetime

# Selenium imports
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
# from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException, ElementClickInterceptedException


# Setup chrome driver options
def setup_chrome_driver():
    chrome_options = Options()
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')

    logger.info("Launching Chrome with options:")
    print("Launching Chrome with options:")

    logger.debug(
        """User Search Request:
            ├─ Arg 1:        --start-maximized
            ├─ Arg 3:        --no-sandbox
            └─ Arg 2:        --disable-blink-features=AutomationControlled"""
    )
    
    try:
        service = ChromeService()  # Auto-find ChromeDriver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        # service = ChromeService()
        # driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
        
    except Exception as chrome_error:
        print(f"Failed to launch Chrome: {chrome_error}")
        logger.critical(f"Failed to launch Chrome: {chrome_error}")
        raise

def go_to_next_page(driver):
    try:
        # <a> tag that leads to next page
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "pnnext"))
        )
        # Get link & navigate to next page
        href = next_button.get_attribute("href")
        if href:
            driver.get(href)
            print("Navigated to next page via href.")
            return True
        else:
            print("Next button has no href.")
            return False

    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print("Next button not found or not clickable:", str(e))
        return False
    
# Performs the search
def perform_search(driver, search_term=None):
    search_term = search_term or "OpenAI"

    try:
        # Navigate to Google
        driver.get("https://www.google.com")
        title = driver.title
        url = driver.current_url
        
        print(f'Title: {title}')
        print(f'URL: {url}')
        logger.info(f'Page loaded - Title: {title}, URL: {url}')
        
    except WebDriverException as e:
        print(f"Failed to navigate to Google: {e}")
        logger.error(f"Failed to navigate to Google: {e}")
        return False

    try:
        # Find and interact with search box
        text_box = WebDriverWait(driver, 4).until(
            EC.visibility_of_element_located((By.ID, "APjFqb"))
        )
        # Type in search
        text_box.send_keys(search_term)
        print(f'Search term "{search_term}" entered successfully')
        logger.info(f'Search term "{search_term}" entered successfully')
        # Return for enter (2 btnK names, 2 different data-veds ), opted for safer text return.
        text_box.send_keys(Keys.RETURN)
        print('Search submitted using Enter key')
        logger.info('Search submitted using Enter key')
        
    except TimeoutException:
        print("Search box not found - Google page structure may have changed")
        logger.error("Search box Id (APjFqb) not found within timeout")
        return False
    except Exception as e:
        print(f"Error interacting with search box: {e}")
        logger.error(f"Error interacting with search box: {e}")
        return False

    return True

def extract_search_results(driver, max_results, results_accum=None):
    # Max_results we want from user input
    max_results = max_results or 5
    # 
    results_accum = results_accum or []

    # Try to find results, can be found possibly in #search too, but #rso apparently more consistent from research 
    try:
        logger.info('Looking for search results...')
        print("Extracting search result titles...")
        print("-" * 50)

        # Wait for search results to load
        # Class used for search results > h3 w/ class just in case
        # "#rso .MjjYud h3.LC20lb" decent, but still returns some results I dont want
        # "#rso .MjjYud h3.LC20lb.MBeuO.DKV0Md" # Not valid, worked on openai not as much on petsmart
        # "#rso a > h3.LC20lb"
        title_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#rso a > h3")
            )
        )

        print(f'Found {len(title_elements)} search result titles')
        logger.info(f'Found {len(title_elements)} search result titles')
    
    except TimeoutException:
        print("Search results not found within timeout - page may not have loaded properly")
        logger.error('Search results not found within timeout - page may not have loaded properly')
        # return False
        return results_accum, 0
    except Exception as e:
        print(f"Error finding search results: {e}")
        logger.error(f"Error finding search results: {e}")
        # return False
        return results_accum, 0

    # Extract results
    successful_results = 0
    # search_results = []
    
    # Process results until we hit desired #
    for i, title_element in enumerate(title_elements):
        if successful_results >= max_results:
            logger.info(f'Finished retrieving {max_results} search results.')
            break
        # Try not to break anything as we get text & URL
        try:
            # Get the title text
            title_text = title_element.get_attribute("textContent")
            print(f'What is the title_text: {title_text}')

            # Check if element is actually displayed 
            if not title_element.is_displayed():
                print(f"Skipping non-visible result: {title_text} at result {i + 1}")
                print("-" * 50)

                logger.info(f"Result {i + 1}. SKIPPING {title_text} | Element not displayed OR visible")
                continue


            # Get the parent link element to extract URL, traverse back up in XPATH
            link_element = title_element.find_element(By.XPATH, "./ancestor::a")
            link_url = link_element.get_attribute("href")

            if title_text:
                # Store for cleaner logs
                results_accum.append({
                "title": title_text,
                "url": link_url
            })
                successful_results += 1
                print(f"Result {i + 1}: {title_text}")
                print(f"URL: {link_url}")
                print("-" * 50)
                logger.info(f"Result {i + 1}: {title_text} | URL: {link_url}")
            else:
                print(f"Empty title found at position {i + 1}")
                print("-" * 50)
                logger.warning(f"Empty title found at position {i + 1}")
                
        except NoSuchElementException:
            print(f"Could not find link for result {i + 1} - skipping")
            print("-" * 50)

            logger.warning(f"Could not find link for result {i + 1}")
        except Exception as e:
            print(f"Error processing result {i + 1}: {e}")
            logger.warning(f"Error processing result {i + 1}: {e}")

    # If we manage to extract results > 0 < requested result 
    # if successful_results > 0:
    #     print("\nSearch Results Summary:")
    #     logger.info("Search Results Summary:")
    #     for i, result in enumerate(search_results, start=1):
    #         print(f"{i}. {result['title']}\n   {result['url']}")
    #         logger.info(f"{i}. {result['title']} | {result['url']}")

    #     print(f"Successfully extracted {successful_results} search results out of {len(title_elements)}\n")
    #     logger.info(f"Successfully extracted {successful_results} search results out of {len(title_elements)}")
    #     return True
    # else:
    #     print("No valid search results found")
    #     logger.error("No valid search results found")
    #     return False
    
    return results_accum, successful_results

def main():
    # Flags & Parameters
    driver, search_term, result_count, fresh_log = None, None, None, False
    
    # Optional CLI args for better experience
    args = get_cli_args()
    # config = vars(args)  #  dict instead of Namespace
    # print(config)

    # Argument to clear log file
    if args.clean:
        fresh_log = True
        print("Clearing logs...")

        today = datetime.now()
        date_time_str = today.strftime("%Y-%m-%d %H:%M:%S")

        # print('DateTime String:', date_time_str)
        clear_log_file()
        logger.info(f"Log created: {date_time_str}")

    # Retrieve user search term
    if args.search:
        print(f"Searching for: {args.search}")
        search_term = args.search

    # Retrieve user result count
    if args.result_count:
        print(f"Retrieving {args.result_count} results")
        result_count = args.result_count

    try:
        # Log user flags if they were ran
        # logger.info(f"User entered query: {search_term}\nRequested {result_count} results.\nIs this a fresh log: {fresh_log}")
        logger.debug(
            f"""User Search Request:
            ├─ Query:          {search_term}
            ├─ Result Count:   {result_count}
            └─ Fresh Log:      {fresh_log}"""
        )

        print(f"User entered query: {search_term}\nRequested {result_count} results.\nIs this a fresh log: {fresh_log}")

        print("Beginning Automated Google Search with Selenium")
        logger.info("Beginning Automated Google Search with Selenium")

        # Setup Chrome driver
        driver = setup_chrome_driver()
        
        # Perform search w/ driver
        if not perform_search(driver, search_term):
            exit_program_fail()
        
        # Extract results
        # if not extract_search_results(driver, result_count):
        #     exit_program_fail()

        # Hold all results and success count of retrieved titles
        all_results = []
        successful_results = 0

        # Loop until we have the desired result amount 
        while successful_results < result_count:
            needed = result_count - successful_results
            all_results, count_results_extracted = extract_search_results(driver, max_results=needed, results_accum=all_results)
            successful_results += count_results_extracted

            if successful_results >= result_count:
                break

            print(f"Collected {successful_results}/{result_count}. Going to next page...")
            if not go_to_next_page(driver):
                print("Next page not available. Ending search.")
                break

        print("\nSearch Results Summary:")
        for i, result in enumerate(all_results, start=1):
            print(f"{i}. {result['title']}\n   {result['url']}")
    

            
        exit_program_success()

    except Exception as e:
        print(f"Unexpected error occurred: {e}")
        logger.error(f"Unexpected error occurred: {e}")
        exit_program_fail()
    finally:
        # Ensure driver is always closed
        if driver:
            try:
                driver.quit()
                print("Browser closed successfully")
                logger.info("Browser closed successfully")
            except Exception as e:
                print(f"Error closing browser: {e}")
                logger.warning(f"Error closing browser: {e}")


def exit_program_success():
    print("\nSUCCESS exiting the program...")
    logger.info('SUCCESS exiting the program')
    sys.exit(0)

def exit_program_fail():
    print("FAIL Exiting the program...")
    logger.info('FAIL exiting the program')
    sys.exit(1)   

if __name__ == "__main__":
    main()

