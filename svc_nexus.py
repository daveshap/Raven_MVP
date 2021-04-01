from time import time
from uuid import uuid4
import flask
import json
from flask import request,send_from_directory
import logging
import requests
from functions import *
import datetime as dt
import os
import subprocess


stream = list()  # stream of consciousness
debug = list()   # TODO log of all messages 
msvcs = dict()   # files and Popen objects of microservices
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)
app = flask.Flask('nexus')
txt = str(dt.datetime.now())
nexusfilename = 'logs/nexus_%s.json' % txt.replace(':','-').replace(' ','T').split('.')[0]


def metadata_only(d):
    new = dict()
    new['key'] = d['key']
    new['sid'] = d['sid']
    new['irt'] = d['irt']
    new['ctx'] = d['ctx']
    new['mid'] = d['mid']
    new['time'] = d['time']
    return new


@app.route('/', methods=['POST', 'GET', 'DELETE'])
def api():
    try:
        if request.method == 'POST':
            payload = request.json
            # required: message (msg), key, service id (sid)
            new = dict()
            new['msg'] = payload['msg']  # message
            new['key'] = payload['key']  # taxonomical key (metadata)
            new['sid'] = payload['sid']  # service id
            new['irt'] = payload['irt']  # in response to
            new['ctx'] = payload['ctx']  # original context MID
            new['mid'] = str(uuid4())  # add message ID
            new['time'] = time()  # add timestamp
            stream.append(new)
            print('API POST:', new['sid'], new['key'], new['time'])
            write_json(nexusfilename, stream)
            # TODO send copy to RECALL SVC
            return json.dumps({'success':True}), 200, {'ContentType':'application/json'} 
        elif request.method == 'GET':
            result = stream
            # filter stream
            if 'key' in request.args:
                result = [i for i in result if request.args['key'] in i['key']]
            if 'sid' in request.args:
                result = [i for i in result if request.args['sid'] in i['sid']]
            if 'ctx' in request.args:
                result = [i for i in result if request.args['ctx'] in i['ctx']]
            if 'mid' in request.args:
                result = [i for i in result if request.args['mid'] in i['mid']]
            if 'irt' in request.args:
                result = [i for i in result if request.args['irt'] in i['irt']]
            if 'keyword' in request.args:
                result = [i for i in result if request.args['keyword'] in i['msg']]
            if 'start' in request.args:
                result = [i for i in result if i['time'] >= float(request.args['start'])]
            if 'end' in request.args:
                result = [i for i in result if i['time'] <= float(request.args['end'])]
            if 'metadata' in request.args:
                result = [metadata_only(i) for i in result]
            #print('API GET:', request.query_string.decode(), '\tCOUNT:', len(result))
            return flask.Response(json.dumps(result), mimetype='application/json')
        elif request.method == 'DELETE':
            # prune stream
            if 'mid' in request.args:
                stream = [i for i in stream if i['mid'] != request.args['mid']]
            if 'ctx' in request.args:
                stream = [i for i in stream if i['ctx'] != request.args['ctx']]
            print('API DELETE:', request.query_string.decode())
            return json.dumps({'success':False}), 404, {'ContentType':'application/json'} 
    except Exception as oops:
        print('ERRORA in NEXUS/API:', oops)
        return json.dumps({'success':False}), 500, {'ContentType':'application/json'} 


@app.route('/nexus', methods=['GET'])
def nexus():
    html = read_file('nexus_base.html')
    #descending_stream = sorted(stream, key=lambda k: k['time'], reverse=True) 
    html += '<h1>Nexus - Stream of Consciousness</h1><p><ul><li>Key: Message type</li><li>SID: Service ID</li><li>Time: UNIX time</li><li>MID: Message ID</li><li>IRT: In response to</li><li>CTX: Original context</li></ul></p>'
    #for message in descending_stream:
    html += stream_table(stream)
    #for message in stream:
    #    html += message_table(message)
    #    # TODO add internal links for IRT to MID (just click on the IRT UUID to take you to the original message
    #    # TODO add sort and filter functions to Nexus (probably use URL query strings for this)
    #    # TODO "show only ideas" or "show only X key" or "show only X service" that kind of thing
    html += '</body></html>'
    return html


@app.route('/context', methods=['GET','POST'])
def context():
    if request.method == 'GET':
        html = read_file('nexus_base.html')
        html += '<h1>Context</h1><p>Enter context below. The more detail, the better!</p>'
        html += '<form action="/context" method="post" id="context">'
        html += '<button type="submit">Submit</button></form>'
        html += '<br><textarea rows="30" cols="175" name="context" form="context"></textarea>'
        html += '</body></html>'
        return html
    elif request.method == 'POST':
        context = request.form['context']
        payload = dict()
        payload['msg'] = context
        payload['key'] = 'context.new'  # context.old is from RECALL
        payload['sid'] = 'nexus'
        payload['ctx'] = 'new'
        payload['irt'] = 'n/a'
        results = requests.request(method='POST', url='http://127.0.0.1:9999/', json=payload)
        response = flask.make_response(flask.redirect('/nexus'))
        return response


@app.route('/output', methods=['GET'])
def output():
    html = read_file('nexus_base.html')
    html += '<h1>Output</h1><p>Coming soon!</p>'
    return html


@app.route('/microservices', methods=['GET'])
def microservices():
    files = [i for i in os.listdir() if 'svc_' in i and '.py' in i]
    # TODO add stop action in args
    if 'action' in request.args:
        filename = request.args['service']
        if request.args['action'] == 'stop':
            kill_service(msvcs, filename)
        elif request.args['action'] == 'start':
            start_service(msvcs, filename)
        elif request.args['action'] == 'startall':
            for file in files:
                start_service(msvcs, file)
        elif request.args['action'] == 'stopall':
            for file in files:
                kill_service(msvcs, file)
    # update microservices data list
    for file in files:
        if file == 'svc_nexus.py':
            continue
        if file not in msvcs:
            msvcs[file] = None
    # generate HTML
    html = read_file('nexus_base.html')
    html += '<h1>Microservices</h1>'
    html += service_table(msvcs)
    # TODO html += '<a href="/microservices?action=startall">START ALL</a><br><a href="/microservices?action=stopall">HALT ALL</a></body></html>'
    return html


@app.route('/favicon.ico')
def fav():
    return send_from_directory(app.root_path,'favicon.ico')


if __name__ == '__main__':
    print('Starting Raven Nexus')
    app.run(host='0.0.0.0', port=9999)
