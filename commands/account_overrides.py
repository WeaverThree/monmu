
import time
import re
from codecs import lookup as codecs_lookup

from django.conf import settings

import evennia
from evennia.utils import create, logger, search, utils
from evennia.typeclasses.attributes import NickTemplateInvalid

_MAX_NR_CHARACTERS = settings.MAX_NR_CHARACTERS
_AUTO_PUPPET_ON_LOGIN = settings.AUTO_PUPPET_ON_LOGIN

from .command import Command, MuxCommand


class CmdSessions(MuxCommand):
    """
    check your connected session(s)

    Usage:
      sessions

    Lists the sessions currently connected to your account.

    """

    key = "sessions"
    locks = "cmd:all()"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    def func(self):
        """Implement function"""
        account = self.account
        sessions = account.sessions.all()
        table = self.styled_table(
            "|wsessid", "|wprotocol", "|whost", "|wpuppet/character", "|wlocation"
        )
        for sess in sorted(sessions, key=lambda x: x.sessid):
            char = account.get_puppet(sess)
            table.add_row(
                str(sess.sessid),
                str(sess.protocol_key),
                isinstance(sess.address, tuple) and sess.address[0] or sess.address,
                char and str(char) or "None",
                char and str(char.location) or "N/A",
            )
            self.msg(f"|wYour current session(s):|n\n{table}")



class CmdOption(MuxCommand):
    """
    Set an account option

    Usage:
      option[/save] [name = value]

    Switches:
      save - Save the current option settings for future logins.
      clear - Clear the saved options.

    This command allows for viewing and setting client interface
    settings. Note that saved options may not be able to be used if
    later connecting with a client with different capabilities.


    """

    key = "option"
    aliases = "options"
    switch_options = ("save", "clear")
    locks = "cmd:all()"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    def func(self):
        """
        Implements the command
        """
        if self.session is None:
            return

        flags = self.session.protocol_flags

        # Display current options
        if not self.args:
            # list the option settings

            if "save" in self.switches:
                # save all options
                self.caller.db._saved_protocol_flags = flags
                self.msg("|gSaved all options. Use option/clear to remove.|n")
            if "clear" in self.switches:
                # clear all saves
                self.caller.db._saved_protocol_flags = {}
                self.msg("|gCleared all saved options.")

            options = dict(flags)  # make a copy of the flag dict
            saved_options = dict(self.caller.attributes.get("_saved_protocol_flags", default={}))

            if "SCREENWIDTH" in options:
                if len(options["SCREENWIDTH"]) == 1:
                    options["SCREENWIDTH"] = options["SCREENWIDTH"][0]
                else:
                    options["SCREENWIDTH"] = "  \n".join(
                        "%s : %s" % (screenid, size)
                        for screenid, size in options["SCREENWIDTH"].items()
                    )
            if "SCREENHEIGHT" in options:
                if len(options["SCREENHEIGHT"]) == 1:
                    options["SCREENHEIGHT"] = options["SCREENHEIGHT"][0]
                else:
                    options["SCREENHEIGHT"] = "  \n".join(
                        "%s : %s" % (screenid, size)
                        for screenid, size in options["SCREENHEIGHT"].items()
                    )
            options.pop("TTYPE", None)

            header = ("Name", "Value", "Saved") if saved_options else ("Name", "Value")
            table = self.styled_table(*header)
            for key in sorted(options):
                row = [key, options[key]]
                if saved_options:
                    saved = " |YYes|n" if key in saved_options else ""
                    changed = (
                        "|y*|n" if key in saved_options and flags[key] != saved_options[key] else ""
                    )
                    row.append("%s%s" % (saved, changed))
                table.add_row(*row)
            self.msg(f"|wClient settings ({self.session.protocol_key}):|n\n{table}|n")

            return

        if not self.rhs:
            self.msg("Usage: option [name = [value]]")
            return

        # Try to assign new values

        def validate_encoding(new_encoding):
            # helper: change encoding
            try:
                codecs_lookup(new_encoding)
            except LookupError:
                raise RuntimeError(f"The encoding '|w{new_encoding}|n' is invalid. ")
            return val

        def validate_size(new_size):
            return {0: int(new_size)}

        def validate_bool(new_bool):
            return True if new_bool.lower() in ("true", "on", "1") else False

        def update(new_name, new_val, validator):
            # helper: update property and report errors
            try:
                old_val = flags.get(new_name, False)
                new_val = validator(new_val)
                if old_val == new_val:
                    self.msg(f"Option |w{new_name}|n was kept as '|w{old_val}|n'.")
                else:
                    flags[new_name] = new_val

                    # If we're manually assign a display size, turn off auto-resizing
                    if new_name in ["SCREENWIDTH", "SCREENHEIGHT"]:
                        flags["AUTORESIZE"] = False

                    self.msg(
                        f"Option |w{new_name}|n was changed from '|w{old_val}|n' to"
                        f" '|w{new_val}|n'."
                    )
                return {new_name: new_val}
            except Exception as err:
                self.msg(f"|rCould not set option |w{new_name}|r:|n {err}")
                return False

        validators = {
            "ANSI": validate_bool,
            "CLIENTNAME": utils.to_str,
            "ENCODING": validate_encoding,
            "MCCP": validate_bool,
            "NOGOAHEAD": validate_bool,
            "NOPROMPTGOAHEAD": validate_bool,
            "MXP": validate_bool,
            "NOCOLOR": validate_bool,
            "NOPKEEPALIVE": validate_bool,
            "OOB": validate_bool,
            "RAW": validate_bool,
            "SCREENHEIGHT": validate_size,
            "SCREENWIDTH": validate_size,
            "AUTORESIZE": validate_bool,
            "SCREENREADER": validate_bool,
            "TERM": utils.to_str,
            "UTF-8": validate_bool,
            "XTERM256": validate_bool,
            "INPUTDEBUG": validate_bool,
            "FORCEDENDLINE": validate_bool,
            "LOCALECHO": validate_bool,
            "TRUECOLOR": validate_bool,
        }

        name = self.lhs.upper()
        val = self.rhs.strip()
        optiondict = False
        if val and name in validators:
            optiondict = update(name, val, validators[name])
        else:
            self.msg("|rNo option named '|w%s|r'." % name)
        if optiondict:
            # a valid setting
            if "save" in self.switches:
                # save this option only
                saved_options = self.account.attributes.get("_saved_protocol_flags", default={})
                saved_options.update(optiondict)
                self.account.attributes.add("_saved_protocol_flags", saved_options)
                for key in optiondict:
                    self.msg(f"|gSaved option {key}.|n")
            if "clear" in self.switches:
                # clear this save
                for key in optiondict:
                    self.account.attributes.get("_saved_protocol_flags", {}).pop(key, None)
                    self.msg(f"|gCleared saved {key}.")
            self.session.update_flags(**optiondict)


