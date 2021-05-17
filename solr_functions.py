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
    if isinstance(query, list):  # query is list of strings
        solr_api = 'http://localhost:8983/solr/%s/select?q=text%3A' % core
        for q in query:
            solr_api += q + '%2B'
    elif isinstance(query, str):  # query is single string
        solr_api = 'http://localhost:8983/solr/%s/select?q=text%3A%s' % (core, query)
    count = 0
    while True:
        count += 1
        if count > 6:
            return None
        try:
            resp = requests.request(method='GET', url=solr_api, headers=headers)
            return resp
        except Exception as oops:
            print(oops)
            sleep(1)