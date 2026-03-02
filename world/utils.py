import re



_MU_NEWLINE_RE = re.compile(r"%[rRnN]", re.MULTILINE)
_MU_TAB_RE = re.compile(r"%[tT]", re.MULTILINE)
_MU_BLANK_RE = re.compile(r"%[bB]", re.MULTILINE)

def replace_mush_escapes(msg):
    """Handle MUSH special characters. Replaces %r->%n, %b->space, %t->spaces."""
    msg = _MU_NEWLINE_RE.sub("\n", msg)
    msg = _MU_TAB_RE.sub("    ", msg)
    msg = _MU_BLANK_RE.sub(" ", msg)
    return msg

def builder_notice(target, message):
    """Error message for builder+ accounts to see. Registers for display after command."""
    if target.permissions.check("Builder"):
        target.register_post_command_message("|[r|XBuilder Notice|n|r {}|n".format(message))

def dev_notice(target, message):
    """Error message for devloper accounts to see. Registers for display after command."""
    if target.permissions.check("Developer"):
        target.register_post_command_message("|[r|XDev Notice|n|r {}|n".format(message))

def header_two_slot(width, slot1, slot2=None, headercolor="|R", color1="|w", color2="|w"):
    """
    Fill width characters with a header line wrapped around slot1 (left) and slot2 (right).
    Slot2 is optional. If given something false, it won't be given a space.
    """

    if slot2:
        header_left = f"{headercolor}--< {color1}{slot1} {headercolor}>-"
        header_right = f"{headercolor}-< {color2}{slot2} {headercolor}>--|n"
        fill = width - len(header_left) - len(header_right) + 4*len(headercolor) + len(color1) + len(color2) + 2
    else:
        header_left = f"{headercolor}--< {color1}{slot1} {headercolor}>-"
        header_right = "|n"
        fill = width - len(header_left) + 2*len(headercolor) + len(color1)


    return "".join((header_left, "-" * fill, header_right))