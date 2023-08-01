import requests
from bs4 import BeautifulSoup
import random
import math
import queue
import threading
import json
from threadify import queuify
url_page_base = 'https://coomer.party/artists#o='
base_url = 'https://coomer.party'

with open('creators.txt.json', 'r') as f:
    creator_details = json.loads(f.read())

PROFILES = []

for creator in random.sample(creator_details, 10):
    PROFILES.append(f"{base_url}/{creator['service']}/user/{creator['id']}")

page_list = [0,1]
USER_COUNT = 57551
PAGE_COUNT = USER_COUNT // 50

def getUsersFromPage(page_number):
    output = []
    print(url_page_base + str(page_number))
    res = requests.get(url_page_base + str(page_number))
    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml')
    users_links = [x['href'] for x in soup.find_all('a', class_='user-card') if x.get('href')]
    user_pfps = [x['src'] for x in soup.find_all('img', class_='fancy-image__image') if x.get('src')]
    for link, pfp in zip(users_links, user_pfps):
        output.append((link, pfp))
    print([x[1] for x in output])
    return output

def getUsersFromPages(page_list):
    output = []
    for page_number in page_list:
        output += getUsersFromPage(page_number)
    return output

def getRandomPages(n, min, max, mult=1):
    output = []
    while len(output) < n:
        x = random.randint(min, max) * mult
        if x not in output:
            output.append(x)
    return output

def getCountFromPageSoup(soup):
    total = int(soup.find('small').text.strip().split(' ')[-1])
    return total

def safeURL(url):
    url = url.split('?')[0]
    if 'https' not in url:
        return 'https://coomer.party/' + url
    return url

def getProfileSoup(profile, page=0, initial=False):
    profile = safeURL(profile)
    if page != 0:
        profile += '?o=' + str(page)
    res = requests.get(profile)
    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml')
    if initial:
        return (soup,getCountFromPageSoup(soup))
    return soup

def getLinksFromProfileSoup(soup):
    post_elems = soup.find_all('article')
    link_elems = [x.find('a') for x in post_elems]
    links = [x['href'] for x in link_elems[1:] if x.get('href')]
    return links

def getRandomLinksFromProfile(profile, n):
    profile = safeURL(profile)
    output = []
    init_soup, total = getProfileSoup(profile, initial=True)
    output += getLinksFromProfileSoup(init_soup)
    pages = getRandomPages(n-1, 1, total, mult=50)
    for page in pages:
        soup = getProfileSoup(profile, page)
        output += getLinksFromProfileSoup(soup)

def getMediaFromLink(link):
    res = requests.get(safeURL(link))
    if res.ok:
        soup = BeautifulSoup(res.text, 'lxml')
    links = soup.find_all('a', class_='post__attachment-link')
    return [x['href'] for x in links if x.get('href')]

# soup, count = getProfileSoup('https://coomer.party/onlyfans/user/lee.ava?o=0', initial=True)

def getRandomSampleMediaFromLinks(links, max, target_percentage):
    count = min(max, math.ceil(len(links)*target_percentage))
    output = []
    for i, link in enumerate(random.sample(links, count)):
        output += getMediaFromLink(link)
    return output

def getMinMediaFromProfile(profile, min, link_timeout=500, page_timeout=100_000):
    output = []
    soup, total = getProfileSoup(profile, initial=True)
    links = getLinksFromProfileSoup(soup)
    for link in links[:link_timeout]:
        output += getMediaFromLink(link)
        if len(output) >= min:
            break
    else:
        pages = list(range(0, total))
        random.shuffle(pages)
        for page in pages[:page_timeout]:
            soup = getProfileSoup(profile, page*50)
            links = getLinksFromProfileSoup(soup)
            for link in links:
                output += getMediaFromLink(link)
                if len(output) >= min:
                    break
            else:
                continue
            break
    return output

@queuify
def hasMediaOnProfile(profile, fast=True):
    output = getMinMediaFromProfile(profile, 1, link_timeout=10, page_timeout=(0 if fast else 100_000))
    return len(output) > 0

profile_queue = queue.Queue()
for profile in PROFILES:
    profile_queue.put(profile)

threads = []
for _ in range(10):
    t = threading.Thread(target=hasMediaOnProfile, args=(profile_queue,))
    threads.append(t)
    t.start()
for t in threads:
    t.join()