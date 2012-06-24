#!/bin/sh
echo 'recreating django db, wiping aliases, and wiping mailman'
. ./drop_recreate.sh
. ./wipe_aliases.sh
. ./wipe_mailman.sh
