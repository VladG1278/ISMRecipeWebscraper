import requests
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import time

# https://stackoverflow.com/questions/9567069/checking-if-an-element-exists-with-python-selenium
def check_exists_by_xpath(xpath, driver):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def check_exists_by_id(id, driver):
    try:
        driver.find_element(By.ID, id)
    except NoSuchElementException:
        return False
    return True


# checks if the title of a recipe already exists, if it does return the row where it exists
def check_title(title, num):
    with open('recipes' + num + '.csv', newline='', encoding="utf-8") as f:
        rowCounter = 0
        reader = csv.reader(f)
        for row in reader:
            if row[0] == title:
                return rowCounter
        rowCounter = rowCounter + 1
    return -1


# adds a key word to an already existing recipe instead of adding the saem recipe
def addKeyWord(title, searchWord, num):
    row = check_title(title, num)
    if row > 0:
        df = pd.read_csv("recipes" + num + ".csv", encoding="utf-8")
        if df.loc[row, 'keywords'].find(searchWord) != -1:
            df.loc[row, 'keywords'] = "|" + df.loc[row, 'keywords'] + searchWord
            df.to_csv("recipes" + num + ".csv", index=False)
        df.close()
        return False
    return True


# this link is the original scroll page
# scrolls through all the pages
def scrollThroughPages(driver, link, searchWord, num):
    onePageRecipieGatherer(driver, link, searchWord, num)
    driver.get(link)
    while check_exists_by_xpath("//*[@id=\"pagination_1-0\"]/li[6]/a", driver):
        driver.get(link)
        newLink = driver.find_element(By.XPATH, "//*[@id=\"pagination_1-0\"]/li[6]/a").get_attribute("href")
        onePageRecipieGatherer(driver, newLink, searchWord, num)
        link = newLink


# saves all recipes on a page
def onePageRecipieGatherer(driver, link, searchWord, num):
    driver.get(link)
    # Force load page to get all lazy loaded images
    # https://stackoverflow.com/questions/62600288/how-to-handle-lazy-loaded-images-in-selenium
    SCROLL_PAUSE_TIME = 0.5
    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(SCROLL_PAUSE_TIME)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height
    driver.implicitly_wait(10)
    images = driver.find_elements(By.XPATH, "//div[@class='img-placeholder']/img")
    imageLink = []
    for image in images[:-1]:
        imageLink.append(image.get_attribute("src"))
    counter = 0
    id = "mntl-card-list-items_1-0"
    while check_exists_by_id(id, driver):
        newLink = driver.find_element("id", id).get_attribute("href")
        if not newLink.find("/recipe/") > 0:
            images.append(counter)
            counter = counter + 1
            id = "mntl-card-list-items_1-0-" + str(counter)
        else:
            secondTab = requests.get(newLink)
            soup = BeautifulSoup(secondTab.content, "html.parser")
            titleResults = soup.find(id="article-heading_1-0").text.replace("\n", "")
            # Grabbing Information WebScraper
            infoResults = soup.find(id="recipe-details_1-0")
            # Formatting
            if infoResults is not None:
                if infoResults.text is not None:
                    word = re.sub(r'someword=|\,.*|\#.*', '', infoResults.text.replace("Jump to Nutrition Facts", ""))
                    infoResults = re.sub(r'\n+', '>', word).strip()
                    splitInfoResults = re.split("[:>]", infoResults)
                    splitInfoResults = [e.strip() for e in splitInfoResults]
                    for index in splitInfoResults[:]:
                        if index == '':
                            splitInfoResults.remove(index)
                            continue
                        if not index[0:1].isdigit():
                            splitInfoResults.remove(index)
            else:
                splitInfoResults = ["none", "none", "none", "none"]
            # Getting ingredients
            scrapedIngredients = soup.findAll(class_="mntl-structured-ingredients__list-item")
            ingredients = ""
            for ingredient in scrapedIngredients:
                ingredients = ingredients + ingredient.text
            word = re.sub(r'someword=|\,.*|\#.*', '', ingredients)
            ingredients = re.sub(r'\n+', '>', word).strip()
            ingredients = re.sub(r'\s+', "_", ingredients)

            # Instructions
            # https://stackoverflow.com/questions/32063985/deleting-a-div-with-a-particular-class-using-beautifulsoup
            delete = soup.findAll(class_="figure-article-caption-owner")
            for caption in delete:
                caption.decompose()
            rawSteps = soup.findAll(class_="comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup")
            steps = ""
            stepCounter = 0
            for step in rawSteps:
                stepCounter = stepCounter + 1
                steps = steps + "]" + str(stepCounter) + "." + step.text.strip()
            steps = re.sub(r'\s+', "_", steps)
            keywords = searchWord.replace(" ", "_")

            id = "mntl-card-list-items_1-0-" + str(counter)
            with open('recipes' + num + '.csv', 'a', newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                if addKeyWord(titleResults, searchWord, num):
                    if len(splitInfoResults) >= 4:
                        writer.writerow([titleResults, splitInfoResults[0], splitInfoResults[1], splitInfoResults[2],
                                         splitInfoResults[3], ingredients, steps, keywords, imageLink[counter]])
            counter = counter + 1

# Main
driver = webdriver.Chrome()
wordList = ["chicken", "pancakes", "beef", "cake", "lollipop", "food", "turtle", "meatballs", "pasta"]
for word in wordList:
    link = "https://www.allrecipes.com/search?q=" + word.replace(" ", "%20")
    scrollThroughPages(driver, link, word, "1")






