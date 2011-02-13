#!/bin/bash

cd `dirname $0`

screen -S stockscreener python manage.py runserver 0.0.0.0:7400

