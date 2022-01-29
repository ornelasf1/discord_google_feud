#!/bin/bash

crontab -l > cronfile

cat << EOL >> cronfile
PATH=/home/gfeudadmin/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
*/1 * * * * /bin/bash -x /home/gfeudadmin/scripts/notify_if_down.sh > /home/gfeudadmin/cron.log 2>&1
0 6 * * * /home/gfeudadmin/discord_google_feud/scripts/reset_contributions.sh
EOL

crontab cronfile
rm -rf cronfile