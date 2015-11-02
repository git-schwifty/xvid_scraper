"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

import webbrowser
import queue
import sys

from gui     import Window
from db_api  import Database
from scraper import Scraper
from brain   import Brain


class Mediator:
    """Handles communication between objects."""
    def __init__(self, look_ahead=2, skip_to_page=1):
        self.viewed_videos = {}
        self.currently_loaded_video_data = {}
        self.q    = queue.PriorityQueue()
        self.look_ahead = look_ahead

        self.scr = Scraper(base_url="http://www.xvideos.com/new/{0}/", pg_n=skip_to_page)
        self.db  = Database()
        self.ai  = Brain(self)
        self.win = Window(self)

        self.get_next()

    def get_next(self):
        """Determine which video should be selected, then update window."""
        # Throw two videos into our priority queue
        vids_added = 0
        while vids_added < self.look_ahead:
            self.scr.next()
            if self.db.has_video(self.scr.cur_vid):
                print("vid already rated", end="\t")
                sys.stdout.flush()
                continue
            else:
                print("\nscraping vid")
                sys.stdout.flush()
                scraped = self.scr.scrape_video()
                # We want to be able to get the scraped data
                # and preview pics by video url.
                self.viewed_videos[self.scr.cur_vid] = (scraped, self.scr.cur_pic)
                guessed_rating = self.ai.predict(scraped)
                self.q.put(self.scr.cur_vid, guessed_rating)
                vids_added += 1
            # Get the video likely to have the best rating
            to_show_url = self.q.get()
            scraped_data, preview_pic_url = self.viewed_videos[to_show_url]
            self.currently_loaded_video_data = scraped_data
            pic1, pic2, pic3 = self.scr.load_pics(preview_pic_url) 
            self.win.update_images(pic1, pic2, pic3)

    def save(self, rating):
        """Save the data scraped from the current video then get next video."""
        self.currently_loaded_video_data["loved"] = rating
        self.db.save(self.currently_loaded_video_data)
        self.get_next()
        
    def open_vid(self):
        webbrowser.open(self.scr.cur_vid)

    def train(self):
        print("getting top tags")
        tags, ratings, tag_to_vec = self.db.vectorize_tags()
        print("training on tags.")
        self.ai.train(tags, ratings, tag_to_vec)
        print("finished training")

    def close_db(self):
        """When a window closes, disconnect from a database."""
        self.db.cnx.close()

if __name__ == "__main__":
    med = Mediator()
