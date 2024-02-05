#!/bin/bash

PUSHBULLET_TOKEN=""

DB_LOG_FILE=$HOME/mongodb_down.log
DB_OUTPUT=$(service mongod status)
DB_STATUS=$?
if [[ $DB_STATUS -ne 0 ]] && [ ! -f "$DB_LOG_FILE"  ]; then
    curl -H "Access-Token: $PUSHBULLET_TOKEN" https://api.pushbullet.com/v2/pushes -d type=note -d title="[$(date)] DBMS for Gfeud is down!" -d body="${DB_OUTPUT}"
    journalctl -u mongod -n 20 > "$DB_LOG_FILE"
    systemctl restart mongod.service
elif [[ $DB_STATUS -eq 0 ]] && [ -f "$DB_LOG_FILE" ]; then
    curl -H "Access-Token: $PUSHBULLET_TOKEN" https://api.pushbullet.com/v2/pushes -d type=note -d title="[$(date)] DBMS for Gfeud is back up!"
    rm -f "$DB_LOG_FILE"
fi


APP_LOG_FILE=$HOME/gfeud_down.log
APP_OUTPUT=$(service gfeud status)
APP_STATUS=$?
if [[ $APP_STATUS -ne 0 ]] && [ ! -f "$APP_LOG_FILE"  ]; then
    curl -H "Access-Token: $PUSHBULLET_TOKEN" https://api.pushbullet.com/v2/pushes -d type=note -d title="[$(date)] Gfeud app is down!" -d body="${APP_OUTPUT}"
    journalctl -u gfeud -n 20 > "$APP_LOG_FILE"
    systemctl restart gfeud.service
elif [[ $APP_STATUS -eq 0 ]] && [ -f "$APP_LOG_FILE" ]; then
    curl -H "Access-Token: $PUSHBULLET_TOKEN" https://api.pushbullet.com/v2/pushes -d type=note -d title="[$(date)] Gfeud app is back up!"
    rm -f "$APP_LOG_FILE"
fi
