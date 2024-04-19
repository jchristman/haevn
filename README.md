Haevn
=====

Haevn is a haven for hacking, designed to help HAck EVerythiNg.

This program is currently in alpha and in heavy development mode (on our free time), so expect unstable behaviors as we develop. We currently have a "stable" master (that is slightly useable) and all current work will be done on the "unstable" branch. If you want to checkout that branch, it will have more current developments included, but it might not work as well as we rework data structures, add new functionality, test new features, etc. 

Dependencies
============
```
apt-get install capstone
pip install pymongo
pip install capstone
```

Architecture
============
```
Meteor
    - Modifies disassembly in MongoDB
    - Launches disassembler_cli.py to do disassembly
disassembler_cli.py
    - Does disassembly 
    - Modifies disassembly in MongoDB
```

Directory Hierarchy
===================
```
haevn/
    disassembler/
        disassembler_cli.py
        disassembler.py
            - determines format 
            - parses using pyelftools/etc
            - feeds bytes to strategy
            - applies debug info/strings/labels
            - adds everything to db
        parsers/
            stringfinder.py
            funcfinder.py
            <more plugins here for vuln finders/etc>
        strategies/
            linear.py - capstone magic here via generator?
            recursive.py - capstone magic here via generator?
            heuristics/
                i386.py
                x86_64.py
                arm.py
                mips.py
                ... 
    haevn.js
    haevn.css
    haevn.html
    server/ ?
    client/ ?
    tests/ ?
    public/
    docs/
```
