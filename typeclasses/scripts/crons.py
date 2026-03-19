
from evennia.utils import logger

from . import Script

from typeclasses.characters import PlayerCharacter

class Crons(Script):
    key = 'crons'

    def at_server_start(self):
        """ 
        Happens on both server start and reload.
        """
        
        self.clear_approve_locks()



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
