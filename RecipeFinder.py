import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv

# https://stackoverflow.com/questions/9567069/checking-if-an-element-exists-with-python-selenium
def check_exists_by_xpath(xpath):
    try:
        driver.find_element(By.XPATH, xpath)
    except NoSuchElementException:
        return False
    return True


def check_exists_by_id(id):
    try:
        driver.find_element(By.ID, id)
    except NoSuchElementException:
        return False
    return True


# this link is the original scroll page
# scrolls through all the pages
def scrollThroughPages(driver, link, searchWord):
    onePageRecipieGatherer(driver, link, searchWord)
    driver.get(link)
    while check_exists_by_xpath("//*[@id=\"pagination_1-0\"]/li[6]/a"):
        driver.get(link)
        newLink = driver.find_element(By.XPATH, "//*[@id=\"pagination_1-0\"]/li[6]/a").get_attribute("href")
        # driver.close()
        onePageRecipieGatherer(driver, newLink, searchWord)
        link = newLink


# saves all recipes on a page
def onePageRecipieGatherer(driver, link, searchWord):
    driver.get(link)
    counter = 0
    id = "mntl-card-list-items_1-0"
    while check_exists_by_id(id):
        newLink = driver.find_element("id", id).get_attribute("href")
        if not newLink.find("/recipe/") > 0:
            counter = counter + 1
            id = "mntl-card-list-items_1-0-" + str(counter)
        else:
            secondTab = requests.get(newLink)
            soup = BeautifulSoup(secondTab.content, "html.parser")
            titleResults = soup.find(id="article-heading_1-0").text.replace("\n", "")

            # Grabbing Information WebScraper
            infoResults = soup.find(id="recipe-details_1-0")

            # Formatting
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
            print(splitInfoResults)
            # Getting ingredients
            scrapedIngredients = soup.findAll(class_="mntl-structured-ingredients__list-item")
            ingredients = ""
            for x in scrapedIngredients:
                ingredients = ingredients + x.text
            word = re.sub(r'someword=|\,.*|\#.*', '', ingredients)
            ingredients = re.sub(r'\n+', '>', word).strip()
            ingredients = re.sub(r'\s+', "_", ingredients)

            # Instructions
            # https://stackoverflow.com/questions/32063985/deleting-a-div-with-a-particular-class-using-beautifulsoup
            delete = soup.findAll(class_="figure-article-caption-owner")
            for x in delete:
                x.decompose()
            wrongSteps = soup.findAll(class_="comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup")
            steps = ""
            stepCounter = 0
            for x in wrongSteps:
                stepCounter = stepCounter + 1
                steps = steps + "]" + str(stepCounter) + "." + x.text.strip()
            steps = re.sub(r'\s+', "_", steps)
            counter = counter + 1
            print(searchWord)
            keywords = searchWord.replace(" ", "_")
            id = "mntl-card-list-items_1-0-" + str(counter)
            with open('recipes.csv', 'a', newline='') as file:
                writer = csv.writer(file)
                print(len(splitInfoResults))
                if len(splitInfoResults) >= 4:
                    writer.writerow([splitInfoResults[0], splitInfoResults[1], splitInfoResults[2], splitInfoResults[3], ingredients, steps, keywords])
        break
        
    # driver.close()


# main
options = Options()
options.add_argument('--headless=new')
driver = webdriver.Chrome(options=options)

wordList = []
wordFile = open("C:\\Users\\monke\\Downloads\\School\\ISM\\List of Food.txt", "r")
for x in wordFile:
    wordList.append(x)
wordFile.close()
with open('recipes.csv', 'w', newline='') as file:
    writer = csv.writer(file)
    field = ["prepTime", "cookTime", "totalTime", "servings", "ingredients", "steps", "keywords"]
file.close()
for x in wordList:
    search = x
    # need to find a huge list of common recipe search words
    link = "https://www.allrecipes.com/search?q=" + search.replace(" ", "%20")
    scrollThroughPages(driver, link, x)
    break

# next step is to add threads then make a better word list to test
