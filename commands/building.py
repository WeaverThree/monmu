
from .command import MuxCommand, Command

from typeclasses.rooms import Room

class CmdZone(Command):
    """
    Sets the zone for the current area. Equivilant to @tag here=zonename:Zone, but ensures that any
    prior zone tagging is also removed. Does not let you clear zones because no room should be
    unzoned.

    Usage:
        @zone <zone name>
    """
    key = "@zone"
    locks = "cmd:perm(Builder)"
    help_category = "Building"

    _usage = "Usage: @zone <zone name>"

    def func(self):
        
        newzone = self.args.strip().lower()

        if not newzone:
            self.caller.msg(self._usage)
            return

        target = self.caller.location

        if not target:
            self.caller.msg(
                "You don't seem to have a location. " 
                "This is probably a serious problem, but get one before using this command."
            )
            return
        
        if not isinstance(target, Room):
            self.caller.msg("You're not in any kind of room. This command only works on rooms. Please come again.")
            return

        oldzones = target.tags.get(category="Zone", return_list=True)
        if not oldzones:
            oldzones = "<nothing>"
        elif len(oldzones) == 1:
            oldzones = oldzones[0]
        else:
            self.caller.msg("|RFound more than one zone to replace. Fixing that.|n")
            oldzones = ', '.join(oldzones)
        
        target.tags.clear(category="Zone")
        target.tags.add(newzone, category="Zone")

        self.caller.msg(f"Updated zone of {target.get_display_name(self.caller)} from {oldzones} to {newzone}")
        

        


