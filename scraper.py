import re
import sys
import time
import requests
from copy import copy
from io   import BytesIO
from lxml import html

from PIL import Image
from PIL.ImageTk import PhotoImage


class Scraper:
    """Scrape data and links from xvideos.com."""
    def __init__(self, med, index_url="", pg_n=0):
        self.med = med
        self.index_url = index_url
        self.pg_n = pg_n
        self.vids = []
        self.pics = []

    def scrape_index(self):
        url = self.index_url.format(self.pg_n)
        r = requests.get(url)
        r.close()
        pg = html.fromstring(r.text)
        # videos links are relative paths
        self.vids += ["http://www.xvideos.com" + ending
                      for ending in pg.xpath("//div[@class='thumb']/a/@href")]
        # image links are not relative
        self.pics += pg.xpath("//div[@class='thumb']/a/img/@src")
        assert len(self.vids) == len(self.pics)
        self.pg_n += 1

    def scrape_video(self, vid_url):
        data = {}
        r = requests.get(vid_url)
        r.close()
        pg = html.fromstring(r.text)
        
        # Title.
        title = pg.xpath("//div[@id='main']/h2//text()")
        title = title[0]  # get the string out of the list (should be only one)
        title = title.strip()

        # Duration.
        duration = pg.xpath("//span[@class='duration']/text()")
        duration = duration[0]  # get the string out of the list (should be only one)
        hours   = re.search("[0-9]*(?=h)",    duration)  # extract hrs and mins
        minutes = re.search("[0-9]*(?= min)", duration)  # with regexes
        if hours:
            hours = hours.group()
        else:
            hours = 0
        if minutes:
            minutes = minutes.group()
        else:
            minutes = 0
        duration = int(hours) * 60 + int(minutes)  # calculate running time in minutes

        # Tags
        tags = pg.xpath("//a[contains(@href, '/tags/')]/text()")
        tags = tags[1:]  # meant to be a list, but first tag is just "Tags"

        # Views.
        views = pg.xpath("//span[@class='nb_views']/text()")
        views = views[0]  # it's the first of many results
        views = views.strip()
        views = views.replace(",","") # get rid of commas
        views = int(views)

        # Raters.
        raters = pg.xpath("//span[@id='ratingTotal']/text()")
        raters = raters[0]  # get string out of list, should be the only one
        raters = raters.replace(",", "")  # remove commas
        raters = int(raters)
    
        # Rating.
        rating = pg.xpath("//span[@id='rating']/text()")
        rating = rating[0]    # get string out of list, should be the only one
        rating = rating[:-1]  # trim percentage symbol
        rating = float(rating)
        
        data = {"title"    : title,
                "duration" : duration, 
                "tags"     : tags,
                "views"    : views,
                "raters"   : raters,
                "rating"   : rating,
                "url"      : self.cur_vid}
        
        return data

    def next(self):
        if len(self.vids) == 0:
            self.scrape_index()
        self.cur_vid = self.vids.pop()
        self.cur_pic = self.pics.pop()

    def load_pics(self, pic_url):
        """Determine the next video to be show and return three preview images."""
        pic_url = re.search(".+\.(?=([0-9]+.jpg))", pic_url).group()
        pic_url = pic_url + "{0}.jpg"  # make url able to take .format() method
        # preview images range from 1 to 30.
        urls = []
        for i in range(1, 30, 31 // self.med.pics_to_display):
            urls.append(pic_url.format(i))
        count = 0
        while count < 2:  # Give it an extra shot if there's a connection time-out.
            count += 1
            try:
                pics = []
                for url in urls:
                    r = requests.get(url)
                    pics.append( PhotoImage(Image.open(BytesIO(r.content))) )
                    r.close()

                return tuple(pics)

            except requests.exceptions.ConnectionError:
                if count < 2:
                    self.med.feedback("Connection error, waiting...")
                    time.sleep(3)
                    self.med.feedback("Trying again.")
                else:
                    self.med.feedback("Connection error. Pics not loaded.")
