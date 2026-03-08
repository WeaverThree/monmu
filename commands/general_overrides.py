from .command import MuxCommand

class CmdPose(MuxCommand):
    """
    strike a pose

    Usage:
      pose <pose text> pose's <pose text>

    Example:
      pose is standing by the wall, smiling.
       -> others will see:
      Tom is standing by the wall, smiling.

    Describe an action being taken. The pose text will automatically begin with your name.

    All commands strip leading space if followed by [',:] ; always does.
    """

    key = "pose"
    aliases = [":", "emote", ";"]
    locks = "cmd:all()"
    arg_regex = ""

    # we want to be able to pose without whitespace between
    # the command/alias and the pose (e.g. :pose)
    arg_regex = None

    def parse(self):
        """
        Custom parse the cases where the emote starts with some special letter, such as 's, at which
        we don't want to separate the caller's name and the emote with a space.

        Include a semicolon command fallback for compatability.
        """
        args = self.args
        if args and not args[0] in ["'", ",", ":"] and not self.cmdstring == ';':
            args = " %s" % args.strip()
        self.args = args

    def func(self):
        """Hook function"""
        if not self.args:
            msg = "What do you want to do?"
            self.msg(msg)
        else:
            msg = "{sender}" + self.args
            self.caller.location.msg_contents(
                text=(msg, self.args, {"type": "pose"}),
                 mapping={'sender':self.caller}, from_obj=self.caller)