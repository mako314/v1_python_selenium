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

    print(
        """Launching Chrome with options::
            ├─ Arg 1:        --start-maximized
            ├─ Arg 3:        --no-sandbox
            └─ Arg 2:        --disable-blink-features=AutomationControlled"""
    )
    logger.debug(
        """Launching Chrome with options::
            ├─ Arg 1:        --start-maximized
            ├─ Arg 3:        --no-sandbox
            └─ Arg 2:        --disable-blink-features=AutomationControlled"""
    )
    
    # Chrome service should be able to find chrome if its installed, otherwise can give it a path to use.
    try:
        service = ChromeService()
        driver = webdriver.Chrome(service=service, options=chrome_options)
        return driver
        
    except Exception as chrome_error:
        print(f"Failed to launch Chrome: {chrome_error}")
        logger.critical(f"Failed to launch Chrome: {chrome_error}")
        raise

def go_to_next_page(driver):
    try:
        logger.info('Attempting to navigate to next page for more results')

        # <a> tag that leads to next page
        next_button = WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, "pnnext"))
        )
        # Get link & navigate to next page
        href = next_button.get_attribute("href")
        if href:
            driver.get(href)
            print("\nSUCCESS | Navigated to NEXT PAGE via href.")
            print("-" * 50)
            logger.info('SUCCESS | Navigated to NEXT PAGE via href')
            return True
        else:
            print("FAIL | Next button has no href.")
            logger.info('FAIL | unable to navigate to NEXT PAGE via href')
            return False

    except (NoSuchElementException, ElementClickInterceptedException, TimeoutException) as e:
        print(f"Next button not found or not clickable: {e}")
        logger.warning(f'Next button not found or not clickable. Results may be missing total requested count. Error: {e}')
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
        print('Search submitted using RETURN key')
        logger.info('Search submitted using RETURN key')
        
    except TimeoutException:
        print("Search box not found - Google page structure may have changed")
        logger.error("Search box Id (APjFqb) not found within timeout")
        return False
    except Exception as e:
        print(f"Error interacting with search box: {e}")
        logger.error(f"Error interacting with search box: {e}")
        return False

    return True

def extract_search_results(driver, max_results, results_accum=None, current_page_number = 1):
    # Max_results we want from user input
    max_results = max_results or 5
    # Hold all results
    results_accum = results_accum or []

    # Try to find results, can be found in #search too, but #rso more consistent from research 
    try:
        logger.info(f'Page [{current_page_number}] | Looking for search results...')
        print(f"\nPage [{current_page_number}] | Looking for search results...")

        # Wait for search results to load
        title_elements = WebDriverWait(driver, 15).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "#rso a > h3")
            )
        )

        print(f'Page [{current_page_number}] | Found {len(title_elements)} search result titles\n')
        print("-" * 50)
        
        logger.info(f'Page [{current_page_number}] | Found {len(title_elements)} search result titles')
    
    except TimeoutException:
        print(f"Page [{current_page_number}] | Search results not found within timeout - page may not have loaded properly")
        logger.error(f'Page [{current_page_number}] | Search results not found within timeout - page may not have loaded properly')
        # return False
        return results_accum, 0
    except Exception as e:
        print(f"Page [{current_page_number}] | Error finding search results: {e}")
        logger.error(f"Page [{current_page_number}] | Error finding search results: {e}")
        # return False
        return results_accum, 0

    # Extract results, return # extracted to main
    successful_results = 0

    # Process results until we've cleared all results on this page
    for i, title_element in enumerate(title_elements):
        # stop all processing after we've reached max results requested
        if successful_results >= max_results:
            logger.info(f'Finished retrieving last {max_results} search results on page {current_page_number}.')
            break
        # Try not to break anything as we get text & URL
        try:
            # Get the title text
            title_text = title_element.get_attribute("textContent")
            print(f'Page [{current_page_number}]')

            # Check if element is actually displayed 
            if not title_element.is_displayed():
                print(f"Page [{current_page_number}] | Skipping non-visible result: {title_text} at result {i + 1}")
                print("-" * 50)
                logger.info(f"Page [{current_page_number}] | Result {i + 1}. SKIPPING {title_text} | Element not displayed OR visible")
                continue

            
            # Get ancestor element to extract URL, traverse back up in XPATH
            # No need to wait or anything, we already have element through title_element
            link_element = title_element.find_element(By.XPATH, "./ancestor::a")
            link_url = link_element.get_attribute("href")

            if title_text:
                # Store for cleaner logs
                results_accum.append({
                "title": title_text,
                "url": link_url if link_url is not None else "No Url Found"
            })
                # Increment return result
                successful_results += 1
                print(f"Result {i + 1} Title: {title_text}")
                print(f"Result {i + 1} URL: {link_url}")
                print("-" * 50)
                logger.info(f"Page [{current_page_number}] | Result {i + 1}: {title_text} | URL: {link_url}")
            else:
                print(f"Page [{current_page_number}] | Empty title found at position {i + 1}")
                print("-" * 50)
                logger.warning(f"Page [{current_page_number}] | Empty title found at position {i + 1}")
                
        except NoSuchElementException:
            print(f"Page [{current_page_number}] | Could not find link for result {i + 1} - skipping")
            print("-" * 50)
            logger.warning(f"Page [{current_page_number}] | Could not find link for result {i + 1} - skipping")
            

        except Exception as e:
            print(f"Page [{current_page_number}] | Error processing result {i + 1}: {e}")
            logger.warning(f"Page [{current_page_number}] | Error processing result {i + 1}: {e}")
    
    return results_accum, successful_results