class CmdPassword(MuxCommand):
    """
    change your password

    Usage:
      password <old password> = <new password>

    Changes your password. Make sure to pick a safe one.
    """

    key = "password"
    locks = "cmd:pperm(Player)"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    def func(self):
        """hook function."""

        account = self.account
        if not self.rhs:
            self.msg("Usage: password <oldpass> = <newpass>")
            return
        oldpass = self.lhslist[0]  # Both of these are
        newpass = self.rhslist[0]  # already stripped by parse()

        # Validate password
        validated, error = account.validate_password(newpass)

        if not account.check_password(oldpass):
            self.msg("The specified old password isn't correct.")
        elif not validated:
            errors = [e for suberror in error.messages for e in error.messages]
            string = "\n".join(errors)
            self.msg(string)
        else:
            account.set_password(newpass)
            account.save()
            self.msg("Password changed.")
            logger.log_sec(
                f"Password Changed: {account} (Caller: {account}, IP: {self.session.address})."
            )


class CmdQuit(MuxCommand):
    """
    quit the game

    Usage:
      quit

    Switch:
      all - disconnect all connected sessions

    Gracefully disconnect your current session from the
    game. Use the /all switch to disconnect from all sessions.
    """

    key = "quit"
    switch_options = ("all",)
    locks = "cmd:all()"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    def func(self):
        """hook function"""
        account = self.account

        if "all" in self.switches:
            account.msg(
                "|RQuitting|n all sessions. Hope to see you soon again.", session=self.session
            )
            reason = "quit/all"
            for session in account.sessions.all():
                account.disconnect_session_from_account(session, reason)
        else:
            nsess = len(account.sessions.all())
            reason = "quit"
            if nsess == 2:
                account.msg("|RQuitting|n. One session is still connected.", session=self.session)
            elif nsess > 2:
                account.msg(
                    "|RQuitting|n. %i sessions are still connected." % (nsess - 1),
                    session=self.session,
                )
            else:
                # we are quitting the last available session
                account.msg("|RQuitting|n. Hope to see you again, soon.", session=self.session)
            account.disconnect_session_from_account(self.session, reason)


