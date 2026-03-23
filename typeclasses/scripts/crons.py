
import time
import datetime

from django.conf import settings

from evennia import AttributeProperty
from evennia.utils import logger

from . import Script

from typeclasses.characters import PlayerCharacter

class Crons(Script):
    key = 'crons'

    next_refresh = AttributeProperty(0)
    next_sweep = AttributeProperty(0)


    def at_server_start(self):
        """ 
        Happens on both server start and reload.
        """
        self.clear_approve_locks()

        if not self.next_sweep:
            self.next_sweep = time.time() + settings.SWEEP_CHECK_TIME


    def clear_approve_locks(self):
        """
        Clean up approval locks that got lost because a server restart interrupted an admin
        approving a character, so that people don't get stuck forever.
        """
        for player in PlayerCharacter.objects.all():
            if player.approvelocked:
                logger.log_info(f"Unlocking {player.name} from approvelock.")
                player.approvelocked = False
                player.approved = False


    def at_repeat(self, **kwargs):
        now = time.time()
        if now > self.next_sweep:
            self.sweep()

        if now > self.next_refresh:
            self.refresh()

    
    def sweep(self):
        now = time.time()

        self.next_sweep = now + settings.SWEEP_CHECK_TIME

        cutoff_time = now - settings.SWEEP_TIME
        nosweep_tag = settings.ROOM_TAG_NOSWEEP

        for character in PlayerCharacter.objects.all_family():
            if not character.has_account:
                if character.last_puppeted < cutoff_time:
                    oldloc = character.location
                    if oldloc.is_ic_room and not oldloc.tags.has(nosweep_tag):
                        if character.move_to(character.home, move_type="sweep"):
                            
                            icmsg = ""
                            if oldloc.is_ic_room and not character.location.is_ic_room:
                                character.last_ic_room = oldloc
                                icmsg = (
                                    f"\nThis moved {character.get_display_name(character)} OOC, "
                                    f"so you can use |b+ic|n to return."
                                )

                            msg = (
                                f"{character.get_display_name(character)} |Mwas left logged off for a long time in a "
                                f"room that's not allowed in, so they were moved to their home at|n "
                                f"{character.location.get_display_name(character)}.{icmsg}"
                            )

                            character.register_post_command_message(msg)
                            
                        else:
                            logger.log_err(f"SWEEPER: Could not move {character.name} to their home.")



    def refresh(self):
        print ("Do refresh here")