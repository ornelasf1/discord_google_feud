#!/bin/bash

crontab -l > cronfile

cat << EOL > cronfile
PATH=$HOME/.local/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin:/usr/games:/usr/local/games:/snap/bin
*/1 * * * * /bin/bash -x $HOME/scripts/notify_if_down.sh > $HOME/cron.log 2>&1
0 6 * * * $HOME/discord_google_feud/scripts/reset_contributions.sh
EOL

crontab cronfile
rm -rf cronfile
