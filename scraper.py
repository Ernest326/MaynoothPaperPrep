import cloudscraper
from bs4 import BeautifulSoup
import os
import threading
import logging

logger = logging.getLogger(__name__)


class Scraper:
    def __init__(self, allowed_years=None):
        logger.debug("Initializing Scraper instance")
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )
        self.url = "https://www.maynoothuniversity.ie/library/exam-papers"
        logger.debug(f"Scraper initialized with URL: {self.url}")
        if allowed_years is None:
            self.allowed_years = set(str(year) for year in range(2020, 2026))
        else:
            self.allowed_years = set(str(y) for y in allowed_years)

    def start(self, username, password, module_code, output_folder):
        logger.info("=" * 50)
        logger.info(f"Starting scraper for module: {module_code}")
        logger.info("=" * 50)
        logger.debug(f"Username: {username[:4]}****")
        logger.debug(f"Output folder: {output_folder}")

        logger.info("Fetching login page...")
        login_page = self.session.get(self.url)
        logger.debug(f"Login page status code: {login_page.status_code}")
        logger.debug(f"Login page content length: {len(login_page.text)} bytes")

        # Scrape the hidden form_build_id from the login page
        soup = BeautifulSoup(login_page.text, "html.parser")
        logger.debug("Parsed login page HTML with BeautifulSoup")

        # Check if we login form exists, so we don't try to login twice
        if soup.find("input", {"name": "form_build_id"}):
            logger.info("Login form detected, proceeding with authentication")

            form_build_id = soup.find("input", {"name": "form_build_id"})["value"]
            logger.debug(f"Extracted form_build_id: {form_build_id[:10]}...")

            # POST credentials for login
            login_data = {
                "name": username,
                "pass": password,
                "form_id": "user_login",
                "form_build_id": form_build_id,
            }
            logger.debug("Prepared login payload")

            logger.info("Submitting login credentials...")
            res = self.session.post(self.url, data=login_data)
            logger.debug(f"Login response status code: {res.status_code}")
            logger.debug(f"Login response content length: {len(res.text)} bytes")

            if res.status_code != 200:
                logger.error(f"Login failed with status code: {res.status_code}")
                logger.debug(f"Response headers: {dict(res.headers)}")
                return "Error: Invalid credentials"
            logger.info("Login successful")
        else:
            logger.info("No login form found - already authenticated or login not required")

        # Fetch the exam papers
        exam_data = {"code_value_1": module_code}
        logger.debug(f"Exam query parameters: {exam_data}")

        logger.info(f"Fetching exam papers for module {module_code}...")
        res = self.session.get(self.url, params=exam_data)
        logger.debug(f"Exam papers response status code: {res.status_code}")
        logger.debug(f"Exam papers response URL: {res.url}")

        if res.status_code != 200:
            logger.error(f"Failed to fetch exam papers: HTTP {res.status_code}")
            return "Error: Unable to fetch exam papers"

        soup = BeautifulSoup(res.text, "html.parser")
        logger.info("Exam papers page fetched and parsed successfully")

        # Find the download links for the papers
        logger.info("Scanning page for PDF download links...")

        papers = []
        all_links = soup.find_all("a", href=True)
        logger.debug(f"Found {len(all_links)} total links on page")

        for a_tag in all_links:
            href = a_tag["href"]
            if href.endswith(".pdf"):
                papers.append(href)
                logger.debug(f"Found PDF link: {href}")

        if not papers:
            logger.warning(f"No papers found for module {module_code}")
            return "No papers found for this module"

        logger.info(f"Found {len(papers)} PDF papers to download")

        # Download the papers
        output_path = f"{output_folder}/{module_code}/papers"
        logger.info(f"Preparing to download papers to: {output_path}")

        # Create the output directory if it doesn't exist
        if not os.path.exists(output_path):
            os.makedirs(output_path)
            logger.info(f"Created output directory: {output_path}")
        else:
            logger.debug(f"Output directory already exists: {output_path}")

        # Filter papers by year in the filename (e.g., "2020", "2021", etc.)
        allowed_years = self.allowed_years
        filtered_papers = []
        for paper in papers:
            filename = paper.split('/')[-1]
            # Look for a 4-digit year in the filename
            for year in allowed_years:
                if year in filename:
                    filtered_papers.append(paper)
                    logger.debug(f"Including paper for year {year}: {filename}")
                    break
            else:
                logger.debug(f"Excluding paper (year not in allowed range): {filename}")

        if not filtered_papers:
            logger.warning(f"No papers found for module {module_code} in years {min(allowed_years)}-{max(allowed_years)}")
            return f"No papers found for this module in years {min(allowed_years)}-{max(allowed_years)}"

        # Download papers in parallel using threads
        threads = []
        self._progress_count = 0
        total = len(filtered_papers)
        logger.info(f"Starting parallel download of {total} papers...")

        def progress_update():
            self._progress_count += 1
            logger.debug(f"Download progress: {self._progress_count}/{total}")
            if hasattr(self, "progress_callback") and callable(self.progress_callback):
                self.progress_callback(self._progress_count, total)

        for i, paper in enumerate(filtered_papers):
            logger.debug(f"Creating download thread {i+1}/{total} for: {paper.split('/')[-1]}")
            thread = threading.Thread(
            target=self.download_paper,
            args=(paper, output_folder, module_code, progress_update),
            )
            threads.append(thread)
            thread.start()

        logger.debug(f"All {len(threads)} download threads started")

        # Wait for all threads to complete
        logger.info("Waiting for all downloads to complete...")
        for i, thread in enumerate(threads):
            thread.join()
            logger.debug(f"Thread {i+1}/{len(threads)} completed")

        logger.info("=" * 50)
        logger.info(f"All {total} papers downloaded successfully")
        logger.info(f"Scraping completed for module: {module_code}")
        logger.info("=" * 50)

        return True

    def download_paper(self, url, output_folder, module_code, progress_update=None):
        filename = url.split("/")[-1]
        file_path = f"{output_folder}/{module_code}/papers/{filename}"

        logger.debug(f"Starting download: {filename}")
        logger.debug(f"Source URL: {url}")

        response = self.session.get(url)
        logger.debug(f"Download response status: {response.status_code} for {filename}")

        if response.status_code == 200:
            content_length = len(response.content)
            logger.debug(f"Downloaded {content_length} bytes for {filename}")

            # Check if file exists already
            if os.path.isfile(file_path):
                logger.info(f"Paper already exists, skipping: {filename}")
                if progress_update:
                    progress_update()
                return

            # If not, download the file
            logger.debug(f"Writing file to: {file_path}")
            with open(file_path, "wb") as f:
                f.write(response.content)
            logger.info(f"Successfully downloaded: {filename} ({content_length} bytes)")
            if progress_update:
                progress_update()
        else:
            logger.error(f"Failed to download {filename}: HTTP {response.status_code}")
            logger.debug(f"Failed URL: {url}")
            if progress_update:
                progress_update()
