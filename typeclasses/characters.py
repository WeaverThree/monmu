"""
Characters

Characters are (by default) Objects setup to be puppeted by Accounts.
They are what you "see" in game. The Character class in this module
is setup to be the "default" character type created by the default
creation commands.

"""

import time

from django.db.models import Q 

from evennia.objects.objects import DefaultCharacter

from .objects import ObjectParent

MOVE_DELAY = 15
IDLE_TIME = 60*5

class Character(ObjectParent, DefaultCharacter):
    """
    A general character. Contains functionality that's important for NPCs and PCs alike.
    """
    
    @property
    def is_idle(self):
        """
            Has the character been idle for longer than the set time?
        """
        if not self.has_account:
            return True
        return self.idle_time > IDLE_TIME
    
    @property
    def is_comms_idle(self):
        """
            Has the character emitted text that others can see for longer than the set time?
        """
        # TODO: Implement comms idle system
        return self.is_idle
    
    @property
    def is_player_character(self):
        """Is this a player character. Better than using instanceof."""
        return False
    
    def get_colored_display_name(self, looker=None):
        """
            Color this character name based on what their account's permissions are,
            or otherwise what type of character it is. Staff is always staff. Quelling
            doesn't change that.

            TODO: Move colors into a config somewhere?
        """

        color = ""
        
        if not self.is_player_character:
            color = "|x"
        elif looker == self or looker == self.account:
            color="|420"
        elif not self.has_account:
            color = ""
        elif self.account.is_superuser:
            color = "|[M|X" if self.is_comms_idle else "|[m|X"
        elif self.account.permissions.check("Developer"):
            color = "|M" if self.is_comms_idle else "|m"
        elif self.account.permissions.check("Admin"):
            color = "|C" if self.is_comms_idle else "|c"
        elif self.account.permissions.check("Builder"):
            color = "|Y" if self.is_comms_idle else "|y"
        elif not self.is_comms_idle:
            color = "|g"
        else:
            color = "|G"

        return "{}{}{}".format(color, self.name, "|n" if color else "")
        

class PlayerCharacter(Character):
    """
        This Character is for accounts to connect to. It adds functionality that only matters for
        characters that are controlled by people. 
    """

    @property
    def is_player_character(self):
        """Is this a player character. Better than using instanceof."""
        return True

    def at_pre_move(self, dest, move_type=None, **kwargs):
        if move_type == "traverse":
            now = time.time()
            if self.ndb.movelock and self.ndb.movelock > now:
                self.msg("Can't move for another {:.0f} seconds".format(self.ndb.movelock - now))
                return False
            else:
                return super().at_pre_move(dest, move_type, **kwargs)
        else:
            return super().at_pre_move(dest, move_type, **kwargs)

    def at_post_move(self, src, **kwargs):
        active_players_in_room = [char 
                for char in PlayerCharacter.objects.filter(Q(db_location=self.location) & ~ Q(db_key=self)) 
                if char.idle_time and char.idle_time < IDLE_TIME]
        if active_players_in_room:
            self.ndb.movelock = time.time() + MOVE_DELAY
            self.register_post_command_message(
                "|MPlayer activity detected|n, locking movement for {} seconds.".format(MOVE_DELAY)
            )
        else:
            self.ndb.movelock = None;
        super().at_post_move(src, **kwargs)