def main():
    # Flags & Parameters
    driver, search_term, result_count, fresh_log = None, "OpenAi", 5, False
    
    # Optional CLI args for better experience
    args = get_cli_args()
    # config = vars(args)  #  dict instead of Namespace
    # print(config)
    today = datetime.now()
    date_time_str = today.strftime("%Y-%m-%d %H:%M:%S")

    # Argument to clear log file, 'create entry' or new log
    if args.clean:
        fresh_log = True
        print("Clearing logs...")
        # print('DateTime String:', date_time_str)
        clear_log_file()
        logger.info(f"NEW Log created: {date_time_str}")
    else:
        logger.info(f"Log ENTRY created at: {date_time_str}")


    # Retrieve user search term
    if args.search:
        #print(f"Searching for: {args.search}")
        search_term = args.search

    # Retrieve user result count
    if args.result_count:
        # print(f"Retrieving {args.result_count} results")
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
        print(
            f"""User Search Request:
            ├─ Query:          {search_term}
            ├─ Result Count:   {result_count}
            └─ Fresh Log:      {fresh_log}"""
        )

        print("Beginning Automated Google Search with Selenium")
        logger.info("Beginning Automated Google Search with Selenium")

        # Setup Chrome driver
        driver = setup_chrome_driver()
        
        # Perform search w/ driver
        if not perform_search(driver, search_term):
            # Fail if we dont arrive on search page
            exit_program_fail()

        # Hold all results and success count of retrieved titles
        all_results = []
        successful_results = 0
        # Start on first page
        pages_processed = 1

        logger.info(" ### Successfully reached search page, now beginning title extraction ### ")

        # Loop until we have the desired result amount 
        while successful_results < result_count:
            print(f"Processing PAGE [{pages_processed}].")
            logger.info(f"Processing PAGE [{pages_processed}].")

            # Amount left to get
            needed = result_count - successful_results
            # Call search method
            all_results, count_results_extracted = extract_search_results(driver, max_results=needed, results_accum=all_results, current_page_number=pages_processed)
            # add successes
            successful_results += count_results_extracted
            
            # Finish if met result request count
            if successful_results >= result_count:
                print(f"Process COMPLETE collected: {successful_results}/{result_count} results.")
                logger.info(f"Process COMPLETE collected {successful_results}/{result_count} results.")
                break
            else:
                print(f"Page [{pages_processed}] | Processed and collected {successful_results}/{result_count}. Going to next page...")
                logger.info(f"Page [{pages_processed}] | Processed and collected {successful_results}/{result_count}. Going to next page...")
                pages_processed +=1

            
            if not go_to_next_page(driver):
                print("Next page not available. Ending search.")
                break

        print("\nSearch Results Summary:")
        logger.info("Search Results Summary:")

        for i, result in enumerate(all_results, start=1):
            print(f"{i}. Title: {result['title']} | Url: {result['url']}")
            logger.info(f"{i}. Title: {result['title']} | Url: {result['url']}")

    
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

