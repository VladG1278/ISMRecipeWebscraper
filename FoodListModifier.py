import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException

options = Options()
options.add_argument('--headless=new')
driver = webdriver.Chrome(options=options)
file = open("Food List.txt", "r")
words = []
for word in file:
    words.append(word)
file.close()
link = ""
print(len(words))
exists = False
for word in words[:]:
    results = ""
    link = "https://www.allrecipes.com/search?q=" + word.replace(" ", "%20").replace("\n", "")
    driver.get(link)
    results = driver.find_element(By.ID, "search-results_1-0").get_attribute("textContent")
    if results.find("Please try") > -1:
        words.remove(word)
    else:
        elems = driver.find_elements(By.XPATH, "//a[@href]")
        for elem in elems:
            if elem.get_attribute("href").find("https://www.allrecipes.com/recipe/") >= 0:
                exists = True
                break
        if not exists:
            words.remove(word)
file = open("New Food List.txt", "w")
for word in words:
    file.write(word)
file.close()
print(len(words))