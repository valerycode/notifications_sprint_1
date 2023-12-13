#!/bin/bash
celery -A config worker -B --loglevel=DEBUG