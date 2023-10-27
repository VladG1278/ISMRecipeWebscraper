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

# Gets all the cuisine links from this page
driver.get("https://en.wikipedia.org/wiki/List_of_cuisines#Regional_and_ethnic_cuisines")
elem = driver.find_elements(By.XPATH, "//*[@title]")
cuisineLinks = []
foodWords = []
for title in elem:
    newTitle = title.get_attribute("title")
    if newTitle.find(" cuisine") != -1 or newTitle.find("cuisine ") != -1:
        link = title.get_attribute("href")
        test = 0
        if link.find("#") != -1:
            test = -1
        elif link.find("php") != -1:
            test = -1
        elif link.find("%") != -1 or link.find("des") != -1:
            test = -1
        elif link.find(":") != -1:
            test = -1
        elif link.find("(") != -1:
            link = link[0:link.find("(")-1]
        if test != -1 and cuisineLinks.count(link) == 0:
            cuisineLinks.append(link)

for link in cuisineLinks:
    driver.get(link)
    elem = driver.find_elements(By.XPATH, "//*[@title]")
    for title in elem:
        newTitle = title.get_attribute("title")
        # plug in method here to decide if the word can be used



