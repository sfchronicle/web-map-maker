#!/bin/bash

# Run with ./deploy.sh
# Takes no arguments, replaces current prod with local version in-place

scp -i ~/.ssh/digital.pem -r . ec2-user@10.68.1.19:Projects/web-map-maker