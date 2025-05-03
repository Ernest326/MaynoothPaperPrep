import requests
from bs4 import BeautifulSoup
import os
import threading

class Scraper:
    def __init__(self):
        self.session = requests.Session()
        self.url = "https://www.maynoothuniversity.ie/library/exam-papers"

    def start(self, username, password, module_code, output_folder):
        print("Starting scraper...")
        login_page = self.session.get(self.url)

        # Scrape the hidden form_build_id from the login page
        soup = BeautifulSoup(login_page.text, "html.parser")

        # Check if we login form exists, so we don't try to login twice
        if soup.find("input", {"name": "form_build_id"}):
            
            form_build_id = soup.find("input", {"name": "form_build_id"})["value"]
            # POST credentials for login
            login_data = {
                "name": username,
                "pass": password,
                "form_id": "user_login",
                "form_build_id": form_build_id,
            }

            print("Logging in...")
            res = self.session.post(self.url, data=login_data)

            if res.status_code != 200:
                print("Login failed")
                return "Error: Invalid credentials"
            print("Login successful")

        # Fetch the exam papers
        exam_data = {
            "code_value_1": module_code
        }

        print("Fetching exam papers...")
        res = self.session.get(self.url, params=exam_data)

        if res.status_code != 200:
            print("Failed to fetch exam papers")
            return "Error: Unable to fetch exam papers"

        soup = BeautifulSoup(res.text, "html.parser")
        print("Exam papers fetched successfully")

        # Find the download links for the papers
        print("Collecting download links...")

        papers = []
        for a_tag in soup.find_all("a", href=True):
            href = a_tag["href"]
            if href.endswith(".pdf"):
                papers.append(href)
        if not papers:
            print("No papers found")
            return "No papers found for this module"

        print(f"Found {len(papers)} papers")

        # Download the papers
        print("Downloading papers...")

        # Create the output directory if it doesn't exist
        if not os.path.exists(f"{output_folder}/{module_code}/papers"):
            os.makedirs(f"{output_folder}/{module_code}/papers")

        # Download papers in parallel using threads
        threads = []
        self._progress_count = 0
        total = len(papers)

        def progress_update():
            self._progress_count += 1
            if hasattr(self, 'progress_callback') and callable(self.progress_callback):
                self.progress_callback(self._progress_count, total)

        for paper in papers:
            thread = threading.Thread(target=self.download_paper, args=(paper, output_folder, module_code, progress_update))
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        print("All papers downloaded")
        print("Scraping completed")

        return True

    def download_paper(self, url, output_folder, module_code, progress_update=None):
        response = self.session.get(url)
        if response.status_code == 200:
            filename = url.split("/")[-1]

            # Check if file exists already
            if os.path.isfile(f"{output_folder}/{module_code}/papers/{filename}"):
                print(f"Paper already exists: {filename}, skipping!")
                if progress_update:
                    progress_update()
                return

            # If not, download the file
            with open(f"{output_folder}/{module_code}/papers/{filename}", "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
            if progress_update:
                progress_update()
        else:
            print(f"Failed to download: {url.split('/')[-1]}")
            if progress_update:
                progress_update()