
import evennia

from .rooms import Room
from commands import chargen

class ChargenRoomCmdset(evennia.CmdSet):
    
    
    def at_cmdset_creation(self):
        
        self.add(chargen.CmdSetSpecies())
        self.add(chargen.CmdSetNature())
        self.add(chargen.CmdBuyIVs())



class ChargenRoom(Room):


    def at_object_creation(self):

        super().at_object_creation()

        self.cmdset.add(ChargenRoomCmdset(), persistent=True)
    

    def get_display_desc(self, looker, **kwargs):

        return f"{'- - -':^80}\n|bThis is a placeholder for the interactive chargen system's dynamic descriptions.|n"