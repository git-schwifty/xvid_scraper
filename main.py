"""
A program for viewing, rating, and getting recommendations for
pornographic videos through the website xvideos.com.
"""
#!/usr/bin/env python

from db_api    import Database
from scraper   import Scraper
from brain     import Brain
from proj_ADTs import MyQueue
from threading import Thread, Lock
#from profile   import ProfileManager

import webbrowser
import time
import sys


class Mediator:
    def __init__(self, win):
        self.win  = win

        # Settings will go here.
        index_url  = "http://www.xvideos.com/c/{0}/anal-12"
        look_ahead = 1
        qmaxsize   = 1

        # State used by various objects.
        self.cur_vid_data = {}

        # Load up all the major elements of the program.
        self.scr  = Scraper(index_url=index_url, pg_n=0)
        self.db   = Database(self)  # db will skip to next video if saving fails
        self.ai   = Brain(self)
        self.q    = MyQueue(maxsize=qmaxsize)
        self.lock = Lock()

        # Scraping websites will be done as a background process.
        self.gather_process = Thread(target = self.gather,
                                     daemon = True)
        self.gather_process.start()

    def gather(self, look_ahead=4):
        """Background process that quietly fills up the video queue with urls."""
        while True:
            if self.q.not_full():
                # If look_ahead = 1, the result would be the there wouldn't
                # be any videos filtered out, you'd just sort of view the
                # first couple out of order, then for every one video you
                # viewed, you'd just see the next video listed on the index.
                # What we want instead is to throw out x videos for every
                # 1 we decide is good enough to show the user. This requires
                # we queue up more videos than the user ever evaluates.
                #
                # We'll implement this as a while loop so we can
                # ignore already seen videos.
                looked_at = 0
                while looked_at < look_ahead:
                    # Tell the scraper to set up the next video for
                    # further processing (sets its internal state to
                    # have a a video URL as scr.cur_vid as it's corr-
                    # esponding preview image URL to scr.cur_pic).
                    self.scr.next()
                    cur_vid = self.scr.cur_vid  # vars with too many dots are uggo

                    if not self.db.has_video(cur_vid):
                        # Scrape the video page for data.
                        scraped_data = self.scr.scrape_video(cur_vid)

                        # Predict how much the user will like this video.
                        prediction = self.ai.predict(scraped_data)

                        # Save some extra data.
                        scraped_data["pic_url"] = self.scr.cur_pic
                        scraped_data["pred"]    = prediction
                        
                        # Put data into queue.
                        # High prediction is high priority, but queue
                        # treats low numbers as high priority, so we
                        # just put it in as a negative number.
                        with self.lock:
                            self.q.put(scraped_data, -prediction)
                        looked_at += 1
                assert looked_at >= look_ahead

            else:
                time.sleep(5)

    def next_(self):
        """Load up the next video in the queue."""
        # Wait until we have save data before going on to the next one.
        while self.q.empty():
            self.feedback("Video queue is empty; waiting...")
            time.sleep(1)

        self.feedback("loading next video...")
        # Get our data out of the queue.
        self.lock.acquire()
        self.cur_vid_data = self.q.get()
        self.lock.release()

        # Refresh the window with new preview images.
        pic_url = self.cur_vid_data["pic_url"]
        self.win.update_images( *self.scr.load_pics(pic_url) )

        # Display a little data about the video.
        txt = ""
        txt += "title:\t"  + str(self.cur_vid_data['title']   ).ljust(20)[:20]   + "\n"
        txt += "\t"        + str(self.cur_vid_data['title']   ).ljust(40)[20:40] + "\n"
        txt += "length:\t" + str(self.cur_vid_data['duration']).ljust(20)[:20]   + "\n"
        txt += "guess:\t"  + str(round(self.cur_vid_data['pred'], 2))
        self.feedback(txt)

    def save(self, rating):
        # I should change the name loved since the program evolved to
        # where there is no longer a binary yes/no for the rating.
        self.cur_vid_data["loved"] = rating
        self.db.save(self.cur_vid_data)
        self.next_()

    def open_vid(self):
        webbrowser.open(self.cur_vid_data["url"])

    def train(self):
        # We need to determine how many features to train on, but
        # we'll just pass in a formula that takes in as an argument
        # the number of unique tags in the database.
        self.feedback("training...")
        n_feats = lambda n: n // 2
        all_vectors, usr_ratings, tag_to_vec = self.db.vectorize_tags(n_feats)
        self.ai.train(all_vectors, usr_ratings, tag_to_vec)

    def feedback(self, text):
        """Tell the user what's going on in a textbox inside the window (not popup)."""
        self.win.feedback_box.config(text=text)

    def close(self):
        """When a window closes, disconnect from a database."""
        self.feedback("closing...")
        try:
            self.train()
        except:
            pass
        self.db.cnx.close()
        self.win.root.destroy()


if __name__ == "__main__":
    # Mediator gets called from inside window because
    # window has to be the main thread in order for it
    # to not throw up a ton of errors.
    win = Window()
