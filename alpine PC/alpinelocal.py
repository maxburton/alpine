"""
Program Name: Alpine
Description: Takes a postcode as input and iterates through all restaurants in that area to scrape all relevant data
Author: Max Burton
Version: 1.0.9
"""

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import smtplib
from email import encoders
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import platform
import sys
import re
import logging
import time
import math

# LOGGING Setup
log_format = '%(asctime)s [%(levelname)s]: %(message)s'
logging.basicConfig(filename='logs.txt', filemode='w', level=logging.INFO,
                    format=log_format, datefmt='%m/%d/%Y %I:%M:%S %p')
# create console handler and set level to debug
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

# create formatter
formatter = logging.Formatter(log_format)

# add formatter to ch
ch.setFormatter(formatter)
logging.getLogger().addHandler(ch)


def encode_file(filename, message):
    # Open file in binary mode
    with open(filename, "rb") as attachment:
        # Add file as application/octet-stream
        # Email client can usually download this automatically as attachment
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment.read())

    # Encode file in ASCII characters to send by email
    encoders.encode_base64(part)

    # Add header as key/value pair to attachment part
    part.add_header(
        "Content-Disposition",
        f"attachment; filename= {filename}",
    )

    # Add attachment to message and convert message to string
    message.attach(part)
    return message


def send_email():
    from_email = "ged.firebird@gmail.com"
    to_email = sys.argv[2]
    password = sys.argv[3]

    message = MIMEMultipart("alternative")
    message["Subject"] = "Scraping Results"
    message["From"] = from_email
    message["To"] = to_email

    text = """\
    Attached are the files generated from the scrape of area %s

    Time Elapsed: %.2fs (%dhrs, %dmins, %dsecs)
    """ % (postcode_area, time_elapsed, hours, minutes, seconds)
    html = """\
    <html>
      <body>
        <p>Attached are the files generated from the scrape of area %s
        <br><br>
        Time Elapsed: %.2fs (%dhrs, %dmins, %dsecs)
        </p>
      </body>
    </html>
    """ % (postcode_area, time_elapsed, hours, minutes, seconds)

    message = encode_file(os.path.join(directory_path, filename), message)
    message = encode_file(os.path.join(os.path.dirname(__file__), "logs.txt"), message)

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(MIMEText(text, "plain"))
    message.attach(MIMEText(html, "html"))

    # creates SMTP session
    s = smtplib.SMTP('smtp.gmail.com', 587)

    # start TLS for security
    s.starttls()

    # password = input("")

    # Authentication
    s.login(from_email, password)

    # sending the mail
    s.sendmail(from_email, to_email, message.as_string())

    # terminating the session
    s.quit()


def slugify(value):
    """
    Normalizes string, converts to lowercase, removes non-alpha characters,
    and converts spaces to hyphens.
    """
    import unicodedata

    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore')
    value = value.decode('utf-8')
    value = re.sub('[^\w\s-]', '', value).strip().lower()
    value = re.sub('[-\s]+', '-', value)
    return value


def get_phone_number():
    allergy_button = driver.find_elements_by_class_name('allergenDefaultLink')[0]
    driver.execute_script("arguments[0].scrollIntoView(true);", allergy_button)  # Scroll to the allergy button
    allergy_button.click()
    allergy_popup = driver.find_elements_by_class_name('c-modal-overlay-container')[0]
    phone_number_str = ""
    try:
        phone_number_element = allergy_popup.find_elements_by_tag_name("a")[0]
        phone_number_str = phone_number_element.get_attribute("innerText")
    except:
        logging.warning("Restaurant doesn't have a phone number!")
    allergy_close_button = driver.find_elements_by_class_name('advisoryDialogClose')[0]
    allergy_close_button.click()
    if phone_number_str[0] != "0" and phone_number_str[0] in "0123456789":
        phone_number_str = "0" + phone_number_str
    return phone_number_str


def strip_url(url):
    # https: + // + justeat.co.uk + / + url + / + menu
    split_url = url.split('/')
    # https: + // + justeat.co.uk + / + url
    return split_url[0] + "//" + split_url[2] + '/' + split_url[3]


def truncate_filename(filename):
    if len(filename) > 15:
        return filename[:15]
    else:
        return filename


