
import evennia

from .rooms import Room
from .characters import PlayerCharacter
from commands import chargen

class ChargenRoomCmdset(evennia.CmdSet):
    
    
    def at_cmdset_creation(self):
        
        self.add(chargen.CmdChargenSetSpecies())
        self.add(chargen.CmdChargenSetNature())
        self.add(chargen.CmdChargenBuyIVs())
        self.add(chargen.CmdChargenResetIVs())
        self.add(chargen.CmdChargenEquipMove())
        self.add(chargen.CmdChargenUnequipMove())
        self.add(chargen.CmdChargenLearnMove())
        self.add(chargen.CmdChargenForgetMove())



class ChargenRoom(Room):


    def at_object_creation(self):

        super().at_object_creation()

        self.cmdset.add(ChargenRoomCmdset(), persistent=True)
    
    
    def at_object_receive(self, moved_obj, source_location, move_type="move", **kwargs):
        super().at_object_receive(moved_obj, source_location, move_type, **kwargs)
        if isinstance(moved_obj, PlayerCharacter):
            if moved_obj.player_mode != "DOWN":
                moved_obj.player_mode = "CG"


    def get_display_desc(self, looker, **kwargs):

        return f"{'- - -':^80}\n|bThis is a placeholder for the interactive chargen system's dynamic descriptions.|n"