#!/bin/bash

echo 'START REGTEST BLOCKCHAIN'
python3 -u start_regtest.py
echo 'BLOCKCHAIN IS RUNNING'
tail -f /dev/null

