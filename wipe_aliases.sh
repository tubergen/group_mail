#!/bin/sh
echo 'deleting aliases table from maildb'
echo 'use maildb; delete from aliases;' | mysql -u root -p 
echo 'delete completed'
