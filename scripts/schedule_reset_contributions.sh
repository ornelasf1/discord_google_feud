#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

#write out current crontab
crontab -l > mycron
#echo new cron into cron file
echo "0 6 * * * ./$SCRIPT_DIR/reset_contributions.sh" >> mycron
#install new cron file
sudo crontab mycron
rm mycron