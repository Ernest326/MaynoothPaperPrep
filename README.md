# MaynoothPaperPrep
A scraper for past papers with integrated LLM!
![screenshot](screenshot.png)

This is a quick simple project that I made in order to aid me in my studies, and was also a fun excuse to mess around with web scraping lol

The project is still a work in progress, ChatGPT processing hasn't been implemented yet!

## Setup

This project uses uv as the package manager. Details for setup can be viewed here: https://github.com/astral-sh/uv  
Once you have the uv package manager ready, run the following commands:

  
Simply clone this repo:
```
git clone https://github.com/Ernest326/MaynoothPaperPrep.git
```
Sync the pacakges:
```
uv sync
```

Run the virtual environment:
```
.venv\Scripts\activate
```

And run the code!
```
uv run main.py
```

## How it works?
The project runs a basic interface using tkinter, handles web requests+session via requests package and scrapes the web data using BeautifulSoup!