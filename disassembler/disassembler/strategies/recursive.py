'''
A recursive disassembler.
Loosely based on the strategy defined in:
http://techbus.safaribooksonline.com/book/software-engineering-and-development/software-testing/9781593273750/1dot-introduction-to-disassembly/the_how_of_disassembly?bookview=search&query=recursive
'''

import capstone
from strategy import Strategy
from disassembler_libs import logger
from disassembler_libs.dbmanager import generate_db_manager
from bson.binary import Binary
from strategy import MyCsInsn
import multiprocessing
import traceback
from ctypes import c_uint32


class SharedBitArray(object):
    def __init__(self, size, m_man=None):
        # create an auto-locking array of unsigned bytes
        self.bitlength = size
        if size % 8 > 0:
            size += 7
        if m_man is None:
            self.array = multiprocessing.Array('B', int(size/8))
        else:
            self.array = m_man.Array('B', [0]*int(size/8))

    def setbit(self, pos, value):
        byte_pos = pos/8
        bit_pos = 7-(pos % 8)
        cur_val = self.array[byte_pos]
        if value:
            # set bit:   number |= 1 << x
            cur_val = cur_val | (1 << bit_pos)
        else:
            # clear bit: number &= ~(1 << x)
            cur_val = cur_val & ~(1 << bit_pos)
        self.array[byte_pos] = cur_val

    def getbit(self, pos):
        byte_pos = pos/8
        bit_pos = 7 - (pos % 8)
        cur_val = self.array[byte_pos]
        return (cur_val >> bit_pos) & 1

    def __str__(self):
        arr = self.array
        return ''.join(['SharedBitArray('] +
                       [bin(x).replace('0b', '').zfill(8) for x in arr] +
                       [')'])

    def __getitem__(self, key):
        if isinstance(key, slice):
            indices = key.indices(self.bitlength)
            return [self.getbit(x) for x in xrange(*indices)]
        else:
            return self.getbit(key)

    def __setitem__(self, key, value):
        if isinstance(key, slice):
            indices = key.indices(self.bitlength)
            for x in xrange(*indices):
                self.setbit(x, 1 if value else 0)
        else:
            self.setbit(key, 1 if value else 0)

    def __len__(self):
        return self.bitlength


def dis_ex_sec(strat, config, proj_name, dis_name,
               todo_queue, miss_counter, max_misses):
    try:
        strat.recurse(config, proj_name, dis_name,
                      todo_queue, miss_counter, max_misses)
    except Exception as e:
        traceback.print_exc()
        raise e


