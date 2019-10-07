Dmon
===

Dmon is a simple app centered around monitoring DNS changes for any domain a user is interested in. This is supported by a basic rest api on top of a celery based tasking system.

API Basics
===

GET /ip/{ip_address} or /ipv4/{ip_address}
```
{'data': [{'dns_session': {'A': ['127.0.0.1'],
                           'AAAA': [],
                           'MX': ['10 mail.threathive.io.'],
                           'NS': ['ns1.malicious.systems.',
                                  'ns2.malicious.systems.'],
                           'SOA': ['ns1.malicious.systems. '
                                   'admin.threathive.io. 15 604800 86400 '
                                   '2419200 604800'],
                           'TXT': ['"v=spf1 mx ip4:178.128.233.114 -all"']},
           'domain': 'threathive.io',
           'first_seen': '2019-10-07T21:35:00Z',
           'last_seen': '2019-10-07T22:37:00.048881'}]}

```

GET /ipv6/{ip_address}

```
{'data': [{'dns_session': {'A': ['108.177.119.102',
                                 '108.177.119.138',
                                 '108.177.119.100',
                                 '108.177.119.101',
                                 '108.177.119.139',
                                 '108.177.119.113'],
                           'AAAA': ['2a00:1450:4013:c00::8b'],
                           'MX': ['50 alt4.aspmx.l.google.com.',
                                  '30 alt2.aspmx.l.google.com.',
                                  '40 alt3.aspmx.l.google.com.',
                                  '10 aspmx.l.google.com.',
                                  '20 alt1.aspmx.l.google.com.'],
                           'NS': ['ns4.google.com.',
                                  'ns3.google.com.',
                                  'ns1.google.com.',
                                  'ns2.google.com.'],
                           'SOA': ['ns1.google.com. dns-admin.google.com. '
                                   '273171295 900 900 1800 60'],
                           'TXT': ['"facebook-domain-verification=22rm551cu4k0ab0bxsw536tlds4h95"',
                                   '"globalsign-smime-dv=CDYX+XFHUw2wml6/Gb8+59BsH31KzUr6c1l2BPvqKX8="',
                                   '"docusign=1b0a6754-49b1-4db5-8540-d2c12664b289"',
                                   '"v=spf1 include:_spf.google.com ~all"',
                                   '"docusign=05958488-4752-4ef2-95eb-aa7ba8a3bd0e"']},
           'domain': 'google.com',
           'first_seen': '2019-10-07T22:39:00Z',
           'last_seen': '2019-10-07T22:39:00.115315'}]}
```

GET /ns/{ns_domain}

```
{'data': [{'dns_session': {'A': ['127.0.0.1'],
                           'AAAA': [],
                           'MX': ['10 mail.threathive.io.'],
                           'NS': ['ns1.malicious.systems.',
                                  'ns2.malicious.systems.'],
                           'SOA': ['ns1.malicious.systems. '
                                   'admin.threathive.io. 15 604800 86400 '
                                   '2419200 604800'],
                           'TXT': ['"v=spf1 mx ip4:178.128.233.114 -all"']},
           'domain': 'threathive.io',
           'first_seen': '2019-10-07T21:35:00Z',
           'last_seen': '2019-10-07T22:37:00.048881'}]}
```

GET /domain/{domain}

```
{'data': [{'dns_session': {'A': ['127.0.0.1'],
                           'AAAA': [],
                           'MX': ['10 mail.threathive.io.'],
                           'NS': ['ns1.malicious.systems.',
                                  'ns2.malicious.systems.'],
                           'SOA': ['ns1.malicious.systems. '
                                   'admin.threathive.io. 15 604800 86400 '
                                   '2419200 604800'],
                           'TXT': ['"v=spf1 mx ip4:178.128.233.114 -all"']},
           'domain': 'threathive.io',
           'first_seen': '2019-10-07T21:35:00Z',
           'last_seen': '2019-10-07T22:37:00.048881'}]}
```

DELETE /domain/{domain}
```
{'data': 'done!'}
```

GET | POST  /enable/{domain}
```
{'data': 'done!'}
```

GET | POST  /disable/{domain}
```
{'data': 'done!'}
```

Run async tasks (on demand tasks)
===
 celery -A worker worker -l warning


Run timed background tasks (automated tasks)
===

 celery -A app.celery worker -l info 


Run API
===

 python3 app.py


Author
======

adam <adam@threathive.com>


License
=======

dmon uses the MIT license, check LICENSE file.


Python versions
===============
Python >= 3.5 should have no problems.


Contributing
============

If you would like to contribute, fork the project, make a patch and send a pull request.



