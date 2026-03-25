
import csv
import os
import time

from evennia.utils import logger

from evennia import AttributeProperty
from evennia.typeclasses.attributes import NAttributeProperty

from . import Script

class ZoneDB(Script):
    """
    Zone info database. Might just be a place to store persistant data about zone, which do not
    exist as objects, only as tags on rooms. They need proper names (tags are all lowercase) and
    descriptions for desc combinations.

    Zones data layout should be:
    {
        'zonetag': {'name': 'actual name', 'desc': 'zone desc' <maybe other properties?},
        .
        .
        .
    }

    This will be mostly implemented in commands
    """

    key = 'zonedb'

    zones = AttributeProperty({})

    def at_script_delete(self):
        """
        This is a database singleton. We don't want people's work to be accidentally lost because of a config file issue or something, so as a safety measure...
        """
        return False







        


        
