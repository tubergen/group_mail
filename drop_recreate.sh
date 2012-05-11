#!/bin/sh
echo 'y\n' | mysqladmin -u root -p drop group_mail_db;
mysqladmin -u root -p create group_mail_db;
python manage.py syncdb 
echo python manage.py syncdb
python manage.py setsite
