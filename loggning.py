import logging
from logging.handlers import TimedRotatingFileHandler

def setupLogging():
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG)
    logger.propagate = True
    
    # Create a handler for the general log that rotates daily
    file_handler = TimedRotatingFileHandler(
        'logs/main.log',
        when='midnight',  
        interval=1,  
        backupCount=7  
    )
    file_handler.setLevel(logging.INFO) 

    # Create a handler for the error log that rotates daily
    error_handler = TimedRotatingFileHandler(
        'logs/main.error.log', 
        when='midnight', 
        interval=1,
        backupCount=7 
    )
    error_handler.setLevel(logging.ERROR)

    # Create a log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Apply the format to the handles
    file_handler.setFormatter(formatter)
    error_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(error_handler)

    logging.info("Logging is set up.")