class Recursive(Strategy):

    def dis_executable_sections(self, sections):
        db_man = generate_db_manager(self.config,
                                     self.proj_name,
                                     self.dis_name)

        log = logger.getLogger(__name__, self.config)
        m_man = multiprocessing.Manager()

        log.info('Recursively disassembling executable sections.')

        self.md = capstone.Cs(self.arch, self.mode)
        self.md.detail = True
        # md.skipdata_setup = ('db', None, None)
        self.md.skipdata = True

        # create a bitmap of visited addresses per section
        self.bitmaps = dict()

        for s in sections:
            self.bitmaps[s.name] = SharedBitArray(s.size, m_man)
            self.bitmaps[s.name][:] = False

        # Keep a counter that is shared among processes.
        # If processes fail to find something to work on
        # in the queue long enough then they will kill themselves.
        # TODO: Find something better than this
        miss_counter = m_man.Value(c_uint32, 0)

        todo_queue = m_man.Queue()
        # todo_queue = multiprocessing.Queue()
        for x in self.entry_points:
            todo_queue.put(x)

        enable_multi = not self.config.getboolean('Debugging',
                                                  'disable_multiprocessing')
        miss_multiplier = 3

        if enable_multi:
            max_procs = self.config.getint('General',
                                           'num_procs')

            # TODO: Arbitrary metric, fix
            max_misses = max_procs*miss_multiplier

            procs = []
            for x in range(max_procs):
                p = multiprocessing.Process(target=dis_ex_sec,
                                            args=(self,
                                                  self.config,
                                                  self.proj_name,
                                                  self.dis_name,
                                                  todo_queue,
                                                  miss_counter,
                                                  max_misses))
                procs.append(p)
                p.start()

            for x in procs:
                x.join()
                x.terminate()
        else:
            self.recurse(self.config,
                         self.proj_name,
                         self.dis_name,
                         todo_queue,
                         miss_counter,
                         1*miss_multiplier)

        # and go through the bitmap, adding everything else as data
        inst_buff = []
        for sec in sections:
            s = self.bitmaps[sec.name]
            for index, byte in enumerate(sec.data):
                if not s[index]:
                    # MyCsInsn = namedtuple('MyCsInsn',
                                            # 'address bytes mnemonic')
                    tuple_inst = MyCsInsn(sec.base_addr + index,
                                          Binary(str(byte)),
                                          '.byte')
                    instruction = self.get_instruction(tuple_inst)
                    inst_buff.append(instruction)
            if len(inst_buff) > 0:
                db_man.batch_add_instructions(sec.name, inst_buff)
                inst_buff = []

        log.info('Finished recursively disassembling executable sections.')

    def get_section_by_addr(self, addr):
        for x in self.sections:
            if x.contains_addr(addr):
                return x
        return None

    def get_exec_section_by_addr(self, addr):
        for x in (s for s in self.sections if s.is_executable()):
            if x.contains_addr(addr):
                return x
        return None

    def flush_rec_inst_buff(self, rec_inst_buff, db_man):
        """Flush the Recursive instruction buffer to the database
        :rec_inst_buff: A tuple of section_name inst
        :db_man: The database manager to use

        """
        # Look at the first instruction and filter out
        #  all belonging to that sec. Rinse, repeat.
        # import ipdb; ipdb.set_trace()
        while len(rec_inst_buff) > 0:
            first_name = rec_inst_buff[0][0]
            filt = [x[1] for x in rec_inst_buff
                    if x[0] == first_name]
            db_man.batch_add_instructions(first_name, filt)
            rec_inst_buff = [x for x in rec_inst_buff
                             if x[0] != first_name]

    def recurse(self, config, proj_name, dis_name,
                todo_queue, miss_counter, max_misses):
        """Recursive disassembly


        """
        log = logger.getLogger(__name__, config)
        # rec_inst_buff is a list of 2-length tuple
        # containing (section_name, inst)
        rec_inst_buff = []

        # how many items to insert into the db
        # at a time
        batch_limit = 300

        # shared_counter = self.shared_counter
        bitarray = self.bitmaps

        db_man = generate_db_manager(config,
                                     proj_name,
                                     dis_name)

        while True:
            log.debug('Starting Loop')
            # get the first addr from the queue
            abs_addr = 0
            try:
                abs_addr = todo_queue.get(True, 1)
                miss_counter.value = 0
            except:
                self.flush_rec_inst_buff(rec_inst_buff, db_man)
                miss_counter.value += 1
                log.debug('miss counter: %d' % miss_counter.value)
                if miss_counter.value > max_misses:
                    return
                continue

            # get the section associated with that address
            sec = self.get_section_by_addr(abs_addr)

            if sec is None:
                # we couldn't find the section with the address
                log.debug('Did not find section for addr while disassembling!')
                import ipdb
                ipdb.set_trace()
                continue

            if not sec.is_executable():
                # TODO: data section; don't care. But how did we get here?
                # maybe malware mmaps this section?
                # or rel jump interpreted wrong?
                log.debug('Found non-executable section while disassembling!')
                import ipdb
                ipdb.set_trace()
                continue

            # Disassemble things
            rel_addr = abs_addr - sec.base_addr
            dis_gen = self.md.disasm(sec.data[rel_addr:], rel_addr)

            for inst in dis_gen:
                # Verify we haven't been here
                if bitarray[sec.name][inst.address]:
                    log.debug('Already visited: %s' % hex(abs_addr))
                    break

                bitarray[sec.name][inst.address:inst.address
                                   + len(inst.bytes)] = True

                instruction = self.get_instruction(inst)  # Parent class method
                rec_inst_buff.append([sec.name, instruction])

                log.debug(''.join([
                          hex(abs_addr), '/', hex(instruction.r_addr),
                          '(', str(inst.address),
                          '/', str(len(rec_inst_buff)), '/',
                          # str(todo_queue.qsize()),')',
                          instruction.mnemonic, ' ',
                          ';'.join(str(x['op_str']) for x in
                                   instruction.operands),
                          ')']))

                # TODO: check for xrefs to .text section
                if self.heuristics.is_conditional_jump(inst):
                    target = self.heuristics.op_conditional_jump_option(inst)

                    if target is not None:
                        import ipdb; ipdb.set_trace()

                        # Test to see if this is a relative jump
                        # TODO: Fix this to not just check exec.
                        test_sec = self.get_exec_section_by_addr(target)
                        if test_sec is None:
                            target = sec.base_addr + target
                            log.debug('Relative jump target: %x' % target)
                        # print 'jX to '+str(target)
                        todo_queue.put(target)

                    # don't break,
                    # continue after the conditional for the other option

                elif self.heuristics.is_call(inst):
                    import ipdb; ipdb.set_trace()
                    target = self.heuristics.op_call_get_addr(inst)

                    if target is not None:
                        # print 'call to '+hex(target)

                        # Test to see if this is a relative jump
                        # TODO: Fix this to not just check exec.
                        test_sec = self.get_exec_section_by_addr(target)
                        if test_sec is None:
                            target = sec.base_addr + target
                            log.debug('Relative call target: %x' % target)

                        todo_queue.put(target)
                        # TODO: should we break? or should we continue
                        #   after the call?
                        # break
                    break

                    # else:
                    #   # This was probably a 'call eax' type of setup,
                    #   # it is highly likely that we should continue
                    #   #   the linear sweep.
                    #   pass

                elif self.heuristics.is_jump(inst):
                    import ipdb; ipdb.set_trace(False)
                    target = self.heuristics.op_jump_get_addr(inst)

                    if target is not None:
                        # print 'jmp to '+hex(target)

                        # Test to see if this is a relative jump
                        # TODO: Fix this to not just check exec.
                        test_sec = self.get_exec_section_by_addr(target)
                        if test_sec is None:
                            target = sec.base_addr + target
                            log.debug('Relative jump target: %x' % target)

                        todo_queue.put(target)

                    # we can't continue in a linear fashion
                    break

                elif self.heuristics.is_ret(inst):
                    break

                abs_addr += len(inst.bytes)

            # Batch instruction insertion greatly speeds up query time
            # we're using a buffer that gets flushed every n insts
            l = len(rec_inst_buff)
            if l != 0 and l > batch_limit:
                log.debug('Inserting %i instructions into DB', l)
                self.flush_rec_inst_buff(rec_inst_buff, db_man)
                rec_inst_buff = []

        return

    # See parent for _disassemble_non_executable_section
