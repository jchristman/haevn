#!/usr/bin/env python
''' This does some basic configuration and then runs the disassembler
in the desired mode as indicated by the arguments it receives.

Usage:
./disassembler_cli.py [-p project_name] [-d disassembly_name]
                      [[-f file_name] | [-s id1 {id2 id3 ...}]]
    -p : the name of the project that the disassembly belongs to
    -d : the name of the disassembly itself (this may be different
         from the name of the binary)
    -f : the name of the file to disassemble
         NOTE: This should be used for any new disassemblies. It
               will create a new disassembly in the database and do
               all default parsing (such as string finding and function
               identification).
    -s : a sequence of database _id fields that should be converted
         from their current format into a disassembled format. This
         should be used for data => text conversions in the disassembly.
         NOTE: This should only be used for existing disassemblies.
         TODO: Decide how this will actually work. Do we want _id args?
               Should we have another flag for 'continue to do disassemble
               from a given point and follow things recursively'?
               Big gray area here that we need to deal with eventually.
Example:
    *   This will create a new disassembly, test_dis, for the project
        test_project. If test_project doesn't exist, then it will be created.
        It will then parse and disassemble elf-Linux-x86:
           ./disassembler_cli.py -p test_project -d test_dis -f ./elf-Linux-x86
    *   This will take an existing disassembly and convert the contents
        of the given database _id's to their equivalent disassemblies.
           ./disassembler_cli.py -p test_project -d test_dis -s 54847e4a1d41c8a51391e58c 54847e4a1d41c8a51391e58f
'''

import sys
import argparse
import ConfigParser
from cProfile import Profile
from pstats import Stats
import disassembler
from disassembler_libs import logger


def parse_args():
    """TODO: Docstring for parse_args"""
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--project_name', dest='project_name',
                        required=True, help='the name of the project')
    parser.add_argument('-d', '--disassembly_name', dest='disassembly_name',
                        required=True, help='the name of the disassembly')

    group = parser.add_mutually_exclusive_group()
    group.add_argument('-f', '--file', dest='filename',
                       help='disassemble a file')
    group.add_argument('-s', '--string', dest='string_val', nargs='+',
                       help=('convert data->text for an existing project.'
                             'requires list of record _id\'s as args'))

    return parser.parse_args()


def run(config, args):
    host = config.get('Database', 'host')
    port = config.getint('Database', 'port')
    log = logger.getLogger(__name__, config)

    log.debug('Building disassembler object')
    dis = disassembler.Disassembler(host,
                                    port,
                                    config,
                                    args.project_name,
                                    args.disassembly_name,
                                    binpath=args.filename)
    if args.filename is not None:
        log.info('Starting to disassemble file')
        dis.disassemble_file()
        log.info('Done disassembling file')

    elif args.string_val is not None:
        dis.start_disassemble_string(host, port, args.string_val)

    else:
        log.error('Command line error')
        sys.exit(-1)


def get_started():
    """TODO: Docstring for get_started."""
    config = ConfigParser.SafeConfigParser()
    config.read('haevn.conf')

    profiler_on = config.getboolean('Debugging', 'profiler_on')

    if profiler_on:
        profile = Profile()
        profile.enable()

    args = parse_args()

    try:
        run(config, args)
    finally:
        if profiler_on:
            profile.disable()
            stats = Stats(profile)
            with open('profile.stats', 'wb') as statsfile:
                stats.stream = statsfile
                stats.sort_stats('cumulative').print_stats()

if __name__ == '__main__':
    get_started()
