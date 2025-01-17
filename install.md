# Installation Notes
Some knowledge about package installation, web server and database configuration
will be needed.

This software was developed and tested on Linux/Debian 10 (codename "bullseye")
and the easiest way to install would be on a Debian 10 system following these
instructions. It may work on other Linux distributions or even on non Linux
systems but would need substantially more knowledge about server administration.

Feel free to also consult our own
[documentation](https://redmine.openatlas.eu/projects/uni/wiki/Debian_server_installation)
we use to set up new Debian servers for OpenAtlas installations.

## Requirements

### Python 3.9 and Flask 1.1.2

    # apt install python3 python3-bcrypt python3-dateutil python3-psycopg2 python3-fuzzywuzzy python3-flask
    # apt install python3-flask-babel python3-flask-login python3-flaskext.wtf python3-markdown python3-numpy
    # apt install python3-pandas python3-jinja2 python3-flask-cors python3-flask-restful p7zip-full
    # apt install python3-wand python3-rdflib python3-dicttoxml python3-rdflib-jsonld python3-flasgger

### Apache 2.4

    # apt install apache2 libapache2-mod-wsgi-py3

### PostgreSQL 13 and PostGIS 3

    # apt install postgresql postgresql-13-postgis-3 postgresql-13-postgis-3-scripts

### gettext, pip, npm

    # apt install gettext npm python3-pip

## Installation

### Files

Copy the files to /var/www/your_site_name or clone OpenAtlas from GitHub and
adapt accordingly e.g.

    $ git clone https://github.com/craws/OpenAtlas.git

### Frontend libraries

    $ pip3 install calmjs
    $ cd openatlas/static
    $ pip3 install -e ./
    $ ~/.local/bin/calmjs npm --install openatlas

### Database

The commands below have to be executed as postgres.

Create an openatlas database user

    $ createuser openatlas -P

Create an openatlas database, make openatlas the owner of it

    $ createdb openatlas -O openatlas

Add postgis and unaccent extension to the database

    $ psql openatlas -c "CREATE EXTENSION postgis; CREATE EXTENSION unaccent;"

Import the scripts: 1_structure.sql, 2_data_web.sql, 3_data_model.sql,
4_data_node.sql

    $ cd install
    $ cat 1_structure.sql 2_data_model.sql 3_data_web.sql 4_data_type.sql | psql -d openatlas -f -

A user with username "OpenAtlas" is created with the password:
**change_me_PLEASE!**

**Important**: change this account immediately. A warning will be displayed for
admins until this account is changed.

### Configuration

Copy instance/example_production.py to instance/production.py

    $ cp instance/example_production.py instance/production.py

Add/change values as appropriate. See config.py which settings are available.

### Apache

As root copy and adapt install/example_apache.conf for a new vhost, activate
the site:

    # a2ensite your_sitename

Test Apache configuration and restart

    # apache2ctl configtest
    # service apache2 restart

### File Upload and Export

Make these directories writable for the Apache user:

    openatlas/uploads
    openatlas/export/csv
    openatlas/export/sql
    openatlas/processed_images/resized

e.g.

    # chown www-data openatlas/uploads
    # chown www-data openatlas/export/*
    # chown www-data openatlas/processed_images/resized

### Finishing

Login with username "OpenAtlas" and password "change_me_PLEASE!" and change the
password in profile. You may want to check the admin area to set up default site
settings, email and similar.

### Upgrade

If you later like to upgrade the application be sure to read and follow the
[upgrade instructions](install/upgrade/upgrade.md).

### Additional security (optional)

You don't need this to run the application, but it will improve server side
security if running an online productive instance.

Use certbot to create a https vhost.

After Apache is configured to use HTTPS only, add this line to
instance/production.py:

    SESSION_COOKIE_SECURE = True

### Tests (optional)

Install required packages:

    # apt install python3-coverage python3-nose

As postgres:

    $ createdb openatlas_test -O openatlas
    $ psql openatlas_test -c "CREATE EXTENSION postgis; CREATE EXTENSION unaccent;"

Copy instance/example_testing.py to instance/testing.py and adapt as needed:

    $ cp instance/example_testing.py instance/testing.py
