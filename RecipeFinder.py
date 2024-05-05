import pandas
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import re
from selenium.webdriver.common.by import By
from selenium.common.exceptions import NoSuchElementException
import csv
import pandas as pd
import threading
import time
from bs4 import BeautifulSoup as BSHTML
import urllib3
from requests.adapters import HTTPAdapter, Retry

titles = []

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

def check_exists_by_class(classN, driver):
    try:
        driver.find_element(By.CLASS_NAME, classN)
    except NoSuchElementException:
        return False
    return True

def findNumber (test):
    index = 0
    for i in test:
        if i.isdigit():
            return index
    return -1

def check_title(title):
    if title in titles:
        return False
    return True



# this link is the original scroll page
# scrolls through all the pages
def scrollThroughPages(driver, link, searchWord, num):
    onePageRecipieGatherer(driver, link, searchWord, num)
    driver.get(link)
    counter = 24
    #checks for next button (bug may occur if window is too small because the next button might not appear
    while check_exists_by_class("mntl-pagination__next", driver):
        newLink = "https://www.allrecipes.com/search?" + searchWord + "=" + searchWord + "&offset=" + str(counter) + "&q=" + searchWord
        onePageRecipieGatherer(driver, newLink, searchWord, num)
        counter += 24
        driver.get(newLink)
    print(searchWord + " Completed!")
# saves all recipes on a page
# note the driver in this method holds the link to the page with the search results, not the actual recipe page
def onePageRecipieGatherer(driver, link, searchWord, num):
    driver.get(link)
    noError = True
    counter = 0
    id = "mntl-card-list-items_1-0"
    while check_exists_by_id(id, driver):
        newLink = driver.find_element("id", id).get_attribute("href")
        if not newLink.find("/recipe/") < 0:
            s = requests.Session()

            retries = Retry(total=5,
                            backoff_factor=0.1,
                            status_forcelist=[500, 502, 503, 504])

            s.mount('http://', HTTPAdapter(max_retries=retries))
            secondTab = s.get(newLink)
            soup = BeautifulSoup(secondTab.content, "html.parser")
            imageLink = soup.find(class_="img-placeholder").prettify()
            beginningIndex = imageLink.find("src=\"") + 5
            lastIndex = imageLink.find("\"", beginningIndex)
            imageLink = imageLink[beginningIndex:lastIndex]

            titleResults = soup.find(id="article-header--recipe_1-0").text.replace("\n", "")
            # find number in titleResults
            titleResultsSplit = re.split('\d', titleResults)
            titleResults = titleResultsSplit[0]

            # Grabbing Information WebScraper
            SILabel = soup.findAll(class_="mntl-recipe-details__label")
            SIValue = soup.findAll(class_="mntl-recipe-details__value")
            SI = []
            SIIndex = 0
            while SIIndex < len(SIValue):
                SI.append(SILabel[SIIndex].text + SIValue[SIIndex].text)
                SI[SIIndex] = re.sub(r'\s+', ' ', SI[SIIndex])
                temp = SI[SIIndex]
                if temp[len(temp) - 1] == ' ':
                    SI[SIIndex] = SI[SIIndex].replace(' ', '')
                SI[SIIndex] = SI[SIIndex].replace(': ', ':')
                SI[SIIndex] = SI[SIIndex].replace(':', ': ')
                SIIndex += 1
            SIFinal = "\n".join(SI)

            # Getting ingredients
            scrapedIngredients = soup.findAll(class_="mntl-structured-ingredients__list-item")
            ingredients = ""
            for ingredient in scrapedIngredients:
                ingredients = ingredients + ingredient.text
            word = re.sub(r'someword=|\,.*|\#.*', '', ingredients)
            ingredients = re.sub(r'\n+', '\n', word).strip()
            ingredients = re.sub(r'\s+', " ", ingredients)

            # Get steps
            delete = soup.findAll(class_="figure-article-caption-owner")
            for caption in delete:
                caption.decompose()
            rawSteps = soup.findAll(class_="comp mntl-sc-block mntl-sc-block-startgroup mntl-sc-block-group--OL")
            steps = ""
            stepCounter = 0
            for step in rawSteps:
                stepCounter = stepCounter + 1
                steps = steps + "]" + str(stepCounter) + "." + step.text.strip()
            steps = re.sub(r'\s+', " ", steps)
            keywords = searchWord.replace(" ", " ")
            with open('recipes' + num + '.csv', 'a', newline='', encoding="utf-8") as file:
                writer = csv.writer(file)
                if check_title(titleResults):  # addKeyWord(titleResults, searchWord, num)
                    titles.append(titleResults)
                    writer.writerow([titleResults, SIFinal, ingredients, steps, keywords, imageLink, newLink])
                    #print('"' + titleResults + '" Recipe Completed!')
        counter = counter + 1
        id = "mntl-card-list-items_" + str(counter) + "-0"
        # print(titleResults + splitInfoResults[0] + splitInfoResults[1] + splitInfoResults[2] +splitInfoResults[3] + ingredients + steps + keywords + imageLink[counter]+ newLink)
