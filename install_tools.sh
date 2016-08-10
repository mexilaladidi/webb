#!/bin/sh
sudo apt-get update
sudo apt-get -y install python3-pip
sudo apt-get -y install apache2
sudo apt-get -y install apache2-mpm-worker
sudo apt-get -y install apache2-threaded-dev
pip3 install django==1.9.2
pip3 install mod_wsgi
pip3 install PyMySQL
sudo apt-get -y install git
git config --global user.email 'mexilaladidi@outlook.com'
git config --global user.name 'mexilaldidi'
sudo apt-get -y install mysql-client mysql-server
DBNAME="polls_1"
mysql -uroot -p'cupid1212123' -e"CREATE DATABASE ${DBNAME} DEFAULT CHARACTER SET utf8 COLLATE utf8_general_ci;"
cd /var/www
git clone https://github.com/mexilaladidi/webb.git
cd webb
python3 manage.py migrate
python3 manage.py loaddata ./data/newest.json
rm staticfiles -r
python3 manage.py collectstatic
service apache2 stop
python3 manage.py runmodwsgi --setup-only --port=80 --user www-data --group www-data --reload-on-changes  --server-root=/etc/mod_wsgi-express-80
/etc/mod_wsgi-express-80/apachectl start
#ssh-keygen -t rsa -b 4096 -C "mexilaladidi@outlook.com"
python3 manage.py createsuperuser
