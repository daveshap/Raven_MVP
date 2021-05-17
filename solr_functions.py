from time import sleep
import requests


def solr_index(payload, core='wiki'):
    headers = {'Content-Type':'application/json'}
    if isinstance(payload, dict):  # individual JSON doc
        solr_api = 'http://localhost:8983/solr/%s/update/json/docs?commitWithin=5000' % core
    elif isinstance(payload, list):  # list of JSON docs
        solr_api = 'http://localhost:8983/solr/%s/update?commitWithin=5000' % core
    count = 0
    while True:
        count += 1
        if count > 6:
            return None
        try:
            resp = requests.request(method='POST', url=solr_api, json=payload, headers=headers)
            return resp
        except Exception as oops:
            print(oops)
            sleep(1)


def solr_search(query, core='wiki'):
    headers = {'Content-Type':'application/json'}
    if ' ' in query:  # query is more than one phrase
        solr_api = 'http://localhost:8983/solr/{core}/select?q=text%3A'.format(core=core)
        for q in query.split():
            solr_api += q + '%2B'
    else:  # query is single word
        solr_api = 'http://localhost:8983/solr/{core}/select?q=text%3A{query}'.format(core=core, query=query)
    count = 0
    while True:
        count += 1
        if count > 6:
            return None
        try:
            resp = requests.request(method='GET', url=solr_api, headers=headers)
            return resp.json()
        except Exception as oops:
            print(oops)
            sleep(1)