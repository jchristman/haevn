'''
A linear disassembler.
Given a list of sections, it will attempt to disassemble them.
If a disassembly is not possible, it will declare the current byte
as data and continue.
'''

import capstone
from strategy import Strategy
from disassembler_libs import logger
from disassembler_libs.dbmanager import generate_db_manager
import multiprocessing


def dis_ex_sec(strat, config, proj_name, dis_name, sec):
    """Disassemble an executable section.

    :strat: An initialization of the strategy to use
    :config: A configuration file to read
    :proj_name: The name of the project
    :dis_name: The name of the disassembly
    :sec: The section to disassemble
    :returns: None

    """
    db_man = generate_db_manager(config, proj_name, dis_name)
    strat.disassemble_executable_section(db_man, sec)


class Linear(Strategy):
    """A linear-sweep disassembly strategy. """

    def disassemble_executable_section(self, db_man, sec):
        """Disassemble an executable section.

        :db_man: The database manager to use
        :sec: The section to disassemble
        :returns: None

        """
        log = logger.getLogger(__name__, self.config)
        log.info(('Disassembling executable section: '
                  '%s -- Length: %d' % (sec.name, sec.size)))
        md = capstone.Cs(self.arch, self.mode)
        md.detail = True
        # Doesn't work for now
        # md.skipdata_setup = ('db', None, None)
        md.skipdata = True

        addr_counter = 0x0000
        dis_gen = md.disasm(sec.data, addr_counter)

        # Batch instruction insertion greatly speeds up our query time
        # we're using a buffer that gets flushed to the db every n insts
        inst_buff = []
        count = 0
        n = 200
        while True:
            inst = None
            try:
                # if detail mode is on and the instruction isn't
                # disassemble-able then this will throw a ValueError
                # for NULL dereferencing the .detail field.
                inst = dis_gen.next()
                addr_counter += len(inst.bytes)
                if md.detail is False:
                    md.detail = True
                    # Generator needs to be reseeded when we change detail
                    # setting - might be a bug in capstone's skipdata
                    dis_gen = md.disasm(sec.data[addr_counter:], addr_counter)
            except ValueError:
                md.detail = False
                dis_gen = md.disasm(sec.data[addr_counter:], addr_counter)
                continue
            except StopIteration:
                break

            instruction = self.get_instruction(inst)  # Parent class method
            inst_buff.append(instruction)
            count += 1
            if count % n == 0:
                db_man.batch_add_instructions(sec.name, inst_buff)
                inst_buff = []

        # Flush anything left over
        if len(inst_buff) > 0:
            db_man.batch_add_instructions(sec.name, inst_buff)

    # See parent for _disassemble_non_executable_section

    def dis_executable_sections(self, sections):
        """Disassemble a list of executable sections.

        :sections: The list of sections to disassemble
        :returns: None

        """
        disable_multi = self.config.getboolean('Debugging',
                                               'disable_multiprocessing')
        if disable_multi:
            for sec in sections:
                dis_ex_sec(self, self.config, self.proj_name,
                           self.dis_name, sec)
        else:
            p = multiprocessing.Pool(self.config.getint('General',
                                                        'num_procs'))

            # Setting self.sections is a Hack to prevent us
            # from pickling every section when
            # we do apply_async
            saved = self.sections
            for sec in sections:
                self.sections = [sec]
                p.apply_async(dis_ex_sec,
                              args=(self, self.config, self.proj_name,
                                    self.dis_name, sec))

            p.close()
            p.join()
            self.sections = saved
