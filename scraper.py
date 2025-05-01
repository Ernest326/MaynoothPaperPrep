import requests
from bs4 import BeautifulSoup
import os

session = requests.Session()
url = "https://www.maynoothuniversity.ie/library/exam-papers"

def scrape(username, password, module_code, output_folder):
    
    print("Starting scraper...")
    login_page = session.get(url)
    if login_page.status_code == 200:
        return "Error: Unable to access login page"
    
    # Scrape the hidden form_build_id from the login page
    soup = BeautifulSoup(login_page.text, "html.parser")
    form_build_id = soup.find("input", {"name": "form_build_id"})["value"]
    
    # POST credentials for login
    login_data = {
        "name": username,
        "pass": password,
        "form_id": "user_login",
        "form_build_id": form_build_id,
    }
    
    print("Logging in...")
    res = session.post(url, data=login_data)
    
    if res.status_code != 200:
        print("Login failed")
        return "Error: Invalid credentials"
    print("Login successful")
    
    # Fetch the exam papers
    exam_data = {
        "code_value_1": module_code
    }
    
    print("Fetching exam papers...")
    res = session.get(url, params=exam_data)
    
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
        return True
    
    print(f"Found {len(papers)} papers")
    
    # Download the papers
    print("Downloading papers...")
    for paper in papers:
        response = session.get(paper)
        if response.status_code == 200:
            filename = paper.split("/")[-1]
            
            #Check if file exists already
            if os.path.isfile(f"{output_folder}/{module_code}/papers/{filename}"):
                print(f"Paper already exists: {filename}, skipping!")
                continue
            
            #If not download the file
            with open(f"{output_folder}/{module_code}/papers/{filename}", "wb") as f:
                f.write(response.content)
            print(f"Downloaded: {filename}")
        else:
            print(f"Failed to download: {paper}")
            
    print("All papers downloaded")
    print("Scraping completed")
    
    return True
    