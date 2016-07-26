#!/usr/bin/env python3

# The MIT License (MIT)

# Copyright (c) 2016 RascalTwo @ therealrascaltwo@gmail.com

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

"""Reddit bot that updates the flair of posts devs have responded to."""

import sqlite3
import praw
import json
import time


class DevResponseFlairer(object):
    """Reddit bot that updates the flair text of posts developers have responded to."""

    def __init__(self):
        """Create databases, load config file, and login to reddit."""
        self.running = False

        with open("config.json", "r") as config_file:
            self.config = json.loads(config_file.read())

        self.db = sqlite3.connect("database.db")
        cur = self.db.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS posts(
                id       TEXT  NOT NULL  PRIMARY KEY,
                utc      INT   NOT NULL,
                comment  TEXT  NOT NULL
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS processed(
                id       TEXT  NOT NULL  PRIMARY KEY,
                utc      INT   NOT NULL
            )
        """)
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS limit_1k AFTER INSERT ON posts
              BEGIN
                DELETE FROM posts WHERE utc <= (SELECT utc FROM posts ORDER BY utc DESC LIMIT 1000, 1);
              END;
        """)
        cur.execute("""
            CREATE TRIGGER IF NOT EXISTS limit_1k AFTER INSERT ON processed
              BEGIN
                DELETE FROM processed WHERE utc <= (SELECT utc FROM processed ORDER BY utc DESC LIMIT 1000, 1);
              END;
        """)
        cur.close()
        self.db.commit()
        self.db.close()

        self.reddit = praw.Reddit(self.config["user_agent"])
        self.reddit.login(self.config["username"],
                          self.config["password"],
                          disable_warning="True")

    def query(self, query, arguments=(), first=False):
        """Make a query and return the results."""
        if not isinstance(arguments, tuple):
            arguments = (arguments, )
        cur = self.db.cursor()
        cur.execute(query, arguments)
        results = cur.fetchall()
        cur.close()
        if len(results) > 0 and first:
            return results[0]
        return results

    def execute(self, statement, arguments=()):
        """Execute a statement, returning nothing."""
        if not isinstance(arguments, tuple):
            arguments = (arguments, )
        cur = self.db.cursor()
        cur.execute(statement, arguments)
        cur.close()
        self.db.commit()

    def _get_processed_ids(self):
        return [pid[0] for pid in self.query("SELECT id FROM processed")]

    def _add_processed(self, cid):
        self.execute("INSERT INTO processed "
                     "VALUES (?, ?)",
                     (cid, int(time.time())))

    def _get_post_ids(self):
        return [pid[0] for pid in self.query("SELECT id FROM posts")]

    def _add_post(self, pid, permalink):
        self.execute("INSERT INTO posts "
                     "VALUES (?, ?, ?)",
                     (pid, int(time.time()), permalink))

    def run(self):
        """Start the bot main loop."""
        self.running = True
        self.db = sqlite3.connect("database.db")
        while True:
            for comment in praw.helpers.comment_stream(self.reddit, "+".join(self.config["subreddits"]), limit=self.config["comment_amount"], verbosity=0):
                if not self.running:
                    break
                if comment.id in self._get_processed_ids():
                    break
                self._add_processed(comment.id)
                if comment.author is None:
                    continue
                if comment.author.name not in self.config["developers"] and comment.author_flair_css_class not in self.config["developer_flairs"]:
                    continue
                post = comment.submission
                if post.id in self._get_post_ids():
                    continue
                if post.link_flair_text is not None and "Dev Response" in post.link_flair_text:
                    continue
                print("Post flaired:")
                print(post)
                print(post.permalink)
                print(comment.permalink)
                self._add_post(post.id, comment.permalink)
                post.set_flair("{} | Dev Response".format(post.link_flair_text),
                               post.link_flair_css_class)
            if not self.running:
                break
            print("...")
            time.sleep(self.config["check_rate"])
        print("Exiting...")

if __name__ == "__main__":
    DevResponseFlairer().run()
