import requests
from sanic import Sanic
from sanic import response
from sanic.exceptions import ServerError
from sanic.exceptions import NotFound
from sanic.exceptions import RequestTimeout
from sanic.exceptions import ServiceUnavailable
from sanic_openapi import swagger_blueprint
from sanic_openapi import doc

import logging
import logging.handlers

from common.tasks import add_domain, get_domain, delete_domain, test, resolve_domains, disable_domain, enable_domain, get_ns, get_ipv4, get_ipv6
from celery.result import AsyncResult

app = Sanic(__name__)

from celery import Celery
from celery.schedules import crontab
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379/13'
app.config['CELERY_RESULT_BACKEND'] = 'redis://localhost:6379/13'
app.config['CELERYBEAT_SCHEDULE'] = {
        # Executes every minute
        'periodic_task-every-minute': {
            'task': 'periodic_task',
            'schedule': crontab(minute="*")
        }
    }

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

app.blueprint(swagger_blueprint)
app.config.API_VERSION = '0.0.1'
app.config.API_TITLE = 'DMON API'
app.config.API_DESCRIPTION = 'DMON API'
app.config.API_TERMS_OF_SERVICE = 'Give me koffie..'
app.config.API_PRODUCES_CONTENT_TYPES = ['application/json']
app.config.API_CONTACT_EMAIL = 'adam@threathive.com'

# index
@app.route("/")
@doc.summary("index endpoint.. nothing to see here")
async def index(request):
    return response.text("dmon")

@celery.task(name ="periodic_task")
def periodic_task():
    task = resolve_domains.delay()
    print(task)
    
    logger.info("Hello! from periodic task")

@app.route('/ip/<ip>', methods=['GET']) #by default we look for ipv4
@app.route('/ipv4/<ip>', methods=['GET'])
@doc.summary("index endpoint.. nothing to see here")
async def fetch_ipv4(request, ip):
    task = get_ipv4.delay(ip)
    while not task.ready():
        pass

    return response.json({"data" : task.get(timeout=1)})

@app.route('/ipv6/<ip>', methods=['GET'])
@doc.summary("index endpoint.. nothing to see here")
async def fetch_ipv6(request, ip):
    task = get_ipv6.delay(ip)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})

@app.route('/ns/<ns_domain>', methods=['GET'])
@doc.summary("index endpoint.. nothing to see here")
async def fetch_ns(request, ns_domain):
    task = get_ns.delay(ns_domain)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})

@app.route('/domain/<domain>', methods=['GET'])
@doc.summary("index endpoint.. nothing to see here")
async def fetch_domain(request, domain):
    task = get_domain.delay(domain)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})

@app.route('/domain/<domain>', methods=['DELETE'])
@doc.summary("index endpoint.. nothing to see here")
async def drop_domain(request, domain):
    task = delete_domain.delay(domain)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})


@app.route('/enable/<domain>', methods=['GET', 'POST'])
@doc.summary("index endpoint.. nothing to see here")
async def turn_on_domain(request, domain):
    task = enable_domain.delay(domain)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})

@app.route('/disable/<domain>', methods=['GET', 'POST'])
@doc.summary("index endpoint.. nothing to see here")
async def turn_off_domain(request, domain):
    task = disable_domain.delay(domain)
    while not task.ready():
        print("waitin")
    print("free!")
    print(task.get(timeout=1))
    return response.json({"data" : task.get(timeout=1)})


@app.listener('before_server_start')
def before_start(app, loop):
    logging.info("SERVER STARTING")

@app.listener('after_server_start')
def after_start(app, loop):
    logging.info("SERVER STARTED")

@app.listener('before_server_stop')
def before_stop(app, loop):
    logging.info("SERVER STOPPING")


@app.listener('after_server_stop')
def after_stop(app, loop):
    logging.info("TRIED EVERYTHING")

# Catches 404 pages
@app.exception(NotFound)
def ignore_404s(request, exception):
    return response.text("Yep, I totally found the page: {}".format(
        request.url))


# Catches ServiceUnavailable
@app.exception(ServiceUnavailable)
def ignore_ServiceUnavailable(request, exception):
    logging.warning("ServiceUnavailable", request.url, exception)
    return response.text("Service Unavailable")

# catch timeouts
@app.exception(RequestTimeout)
def Timeout(request, exception):
    return response.text("Request Timeout")
    print(request.url, exception)
    logging.info(request.url)


@app.exception(ServerError)
def log_any_exception(request, exception):
    logging.error(request.url, exception)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8181, debug=True, access_log=True, workers=1)

