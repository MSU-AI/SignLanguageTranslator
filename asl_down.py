"""
A script that handles downloading videos from :

https://www.signasl.org

We automatically download, sort, and organize these incoming videos.
We utilize yt-dlp for downloading videos from an arbitrary source
"""

import os
import argparse

from collections import defaultdict

import requests

from yt_dlp import YoutubeDL
from bs4 import BeautifulSoup
from utils.dataset_utils import load_dataset, save_landmarks_from_video

FOLDER = os.path.join("data", "videos")
BASE_URL = 'https://www.signasl.org/sign/'

def scrape_warn(text, *args):

    # First, print out generic text:

    print("WARNING: {}".format(text))

    if args:

        print("Extra Debugging Info:")

        # Next, print out each argument:

        for arg in args:

            print(arg.prettify())

def download_video(name, url, start_time, duration_time):

    # First, create the directory structure:

    file_path = os.path.join(FOLDER, name)
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    # Next, create the parameters:

    params = {
        'format': 'mp4',
        'paths': {
            'home': file_path,
        },
        'outtmpl': {
            'default': '{}-%(title)s-%(upload_date)s.%(ext)s'.format(name),

        }
    }

    # Finally, create and download the video

    down = YoutubeDL(params)

    down.download(url)
    
def get_video_urls(name, ignore=False):

    # First, generate a valid URL and fetch the content:

    print("Getting page at URL: {}".format(BASE_URL + name))

    data = requests.get(BASE_URL + name)

    # Next, create a parser and load the content:

    print("Starting parse operation ...")

    soup = BeautifulSoup(data.content, "html.parser")

    # Get all video elements:

    results = soup.find_all("div", itemprop='video')

    print("Number of videos to extract: {}".format(len(results)))

    vid_map = defaultdict(list)

    found = 0
    non_match = 0

    for thing in results:

        # Now, get URL of this video:

        URL = None

        vid = thing.find("video")

        if vid == None:

            # No video element, see if we have an iframe element:
            # TODO: iframes might be missing the protocol header, check if this is a problem...

            URL = thing.find('iframe')['src']

            if URL is None:

                # Alright, no valid elements found, freak out:

                scrape_warn("No valid video element found!", thing)

        else:

            # We found our video, extract the URL:

            URL = vid.find('source')['src']

            # Check to ensure it is valid:

            if URL is None:

                scrape_warn("Video element found, but no valid URL!", thing, vid)

                continue

        # Sweet, got past our error checks, get the sign name:

        sign = thing.find('div', style='float:left').find('i').contents[0].lower()

        # Determine if we should ignore this video:

        if sign != name:

            non_match += 1

            if ignore:

                # Just continue:

                print("Found non-matching sign and ignoring ....")

                continue

        # Finally, add the data to the collection:

        vid_map[sign].append(URL)

        print("Got {} [{}]: {}".format(sign, found,  URL))

        # Add to our found value:

        found += 1

    # Show some basic stats:

    print("\nBasic Stats:")
    print("Total Videos Found: {}".format(found))
    print("Non-matching Videos Found: {}".format(non_match))
    print("Sign Map:")

    for key in vid_map.keys():

        print("   {} : {}".format(key, len(vid_map[key])))

    # Finally, ensure we found all the videos:

    if ((ignore and found != len(results) - non_match) or (not ignore and found != len(results))):

        # Print a warning

        scrape_warn("Not all valid videos scrapped! Check above for error logs")

    return vid_map, found

def get_videos(name, ignore=False):

    # First, get a mapping of names to vids:

    print("\n --== [ Web Scraping ] ==-- \n")

    vid_map, found = get_video_urls(name, ignore)

    print("\n --== [ End Web Scraping ] ==-- \n")

    # Next, create directory structure:

    print("Creating directory structure ...")

    file_path = 'data'
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_path = os.path.join('data', 'videos')
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    file_path = os.path.join('data', 'dataset')
    if not os.path.exists(file_path):
        os.mkdir(file_path)

    # Next, download each video:

    print("\n --== [ Video Download ] ==--\n")

    down = 1

    for sign in vid_map.keys():

        for url in vid_map[sign]:

            # Download this video:

            print("> Downloading Video {}/{}".format(down, found))

            download_video(sign, url, 0, 0)