class CmdColorTest(MuxCommand):
    """
    testing which colors your client support

    Usage:
      color ansi | xterm256 | truecolor

    Prints a color map along with in-mud color codes to use to produce
    them.  It also tests what is supported in your client. Choices are
    16-color ansi (supported in most muds), the 256-color xterm256
    standard, or truecolor. No checking is done to determine your client supports
    color - if not you will see rubbish appear.
    """

    key = "color"
    locks = "cmd:all()"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    # the slices of the ANSI_PARSER lists to use for retrieving the
    # relevant color tags to display. Replace if using another schema.
    # This command can only show one set of markup.
    slice_bright_fg = slice(13, 21)  # from ANSI_PARSER.ansi_map
    slice_dark_fg = slice(21, 29)  # from ANSI_PARSER.ansi_map
    slice_dark_bg = slice(-8, None)  # from ANSI_PARSER.ansi_map
    slice_bright_bg = slice(None, None)  # from ANSI_PARSER.ansi_xterm256_bright_bg_map

    def table_format(self, table):
        """
        Helper method to format the ansi/xterm256 tables.
        Takes a table of columns [[val,val,...],[val,val,...],...]
        """
        if not table:
            return [[]]

        extra_space = 1
        max_widths = [max([len(str(val)) for val in col]) for col in table]
        ftable = []
        for irow in range(len(table[0])):
            ftable.append(
                [
                    str(col[irow]).ljust(max_widths[icol]) + " " * extra_space
                    for icol, col in enumerate(table)
                ]
            )
        return ftable

    def make_hex_color_from_column(self, column_number, count):
        r = 255 - column_number * 255 / count
        g = column_number * 510 / count
        b = column_number * 255 / count

        if g > 255:
            g = 510 - g

        return (
            f"#{hex(round(r))[2:].zfill(2)}{hex(round(g))[2:].zfill(2)}{hex(round(b))[2:].zfill(2)}"
        )

    def func(self):
        """Show color tables"""

        if self.args.startswith("a"):
            # show ansi 16-color table
            from evennia.utils import ansi

            ap = ansi.ANSI_PARSER
            # ansi colors
            # show all ansi color-related codes
            bright_fg = [
                "%s%s|n" % (code, code.replace("|", "||"))
                for code, _ in ap.ansi_map[self.slice_bright_fg]
            ]
            dark_fg = [
                "%s%s|n" % (code, code.replace("|", "||"))
                for code, _ in ap.ansi_map[self.slice_dark_fg]
            ]
            dark_bg = [
                "%s%s|n" % (code.replace("\\", ""), code.replace("|", "||").replace("\\", ""))
                for code, _ in ap.ansi_map[self.slice_dark_bg]
            ]
            bright_bg = [
                "%s%s|n" % (code.replace("\\", ""), code.replace("|", "||").replace("\\", ""))
                for code, _ in ap.ansi_xterm256_bright_bg_map[self.slice_bright_bg]
            ]
            dark_fg.extend(["" for _ in range(len(bright_fg) - len(dark_fg))])
            table = utils.format_table([bright_fg, dark_fg, bright_bg, dark_bg])
            string = "ANSI colors:"
            for row in table:
                string += "\n " + " ".join(row)
            self.msg(string)
            self.msg(
                "||X : black. ||/ : return, ||- : tab, ||_ : space, ||* : invert, ||u : underline\n"
                "To combine background and foreground, add background marker last, e.g. ||r||[B.\n"
                "Note: bright backgrounds like ||[r requires your client handling Xterm256 colors."
            )

        elif self.args.startswith("x"):
            # show xterm256 table
            table = [[], [], [], [], [], [], [], [], [], [], [], []]
            for ir in range(6):
                for ig in range(6):
                    for ib in range(6):
                        # foreground table
                        table[ir].append("|%i%i%i%s|n" % (ir, ig, ib, "||%i%i%i" % (ir, ig, ib)))
                        # background table
                        table[6 + ir].append(
                            "|%i%i%i|[%i%i%i%s|n"
                            % (5 - ir, 5 - ig, 5 - ib, ir, ig, ib, "||[%i%i%i" % (ir, ig, ib))
                        )
            table = self.table_format(table)
            string = (
                "Xterm256 colors (if not all hues show, your client might not report that it can"
                " handle xterm256):"
            )
            string += "\n" + "\n".join("".join(row) for row in table)
            table = [[], [], [], [], [], [], [], [], [], [], [], []]
            for ibatch in range(4):
                for igray in range(6):
                    letter = chr(97 + (ibatch * 6 + igray))
                    inverse = chr(122 - (ibatch * 6 + igray))
                    table[0 + igray].append("|=%s%s |n" % (letter, "||=%s" % letter))
                    table[6 + igray].append("|=%s|[=%s%s |n" % (inverse, letter, "||[=%s" % letter))
            for igray in range(6):
                # the last row (y, z) has empty columns
                if igray < 2:
                    letter = chr(121 + igray)
                    inverse = chr(98 - igray)
                    fg = "|=%s%s |n" % (letter, "||=%s" % letter)
                    bg = "|=%s|[=%s%s |n" % (inverse, letter, "||[=%s" % letter)
                else:
                    fg, bg = " ", " "
                table[0 + igray].append(fg)
                table[6 + igray].append(bg)
            table = self.table_format(table)
            string += "\n" + "\n".join("".join(row) for row in table)
            self.msg(string)

        elif self.args.startswith("t"):
            # show abbreviated truecolor sample (16.7 million colors in truecolor)
            string = (
                "\n"
                "True Colors (if this is not a smooth rainbow transition, your client might not "
                "report that it can handle truecolor): \n"
            )
            display_width = self.client_width()
            num_colors = display_width * 1
            color_block = [
                f"|[{self.make_hex_color_from_column(i, num_colors)} " for i in range(num_colors)
            ]
            color_block = [
                "".join(color_block[iline : iline + display_width])
                for iline in range(0, num_colors, display_width)
            ]
            string += "\n".join(color_block)

            string += (
                "\n|nfg: |#FF0000||#FF0000|n (|#F00||#F00|n) to |#0000FF||#0000FF|n (|#00F||#00F|n)"
                "\n|nbg: |[#FF0000||[#FF0000|n (|[#F00||[#F00|n) to |n|[#0000FF||[#0000FF |n(|[#00F||[#00F|n)"
            )

            self.msg(string)

        else:
            # malformed input
            self.msg("Usage: color ansi || xterm256 || truecolor")


