r"""
Evennia settings file.

The available options are found in the default settings file found
here:

https://www.evennia.com/docs/latest/Setup/Settings-Default.html

Remember:

Don't copy more from the default file than you actually intend to
change; this will make sure that you don't overload upstream updates
unnecessarily.

When changing a setting requiring a file system path (like
path/to/actual/file.py), use GAME_DIR and EVENNIA_DIR to reference
your game folder and the Evennia library folders respectively. Python
paths (path.to.module) should be given relative to the game's root
folder (typeclasses.foo) whereas paths within the Evennia library
needs to be given explicitly (evennia.foo).

If you want to share your game dir, including its settings, you can
put secret game- or server-specific settings in secret_settings.py.

"""

# Use the defaults from Evennia unless explicitly overridden
from evennia.settings_default import *

######################################################################
# Evennia base server config
######################################################################

# This is the name of your game. Make it catchy!

WEBSERVER_ENABLED = False


TIME_ZONE = "America/Los_Angeles"
TIME_FACTOR = 1.0
MAX_CHAR_LIMIT = 20000

# Different Multisession modes allow a player (=account) to connect to the
# game simultaneously with multiple clients (=sessions).
#  0 - single session per account (if reconnecting, disconnect old session)
#  1 - multiple sessions per account, all sessions share output
#  2 - multiple sessions per account, one session allowed per puppet
#  3 - multiple sessions per account, multiple sessions per puppet (share output)
#      session getting the same data.
MULTISESSION_MODE = 2







######################################################################
# Settings given in secret_settings.py override those in this file.
######################################################################
try:
    from server.conf.secret_settings import *
except ImportError:
    print("secret_settings.py file not found or failed to import.")
