# Scraper for prnt.sc

## Introduction

This tool is designed to programmatically index images from [LightShot or prnt.sc](https://prnt.sc/), a public image sharing website known for its quick, easy-to-use sharing utility activated by pressing the PrtScn key. Prnt.sc stores images based on a sequential 6-digit code, which means the 1.3 billion or so images uploaded there can be indexed with ease. This is exactly what our tool does.

## Pre-requisites

This script was tested with the following python modules. However, earlier or later versions may also work:

```
- python 3.6
- requests 2.8.1
- beautifulsoup4 4.6.0
- lxml 3.8.0
- faker 8.11.0
- pytesseract 0.3.8 (requires additional binary install on Windows [here](https://github.com/UB-Mannheim/tesseract/wiki). Windows users need to change line 17 to the path of their Tesseract install)
- pillow 8.4.0
- argparse
- multiprocessing
- time
```

## Using the Script

The script takes several arguments as follows:

* ```--starting_url```: The URL to scrape from.
  * e.g., ```'https://prnt.sc/'```
* ```--start_code```: 6 or 7 character string made up of lowercase letters and numbers, which indicates where the scraper will start.
  * e.g., ```'ocpfx'```
* ```--code_direction```: True for ascending, False for descending.
  * e.g., ```True``` or ```False```
* ```--count```: The number of images to scrape.
  * e.g., ```'1000000'```
* ```--save_all```: Enable saving all files, even those that don't match the OCR list or spam list.
  * e.g., ```True``` or ```False```
* ```--enable_regex```: Enable saving files that match the OCR list.
  * e.g., ```True``` or ```False```
* ```--output_path```: The path where images that match the regex will be stored.
  * e.g., ```'regex/'```
* ```--num_of_workers```: The number of workers to use for scraping.
  * e.g., ```16```

## Uses/Explanation

The tool allows you to browse through what people upload to these sites, raising awareness of the issues that come with sequential IDs. Users may not be aware that their uploads are visible to others, despite prnt.sc/lightshot's lack of indication to change their site design.

The OCR feature is designed to filter out spam and only save files that match certain keywords. 

- Spam filter, defined as ```listToRemove```, is a list of strings. 
- Keywords to match, defined as ```listOcr```, is a list of strings.

These lists can be customized to match/reject any value.

The script uses multiprocessing with a pool of workers. If the pool size exceeds 10, you might get IP banned as 10 requests will be sent simultaneously.

## TO DO 

* Implement a proxy system to allow more than 10 workers in a pool.
* Keep images in memory until they need to be written to the hard disk for performance reasons.
* Consider a different OCR implementation - for instance, download 200 images, then run OCR. This might improve performance.
* Implement exception handling to prevent crashes from unexpected issues.	

## Licensing

This project is released under the MIT license, see LICENSE.md for more details.
