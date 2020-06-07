"""
Program Name: Alpine
Description: Scrapes postcodes in a format for alpine
Author: Max Burton
Version: 1.0.0
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import re

options = Options()
options.add_argument("--headless")
driver = webdriver.Firefox(options=options, executable_path="./geckodriver")

postcodes = ""
url = "https://www.gbmaps.com/4-digit-postcode-maps/hs-isle%20of%20harris-postcode-map.html"
prefix = "HS"
driver.get(url)
table = driver.find_elements_by_tag_name("tbody")[0]
tds = table.find_elements_by_tag_name("td")
for td in tds:
    innerText = td.get_attribute("innerText")
    isAPostcodeArea = re.search(prefix + "[0-9]+", innerText)
    if isAPostcodeArea:
        postcodes += innerText + "-"

print(postcodes)

driver.close()
