"""
Provides a standard configuration for log files.
Maintained seperately to allow multiprocessing processes
to have standardized access to initialize log access.
"""
import logging

log_created = False

def init_logger(config=None):
    """Initializes configuration of the haevn logger.

    :config: Configuration file tor ead from

    """
    if config is not None:
        log_path = config.get('Debugging', 'log_path')
    else:
        log_path = 'log/haevn.log'
    # set up logging to file - see previous section for more details
    logging.basicConfig(level=logging.DEBUG,
                        format=('%(asctime)s - %(name)s - '
                                '%(levelname)s - %(message)s'),
                        datefmt='%m-%d %H:%M:%S',
                        filename=log_path,
                        filemode='w')
    # define a Handler which writes INFO messages or higher to the sys.stderr
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    # set a format which is simpler for console use
    formatter = logging.Formatter('%(asctime)s - %(message)s')
    formatter.datefmt = '%m-%d %H:%M:%S'
    # tell the handler to use this format
    console.setFormatter(formatter)
    # add the handler to the root logger
    logging.getLogger('').addHandler(console)

def getLogger(name, config=None):
    """Returns a logger object and initializes it if hasn't been init'ed yet.

    :config: Configuration file to read from
    :returns: A logger

    """
    if config is not None:
        global log_created
        if not log_created:
            print 'Creating logger for',name
            init_logger(config)
            log_created = True
    return logging.getLogger(name)
