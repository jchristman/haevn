#!/bin/bash

# This script will do everything needed to reload mongo to a clean, after-disassembly
# state - which is useful for testing just parsers
#
# Usage Instructions:
# 1. Use haevn to do a full disassembly of whatever you're using as a test case. 
#    This should populate the database the records you need.
# 2. Run mongodump to dump a backup of the db
# 3. Find the 3 'PARSER TESTING' comments in disassembler.py and do whatever they say to
#    skip the disassembly step and go straight to running the parsers - we'll eventually
#    make this a startup option for disassembly_cli.py, but for now, go with it.
# 4. Run this from the testing/ directory - just so it knows where to find ./clear_haevn_db.py
#
./clear_haevn_db.py
mongorestore ./dump
python -m cProfile -o profile.log ../disassembler/disassembler_cli.py -f tmp.txt
