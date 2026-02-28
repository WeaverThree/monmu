from evennia import Command

class CmdOOC(Command):
    """
    OOC - provides an easy way to state something as out of character, prepending
          'ooc' to the text or pose as inputted.

    Usage:
        ooc [text]: output <OOC> [name] says, "[text]"
        ooc :[text]: output <OOC> [name] [text]
    """

    key = "ooc"
    lock = "cmd:all()"
    help_category = "General"

    def func(self):

        caller = self.caller
        args = str(self.args.strip())
        location = self.caller.location

        
        if not args:
            self.msg("Can't OOC blank message.")
            return

        string = "|Y<OOC>|n {}".format(caller.name)
        if args[0] == ":":
            if args[1] == "'":
                string += "{}".format(args[1:])
            else:
                string += " {}".format(args[1:])
        else:
            string += ' says, "{}"'.format(args)

        location.msg_contents(string)
