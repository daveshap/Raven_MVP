import re
import os
import openai
import requests
import json
from time import sleep
from functions import *
from solr_functions import *
import urllib3


default_sleep = 1
urllib3.disable_warnings()
open_ai_api_key = read_file('openaiapikey.txt')
openai.api_key = open_ai_api_key
last_msg = {'time':0.0}


def make_prompt(context):
    prompt = read_file('base_action_prompt.txt')
    return prompt.replace('<<CONTEXT>>', context)


def query_gpt3(context):
    prompt = make_prompt(context)
    response = openai.Completion.create(
        engine='davinci',
        #engine='curie',
        prompt=prompt,
        temperature=0.7,
        max_tokens=1000,
        top_p=1,
        frequency_penalty=0.7,
        presence_penalty=0.7,
        stop=['ACTION4:', 'CONTEXT:', 'INSTRUCTIONS:', '<<END>>'])
    return response['choices'][0]['text'].strip().splitlines()


def post_articles(articles, context):
    for article in articles:
        try:
            # TODO massage article
            payload = dict()
            payload['msg'] = article['title'] + ' : ' + article['text']
            payload['irt'] = context['mid']
            payload['ctx'] = context['mid']
            payload['key'] = 'encyclopedia.article'
            payload['sid'] = 'encyclopedia.wiki'
            result = nexus_post(payload)
            #print(result)
        except Exception as oops:
            print('ERROR in ENCYCLOPEDIA/POST_ARTICLES:', oops)


def query_nexus():
    global last_msg
    try:
        stream = nexus_get(key='context', start=last_msg['time'])
        for context in stream:
            if context['time'] <= last_msg['time']:
                continue
            if context['time'] > last_msg['time']:
                last_msg = context
            queries = get_gpt3_prompts(context['msg'])  # TODO
            articles = list()
            for query in queries:
                result = solr_search(query)
                articles += result['response']['docs']
            post_articles(articles, context)
    except Exception as oops:
        print('ERROR in ACTIONS/QUERY_NEXUS:', oops)


if __name__ == '__main__':
    print('Starting Encyclopedia Service')
    while True:
        query_nexus()
        sleep(default_sleep)
