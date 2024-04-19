'''
A database manager to abstract functionality away from direct
calls to the database.

A DBManager is directly linked to a given project and disassembly
for all low-level interaction, yet also manages high-level
structure as necessary. Reference docs/db.txt for db schema.
'''

import pymongo
import functools
import sys
from bson.binary import Binary
from disassembler_libs import logger
from attributes import Attributes
from string import String
from location import Location
from section import Section
from function import Function
from instruction import Instruction

HAEVN_DB_NAME = 'meteor'


class DBManager():
    """An object that interfaces with the database so you don't have to.

    The DBManager should never return the database's representation of data
    structures and should instead only return our internal representation. For
    example, all functions dealing with Instructions will accept only our
    version of Instruction and will return our version as well.

    """

    def __init__(self, host=None, port=None):
        """Create a DBManager.

        :host: The host to connect to
        :port: The port to connect to

        """
        self.host = host
        self.port = port
        self.db = self.get_haevn_db()
        self.proj_id = None
        self.dis_id = None
        self.log = logger.getLogger(__name__)

    ##################################
    # Utilities
    ##################################

    def memoize(obj):
        """Standard memoization decorator. Operates for args and kwargs. """
        cache = obj.cache = {}

        @functools.wraps(obj)
        def memoizer(*args, **kwargs):
            key = str(args) + str(kwargs)
            if key not in cache:
                cache[key] = obj(*args, **kwargs)
            return cache[key]
        return memoizer

    ##################################
    # Initialization
    ##################################

    def get_haevn_db(self):
        """Return a client connection to whichever DB haevn is using.

        :returns: A client connection to the db.

        """
        client = self._get_client()
        return client[HAEVN_DB_NAME]

    def _get_client(self):
        """Creates a client connection to the db

        :returns: A client connection to the db.

        """
        if self.host is None:
            client = pymongo.MongoClient()
        elif self.host is not None and self.port is None:
            client = pymongo.MongoClient(self.host)
        else:
            client = pymongo.MongoClient(self.host, self.port)
        return client

    def load_project(self, project_name):
        """Prepare manager to use project by this name. Create if new.

        :project_name: Name of project to use
        :returns: None

        """
        proj_id = self._get_proj_id(project_name)
        if proj_id is None:
            proj_id = self._create_new_project(project_name)
        self._set_proj_id(proj_id)

    @memoize
    def _get_proj_id(self, proj_name):
        """Fetches the project id for the project by this name.

        :proj_name: Name of the project whose id to fetch
        :returns: Project id or None

        """
        proj_col = self.db.project_information
        res = proj_col.find_one({'project_name': proj_name})
        if res is not None:
            return res['_id']
        return None

    def _set_proj_id(self, proj_id):
        """Sets the project id for the manager to proj_id.

        :returns: None
        """
        if proj_id is not None:
            self.proj_id = proj_id
        else:
            self.log.error('Trying to set None proj_id')
            sys.exit(0)

    def load_disassembly(self, dis_name):
        """Prepare manager to use disassembly by this name.

        :dis_name: Name of the disassembly to use
        :returns: None

        """
        self._set_dis_id(self._get_dis_id(self.proj_id, dis_name))

    @memoize
    def _get_dis_id(self, proj_id, dis_name):
        """Fetches the disassembly id for the dis by this name

        Note: proj_id is included to make memoization more amenable
              to changes - loading a different project, etc.

        :proj_id: project that the disassembly belongs to
        :dis_name: Name of the disassembly whose id to fetch
        :returns: Disassembly id or None

        """
        dis_col = self.db.disassemblies

        for dis_id in self._get_project_dis_ids(proj_id):
            rec = dis_col.find_one({'_id': dis_id,
                                    'dis_name': dis_name})
            if rec is not None:
                return rec['_id']
        return None

    def _set_dis_id(self, dis_id):
        """Sets the disassembly id for the manager to dis_id.

        :returns: None

        """
        if dis_id is not None:
            self.dis_id = dis_id
        else:
            self.log.error('Trying to set None dis_id')
            sys.exit(0)

    def _get_project_dis_ids(self, proj_id):
        """Returns the disassembly_ids field of the given project record.

        :returns: The disassembly_id's field

        """
        proj_col = self.db.project_information
        rec = proj_col.find_one({'_id': proj_id})
        return rec['disassembly_ids']

    ##################################
    # Updating and Insertion
    ##################################

    def _create_new_project(self, project_name):
        """Adds a new project to the project_information collection.

        :returns: _id of the created project

        """
        proj_col = self.db.project_information
        return proj_col.insert({'project_name': project_name,
                                'disassembly_ids': []})

    def get_project_record(self, proj_id):
        """Fetches the project_information record for proj_id

        :returns: A project_information record

        """
        proj_col = self.db.project_information
        return proj_col.find_one({'_id': proj_id})

    def get_project_records(self):
        """Fetches all project_information records

        :returns: Each project_information record

        """
        for proj in self.db.project_information.find():
            yield proj

    def get_disassembly_record(self, dis_id):
        """Fetches the disassemblies record for dis_id

        :returns: A disassemblies record

        """
        dis_col = self.db.disassemblies
        return dis_col.find_one({'_id': dis_id})

    def get_disassembly_record_current(self):
        return self.get_disassembly_record(self.dis_id)

    def get_disassembly_records(self):
        """Fetches all disassemblies records

        :returns: Each disassemblies record

        """
        for dis in self.db.disassemblies.find():
            yield dis

    def project_exists(self, project_name):
        """Return true if a project by the given name exists

        :returns: True if exists, otherwise False

        """
        return self._get_proj_id(project_name) is not None

    def dissassembly_exists(self, dis_name):
        """Return true if a disassembly by the given name exists in our project

        :returns: True if exists, otherwise False

        """
        return self._get_dis_id(self.proj_id, dis_name) is not None

    @memoize
    def _get_sec_id(self, dis_id, sec_name):
        """Fetches the sec id for a section in this project/dis with name.

        Note: dis_id is included to make memoization
              more amenable to changes - loading different dis, etc.

        :dis_id: Disassembly id that the section belongs to
        :sec_name: Name of the section whose _id to fetch.
        :returns: _id of section

        """
        lab_col = self.db.labels
        return lab_col.find_one({'dis_id': dis_id, 'name': sec_name,
                                 'type': 'sec'})['_id']

    @memoize
    def _get_sec_base_addr(self, dis_id, sec_name):
        """Fetches the sec id for a section in this project/dis with name.

        Note: dis_id is included to make memoization
              more amenable to changes - loading different dis, etc.

        :dis_id: Disassembly id that the section belongs to
        :sec_name: Name of the section whose _id to fetch.
        :returns: _id of section

        """
        lab_col = self.db.labels
        return lab_col.find_one({'dis_id': dis_id, 'name': sec_name,
                                 'type': 'sec'})['base_addr']

    #
    # Instruction
    #

    def _process_operands(self, operands):
        """Replaces all xref fields with corresponding Location _id

        :operands: Operands for an instruction
        :returns: A list of operands with all 'xref' fields replaced

        """
        ops = []
        for op in operands:
            # The xref field holds a Location object - add it
            if 'xref' in op:
                loc_rec = self._upsert_location(op['xref']),
                op['xref'] = loc_rec['_id']
            ops.append(op)

        return ops

    def batch_add_instructions(self, sec_name, insts):
        """Adds all Instruction objects in the list to the db.

        Does a bulk insert for improved query time.

        :sec_name: Name of the section these insts belong to
        :insts: A list of Instruction objects to add

        """
        dis_col = self.db.disassembler
        dis_col.ensure_index([('addr', pymongo.ASCENDING)], cache_for=300)
        query = []
        for inst in insts:
            inst_dict = {'project_id': self.proj_id,
                         'dis_id': self.dis_id,
                         'addr': inst.r_addr + self._get_sec_base_addr(self.dis_id, sec_name),
                         #'r_addr': inst.r_addr,
                         'is_text': inst.is_text,
                         'my_bytes': inst.my_bytes,
                         #'sec_id': self._get_sec_id(self.dis_id, sec_name),
                         'sec_name': sec_name,
                         'mnemonic': inst.mnemonic}

            if inst.is_text:
                ops = self._process_operands(inst.operands)
                inst_dict['operands'] = ops
            else:
                inst_dict['disp'] = inst.disp

            query.append(inst_dict)

        ids = dis_col.insert(query)
        if len(ids) != len(insts):
            raise Exception("could not batch insert")

    def add_instruction(self, sec_name, inst, update=False):
        """Adds an Instruction object to the db.

        Note: This requires that the user first make sure that
              the manager's proj_id and dis_id are set and
              exist in the database.

        :sec_name: Name of the section this instruction belongs to
        :inst: The Instruction object to add

        """
        dis_col = self.db.disassembler
        dis_col.ensure_index([('addr', pymongo.ASCENDING)], cache_for=300)
        inst_dict = {'project_id': self.proj_id,
                     'dis_id': self.dis_id,
                     'addr': inst.r_addr + self._get_sec_base_addr(self.dis_id, sec_name),
                     #'r_addr': inst.r_addr,
                     'is_text': inst.is_text,
                     'my_bytes': inst.my_bytes,
                     #'sec_id': self._get_sec_id(self.dis_id, sec_name),
                     'sec_name': sec_name,
                     'mnemonic': inst.mnemonic}

        if inst.is_text:
            ops = self._process_operands(inst.operands)
            inst_dict['operands'] = ops
        else:
            inst_dict['disp'] = inst.disp

        if update:
            query = {'project_id': self.proj_id,
                     'dis_id': self.dis_id,
                     'sec_id': inst_dict['sec_id'],
                     'r_addr': inst.r_addr}
            return dis_col.update(query, {'$set': inst_dict}, upsert=False)
        else:
            dis_col.insert(inst_dict)

    #
    # Labels
    #
    '''
    Some aliases for adding labels.
    Public versions return None
    Private versions return either the record's
            _id field for upsert=False or the
            matching record for upsert=True

    '''
    def add_function(self, func):
        self._add_function(func)

    def _add_function(self, func, upsert=False, query=None):
        lab_dict = {'r_start_addr': func.r_start_addr,
                    'r_end_addr': func.r_end_addr,
                    'sec_id': self._get_sec_id(self.dis_id,
                                               func.sec_name),
                    'l_vars': func.l_vars}
        return self._add_label(func, lab_dict, upsert, query)

    def add_string(self, string):
        self._add_string(string)

    def _add_string(self, string, upsert=False, query=None):
        lab_dict = {'r_addr': string.r_addr,
                    'sec_id':
                    self._get_sec_id(self.dis_id,
                                     string.sec_name)}
        return self._add_label(string, lab_dict, upsert, query)

    def add_section(self, sec):
        self._add_section(sec)

    def _add_section(self, sec, upsert=False, query=None):
        lab_dict = {'base_addr': sec.base_addr,
                    'data': Binary(sec.data),
                    'size': sec.size,
                    'attribs': str(sec.attribs)}
        return self._add_label(sec, lab_dict, upsert, query)

    def add_location(self, loc):
        self._add_location(loc)

    def _add_location(self, loc, upsert=False, query=None):
        lab_dict = {'r_addr': loc.r_addr,
                    'sec_id':
                    self._get_sec_id(self.dis_id,
                                     loc.sec_name)}
        return self._add_label(loc, lab_dict, upsert, query)

    def upsert_function(self, func):
        self._upsert_function(func)

    def _upsert_function(self, func):
        query = {'r_start_addr': func.r_start_addr}
        return self._add_function(func, True, query)

    def upsert_string(self, string):
        self._upsert_string(string)

    def _upsert_string(self, string):
        query = {'r_addr': string.r_addr}
        return self._add_label(string, True, query)

    def upsert_section(self, sec):
        self._upsert_section(sec)

    def _upsert_section(self, sec):
        query = {'base_addr': sec.base_addr}
        return self._add_section(sec, True, query)

    def upsert_location(self, loc):
        self._upsert_location(loc)

    def _upsert_location(self, loc):
        query = {'r_addr': loc.r_addr}
        return self._add_location(loc, True, query)

    def _add_label(self, label, lab_dict, upsert=False, query=None):
        '''Given a Label object, add it to the disassembly.

        TODO: Make the update functionality work - currently untested

        :label: The label object to add
        :lab_dict: A dictionary representation of the label
        :upsert: If the label should be upserted
        :query: A query to match records for an upsert
        '''
        lab_col = self.db.labels
        lab_dict.update({'project_id': self.proj_id,
                         'dis_id': self.dis_id,
                         'type': label.type,
                         'name': label.name})

        if upsert:
            query.update({'project_id': self.proj_id,
                          'dis_id': self.dis_id,
                          'sec_id': label.sec_id})
            return lab_col.update(query, {'$set': lab_dict}, upsert=True)
        else:
            return lab_col.insert(lab_dict)

    #
    # Disassembly
    #
    def add_disassembly(self, disassembly):
        '''Add a Disassembly object to the database.

        :disassembly: A disassembly object to add
        :returns: False if already exists, else None

        '''
        # If it already exists, exit
        if self._get_dis_id(self.proj_id, disassembly.dis_name) is not None:
            return False

        dis_dict = {'dis_name': disassembly.dis_name,
                    'binary_name': disassembly.binary_name,
                    'binary_format': disassembly.binary_format,
                    'architecture': disassembly.architecture,
                    'mode': disassembly.mode,
                    'md5': disassembly.md5,
                    'size': disassembly.size,
                    'entry_point': disassembly.entry_point}

        # First, add it to the disassemblies collection
        dis_col = self.db.disassemblies
        new_id = dis_col.insert(dis_dict)

        # Then, add it to the existing project_information
        proj_col = self.db.project_information
        proj_col.update({'_id': self.proj_id},
                        {'$push': {'disassembly_ids': new_id}},
                        upsert=False)

        self._set_dis_id(new_id)

        return True

    #
    # Xrefs
    #
    def add_xref(self, xref):
        """
        Adds an Xref object to the database.

        :xref: The object to be added
        :returns: None

        """
        # If it already exists then return False
        xref_col = self.db.xrefs
        xref_dict = {'project_id': self.proj_id,
                     'dis_id': self.dis_id,
                     'base_addr': xref.base_addr,
                     'base_sec_id': self._get_sec_id(self.dis_id,
                                                     xref.base_sec_name),
                     'ref_addr': xref.base_addr,
                     'ref_sec_id': self._get_sec_id(self.dis_id,
                                                    xref.ref_loc.sec_name)}

        xref_col.insert(xref_dict)

    ##################################
    # Querying
    ##################################

    #
    # Disassemblies
    #
    def get_bin_name(self):
        rec = self.get_disassembly_record(self.dis_id)
        return rec['dis_name']

    def get_bin_size(self):
        rec = self.get_disassembly_record(self.dis_id)
        return rec['size']

    def get_md5(self):
        rec = self.get_disassembly_record(self.dis_id)
        return rec['md5']

    def get_arch(self):
        rec = self.get_disassembly_record(self.dis_id)
        return rec['architecture']

    def get_mode(self):
        rec = self.get_disassembly_record(self.dis_id)
        return rec['mode']

    def get_instructions(self, sec_name):
        """A portability hack.
        """
        for x in self.get_disassembler_records(sec_name):
            yield x

    def get_disassembler_records(self, sec_name):
        """Yields all instruction objects in the given section

        :sec_name: Name of the section to retrieve instructions for.
        :returns: Instruction objects
        """

        """
        query = {'sec_id': self._get_sec_id(self.dis_id, sec_name)}
        for each in self.db.disassembler.find(query).sort('r_addr', 1):
            yield each
        """

        #query = {'sec_id': self._get_sec_id(self.dis_id, sec_name)}
        query = {'sec_name': sec_name}
        for each in self.db.disassembler.find(query).sort('addr',
                                                          pymongo.ASCENDING):
            is_text = each['is_text']
            if is_text:
                yield Instruction(each['addr'], each['is_text'],
                                  each['my_bytes'], each['mnemonic'],
                                  operands=each['operands'])
            else:
                yield Instruction(each['addr'], each['is_text'],
                                  each['my_bytes'], each['mnemonic'],
                                  disp=each['disp'])
    #
    # Labels
    #

    def get_instructions_count(self, sec_name):
        """Count the number of instructions in the given section

        :sec_name: Name of the section
        :returns: Number of instructions in the section

        """
        query = {'sec_id': self._get_sec_id(self.dis_id, sec_name)}
        return self.db.disassembler.count(query)

    def _get_bytes_for_sec(self, sec_rec):
        """Returns the raw bytes of the section

        :sec_rec: The section record
        :returns: A string of raw bytes

        """
        dis_col = self.db.disassembler
        inst_recs = dis_col.find({'sec_id': sec_rec['_id']}, {'my_bytes': 1})

        return ''.join(r['my_bytes'] for r in inst_recs)

    def get_functions(self):
        """Get all functions in the project

        :returns: A list of function objects

        """
        return [Function(x['name'],
                         x['r_start_addr'],
                         x['r_end_addr'],
                         x['l_vars'])
                for x in self._get_label_records('func')]

    def get_strings(self):
        """Get all strings in the project

        :returns: A list of String objects

        """
        return [String(x['name'], x['r_addr'])
                for x in self._get_label_records('str')]

    @memoize
    def get_section_containing_addr(self, addr, executable=None):
        """Returns the section that 'owns' the address `addr`
        This has undefined behavior for sections that 'share' address space,
        such as unmapped sections, which are likely to have an address space
        beginning at zero.

        :addr: The absolute (not relative) address to test for
        :executable: A flag to filter results to either ex or nx sections

        """
        for x in self.get_sections(executable):
            if x.base_addr <= addr and x.base_addr + x.size > addr:
                return x
        return None

    def get_exec_sections(self):
        """Yields all executable sections in this disassembly

        :returns: Executable section objects

        """
        for x in self.get_sections(executable=True):
            yield x

    def get_non_exec_sections(self):
        """Yields all non-executable sectios in this disassembly

        :returns: Non-executable section objects

        """
        for x in self.get_sections(executable=False):
            yield x

    def get_sections(self, executable=None):
        """Yields all sections in the disassembly

        :executable: A flag to filter results to either ex or nx sections
        :returns: Section objects
        """
        labels = self._get_label_records('sec')

        for x in labels:
            att = Attributes(x['attribs'])
            if executable is None:
                yield Section(x['name'], x['data'], att,
                              x['base_addr'], x['size'])

            elif executable and att.executable:
                yield Section(x['name'], x['data'], att,
                              x['base_addr'], x['size'])

            elif not executable and not att.executable:
                yield Section(x['name'], x['data'], att,
                              x['base_addr'], x['size'])

    def get_section(self, sec_name):
        """Returns a section object for a section with this name.

        :sec_name: Name of the section to fetch.
        :returns: A Section object

        """
        labels = self._get_label_records('sec')
        for x in labels:
            if x['name'] == sec_name:
                return Section(x['name'], self._get_bytes_for_sec(x),
                               x['attribs'], x['base_addr'], x['size'])

    def get_locations(self):
        """Returns a list of all location objects in the disassembly

        :returns: A list of location objects

        """
        return [Location(x['name'], x['r_addr'])
                for x in self.get_labels('loc')]

    def _get_label_records(self, filt):
        """Returns all label records matching the given filter

        :filt: The filter to search for
        :returns: A pymongo cursor for found records

        """
        lab_col = self.db.labels
        if filt is None:
            return lab_col.find({'project_id': self.proj_id,
                                 'dis_id': self.dis_id})

        if filt == 'sec':
            return lab_col.find({'project_id': self.proj_id,
                                 'dis_id': self.dis_id, 'type': filt}).sort('base_addr', 1)
        elif filt == 'func' or filt == 'str' or filt == 'loc':
            return lab_col.find({'project_id': self.proj_id,
                                 'dis_id': self.dis_id, 'type': filt})
        else:
            self.log.error('Unknown filter type: ' + filt)
            return None

    ##################################
    # Deletion
    ##################################
    def batch_delete_insts_in_addr_ranges(self, sec_name, address_ranges):
        """Removes all instructions in the list of address ranges.

        Does a bulk removal for improved query time.

        :sec_name: Name of the section addresses belong to
        :address_ranges: A list of [start, end] address pairs
        :returns: None

        """
        self.log.debug('Removing instructions in address ranges: %s'
                       % str(address_ranges))
        dis_col = self.db.disassembler
        sec_id = self._get_sec_id(self.dis_id, sec_name)
        query = []
        for r in address_ranges:
            d = {'sec_id': sec_id,
                 'r_addr': {'$gte': r[0],
                            '$lt': r[1]}}
            query.append(d)
        dis_col.remove(query)

    def delete_insts_in_addr_range(self, sec_name, start_addr, end_addr):
        """Deletes all instructions in the given range

        :sec_name: Name of the section
        :start_addr: Starting relative address (inclusive)
        :end_addr: Ending relative address (exclusive)
        :returns: None

        """
        self.log.debug('Removing instructions in address range: %s to %s'
                       % (str(start_addr), str(end_addr)))
        dis_col = self.db.disassembler
        sec_id = self._get_sec_id(self.dis_id, sec_name)
        dis_col.remove({'sec_id': sec_id,
                        'r_addr': {'$gte': start_addr,
                                   '$lt': end_addr}})

    ##################################
    # Cleaning up
    ##################################

    def drop_haevn_db(self):
        """Drops the full haevn database

        :returns: None

        """
        self.log.info('dropping the haevn db...')
        client = self._get_client()
        self.db = None  # make sure it's obvious that it doesn't exist anymore
        client.drop_database(HAEVN_DB_NAME)


##################################
# Class utils
##################################


def generate_db_manager(config, project_name, dis_name):
    """Factory to return a DBManager.

    :config: A config file to read values from
    :project_name: Name of the project we're using
    :dis_name: Name of the disassembly we're using

    """
    host = config.get('Database', 'host')
    port = config.getint('Database', 'port')
    db_man = DBManager(host, port)
    db_man.load_project(project_name)
    db_man.load_disassembly(dis_name)
    return db_man
