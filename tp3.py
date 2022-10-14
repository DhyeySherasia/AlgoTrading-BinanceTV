# importing module
import logging

# Create and configure logger
logging.basicConfig(filename="newfile1.log", level=logging.DEBUG, format='%(asctime)s %(levelname)s %(message)s', filemode='w')

# Creating an object
logger = logging.getLogger()


# Test messages
x = "hey"
logger.debug("Harmless debug Message")
logger.info(f"{x} Just an information\n")
logger.warning("Its a Warning")
logger.error("Did you try to divide by zero")
logger.critical("Internet is down")
