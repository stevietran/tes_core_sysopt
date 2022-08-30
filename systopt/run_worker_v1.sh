#!/bin/sh
celery --app worker_v1.celery worker -n opt_pls -Q opt_pls