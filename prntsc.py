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
listOCR = ["pass", "personal information", "confidential", "private", "outlook", "gmail", "aol"
           "ssn", "personal data", "username", "email", "password", "code", "pin number", "db_user", "db_name",
           "db_password", "auth_key", "access key id", "secret access key", "security credentials",
            "sshkey", "secret_key", "smtp_pass", "wp_home","security code"
           "private key", "localdb_url", "access_token", "dbpass", "client_secret", "postgresql://"]
# List of strings that should be removed cus spam
listToRemove = ["btcx.one", "bittr.org", "btc-ex", "jamesgr001", "btc to eth", "trade btc", "trade-btc"]


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
    html = requests.get(f"http://prnt.sc/{code}", headers=headers).text
    soup = BeautifulSoup(html, 'lxml')
    img_url = soup.find_all('img', {'class': 'no-click screenshot-image'})
    return urljoin("https://", img_url[0]['src'])


# Saves image from URL
def get_img(path):
    response = requests.get(get_img_url(path.stem), headers=headers)
    path = path.with_suffix(mimetypes.guess_extension(response.headers["content-type"]))
    with open(path, 'wb') as f:
        f.write(response.content)
        f.close()
        get_ocr(path)

def get_ocr(image):
    
    imagestring = pytesseract.image_to_string(Image.open(os.path.abspath(image)))
    imagestring = imagestring.lower()
    for z in listToRemove:
        if z in imagestring:
            os.remove(image)
            print(f"Removed image number with code: {os.path.abspath(image)} as it was in spam filter")
            return
    for z in listOCR:
        if z in imagestring:
            print(f"Saved image number with code: {os.path.abspath(image)} as it DID match OCR")
            return
        else:
            os.remove(image)
            print(f"Removed image number with code: {os.path.abspath(image)} as it DID NOT match OCR")
            return


if __name__ == '__main__':
    parser = parser.ArgumentParser()
    parser.add_argument('--start_code',
                        help='6 or 7 character string made up of lowercase letters and numbers which is '
                             'where the scraper will start. e.g. abcdef -> abcdeg -> abcdeh',
                        default='21magyb')

    # set to something like 10 billion to just go forever, or until we are out of storage
    parser.add_argument(
        '--count',
        help='The number of images to scrape.',
        default='1000000')

    parser.add_argument(
        '--output_path',
        help='The path where images will be stored.',
        default='output_001/')

    args = parser.parse_args()

    output_path = Path(args.output_path)
    output_path.mkdir(exist_ok=True)
    code = args.start_code

    code = str_base(max(int(code, base) + 1, int(args.start_code, base)), base)

    # Scrape images until --count is reached
    num_of_chunks = int(int(args.count) / 100)
    count = 100

    # run multiprocessing in chunks of 100
    for i in range(num_of_chunks):

        codes = []
        for i in range(count-100, count):
            codes.append(output_path.joinpath(code))
            code = next_code(code)

        tic = time.time()

        pool = multiprocessing.Pool(5)
        pool.map(get_img, codes)
        pool.close()

        count += 100

        toc = time.time()
        print('Chunk done in {:.4f} seconds'.format(toc - tic))


    # for i in range(int(args.count)):
    #     try:
    #         tic = time.time()
    #         get_img(output_path.joinpath(code))
    #         toc = time.time()
    #         print('Done in {:.4f} seconds'.format(toc - tic))
    #     except KeyboardInterrupt:
    #         break
    #     except ConnectionResetError:
    #         # Start new sesh if it breaks
    #         request_session = requests.Session()
    #         break
    #     except Exception as e:
    #         print(f"{e} with image: {code}")
    #     code = next_code(code)
