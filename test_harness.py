#!/usr/bin/env python3
"a harness for testing"

import json

import lambda_function

def main():
    "do the work"
    with open("test.json") as jsonfile:
        obj = json.load(jsonfile)
    lambda_function.lambda_handler(obj, None)


if __name__ == "__main__":
    main()
