#!/bin/bash

commitName=$(git log | grep -E '^commit [0-9a-f]+' | cut -d ' ' -f 2 | head -n 1)

docker build -t kennethstebbins/radiorec:$commitName .
docker tag kennethstebbins/radiorec:$commitName kennethstebbins/radiorec:latest

docker push kennethstebbins/radiorec:$commitName
docker push kennethstebbins/radiorec:latest