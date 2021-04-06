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
    stream = nexus_get(start=last_msg['time'])
    return stream


def save_nexus(messages, connection, cursor):
    # order: msg, key, sid, irt, ctx, mid, time
    values = [(i['msg'], i['key'], i['sid'], i['irt'], i['ctx'], i['mid'], i['time']) for i in messages if 'recall' not in i['key']]  # exclude recalled messages
    for value in values:
        result = cursor.execute('INSERT OR IGNORE INTO recall VALUES (?,?,?,?,?,?,?)', value)  # skip over duplicate values
    connection.commit()


def find_keywords(messages):
    results = list()
    r = Rake()
    for message in messages:
        r.extract_keywords_from_text(message['msg'])
        scores = r.get_ranked_phrases_with_scores()
        terms = [i[1] for i in scores if i[0] > 2.0]  # generally seems like nothing below 2.0 is interesting
        results += terms
    return results


def fetch_recall(terms, cursor):
    results = list()
    for term in terms:
        # TODO split term up based on whitespace, remove punctuation, add multiple LIKE clauses to WHERE condition
        query = """SELECT * FROM recall WHERE msg LIKE '%{0}%'""".format(term)
        cursor.execute(query)
        fetch = cursor.fetchall()
        results += fetch
    final = [{'msg': i[0], 'key': i[1], 'sid': i[2], 'irt': i[3], 'ctx': i[4], 'mid': i[5], 'time': i[6]} for i in results]
    return final


def post_messages(messages):
    for message in messages:
        try:
            payload = dict()
            payload['msg'] = message['msg']
            payload['irt'] = message['irt']
            payload['ctx'] = message['ctx']
            payload['mid'] = message['mid']  # nexus can decide whether or not to keep
            payload['time'] = message['time']  # nexus can decide whether or not to keep
            payload['key'] = 'recall.' + message['key']
            payload['sid'] = 'recall.' + message['sid']
            result = nexus_post(payload)
            #print(result)
        except Exception as oops:
            print('ERROR in RECALL/POST_MESSAGES:', oops)    


if __name__ == '__main__':
    print('Starting Recall Service')
    dbcon = sqlite3.connect('raven_recall.sqlite')
    dbcur = dbcon.cursor()
    start_db(dbcon, dbcur)
    while True:
        latest = query_nexus()
        save_nexus(latest, dbcon, dbcur)
        keywords = find_keywords(latest)
        recall_messages = fetch_recall(keywords, dbcur)
        post_messages(recall_messages)
        sleep(default_sleep)