class CmdQuell(MuxCommand):
    """
    use character's permissions instead of account's

    Usage:
      quell
      unquell

    Normally the permission level of the Account is used when puppeting a
    Character/Object to determine access. This command will switch the lock
    system to make use of the puppeted Object's permissions instead. This is
    useful mainly for testing.
    Hierarchical permission quelling only work downwards, thus an Account cannot
    use a higher-permission Character to escalate their permission level.
    Use the unquell command to revert back to normal operation.
    """

    key = "quell"
    aliases = ["unquell"]
    locks = "cmd:pperm(Player)"
    help_category = "System"

    # this is used by the parent
    account_caller = True

    def _recache_locks(self, account):
        """Helper method to reset the lockhandler on an already puppeted object"""
        if self.session:
            char = self.session.puppet
            if char:
                # we are already puppeting an object. We need to reset
                # the lock caches (otherwise the superuser status change
                # won't be visible until repuppet)
                char.locks.reset()
        account.locks.reset()

    def func(self):
        """Perform the command"""
        account = self.account
        permstr = (
            account.is_superuser and "(superuser)" or "(%s)" % ", ".join(account.permissions.all())
        )
        if self.cmdstring in ("unquell", "unquell"):
            if not account.attributes.get("_quell"):
                self.msg(f"Already using normal Account permissions {permstr}.")
            else:
                account.attributes.remove("_quell")
                self.msg(f"Account permissions {permstr} restored.")
        else:
            if account.attributes.get("_quell"):
                self.msg(f"Already quelling Account {permstr} permissions.")
                return
            account.attributes.add("_quell", True)
            puppet = self.session.puppet if self.session else None
            if puppet:
                cpermstr = "(%s)" % ", ".join(puppet.permissions.all())
                cpermstr = f"Quelling to current puppet's permissions {cpermstr}."
                cpermstr += (
                    f"\n(Note: If this is higher than Account permissions {permstr},"
                    " the lowest of the two will be used.)"
                )
                cpermstr += "\nUse unquell to return to normal permission usage."
                self.msg(cpermstr)
            else:
                self.msg(f"Quelling Account permissions {permstr}. Use unquell to get them back.")
        self._recache_locks(account)


