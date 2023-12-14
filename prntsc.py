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
from io import BytesIO
import shutil
from time import perf_counter
import re

# pytesseract.pytesseract.tesseract_cmd = '<path-to-tesseract-bin>'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
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
listOCR = ["examity", "proctor", "exam", "user", "pass", "confidential", "gmail", "outlook", "ssn", "personal data",
           "pin number", "db_user",
           "db_name", "private", "confidential", "password", "username", "login", "email", "account", "credent"]

# List of strings that should be removed cus spam
listToRemove = ["btcx.one", "btc-ex", "bittrading", "bittr.org", "jamesgr001", "btc to eth",
                "trade btc", "trade-btc"]

# Convert lists to regular expressions
regexOCR = re.compile('|'.join(listOCR))
regexToRemove = re.compile('|'.join(listToRemove))


# Converts digit to a letter based on character codes
def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)


def get_public_ip():
    response = requests.get('https://api.ipify.org?format=json')
    if response.status_code == 200:
        data = response.json()
        ip_address = data['ip']
        return ip_address
    else:
        return "Unable to retrieve public IP"


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
    if args.code_direction:
        return str_base(curr_code_num + 1, base)
    else:
        return str_base(curr_code_num - 1, base)


# Parses the HTML from the page to get the image URL.
def get_img_url(urlcode):
    url = args.starting_url + urlcode
    html = requests.get(url, headers=headers).text
    soup = BeautifulSoup(html, 'html.parser')
    img_elements = soup.select(args.selector)
    if img_elements:  # if the list is not empty
        img_url = urljoin("https://", img_elements[0]['src'])
        return img_url
    else:
        return None


# Saves image from URL
def get_img(path):
    t1_start = perf_counter()
    try:
        response = requests.get(get_img_url(path.stem), headers=headers, timeout=100)
    except:
        print("No image")
        print("URL: " + path.stem)
        return

    # Store image in a BytesIO object
    img_content = BytesIO(response.content)

    # Guess image file extension
    file_extension = mimetypes.guess_extension(response.headers["content-type"])
    path = path.with_suffix(file_extension)

    # Use pytesseract to convert image to string
    imagestring = pytesseract.image_to_string(Image.open(img_content)).lower()

    if args.enable_regex:
        if regexToRemove.search(imagestring):
            t1_stop = perf_counter()
            print(f"SPAM: Removed image {path.name} -> {response.url}, TIME TAKEN {t1_stop - t1_start}")
            return
        elif regexOCR.search(imagestring):
            t1_stop = perf_counter()
            with open(path, 'wb') as f:
                f.write(img_content.getvalue())  # Write image to disk
            shutil.move(path, args.output_path + path.name + '.png')
            print(f"OCR MATCH: Saved image {path.name} -> {response.url}, TIME TAKEN {t1_stop - t1_start}")
            return

    if args.save_all:
        t1_stop = perf_counter()
        with open(path, 'wb') as f:
            f.write(img_content.getvalue())  # Write image to disk
        shutil.move(path, 'all_images/'  + path.name + '.png')
        print(f"SAVE ALL ENABLED: Saved image {path.name} -> {response.url}, TIME TAKEN {t1_stop - t1_start}")
        return

    t1_stop = perf_counter()
    print(f"NO OCR MATCH: Removed image {path.name} -> {response.url}, TIME TAKEN {t1_stop - t1_start}")
    return


# PARSE ARGUMENTS AND MAKE GLOBAL
parser = parser.ArgumentParser()

##URL to scrae
parser.add_argument(
    '--starting_url',
    help='The URL to scrape from.',
    default='https://paste.pics/')

##Start code options
parser.add_argument(
    '--start_code',
    help='6 or 7 character string made up of lowercase letters and numbers which is '
         'where the scraper will start. e.g. abcdef -> abcdeg -> abcdeh',
    default='q17e1')

##Start code options
parser.add_argument(
    '--code_direction',
    help='True for ascending, False for descending',
    default=False)

##IMAGE OPTIONS
parser.add_argument(
    '--count',
    help='The number of images to scrape.',
    default='1000000')

parser.add_argument(
    '--save_all',
    help='Enable saving all files.',
    default=True)

##REGEX OPTIONS
parser.add_argument(
    '--enable_regex',
    help='Enable saving files that match the OCR list.',
    default=True)

parser.add_argument(
    '--output_path',
    help='The path where images that match the regex will be stored.',
    default='regex/')

parser.add_argument(
    '--num_of_workers',
    help='The number of workers to use for scraping.',
    default=16)

parser.add_argument(
    '--selector',
    help='The html selector to use to find the img element.',
    default='#content > div.view-main > div > div.dm-image-wrap > div:nth-child(2) > a > img')

global args
# noinspection PyRedeclaration
args = parser.parse_args()

# START MAIN PROGRAM
if __name__ == '__main__':

    # timer
    #print("Beginning scraping on IP Address:", get_public_ip())
    #time.sleep(3)

    # Set output directory according to directory
    output_path = Path(args.output_path)
    output_path.mkdir(exist_ok=True)

    # If save_all is enabled then create dir for it
    if args.save_all:
        all_images_path = Path("all_images")
        all_images_path.mkdir(exist_ok=True)

    if args.enable_regex:
        regex = Path("regex")
        regex.mkdir(exist_ok=True)

    # Set start code according to arg
    code = args.start_code

    # Scrape images until --count is reached
    num_of_chunks = int(int(args.count) / 100)
    count = 100

    # Create a pool of workers
    pool = multiprocessing.Pool(int(args.num_of_workers))

    # run multiprocessing in chunks of 100
    for x in range(num_of_chunks):

        # create list of 100 codes
        codes = []
        for y in range(count - 99, count):
            codes.append(output_path.joinpath(code))
            code = next_code(code)

        tic = time.perf_counter()

        for _ in pool.imap_unordered(get_img, codes):
            pass

        count += 100

        toc = time.perf_counter()
        print(f'CHUNK COMPLETE IN {toc - tic}')

    pool.close()
    pool.join()

    print('Scraping complete')
