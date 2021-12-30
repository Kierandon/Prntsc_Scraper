import argparse as parser
import mimetypes
import string
from pathlib import Path
import faker
import requests
from urllib.parse import urljoin
from bs4 import BeautifulSoup
import os.path
import pytesseract
from PIL import Image
import multiprocessing
import time
import shutil
from time import perf_counter

# pytesseract.pytesseract.tesseract_cmd = '<path-to-tesseract-bin>'
pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'
# May need to do 'export OMP_THREAD_LIMIT=1' on linux if experiencing performance issues.

# Add webp type to mimetypes
mimetypes.add_type("image/webp", ".webp")

# Standard headers to prevent problems while scraping. They are randomly generated using the faker library
fake = faker.Faker()
fake.add_provider(faker.providers.user_agent)
headers = {
    'authority': 'prnt.sc',
    'cache-control': 'max-age=0',
    'upgrade-insecure-requests': '1',
    'user-agent': fake.chrome(),
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
    'accept-encoding': 'gzip, deflate',
    'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8'
}

# List of all possible characters in a prnt.sc code, base stores the length of this.
# The idea is that we can work in base 36 (length of all lowercase + digits) to add
# one to a code i.e. if we have abcdef, we can essentially write abcdef + 1 to get
# abcdeg, which is the next code.
# order for prnt.sc appears to be numeric then alphabetic
code_chars = list(string.ascii_lowercase) + ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
base = len(code_chars)

# List of strings that should be matched using OCR (pytesseract) - KD
listOCR = ["user", "pass", "confidential", "gmail", "outlook", "ssn", "personal data", "pin number", "db_user",
           "db_name", "private"]

# List of strings that should be removed cus spam
listToRemove = ["btcx.one", "btc-ex", "bittrading", "bittr.org",  "jamesgr001", "btc to eth",
                "trade btc", "trade-btc"]


# Converts digit to a letter based on character codes
def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)


# Returns the string representation of a number in a given base. Credit: https://stackoverflow.com/a/2063535
def str_base(number, numberbase):
    if number < 0:
        return '-' + str_base(-number, numberbase)
    (d, m) = divmod(number, numberbase)
    if d > 0:
        return str_base(d, numberbase) + digit_to_char(m)
    return digit_to_char(m)


# Returns the next code given the current code
def next_code(curr_code):
    curr_code_num = int(curr_code, base)
    return str_base(curr_code_num + 1, base)


# Parses the HTML from the prnt.sc page to get the image URL.
def get_img_url(urlcode):
    html = requests.get(f"http://prnt.sc/{urlcode}", headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    img_url = soup.find_all('img', {'class': 'no-click screenshot-image'})
    return urljoin("https://", img_url[0]['src'])


# Saves image from URL
def get_img(path):
    t1_start = perf_counter()
    response = requests.get(get_img_url(path.stem), headers=headers)
    path = path.with_suffix(mimetypes.guess_extension(response.headers["content-type"]))
    with open(path, 'wb') as f:
        f.write(response.content)
        f.close()

    # open the image, then use pytesseract to convert that image to a string
    imagestring = pytesseract.image_to_string(Image.open(path))

    # Convert string to lowercase so can be matched with listOCR and listToRemoves
    imagestring = imagestring.lower()

    # For every word in the spam filter
    for z in listToRemove:
        # If word in the string then remove the image
        if z in imagestring:
            os.remove(path)
            t1_stop = perf_counter()
            print(f"REMOVED {path.name} -> {response.url} - SPAM FILTER - TIME TAKEN {t1_stop-t1_start}")
            return
    # For every word in listOCR
    for z in listOCR:
        # If word in the string then keep the image
        if z in imagestring:
            t1_stop = perf_counter()
            print(f"Saved image {path.name} -> {response.url} - OCR MATCH, TIME TAKEN {t1_stop-t1_start}")
            return
        # If save_all is true then save the image
        elif args.save_all:
            t1_stop = perf_counter()
            shutil.move(path, 'all_images/' + os.path.basename(path))
            print(f"Saved image {path.name} -> {response.url} - SAVE ALL ENABLED, TIME TAKEN {t1_stop - t1_start}")
            return
        # Else remove the image
        else:
            os.remove(path)
            t1_stop = perf_counter()
            print(f"Removed image {path.name} -> {response.url} - NO OCR MATCH, TIME TAKEN {t1_stop-t1_start}")
            return


# PARSE ARGUMENTS AND MAKE GLOBAL
parser = parser.ArgumentParser()
parser.add_argument(
        '--start_code',
        help='6 or 7 character string made up of lowercase letters and numbers which is '
        'where the scraper will start. e.g. abcdef -> abcdeg -> abcdeh',
        default='24bjh4r')

# set to something like 10 billion to just go forever, or until we are out of storage
parser.add_argument(
        '--count',
        help='The number of images to scrape.',
        default='1000000')

parser.add_argument(
        '--output_path',
        help='The path where images will be stored.',
        default='output/')

parser.add_argument(
        '--save_all',
        help='Enable saving files that dont match the spam list or the OCR list.',
        default=True)

global args
# noinspection PyRedeclaration
args = parser.parse_args()

# START MAIN PROGRAM
if __name__ == '__main__':

    # Set output directory according to directory
    output_path = Path(args.output_path)
    output_path.mkdir(exist_ok=True)

    # If save_all is enabled then create dir for it
    if args.save_all:
        all_images_path = Path("all_images")
        all_images_path.mkdir(exist_ok=True)

    # Set start code according to arg
    code = args.start_code

    # Scrape images until --count is reached
    num_of_chunks = int(int(args.count) / 100)
    count = 100

    # run multiprocessing in chunks of 100
    for x in range(num_of_chunks):

        # create list of 100 codes
        codes = []
        for y in range(count-99, count):
            codes.append(output_path.joinpath(code))
            code = next_code(code)

        tic = time.perf_counter()

        pool = multiprocessing.Pool(6)
        pool.map(get_img, codes)
        pool.close()

        count += 100

        toc = time.perf_counter()
        print(f'CHUNK COMPLETE IN {toc-tic}')
    print('Printing complete')
