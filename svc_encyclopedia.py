import sqlite3
import re
import os
import requests
import json
from time import sleep
from functions import *
from rake_nltk import Rake


default_sleep = 1
last_msg = {'time':0.0}


def start_db(connection, cursor):
    # create table if it doesn't exist
    cursor.execute('CREATE TABLE IF NOT EXISTS recall (msg text, key text, sid text, irt text, ctx text, mid text UNIQUE, time real)')
    # create index if it doesn't exist
    cursor.execute('CREATE INDEX IF NOT EXISTS msg_idx ON recall(msg)')
    connection.commit()


def query_nexus():
    global last_msg
    stream = nexus_get(start=last_msg['time'], key='context.new')
    for i in stream:
        if i['time'] > last_msg['time']:
            last_msg = i
    return stream


def find_keywords(messages):
    results = list()
    r = Rake()
    for message in messages:
        r.extract_keywords_from_text(message['msg'])
        scores = r.get_ranked_phrases_with_scores()
        terms = [(i[1], message['ctx']) for i in scores if i[0] > 2.0]  # generally seems like nothing below 2.0 is interesting
        results += terms
    return results


def fetch_encyclopedia(terms, cursor):
    results = list()
    for term in terms:
        # TODO split term up based on whitespace, remove punctuation, add multiple LIKE clauses to WHERE condition
        query = """SELECT article FROM wiki WHERE title LIKE '%{0}%'""".format(term[0])
        cursor.execute(query)
        fetch = cursor.fetchall()
        results += [(i, term[1]) for i in fetch]  # i is article, term[1] is CTX
    return results


def post_messages(articles):
    for article in articles:
        try:
            payload = dict()
            payload['msg'] = article[0]
            payload['irt'] = article[1]
            payload['ctx'] = article[1]
            payload['key'] = 'encyclopedia.article'
            payload['sid'] = 'encyclopedia.wiki.simple'
            result = nexus_post(payload)
            #print(result)
        except Exception as oops:
            print('ERROR in RECALL/POST_MESSAGES:', oops)    


if __name__ == '__main__':
    print('Starting Recall Service')
    dbcon = sqlite3.connect('simple_wiki.sqlite')
    dbcur = dbcon.cursor()
    while True:
        latest = query_nexus()
        keywords = find_keywords(latest)
        encyclopedia_articles = fetch_encyclopedia(keywords, dbcur)
        post_messages(encyclopedia_articles)
        sleep(default_sleep)
