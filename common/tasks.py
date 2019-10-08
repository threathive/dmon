from celery import Celery
from os import environ
import requests
import json
import dns.resolver
import uuid
import datetime
import hashlib
from bson import ObjectId

import pymongo
from pymongo import ReturnDocument

from bson import json_util, ObjectId
import json

from celery.utils.log import get_task_logger
import logging
import logging.handlers
logger = get_task_logger(__name__)


def ordered(obj):
    if isinstance(obj,dict):
        return sorted(((k, ordered(v)) for k,v in obj.items()), key=str)
    if isinstance(obj,list):
        return sorted((ordered(x) for x in obj), key=str)
    else:
        return str(obj)


myclient = pymongo.MongoClient("mongodb://localhost:27017/")
mydb = myclient["mydatabase"]
dns_history = mydb["dns_history"]
domains = mydb["domains"]

#print(myclient.drop_database('mydatabase'))


app = Celery('tasks', broker='redis://127.0.0.1/12', backend='redis://127.0.0.1/13')

@app.task
def add_domain(domain):
    mydict = { "domain" : domain, "enabled" : True, 'last_updated': datetime.datetime.utcnow().isoformat(), "status" : "active" }
    x = domains.insert_one(mydict)
    return "done!"


@app.task
def get_domains_by_status(status):
    _hits = []
    match = {"status" : status}
    if status == 'all':
        match = {}

    for x in domains.find(match):
        _hits.append({
                  'domain': x.get('domain'),
                  'enabled': x.get("enabled"),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_updated': x.get('last_updated'),
                  'status': x.get('status')
        })

    return _hits

@app.task
def get_domains_by_enabled_status(status):
    _hits = []
    match = {}
    if status == "enabled":
        match = {"enabled" : True}
    elif status == "disabled":
        match = {"enabled": False}

    for x in domains.find(match ):
        _hits.append({
                  'domain': x.get('domain'),
                  'enabled': x.get("enabled"),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_updated': x.get('last_updated'),
                  'status': x.get('status')
        })

    return _hits


@app.task
def get_domain(domain): 
    _hits = []
    for x in dns_history.find({ "domain": domain }):
        _hits.append({
                  'domain': x.get('domain'),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_seen': x.get('last_seen'),
                  'dns_session' : x.get('_dns_session')
        })

    return _hits


@app.task
def get_ipv4(ip):
    _hits = []
    for x in dns_history.find({ "_dns_session.A": ip }):
        _hits.append({
                  'domain': x.get('domain'),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_seen': x.get('last_seen'),
                  'dns_session' : x.get('_dns_session')
        })

    return _hits

@app.task
def get_ipv6(ip):
    _hits = []
    for x in dns_history.find({ "_dns_session.AAAA": ip }):
        _hits.append({
                  'domain': x.get('domain'),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_seen': x.get('last_seen'),
                  'dns_session' : x.get('_dns_session')
        })

    return _hits

@app.task
def get_ns(ns_domain):
    _hits = []
    for x in dns_history.find({ "_dns_session.NS": ns_domain }):
        _hits.append({
                  'domain': x.get('domain'),
                  'first_seen': ObjectId(x.get('_id')).generation_time,
                  'last_seen': x.get('last_seen'),
                  'dns_session' : x.get('_dns_session')
        })

    return _hits

@app.task
def delete_domain(domain):
    domains.delete_many({ "domain": domain })
    return "done!"

@app.task
def disable_domain(domain):
    try:
        x = domains.find_one_and_update(
            {'domain' : domain },
            {'$set': {
                'enabled' : False,
                'last_updated': datetime.datetime.utcnow().isoformat()
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return "done!"
    except Exception as e:
        logger.error(e)
        return "sorry we hit an issue updating your domain status"



@app.task
def enable_domain(domain):
    try:
        x = domains.find_one_and_update(
            {'domain' : domain },
            {'$set': {
                'enabled' : True,
                'last_updated': datetime.datetime.utcnow().isoformat()
            }},
            upsert=True,
            return_document=ReturnDocument.AFTER
        )

        return "done!"
    except Exception as e:
        logger.error(e)
        return "sorry we hit an issue updating your domain status"


@app.task
def test():
    return "test works!"

@app.task
def resolve_domains():
    records = ['A', 'AAAA', 'MX', 'NS', 'TXT', 'SOA']
    for d in domains.find( {"enabled" : True} ):
        _dns_session = {
            "A": [],
            "AAAA": [],
            "MX": [],
            "NS": [],
            "TXT": [],
            "SOA": []
        }

        for record in records:
            try:
                answer = dns.resolver.query(d.get("domain"), record)
                for item in answer.rrset.items:
                    _dns_session[record].append(item.to_text().strip("."))
                    try:
                        x = domains.find_one_and_update(
                        {'domain' : d.get("domain") },
                        {'$set': {
                           'enabled' : True,
                           'status': 'active',
                           'last_updated': datetime.datetime.utcnow().isoformat()
                        }},
                         upsert=True,
                         return_document=ReturnDocument.AFTER
                        )

                    except Exception as e:
                        logger.error("Error updating domain status {} {}".format(d.get("domain"), e))

            except dns.resolver.NXDOMAIN as nxdomain:
                logger.warning("NXDOMAIN {} disabling ".format(d.get("domain")))

                try:
                    x = domains.find_one_and_update(
                    {'domain' : d.get("domain") },
                    {'$set': {
                       'enabled' : False,
                       'status': 'nxdomain',
                       'last_updated': datetime.datetime.utcnow().isoformat()

                    }},
                     upsert=True,
                     return_document=ReturnDocument.AFTER
                    )

                except Exception as e:
                    logger.error("Error updating domain status {} {}".format(d.get("domain"), e))

                break

            except dns.resolver.NoAnswer as no_answer:
                logger.warning("NO ANSWER {}".format(no_answer))

            except dns.resolver.NoNameservers as no_ns:
                logger.warning("NO NAMESERVERS {}".format(no_ns))
                try:
                    x = domains.find_one_and_update(
                    {'domain' : d.get("domain") },
                    {'$set': {
                       'enabled' : False,
                       'status': 'no_nameservers',
                       'last_updated': datetime.datetime.utcnow().isoformat()

                    }},
                     upsert=True,
                     return_document=ReturnDocument.AFTER
                    )

                except Exception as e:
                    logger.error("Error updating domain status {} {}".format(d.get("domain"), e))

                break

            except Exception as e:
                logger.warning("ran into an error {} for record type {} when working on domain {}".format(e, record, d.get("domain")))

        event_id = hashlib.sha256(repr(ordered(_dns_session)).encode("utf-8")).hexdigest()

        try:
            x = dns_history.find_one_and_update(
                {'event_id' : event_id },
                {'$set': {
                  'event_id': event_id,
                  'last_seen': datetime.datetime.utcnow().isoformat(),
                  'domain': d.get("domain"),
                  '_dns_session' : _dns_session
                }},
                upsert=True,
                return_document=ReturnDocument.AFTER
            )
        except Exception as e:
            logger.error(e)
