import tkinter as tk
from tkinter import filedialog, messagebox
import requests
import scraper

root = tk.Tk()
root.title("Maynooth Paper Scraper")
root.geometry("640x400")
root.resizable(False, False)

output_folder = "./papers"  # Default output folder
# -----------------------------------------------------------------------

def start_scraper():
    result = scraper.scrape(user.get(), password.get(), module.get(), output_folder)
    if result != True:
        messagebox.showerror("Error", result)
    else:
        print("Generating Notes...")
        messagebox.showinfo("Success", "Scraping completed successfully!")

def select_output_folder():
    global output_folder
    folder_path = filedialog.askdirectory(title="Select Output Folder")
    if folder_path:
        output_folder = folder_path
        output_label.config(text=output_folder)


# -----------------------------------------------------------------------
# UI SETUP
# -----------------------------------------------------------------------

# USER INFO
user_frame = tk.LabelFrame(root, text="Login Info", padx=10, pady=5)
user_frame.pack(fill="both", padx=10, pady=5)

tk.Label(user_frame, text="Username").grid(row=0, column=0, padx=5, pady=5, sticky="w")
user = tk.Entry(user_frame)
user.grid(row=0, column=1, padx=5, pady=5, sticky="w")

tk.Label(user_frame, text="Password").grid(row=1, column=0, padx=5, pady=5, sticky="w")
password = tk.Entry(user_frame, show="*")
password.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# MODULE CODE
paper_frame = tk.LabelFrame(root, text="Paper Info", padx=10, pady=10)
paper_frame.pack(fill="both", padx=10, pady=10)
tk.Label(paper_frame, text="Module Code:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
module = tk.Entry(paper_frame)
module.grid(row=0, column=1, padx=5, pady=5, sticky="w")

output_btn = tk.Button(paper_frame, text="Output Directory", command=select_output_folder).grid(row=1, column=0, padx=5, pady=5)
output_label = tk.Label(paper_frame, text="./papers")
output_label.grid(row=1, column=1, padx=5, pady=5, sticky="w")

# AI SETTINGS
ai_frame = tk.LabelFrame(root, text="AI Settings", padx=10, pady=10)
ai_frame.pack(fill="both", padx=10, pady=10)
tk.Label(ai_frame, text="GPT API Key:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
tk.Label(ai_frame, text="Options:").grid(row=1, column=0, padx=5, pady=5, sticky="w")

api_key = tk.Entry(ai_frame).grid(row=0, column=1, padx=5, pady=5, sticky="w")
ai_plan = tk.Checkbutton(ai_frame, text="Create Study Plan").grid(row=1, column=1, padx=5, pady=5, sticky="w")
ai_questions = tk.Checkbutton(ai_frame, text="Create Sample Questions").grid(row=1, column=2, padx=5, pady=5, sticky="w")
ai_flashcards = tk.Checkbutton(ai_frame, text="Create Flashcards").grid(row=1, column=3, padx=5, pady=5, sticky="w")
lolcat = tk.Checkbutton(ai_frame, text="lolcat").grid(row=1, column=4, padx=5, pady=5, sticky="w")

start_button = tk.Button(root, text="Start", bg="lightblue", command=start_scraper)
start_button.pack(pady=10)

# ------------------------------------------------------------------------

root.mainloop()