#!/bin/bash

set -e

zip lambdafunction.zip lambda_function.py

aws lambda update-function-code --function-name batch_instance_tagger --zip-file fileb://lambdafunction.zip
