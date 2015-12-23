#!/bin/bash

set -x
set -e

prospector -P .prospector.yml -u django
tox

# If coveralls token is present, submit coverage data to coveralls
if [ -n "$COVERALLS_REPO_TOKEN" ]; then
    coveralls
fi
