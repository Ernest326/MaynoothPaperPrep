import requests
from bs4 import BeautifulSoup
import json
import logging

logger = logging.getLogger(__name__)

courses_url = "https://www.maynoothuniversity.ie/international/study-maynooth/available-courses"
department_links = list()

# Fetch all module codes from the available courses page
def fetch_deparments():
    logger.info("=" * 50)
    logger.info("Fetching department links from Maynooth website")
    logger.info("=" * 50)
    logger.debug(f"Courses URL: {courses_url}")

    response = requests.get(courses_url)
    logger.debug(f"Response status code: {response.status_code}")
    logger.debug(f"Response content length: {len(response.text)} bytes")

    soup = BeautifulSoup(response.text, 'html.parser')
    logger.debug("Parsed HTML with BeautifulSoup")

    links = soup.find_all('a', href=True)
    logger.debug(f"Found {len(links)} total links on page")

    for link in links:
        href = link['href']
        if "available-courses" in href:
            department_links.append(href)
            logger.debug(f"Found department link: {href}")

    logger.info(f"Discovered {len(department_links)} department links")

# Fetch all modules from the deparment pages
def fetch_modules():
    logger.info("=" * 50)
    logger.info("Fetching modules from department pages")
    logger.info("=" * 50)

    modules = []
    for i, link in enumerate(department_links):
        logger.info(f"Processing department {i+1}/{len(department_links)}: {link}")
        try:
            response = requests.get(link)
            response.raise_for_status()
            logger.debug(f"Response status: {response.status_code}, length: {len(response.text)} bytes")

            soup = BeautifulSoup(response.text, 'html.parser')

            table = soup.find('tbody')
            if table:
                rows = table.find_all('tr')
                logger.debug(f"Found {len(rows)} rows in table for {link}")

                department_modules_count = 0
                for row in rows:
                    columns = row.find_all('td')
                    if len(columns) > 2:  # Ensure there are enough columns
                        module = {
                            "name": columns[0].get_text(strip=True),
                            "index": columns[1].get_text(strip=True),
                            "semester": columns[3].get_text(strip=True),
                            "deparment": link.split('/')[-1].replace('-', ' ').title()
                        }
                        modules.append(module)
                        department_modules_count += 1
                        logger.debug(f"Added module: {module['index']} - {module['name']}")

                logger.info(f"Found {department_modules_count} modules in department")
            else:
                logger.warning(f"No <tbody> found for {link}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching {link}: {e}")
            logger.exception("Full exception details:")

    logger.info(f"Total modules collected: {len(modules)}")
    logger.debug("Sorting modules by index")
    modules = sorted(modules, key=lambda x: (x['index']))  # Sort by name and index
    logger.info("Modules sorted successfully")
    return modules

# Run the scraper and save the data to a JSON file
def run():
    logger.info("=" * 60)
    logger.info("Starting Module Scraper")
    logger.info("=" * 60)

    logger.info("Step 1: Fetching departments")
    fetch_deparments()

    logger.info("Step 2: Fetching modules from departments")
    modules = fetch_modules()

    logger.info("Step 3: Writing modules to JSON file")
    json_data = json.dumps(modules, indent=4)
    output_file = "modules.json"
    logger.debug(f"JSON data size: {len(json_data)} characters")

    with open(output_file, "w") as f:
        f.write(json_data)

    logger.info(f"Successfully wrote {len(modules)} modules to {output_file}")
    logger.info("=" * 60)
    logger.info("Module Scraper completed")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Configure logging when running as standalone script
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('module_scraper.log')
        ]
    )
    logger.info("Running module_scraper as standalone script")
    run()