class CmdNick(MuxCommand):
    """
    define a personal alias/nick by defining a string to
    match and replace it with another on the fly

    Usage:
      nick[/switches] <string> [= [replacement_string]]
      nick[/switches] <template> = <replacement_template>
      nick/delete <string> or number
      nicks

    Switches:
      inputline - replace on the inputline (default)
      object    - replace on object-lookup
      account   - replace on account-lookup
      list      - show all defined aliases (also "nicks" works)
      delete    - remove nick by index in /list
      clearall  - clear all nicks

    Examples:
      nick hi = say Hello, I'm Sarah!
      nick/object tom = the tall man
      nick build $1 $2 = create/drop $1;$2
      nick tell $1 $2=page $1=$2
      nick tm?$1=page tallman=$1
      nick tm\\\\=$1=page tallman=$1

    A 'nick' is a personal string replacement. Use $1, $2, ... to catch arguments.
    Put the last $-marker without an ending space to catch all remaining text. You
    can also use unix-glob matching for the left-hand side <string>:

        * - matches everything
        ? - matches 0 or 1 single characters
        [abcd] - matches these chars in any order
        [!abcd] - matches everything not among these chars
        \\\\= - escape literal '=' you want in your <string>

    Note that no objects are actually renamed or changed by this command - your nicks
    are only available to you. If you want to permanently add keywords to an object
    for everyone to use, you need build privileges and the alias command.

    """

    key = "nick"
    switch_options = ("inputline", "object", "account", "list", "delete", "clearall")
    aliases = ["nickname", "nicks"]
    locks = "cmd:all()"
    help_category = "System"

    def parse(self):
        """
        Support escaping of = with \\=
        """
        super().parse()
        args = (self.lhs or "") + (" = %s" % self.rhs if self.rhs else "")
        parts = re.split(r"(?<!\\)=", args, 1)
        self.rhs = None
        if len(parts) < 2:
            self.lhs = parts[0].strip()
        else:
            self.lhs, self.rhs = [part.strip() for part in parts]
        self.lhs = self.lhs.replace("\\=", "=")

    def func(self):
        """Create the nickname"""

        def _cy(string):
            "add color to the special markers"
            return re.sub(r"(\$[0-9]+|\*|\?|\[.+?\])", r"|Y\1|n", string)

        caller = self.caller
        switches = self.switches
        nicktypes = [switch for switch in switches if switch in ("object", "account", "inputline")]
        specified_nicktype = bool(nicktypes)
        nicktypes = nicktypes if specified_nicktype else ["inputline"]

        nicklist = (
            utils.make_iter(caller.nicks.get(category="inputline", return_obj=True) or [])
            + utils.make_iter(caller.nicks.get(category="object", return_obj=True) or [])
            + utils.make_iter(caller.nicks.get(category="account", return_obj=True) or [])
        )

        if "list" in switches or self.cmdstring in ("nicks",):
            if not nicklist:
                string = "|wNo nicks defined.|n"
            else:
                table = self.styled_table("#", "Type", "Nick match", "Replacement")
                for inum, nickobj in enumerate(nicklist):
                    _, _, nickvalue, replacement = nickobj.value
                    table.add_row(
                        str(inum + 1), nickobj.db_category, _cy(nickvalue), _cy(replacement)
                    )
                string = "|wDefined Nicks:|n\n%s" % table
            caller.msg(string)
            return

        if "clearall" in switches:
            caller.nicks.clear()
            if caller.account:
                caller.account.nicks.clear()
            caller.msg("Cleared all nicks.")
            return

        if "delete" in switches or "del" in switches:
            if not self.args or not self.lhs:
                caller.msg("usage nick/delete <nick> or <#num> ('nicks' for list)")
                return
            # see if a number was given
            arg = self.args.lstrip("#")
            oldnicks = []
            if arg.isdigit():
                # we are given a index in nicklist
                delindex = int(arg)
                if 0 < delindex <= len(nicklist):
                    oldnicks.append(nicklist[delindex - 1])
                else:
                    caller.msg("Not a valid nick index. See 'nicks' for a list.")
                    return
            else:
                if not specified_nicktype:
                    nicktypes = ("object", "account", "inputline")
                for nicktype in nicktypes:
                    oldnicks.append(caller.nicks.get(arg, category=nicktype, return_obj=True))

            oldnicks = [oldnick for oldnick in oldnicks if oldnick]
            if oldnicks:
                for oldnick in oldnicks:
                    nicktype = oldnick.category
                    nicktypestr = "%s-nick" % nicktype.capitalize()
                    _, _, old_nickstring, old_replstring = oldnick.value
                    caller.nicks.remove(old_nickstring, category=nicktype)
                    caller.msg(
                        f"{nicktypestr} removed: '|w{old_nickstring}|n' -> |w{old_replstring}|n."
                    )
            else:
                caller.msg("No matching nicks to remove.")
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("object", "account", "inputline")
            for nicktype in nicktypes:
                nicks = [
                    nick
                    for nick in utils.make_iter(
                        caller.nicks.get(category=nicktype, return_obj=True)
                    )
                    if nick
                ]
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(f"{nicktype.capitalize()}-nick: '{nick}' -> '{repl}'")
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(f"No nicks found matching '{self.lhs}'")
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("object", "account", "inputline")
            for nicktype in nicktypes:
                if nicktype == "account":
                    obj = caller.account
                else:
                    obj = caller
                nicks = utils.make_iter(obj.nicks.get(category=nicktype, return_obj=True))
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(f"{nicktype.capitalize()}-nick: '{nick}' -> '{repl}'")
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(f"No nicks found matching '{self.lhs}'")
            return

        if not self.rhs and self.lhs:
            # check what a nick is set to
            strings = []
            if not specified_nicktype:
                nicktypes = ("object", "account", "inputline")
            for nicktype in nicktypes:
                if nicktype == "account":
                    obj = caller.account
                else:
                    obj = caller
                nicks = utils.make_iter(obj.nicks.get(category=nicktype, return_obj=True))
                for nick in nicks:
                    _, _, nick, repl = nick.value
                    if nick.startswith(self.lhs):
                        strings.append(f"{nicktype.capitalize()}-nick: '{nick}' -> '{repl}'")
            if strings:
                caller.msg("\n".join(strings))
            else:
                caller.msg(f"No nicks found matching '{self.lhs}'")
            return

        if not self.args or not self.lhs:
            caller.msg("Usage: nick[/switches] nickname = [realname]")
            return

        # setting new nicks

        nickstring = self.lhs
        replstring = self.rhs

        if replstring == nickstring:
            caller.msg("No point in setting nick same as the string to replace...")
            return

        # check so we have a suitable nick type
        errstring = ""
        string = ""
        for nicktype in nicktypes:
            nicktypestr = f"{nicktype.capitalize()}-nick"
            old_nickstring = None
            old_replstring = None

            oldnick = caller.nicks.get(key=nickstring, category=nicktype, return_obj=True)
            if oldnick:
                _, _, old_nickstring, old_replstring = oldnick.value
            if replstring:
                # creating new nick
                errstring = ""
                if oldnick:
                    if replstring == old_replstring:
                        string += f"\nIdentical {nicktypestr.lower()} already set."
                    else:
                        string += (
                            f"\n{nicktypestr} '|w{old_nickstring}|n' updated to map to"
                            f" '|w{replstring}|n'."
                        )
                else:
                    string += f"\n{nicktypestr} '|w{nickstring}|n' mapped to '|w{replstring}|n'."
                try:
                    caller.nicks.add(nickstring, replstring, category=nicktype)
                except NickTemplateInvalid:
                    caller.msg(
                        "You must use the same $-markers both in the nick and in the replacement."
                    )
                    return
            elif old_nickstring and old_replstring:
                # just looking at the nick
                string += f"\n{nicktypestr} '|w{old_nickstring}|n' maps to '|w{old_replstring}|n'."
                errstring = ""
        string = errstring if errstring else string
        caller.msg(_cy(string))