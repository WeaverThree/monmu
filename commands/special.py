


from .command import Command, MuxCommand
from typeclasses.characters import Character

from evennia.server.signals import SIGNAL_EXIT_TRAVERSED


class FollowExitCommand(MuxCommand):
    """
    This is a command that simply cause the caller to traverse
    the object it is attached to.

    """

    obj = None

    def func(self):
        """
        Default exit traverse if no syscommand is defined.
        """

        caller = self.caller

        if self.obj.access(self.caller, "traverse"):
            # we may traverse the exit.
            oldloc = caller.location

            self.obj.at_traverse(caller, self.obj.destination)
            SIGNAL_EXIT_TRAVERSED.send(sender=self.obj, traverser=self.caller)
            
            if caller.location == oldloc:
                # We got blocked from moving down the pipe, no need to process followers
                return

            if caller.is_typeclass(Character):
                if caller.followers:
                    for follower in caller.followers:
                        if follower.location != oldloc:
                            # Follower wandered off somehow
                            follower.stop_following(caller)
                        follower.msg(
                            f"{follower.get_display_name(follower)} attempts to follow "
                            f"{caller.get_display_name(follower)} to {self.obj.destination.get_display_name(caller)}."
                        )
                        caller.msg(
                            f"{follower.get_display_name(caller)} attempts to follow "
                            f"{caller.get_display_name(caller)} to {self.obj.destination.get_display_name(caller)}."
                        )
                        # This should cause them to follow...
                        follower.execute_cmd(self.key)
                    
                    yield 1 # Wait 1 second to give followers time to follow maybe
                    
                    for follower in caller.followers:
                        if follower.location != caller.location:
                            # They didn't follow
                            follower.stop_following(caller)
                    
        else:
            # exit is locked
            if self.obj.db.err_traverse:
                # if exit has a better error message, let's use it.
                caller.msg(self.obj.db.err_traverse)
            else:
                # No shorthand error message. Call hook.
                self.obj.at_failed_traverse(caller)

    def get_extra_info(self, caller, **kwargs):
        """
        Shows a bit of information on where the exit leads.

        Args:
            caller (DefaultObject): The object (usually a character) that entered an ambiguous command.
            **kwargs (dict): Arbitrary, optional arguments for users
                overriding the call (unused by default).

        Returns:
            str: A string with identifying information to disambiguate the command, conventionally
            with a preceding space.

        """
        if self.obj.destination:
            return " (exit to {destination})".format(
                destination=self.obj.destination.get_display_name(caller, **kwargs)
            )
        else:
            return " (%s)" % self.obj.get_display_name(caller, **kwargs)