# threadInitializer
def threadStart(wordList, num):
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)

    with open('recipes' + num + '.csv', 'w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        field = ["title", "information", "ingredients", "steps", "keywords",
                 "imageLinks", "link"]
    file.close()
    for word in wordList:
        link = "https://www.allrecipes.com/search?q=" + word.replace(" ", "+")
        scrollThroughPages(driver, link, word, num)
    print("Thread " + num + " Finished")


# main
start_time = time.time()
# opens wordList and makes csv file
wordList1 = []
wordList2 = []
wordList3 = []
wordList4 = []
wordList5 = []
wordList6 = []
wordList7 = []
wordList8 = []
wordList9 = []
wordFile = open("New Food List.txt", "r")
length = (len(wordFile.readlines()))
wordFile.close()
wordFile = open("New Food List.txt", "r")
counter = 0
for searchWord in wordFile:
    if counter >= length / 9 * 8:
        wordList9.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 7:
        wordList8.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 6:
        wordList7.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 5:
        wordList6.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 4:
        wordList5.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 3:
        wordList4.append(searchWord.replace("\n", ""))
    elif counter >= length / 9 * 2:
        wordList3.append(searchWord.replace("\n", ""))
    elif counter >= length / 9:
        wordList2.append(searchWord.replace("\n", ""))
    else:
        wordList1.append(searchWord.replace("\n", ""))
    counter = counter + 1
wordFile.close()


# Create and start threads
t1 = threading.Thread(target=threadStart, args=(wordList1, "1"))
t2 = threading.Thread(target=threadStart, args=(wordList2, "2"))
t3 = threading.Thread(target=threadStart, args=(wordList3, "3"))
t4 = threading.Thread(target=threadStart, args=(wordList4, "4"))
t5 = threading.Thread(target=threadStart, args=(wordList5, "5"))
t6 = threading.Thread(target=threadStart, args=(wordList6, "6"))
t7 = threading.Thread(target=threadStart, args=(wordList7, "7"))
t8 = threading.Thread(target=threadStart, args=(wordList8, "8"))
t9 = threading.Thread(target=threadStart, args=(wordList9, "9"))

t1.start()
t2.start()
t3.start()
t4.start()
t5.start()
t6.start()
t7.start()
t8.start()
t9.start()

t1.join()
t2.join()
t3.join()
t4.join()
t5.join()
t6.join()
t7.join()
t8.join()
t9.join()

df1 = pandas.read_csv("recipes1.csv", encoding="utf-8")
df2 = pandas.read_csv("recipes2.csv", encoding="utf-8")
df3 = pandas.read_csv("recipes3.csv", encoding="utf-8")
df4 = pandas.read_csv("recipes4.csv", encoding="utf-8")
df5 = pandas.read_csv("recipes5.csv", encoding="utf-8")
df6 = pandas.read_csv("recipes6.csv", encoding="utf-8")
df7 = pandas.read_csv("recipes7.csv", encoding="utf-8")
df8 = pandas.read_csv("recipes8.csv", encoding="utf-8")
df9 = pandas.read_csv("recipes9.csv", encoding="utf-8")
df10 = pandas.concat([df1, df2, df3, df4, df5, df6, df7, df8, df9], ignore_index=True)
with open('recipes.csv', 'w', newline='', encoding="utf-8") as file:
    writer = csv.writer(file)
    field = ["title", "information", "ingredients", "steps", "keywords", "imageLinks", "link"]
file.close()
df10.to_csv('recipes.csv')
end_time = time.time()
print("Time taken: ", end_time - start_time, "seconds")