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

    # Force load page to grab all lazy loaded images
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
    # print(str(len(images)) + " -- " + str(len(imageLink)) + " -- " + searchWord)
    counter = 0
    id = "mntl-card-list-items_1-0"
    while check_exists_by_id(id, driver):
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
                                         splitInfoResults[3], ingredients, steps, keywords, imageLink[counter], link])
            counter = counter + 1


# threadInitializer
def threadStart(wordList, num):
    options = Options()
    options.add_argument('--headless=new')
    driver = webdriver.Chrome(options=options)
    with open('recipes' + num + '.csv', 'w', newline='', encoding="utf-8") as file:
        writer = csv.writer(file)
        field = ["title", "prepTime", "cookTime", "totalTime", "servings", "ingredients", "steps", "keywords",
                 "imageLinks", "link"]
    file.close()
    for word in wordList:
        link = "https://www.allrecipes.com/search?q=" + word.replace(" ", "%20")
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
    field = ["title", "prepTime", "cookTime", "totalTime", "servings", "ingredients", "steps", "keywords", "imageLinks", "link"]
file.close()
df10.to_csv('recipes.csv', index=False)
end_time = time.time()
print("Time taken: ", end_time - start_time, "seconds")