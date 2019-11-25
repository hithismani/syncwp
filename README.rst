======
SyncWP
======


.. image:: https://img.shields.io/pypi/v/syncwp.svg
        :target: https://pypi.python.org/pypi/syncwp

A quick script that helps migrate sites hosted with the help of EasyEngine, into your local Lando work environment. This work in progress script has already gotten the time I need to migrate a few sites from 20-60 minutes down to about 3-5 minutes. Goodbye you pesky backup plugins!

THIS SCRIPT IS STILL IN DEVELOPMENT.

Installation Steps:
-------------------

- run `pip install git+https://github.com/hithismani/syncwp`

Requirements & Use Case
-----------------------
- http://EasyEngine.io on your wordpress server.
- https://lando.dev/ (and Docker) on your local wordpress machine.

Usage:
------
- Cd into your Lando Wordpress Folder
- If you're pulling from a live server:
        * Run `syncwp -domain <host url as in database> -local <local server url> -host <host ip to ssh> -user <ssh username> -password <ssh password> -dev S -server <commands>` 
- If you're pushing from a local machine:
        * Run `syncwp -domain <host url as in database> -local <local server url> -host <host ip to ssh> -user <ssh username> -password <ssh password> -dev <commands> -server S` 

Features
--------

- Exports Database (into SQL) and Wp-Content (as .tar.gz) file, for migration with a single command. Optionally deletes the backup file after download.
- Runs a 'find replace' in the database during the time of migration to ensure links are not broken.
- SSH's into the server and performs all migration tasks as specified.

Commands
--------

+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| Command | Description                                                                                                                                                                    | Required? | Example            | Value To Enter To Skip               |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -domain | Remote Domain Name without http/https prefix. Helps in replacing URL in database.                                                                                              | Yes       | example.com        |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -local  | Local Dev Server Domain Name (Usually .lando.site suffix in Lando Installations) without http/https prefix. Helps in replacing URL in database.                                | Yes       | example.lando.site |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -host   | Host IP Address. To SSH.                                                                                                                                                       | Yes       | 198.111.111.11     |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -user   | Host Username.                                                                                                                                                                 | Yes       | root               |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -pass   | Host Password. Optional. You can skip if this argument if you want the more secure (getpass) implementation that would request password separately, if this argument is empty. | No        | pass               | <don't enter -pass in your terminal> |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -dev    | Tasks to run from Dev Environment. Tasks Are:                                                                                                                                  | Yes       | BdwUR              | S                                    |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (B)ackup: Let's the script know that backup tasks are to be started.                                                                                                           |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | -(d)atabase: Let's the backup task know that database is to be backed up.                                                                                                      |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | -(w)p_content: Let's the backup task know that wp-content is to be backed up.                                                                                                  |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (U)pload: Let's the script know that backed up files are to be uploaded and Migrated.                                                                                          |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (S)kip All Tasks.                                                                                                                                                              |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (R)emove: Remove backup files from the server.                                                                                                                                 |           |                    |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+
| -server | Tasks to run from Server/Production Environment. Tasks Are:                                                                                                                    | Yes       | BdwDREM            | S                                    |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (B)ackup: Let's the script know that backup tasks are to be started.                                                                                                           |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | -(d)atabase: Let's the backup task know that database is to be backed up.                                                                                                      |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | -(w)p_content: Let's the backup task know that wp-content is to be backed up.                                                                                                  |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (D)ownload: Let's the script know that backed up files are to be downloaded from the server.                                                                                   |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (E)xtract: Let's the script know that downloaded backups need to be extracted into your wp-content folder. (.tar extraction)                                                   |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (R)emove: Remove backup files from the server.                                                                                                                                 |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (M)igrate Into Local: Replaces all links in the database with specified -local link, imports it into the website database.                                                     |           |                    |                                      |
|         +--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+           |                    |                                      |
|         | (S)kip All Tasks.                                                                                                                                                              |           |                    |                                      |
+---------+--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------+-----------+--------------------+--------------------------------------+

TODO

* Remove Requirement Of Lando + Easy Engine, move commands into TXT File for easy adaptability.
* Production Tests. 

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage
