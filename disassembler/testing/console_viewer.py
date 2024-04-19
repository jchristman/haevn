#!/usr/bin/env python

import sys
sys.path.append('../disassembler/')
from disassembler_libs.dbmanager import DBManager

cs_arch = {0: 'ARM',
           1: 'ARM64',
           2: 'MIPS',
           3: 'X86',
           4: 'PPC',
           5: 'ERROR1',
           0xffff: 'ERROR2'
           }

cs_mode = {0: 'LITTLE ENDIAN',
           # 0:      'ARM',
           1 << 1: '16',
           1 << 2: '32',
           1 << 3: '64',
           1 << 4: 'THUMB',
           1 << 4: 'MICRO',
           1 << 5: 'N64',
           1 << 31: 'BIG ENDIAN'
           }


def get_op_str(op):
    """Returns the string representation of the given operand.

    :operand: The operand to be rendered
    :returns: A string representing that operand

    """
    if op['type'] == 'fp':
        disp = op['fp']['disp']
        if disp == 'dec':
            return '%d' % op['fp']['val']
        elif disp == 'hex':
            return '0x%x' % op['fp']['val']
        else:
            raise TypeError
    elif op['type'] == 'imm':
        disp = op['imm']['disp']
        if disp == 'dec':
            return '%d' % op['imm']['val']
        if disp == 'hex':
            return '0x%x' % op['imm']['val']
        else:
            raise TypeError
    elif op['type'] == 'inv':
        return 'I_DONT_KNOW_WHAT_TO_RENDER_FOR_"INV"_TYPE'
    elif op['type'] == 'mem':
        text = ''
        if 'size' in op:
            text += op['size']
        else:
            text += 'dword'
        text += ' ptr '
        text += '[' + str(op['base'])

        # Either indexed (uses a register as index) or relative (uses imm)
        indexed = op['index'] != 0
        if indexed:
            text += ' + ' + op['index'] + '*'
            disp = op['scale']['disp']
            val = op['scale']['val']
            if disp == 'dec':
                text += '%d' % val
            elif disp == 'hex':
                text += '0x%x' % val
            else:
                raise TypeError
        else:
            disp = op['rel']['disp']
            val = op['rel']['val']
            if val != 0:
                if disp == 'dec':
                    text += ' + %d' % op['rel']['val']
                elif disp == 'hex':
                    text += ' + 0x%x' % op['rel']['val']
                else:
                    raise TypeError
        text += ']'
        return text
    elif op['type'] == 'reg':
        return op['reg']
    raise TypeError


def main(host, port, proj=None, disassembly=None, section=None):
    port = int(port)
    db_man = DBManager(host, port)

    # Test for project name
    if not proj:
        print("Projects:")
        for project in db_man.get_project_records():
            print("%s" % (project['project_name']))
        sys.exit(0)

    if not db_man.project_exists(proj):
        print("Project '%s' doesn't exist!" % (proj))
        sys.exit(1)

    db_man.load_project(proj)

    # Then disassembly name
    if not disassembly:
        for each in db_man.get_disassembly_records():
            print each['dis_name']
        sys.exit(0)

    db_man.load_disassembly(disassembly)
    dis_record = db_man.get_disassembly_record_current()

    print("Disassembly of %s:" % (db_man.get_bin_name()))
    print("\tMD5: %s" % (db_man.get_md5()))
    print("\tArch: %s" % (cs_arch[db_man.get_arch()]))
    print("\tMode: %s" % (cs_mode[db_man.get_mode()]))
    print("\tSize: %s bytes (%.4f MB)" % (db_man.get_bin_size(),
          int(db_man.get_bin_size())/1024.000/1024.000))
    print("\tEntry point: 0x%08x" % (dis_record['entry_point']))
    print("")


    # Then section name
    print("Sections:")
    for sec in db_man.get_sections():
        print("0x%08x-0x%08x\t[% 4s]\t%s" % (sec.base_addr,
              (sec.base_addr+sec.size), sec.attribs, sec.name))

    """
    A. type=func
       type            : func|str|sec
       r_start_addr    : int                //Relative start address
       r_end_addr      : int                //Relative end address
       sec_id          : int
       name            : str
       vars            : [name : str]
    """
    # create the function dicts (so we have nice O(1) lookup time)
    funcs = db_man.get_functions()
    funcs_s = {}
    funcs_e = {}
    for func in funcs:
        funcs_s[func.r_start_addr] = func
        funcs_e[func.r_end_addr] = func

    # show disassembly
    """
    disassembler -
    A. is_text=true
    project_id       : bson_objectid  //Foreign key (project_information)
    dis_id           : bson_objectid  //Foreign key (disassemblies)
    r_addr           : int            //Relative address
    is_text          : bool
    my_bytes         : byte_str
    sec_id           : bson_objectid  //Foreign key (labels)
    mnemonic         : str
    operands         : [{ operand : str
                          type    : mem|reg|imm|loc|var
                          (if imm, also have - disp : hex|dec|oct|bin|str)
                        }]
    B. is_text=false
    project_id       : bson_objectid  //Foreign key (project_information)
    dis_id           : bson_objectid  //Foreign key (disassemblies)
    r_addr           : int            //Relative address
    is_text          : bool
    my_bytes         : byte_str
    disp             : bytes|str
    sec_id           : bson_objectid  //Foreign key (labels)
    mnemonic         : str
    """

    for section in db_man.get_exec_sections():
        for dis in db_man.get_disassembler_records(section.name):
            text = ""
            if dis.is_text:

                # see if this addr is the start of a function
                if dis.r_addr in funcs_s:
                    func = funcs_s[dis.r_addr]
                    text += "function "+func.name
                    for each in func.vars:
                        text += '\t'+repr(each)

                conts = '{0: <20}'.format(dis.my_bytes.encode('hex'))
                text += '% 8s:0x%08x: %s\t%s\t' % (
                                              section.name,
                                              dis.r_addr,
                                              conts,
                                              dis.mnemonic
                                              )

                text += ', '.join((get_op_str(x) for x in dis.operands))

                # see if this addr is the end of a function
                if dis.r_addr in funcs_e:
                    text += "end of "+funcs_s[dis.r_addr].name
                    text += '\n'

            else:
                text += '% 8s:0x%08x: %s\t0x%s\t' % (section.name,
                                                   dis.r_addr,
                                                   dis.mnemonic,
                                                   dis.my_bytes.encode('hex'))



                #text = '.byte 0x%02x' % ord(dis.my_bytes[0])
            print(text)

if __name__ == '__main__':
    if len(sys.argv) > 5 or len(sys.argv) < 3:
        print("Usage: %s host port project_name disassembly"
              % (sys.argv[0]))
        print(("If any of the arguments are left out, it will print "
               "the available options for that field."))
        sys.exit(1)
    else:
        main(*sys.argv[1:])