for tries in range(3):
    if len(sys.argv) < 2:
        logging.fatal("You forgot to enter the postcode! Paste the postcode after alpine.py")
        exit(1)
    if len(sys.argv) < 3:
        logging.fatal("You forgot to enter your email! Paste your email after the URL")
        exit(1)
    if len(sys.argv) < 4:
        logging.fatal("You forgot to enter firebird's gmail password! Paste the password after your email")
        exit(1)

    # postcode to be scraped
    postcode_area = sys.argv[1]
    postcode_list = postcode_area.split('-')
    for postcode in postcode_list:
        if 0 >= len(postcode) > 4:
            logging.fatal("Postcode is of invalid size! make sure you only put the first part (e.g. PA2)")
            exit(1)

    # create a new Firefox session
    options = Options()
    options.add_argument("--headless")
    this_os = platform.system()
    logging.info("OS: " + this_os)

    driver = None
    if this_os == "Linux" or this_os == "Windows" or this_os == "Darwin":  # Darwin = Mac
        driver = webdriver.Firefox(options=options, executable_path="./geckodriver")
    else:
        logging.error("Incompatible OS!")
        exit(1)

    directory_path = os.path.join(os.path.dirname(__file__), 'Areas_Scraped')
    try:
        os.mkdir(directory_path, 0o0777)
    except FileExistsError:
        logging.debug("Areas Scraped directory already exists")

    filename = str(truncate_filename(postcode_area)) + '.csv'
    with open(os.path.join(directory_path, filename), mode='w', encoding='utf-8') as outfile:
        outfile.write("Restaurant Name,Cuisines,Address,City,Postcode,Phone Number,Reviews,Average Review\n")

    success = False
    num_of_restaurants = 0
    restaurant_links = {}
    try:
        start = time.time()  # measure time taken to parse menu
        driver.implicitly_wait(0)  # proceed immediately

        for postcode in postcode_list:
            url = "https://www.just-eat.co.uk/area/" + postcode
            logging.info("Loading URL for area " + postcode)
            driver.get(url)
            logging.info("Loaded")

            restaurant_elements = driver.find_elements_by_tag_name("a.c-listing-item-link.u-clearfix")

            for restaurant_element in restaurant_elements:
                restaurant_link = restaurant_element.get_attribute("href")
                restaurant_links[restaurant_link] = 1
        num_of_restaurants = len(restaurant_links)
        logging.info("Restaurants found: " + str(num_of_restaurants))

        for restaurant_url in restaurant_links:
            try:
                stripped_url = strip_url(restaurant_url)
                driver.get(stripped_url)

                restaurant_name_element = driver.find_elements_by_tag_name('h1.name')[0]
                restaurant_name = restaurant_name_element.get_attribute("innerText")
                logging.info("Scraping info from " + restaurant_name)

                # Scrape all useful info from the info screen
                street = driver.find_element_by_id('street').get_attribute('innerText')
                city = driver.find_element_by_id('city').get_attribute('innerText')
                postcode = driver.find_element_by_id('postcode').get_attribute('innerText')
                ratings_element = driver.find_elements_by_tag_name("p.rating")[0]
                avg_rating = ratings_element.find_elements_by_tag_name("img")[0].get_attribute("title").split(' ')[0]
                num_of_ratings = ratings_element.find_elements_by_tag_name("a")[0].get_attribute("innerText").split(' ')[0]
                cuisines_element = driver.find_elements_by_tag_name("p.cuisines")[0].find_elements_by_tag_name("span")
                cuisines = ""
                for j in range(len(cuisines_element)):
                    if j == 0:
                        cuisines += cuisines_element[j].get_attribute("innerText")
                    else:
                        cuisines += ", " + cuisines_element[j].get_attribute("innerText")
                phone_number = get_phone_number()

                logging.info("Appending to csv file...")
                with open(os.path.join(directory_path, filename), mode='a',
                          encoding='utf-8') as outfile:
                        out_line = '"' + str(restaurant_name) + '","' + str(cuisines) + '","' + str(street) + '","' +\
                                   str(city) + '","' + str(postcode) + '","' + str(phone_number) + '","' + \
                                   str(num_of_ratings) + '","' + str(avg_rating) + '"\n'
                        outfile.write(out_line)
                logging.info(restaurant_name + " scrape complete")
            except:
                logging.exception("Error scraping this restaurant:")
    except:
        logging.exception("Runtime Error:")
    finally:
        driver.close()

    # measure how long the scraper took to execute
    end = time.time()
    time_elapsed = end - start
    hours = math.floor(time_elapsed / 3600)
    minutes = math.floor((time_elapsed % 3600) / 60)
    seconds = round(time_elapsed % 60)
    logging.info("time elapsed: %.2fs (%dhrs, %dmins, %dsecs)" % (time_elapsed, hours, minutes, seconds))

    send_email()
    success = True

    if success:
        logging.info("Program succeeded, exiting")
        exit(0)
    else:
        logging.warning("Something went wrong, trying again...")
logging.error("Retries exceeded, program exiting")
exit(1)
