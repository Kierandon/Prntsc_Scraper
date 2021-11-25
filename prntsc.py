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

# for testing time per download
import time

# pytesseract.pytesseract.tesseract_cmd = '<path-to-tesseract-bin>'
pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

mimetypes.add_type("image/webp", ".webp")

# Standard headers to prevent problems while scraping. They are necessary
# randomly generated using the faker library
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
listOCR = ["pass", "personal information", "username", "email", "password", "code", "pin number", "db_user", "db_name",
           "db_password", "auth_key", "access key id", "Secret access key", "security credentials",
           "aws management console",
           "bitbucket_token", "sshkey", "secret_key", "smtp_pass", "wp_home", "slack_webhook_uri", "imap_server",
           "bitbucket_token", "google_maps_api_key", "private key", "sq0csp", "hooks.slack.com", "localdb_url",
           "access_token", "dbpass", "CLIENT_SECRET", "AIzaSy", "mongodb+srv", "postgresql://"]
# List of strings that should be removed cus spam
listToRemove = ["btcx.one", "bittr.org", "btc-ex.org", "btc-ex.org", "jamesgr001", "btc to eth exchanger login pass",
                "trade btc", "trade-btc.online"]


# Converts digit to a letter based on character codes
def digit_to_char(digit):
    if digit < 10:
        return str(digit)
    return chr(ord('a') + digit - 10)


# Returns the string representation of a number in a given base. Credit: https://stackoverflow.com/a/2063535
def str_base(number, base):
    if number < 0:
        return '-' + str_base(-number, base)
    (d, m) = divmod(number, base)
    if d > 0:
        return str_base(d, base) + digit_to_char(m)
    return digit_to_char(m)


# Returns the next code given the current code
def next_code(curr_code):
    curr_code_num = int(curr_code, base)
    return str_base(curr_code_num + 1, base)


# Parses the HTML from the prnt.sc page to get the image URL.
def get_img_url(code):
    html = request_session.get(f"http://prnt.sc/{code}", headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    img_url = soup.find_all('img', {'class': 'no-click screenshot-image'})
    return urljoin("https://", img_url[0]['src'])


# Saves image from URL
def get_img(path):
<<<<<<< Updated upstream
    response = requests.get(get_img_url(path.stem), headers=headers)
    ### zfill makes logical sense, but from some testing prnt.sc 
    ### does not resolve anything that begins with a 0
    # not used :: path = path.with_stem(path.stem.zfill(7))
    response.raise_for_status()
=======
    response = request_session.get(get_img_url(path.stem), headers=headers)
>>>>>>> Stashed changes
    path = path.with_suffix(mimetypes.guess_extension(response.headers["content-type"]))
    with open(path, 'wb') as f:
        f.write(response.content)
        f.close()
        if args.enable_ocr:
            get_ocr(path)
        else:
            print(
                f"Saved image number {i}/{args.count} with code: {code}")

def get_ocr(image):
    imagestring = pytesseract.image_to_string(Image.open(os.path.abspath(image)))
    imagestring = imagestring.lower()
    for z in listToRemove:
        if z in imagestring:
            os.remove(image)
            print(f"Removed image number with code: {code} as it was in spam filter")
            return
    for z in listOCR:
        if z in imagestring:
            print(f"Saved image number with code: {code} as it DID match OCR")
            return
        else:
            os.remove(image)
            print(f"Removed image number with code: {code} as it DID NOT match OCR")
            return


if __name__ == '__main__':
    parser = parser.ArgumentParser()
    parser.add_argument('--start_code',
                        help='6 or 7 character string made up of lowercase letters and numbers which is '
                             'where the scraper will start. e.g. abcdef -> abcdeg -> abcdeh',
                        default='20wz9em')

    # set to something like 10 billion to just go forever, or until we are out of storage
    parser.add_argument(
        '--count',
        help='The number of images to scrape.',
        default='2000')

    parser.add_argument(
        '--output_path',
        help='The path where images will be stored.',
        default='output_001/')

    parser.add_argument(
        '--enable_ocr',
        help='experimental feature to match keywords in images using OCR',
        default=True)

    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.mkdir(exist_ok=True)
    code = args.start_code

    code = str_base(max(int(code, base) + 1, int(args.start_code, base)), base)
    request_session = requests.Session()
    # Scrape images until --count is reached
    for i in range(int(args.count)):
        get_img(output_path.joinpath(code))
        code = next_code(code)