#!/bin/bash

function help_message {
cat << EOT
Usage: $0 [-h|--help] PARAMETERS

 -n, --name=NAME               Query rocks vm name by user name
 -r, --rocks=ROCKS_NAME        Query user name by rocks name
 -u, --unsetpass=USERNAME      Unset user's password

EOT
}

NAME=
ROCKS=
UNSETPASSUSER=

while true; do
  case "$1" in
    -n|--name ) NAME="$2"; shift 2;;
    -r|--rocks ) ROCKS="$2"; shift 2;;
    -u|--unsetpass ) UNSETPASSUSER="$2"; shift 2;;
    -h|--help ) help_message; exit 0; shift ;;
    -- ) shift; break ;;
    * ) break ;;
  esac
done

if [ -z "$NAME" ] && [ -z "$ROCKS" ] && [ -z "$UNSETPASSUSER" ]; then echo "specify either rocks name or user name"; help_message; exit 1; fi

if [ -n "$NAME" ]; then
    echo
    echo "select rocks_name as vm_rocks_name from api_compute where name = \"$NAME\" " | mysql --defaults-extra-file=/opt/rocks/etc/.nucleus.my.cnf
    echo
    echo "select api_computeset.\`name\`, api_computeset.\`state\`, api_computeset.\`jobid\` from api_computeset
          JOIN api_computeset_computes ON api_computeset_computes.\`computeset_id\` = api_computeset.\`id\`
          JOIN api_compute ON api_compute.\`id\` = api_computeset_computes.\`compute_id\`
          WHERE api_compute.\`name\` = \"$NAME\" ORDER BY api_computeset.\`state\`, api_computeset.\`id\`;" | mysql --defaults-extra-file=/opt/rocks/etc/.nucleus.my.cnf
fi

if [ -n "$ROCKS" ]; then
    echo
    echo "select name as vm_user_name from api_compute where rocks_name = \"$ROCKS\" " | mysql --defaults-extra-file=/opt/rocks/etc/.nucleus.my.cnf
    echo
    echo "select api_computeset.\`name\`, api_computeset.\`state\`, api_computeset.\`jobid\` from api_computeset
          JOIN api_computeset_computes ON api_computeset_computes.\`computeset_id\` = api_computeset.\`id\`
          JOIN api_compute ON api_compute.\`id\` = api_computeset_computes.\`compute_id\`
          WHERE api_compute.\`rocks_name\` = \"$ROCKS\" ORDER BY api_computeset.\`state\`, api_computeset.\`id\`;" | mysql --defaults-extra-file=/opt/rocks/etc/.nucleus.my.cnf
fi

if [ -n "$UNSETPASSUSER" ]; then
   echo "from django.contrib.auth.models import User; user = User.objects.get(username='$UNSETPASSUSER'); user.set_unusable_password(); user.save()" | python /opt/python/lib/python2.7/site-packages/nucleus/nucleus_service/manage.py shell
fi