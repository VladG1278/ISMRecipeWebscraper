import time
import requests
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import os
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException


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

            # Creates new file for the recipe
            # Checks if file already exists and if so then add the parameter as a search word
            filepath = os.path.join("D:\\Recipes", titleResults)
            if not os.path.exists(filepath + ".txt"):
                file = open(filepath + ".txt", "w")
            else:
                file = open(filepath + ".txt", "a")
                file.write("\"" + searchWord + "\", ")
            file.close()

            # Grabbing Information WebScraper
            infoResults = soup.find(id="recipe-details_1-0")

            # Formatting
            if infoResults.text is not None:
                infoResults = infoResults.text
                infoResults = infoResults.replace("\n", "").replace("Jump to Nutrition Facts", "")
                infoResults = infoResults.replace(":", ": ").replace("mins", "mins\n").replace("hrsS",
                                                                                               "hrs\nS").replace("hrsT",
                                                                                                                 "hrs\nT")
                infoResults = infoResults.replace("Yield: ", "\nYield: ")

            # Putting Info Into File
            file = open(filepath + ".txt", "a")
            file.write(titleResults + "\n\nHelpful Information:\n" + infoResults)
            file.close()

            # Getting ingredients
            ingredients = soup.findAll(class_="mntl-structured-ingredients__list-item")
            file = open(filepath + ".txt", "a")
            file.write("\n\nIngredients: ")

            # Putting Ingredients Into A File
            for x in ingredients:
                file.write(
                    "\n" + x.text.replace("\n", "").replace('\u2153', "1/3").replace('\u215b', "1/8").replace('\u2154',
                                                                                                              "2/3"))
            file.close()

            # Instructions
            # https://stackoverflow.com/questions/32063985/deleting-a-div-with-a-particular-class-using-beautifulsoup
            delete = soup.findAll(class_="figure-article-caption-owner")
            for x in delete:
                x.decompose()
            steps = soup.findAll(class_="comp mntl-sc-block-group--LI mntl-sc-block mntl-sc-block-startgroup")
            file = open(filepath + ".txt", "a")
            stepCounter = 1
            file.write("\n\nSteps:\n")
            for x in steps:
                file.write(str(stepCounter) + ". " + x.text.replace("\n", "") + '\n')
                stepCounter = stepCounter + 1
                file.write("\nKeywords: \"" + searchWord + "\",")
            file.close()
            counter = counter + 1
            id = "mntl-card-list-items_1-0-" + str(counter)
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
for x in wordList:
    search = x
    # need to find a huge list of common recipe search words
    link = "https://www.allrecipes.com/search?q=" + search.replace(" ", "%20")
    scrollThroughPages(driver, link, x)
    break

# next step is to add threads then make a better word list to test
