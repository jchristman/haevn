#!/usr/bin/env python

import sys
sys.path.append('../disassembler/')
from disassembler_libs.dbmanager import DBManager


def clear_db(host=None, port=None):
    if not port is None:
        port = int(port)
    db_man = DBManager(host, port)
    db_man.drop_haevn_db()

if __name__ == '__main__':
    if len(sys.argv) == 3:
        clear_db(*sys.argv[1:])
    else:
        clear_db()
