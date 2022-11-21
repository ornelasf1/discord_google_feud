# Discord Gfeud
Game bot available on Discord, simply invite the bot to your server https://discord.com/invite/xX5mk8Esg3

The premise of the game is to guess what Google suggest as auto-completion words. Everyone is able to participate in guessing the auto-completes. The person with the highest score wins the game! 

# Demo
![Alt text](discord_gfeud.gif)

# Python Environment
Requires Python 3.9

Run application with
```python
python3.9 main.py
```

# Graphite

Virtual env in /opt/graphite

Activate virtual environment with
source /opt/graphite/bin/activate

Exit virtual env:
deactivate

We need to carry over variables from virtualenv to run commands with virtualenv and sudo powers.
For example to run sudo pip install do,

sudo /opt/graphite/bin/pip install <module>

Verify pip is coming from virtualenv:
which pip -> /opt/graphite/bin/pip

Install graphite
https://graphite.readthedocs.io/en/latest/install-pip.html

export PYTHONPATH="/opt/graphite/lib/:/opt/graphite/webapp/"
sudo /opt/graphite/bin/pip install --no-binary=:all: https://github.com/graphite-project/whisper/tarball/master
sudo /opt/graphite/bin/pip install --no-binary=:all: https://github.com/graphite-project/carbon/tarball/master
sudo /opt/graphite/bin/pip install --no-binary=:all: https://github.com/graphite-project/graphite-web/tarball/master

VM command dump
sudo apt-get install python-dev   # for python2.x installs
sudo apt-get install python3-dev  # for python3.x installs
sudo apt install libpython3.6-dev
sudo apt-get install libffi-dev

Django depens
sudo apt-get install libpango1.0-0
sudo apt-get install libcairo2
sudo apt-get install libpq-dev

## Confguring web app

https://graphite.readthedocs.io/en/latest/config-webapp.html#nginx-gunicorn

Web app systemd service file path: /etc/systemd/system/graphite-web.service
Web app systemd unit file path: /etc/systemd/system/graphite-web.socket

sudo pip3 install gunicorn
sudo apt install nginx

sudo systemctl start graphite-web

systemd commands:
sudo systemctl daemon-reload
sudo systemctl (status/start/restart) graphite-web.service
journalctl -u graphite-web.service

VM command dump:
sudo chown -R gfeudadmin:gfeudadmin /opt/graphite/

Error: No module named graphite.settings:
Ran the following to fix:
cd /opt/graphite/webapp/; PYTHONPATH=/opt/graphite/webapp django-admin.py migrate --settings=graphite.settings --run-syncdb

### Configure nginx

sudo touch /var/log/nginx/graphite.access.log
sudo touch /var/log/nginx/graphite.error.log
sudo chmod 640 /var/log/nginx/graphite.*
sudo chown www-data:www-data /var/log/nginx/graphite.*

sudo service nginx reload

nginx file path: /etc/nginx/sites-available/graphite

### Start web app

sudo systemctl start graphite-web.service

### Graphite on Ubuntu
https://www.digitalocean.com/community/tutorials/how-to-install-and-use-graphite-on-an-ubuntu-14-04-server

DB_PASSWORD = graphite-admin

sudo graphite-manage migrate
sudo graphite-manage createsuperuser
U: root
P: graphite-pass

sudo chmod a+rwx /var/log/graphite/info.log
sudo chmod a+rwx /var/log/graphite/exception.log

PYTHONPATH=$GRAPHITE_ROOT/webapp
cd /usr/bin
sudo django-admin migrate --settings=graphite.settings --run-syncdb

Apache2 configurations
/etc/apache2/sites-available/

Allow http port in Azure firewall

Use Graphyte for Python to send metrics
https://pypi.org/project/graphyte/

import graphyte
graphyte.init('127.0.0.1', prefix='gfeud')
graphyte.send('test.count', 10)
OR
python3 -m graphyte test.count 3

/etc/carbon/storage-schemas.conf
/etc/carbon/storage-aggregation.conf


### StatsD on Ubuntu
https://www.digitalocean.com/community/tutorials/how-to-configure-statsd-to-collect-arbitrary-stats-for-graphite-on-ubuntu-14-04

### Install Grafana
https://grafana.com/docs/grafana/latest/installation/debian/



[min]
pattern = \.min$
xFilesFactor = 0.1
aggregationMethod = min

[max]
pattern = \.max$
xFilesFactor = 0.1
aggregationMethod = max

[count]
pattern = \.count$
xFilesFactor = 0
aggregationMethod = sum

[lower]
pattern = \.lower(_\d+)?$
xFilesFactor = 0.1
aggregationMethod = min

[upper]
pattern = \.upper(_\d+)?$
xFilesFactor = 0.1
aggregationMethod = max

[sum]
pattern = \.sum$
xFilesFactor = 0
aggregationMethod = sum

[gauges]
pattern = .*gauges.*
xFilesFactor = 0
aggregationMethod = last

[default_average]
pattern = .* 
xFilesFactor = 0.5
aggregationMethod = average



