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

from common.tasks import add_domain, get_domain, delete_domain, test, resolve_domains, disable_domain, enable_domain, get_ns, get_ipv4, get_ipv6, get_domains_by_status, get_domains_by_enabled_status, get_whois, get_domain_whois
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
            'schedule': crontab(minute="*/5")
        },
        'collect_whois': {
            'task': 'collect_whois',
            'schedule': crontab(minute="*/15")
        }
    }

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

app.blueprint(swagger_blueprint)
app.config.API_VERSION = '0.0.2'
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
    resolve_domains.delay()

@celery.task(name ="collect_whois")
def collect_whois():
    get_whois.delay()

@app.route('/ip/<ip>', methods=['GET']) #by default we look for ipv4
@app.route('/ipv4/<ip>', methods=['GET'])
@doc.summary("Lookup a ipv4 address.")
async def fetch_ipv4(request, ip):
    task = get_ipv4.delay(ip)
    while not task.ready():
        pass

    return response.json({"data" : task.get(timeout=1)})

@app.route('/ipv6/<ip>', methods=['GET'])
@doc.summary("Lookup a ipv6 address.")
async def fetch_ipv6(request, ip):
    task = get_ipv6.delay(ip)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.route('/ns/<ns_domain>', methods=['GET'])
@doc.summary("Lookup an ns address.")
async def fetch_ns(request, ns_domain):
    task = get_ns.delay(ns_domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.route('/status/domains', methods=['GET'])
@app.route('/status/<status>/domains', methods=['GET'])
@doc.summary("Get back a list of all domains filterable by dns status.")
async def fetch_domain_status(request, status='all'):
    task = get_domains_by_status.delay(status)
    while not task.ready():  
        pass

    return response.json({"data" : task.get(timeout=1)})

@app.route('/enabled/domains', methods=['GET'])
@app.route('/enabled/<status>/domains', methods=['GET'])
@doc.summary("Get back a list of all domains filterable by enabled status.")
async def fetch_domain_enabled_status(request, status="all"):
    task = get_domains_by_enabled_status.delay(status)
    while not task.ready():
        pass

    return response.json({"data" : task.get(timeout=1)})


@app.route('/domain/<domain>', methods=['GET'])
@doc.summary("Get all history for a specific domain.")
async def fetch_domain(request, domain):
    task = get_domain.delay(domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.route('/whois/domain/<domain>', methods=['GET'])
@doc.summary("Get whois for a  specific domain.")
async def fetch_domain_whois(request, domain):
    task = get_domain_whois.delay(domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.route('/domain/<domain>', methods=['DELETE'])
@doc.summary("Remove a domain completely.")
async def drop_domain(request, domain):
    task = delete_domain.delay(domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})


@app.route('/enable/<domain>', methods=['GET', 'POST'])
@doc.summary("Enable a domain.")
async def turn_on_domain(request, domain):
    task = enable_domain.delay(domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.route('/disable/<domain>', methods=['GET', 'POST'])
@doc.summary("Disable a domain.")
async def turn_off_domain(request, domain):
    task = disable_domain.delay(domain)
    while not task.ready():
        pass
    return response.json({"data" : task.get(timeout=1)})

@app.listener('before_server_start')
def before_start(app, loop):
    logger.debug("Staring app.")

@app.listener('after_server_start')
def after_start(app, loop):
    logger.debug("App started.")

@app.listener('before_server_stop')
def before_stop(app, loop):
    logger.debug("Stopping app.")


@app.listener('after_server_stop')
def after_stop(app, loop):
    logger.debug("App stopped.")

# Catches 404 pages
@app.exception(NotFound)
def ignore_404s(request, exception):
    return response.text("404: {}".format(
        request.url))


# Catches ServiceUnavailable
@app.exception(ServiceUnavailable)
def ignore_ServiceUnavailable(request, exception):
    logging.warning("ServiceUnavailable", request.url, exception)
    return response.text("Service Unavailable")

# catch timeouts
@app.exception(RequestTimeout)
def Timeout(request, exception):
    logger.warnin("Hit a timeout error {}".format(request.url))
    return response.text("Request Timeout")


@app.exception(ServerError)
def log_any_exception(request, exception):
    logger.error(request.url, exception)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8181, debug=False, access_log=True, workers=1)

