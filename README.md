# Scraper for prnt.sc

## Introduction

The website [LightShot or prnt.sc](https://prnt.sc/) is a public image sharing website which is most well known for its quick and easy
downloadable sharing utility activated by pressing the PrtScn key. It's a very useful tool, however I noticed that it stores images
based on a sequential 6-digit code, meaning the 1.3 billion or so images uploaded there can be indexed programmatically quite easily.
That is what this utility does.

## Pre-requisites

This script was tested on the following python modules, however earlier/later versions may work fine:

```
- python 3.6
- requests 2.8.1
- beautifulsoup4 4.6.0
- lxml 3.8.0
- faker 8.11.0
- pytesseract 0.3.8 (requires additional binary install on windows https://github.com/UB-Mannheim/tesseract/wiki)
  if on windows you alse  need to change line 17 to the path of your tesseract install
- pillow 8.4.0

- multiprocessing
- time
```

## Using the Script

The script takes 6 arguments as follows:

* ```--start_code```: 6 or 7 character string made up of lowercase letters and numbers which is where the scraper will start.
  * e.g. ```'lj9me9'```
* ```--count```: The number of images to scrape. Needs to be a factor of 100.
  * e.g. ```'100000'```
* ```--output_path```: The path where images will be stored.
  * e.g. ```'output_001/```
  
## Uses/Explanation

It can be very interesting to see what people upload to these sites, generally having sequential IDs of any type is bad, and the
same applies here. People might not be aware that what they are uploading is visible to others, however prnt.sc/lightshot have
not shown any inclination in wanting to change their site design.

The OCR deletes all files that either match the spam filter, or pass the spam filter but do not match the keywords.

Spam filter is a list of strings defined as ```listToRemove``` on line 49.

Keywords to match is a list of strings defined as ```listOcr``` on line 43.

These lists can be changed to match/reject any value.


This script uses multiprocessing with a pool of 5 workers, if you go over 10 you will get IP banned as 10 requests will
be sent simultaneously.

## TO DO 

* Implement proxy system so pool workers can be greater than 10.
* Add option to save all files that pass spam filter but don't match OCR, currently only OCR matches are saved at this time
* Keep images in memory until needing to be written to hard disk for performance reasons
* Maybe implement OCR differently <- download 200 images, then run OCR, may be more performant
* Implement exception handling as if anything goes wrong now it will just crash	
	
## Licensing

This project is released under the MIT license, see LICENSE.md for more details.
