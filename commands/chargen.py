import math
import random

from .command import MuxCommand, Command
from evennia import GLOBAL_SCRIPTS
from evennia.utils import evtable, string_suggestions

from world.monutils import type_vuln_table, get_display_mon_name, get_display_mon_type, get_display_mon_banner

_MAX_EQUIPPED_MOVES = 6

class CmdChargenSetSpecies(Command):
    """
    Usage:
        setspecies (subtype,||subtype,form,)<species name or dex number>
    """
    key = 'setspecies'
    aliases = ['setmon']
    locks = "cmd:all()"
    help_category = "Chargen"
    
    _usage = "Usage: setspecies (subtype,||subtype,form,)<species name or dex number>"

    def func(self):
        mondata = GLOBAL_SCRIPTS.mondata
    
        target = self.caller

        if not (target.access(self.caller, "control") or target.access(self.caller, "edit")):
            # Should never happen, but
            self.caller.msg(f"You don't have permission to work on {target.name}.")
            return

        arglist = [arg.strip() for arg in self.args.split(',')]

        if len(arglist) == 3:
            subtype, form, monname = arglist
        elif len(arglist) == 2:
            subtype, monname = arglist
            form = ""
        elif len(arglist) == 1:
            monname = arglist[0]
            form, subtype = "",""
        else:
            self.caller.msg(self._usage)
            return

        if not monname:
            self.caller.msg(self._usage)

        mons = mondata.search_mons(monname,subtype,form)

        if not mons:
            subtypemsg = f" with subtype '{subtype}'" if subtype else ""
            formmsg = f" {'and' if subtypemsg else 'with'} form '{form}'" if form else ""

            dexno = None
            try:
                dexno = int(monname)
            except ValueError:
                pass

            if dexno is not None:
                self.caller.msg(f"No mons found by the dex number '{dexno}'{subtypemsg}{formmsg}")
            else:
                self.caller.msg(f"No mons found by the species name '{monname}'{subtypemsg}{formmsg}")
                suggestions = string_suggestions(monname, mondata.monnames)
                self.caller.msg(f"Did you mean any of: {', '.join(suggestions)}")
            return

        if len(mons) == 1:
            mon = mons[0]
        else:
            out = ["Found multiple matches, please chose from:"]
            for idx, mon in enumerate(mons):
                out.append(f" - {idx+1} - {get_display_mon_banner(mon)}")
            out.append(f"Select [1-{len(mons)}]:")

            answer = yield('\n'.join(out))

            try:
                answer = int(answer.strip())
            except ValueError:
                self.caller.msg("|xAborted.|n")
                return
    
            if answer-1 >= 0 and answer-1 < len(mons):
                mon = mons[answer-1]
            else:
                self.caller.msg("|xAborted.|n")
                return
            

        self.caller.msg(f"Selected {get_display_mon_banner(mon)}")

        all_abilities = [abi for abi in mon['abilities'] if abi]
        all_abilities.extend([abi for abi in mon['hidden_abilities'] if abi])

        if not all_abilities:
            ability = ""
            self.caller.msg(f"{get_display_mon_banner(mon)} has no abilities.")
        elif len(all_abilities) == 1:
            ability = all_abilities[0]
            self.caller.msg(f"{get_display_mon_banner(mon)} only has ability '{ability}', selecting it.")
        else:
            idx = 1
            choices = []
            out = [f"{get_display_mon_banner(mon)} has these abilities available:"]
            for abi in mon['abilities']: 
                if abi:
                    out.append(f" - {idx} - Ability: {abi}")
                    choices.append(abi)
                    idx += 1
            for abi in mon['hidden_abilities']: 
                if abi:
                    out.append(f" - {idx} - |bHidden|n ability: {abi}")
                    choices.append(abi)
                    idx += 1

            out.append(f"Select [1-{len(choices)}]:")

            answer = yield('\n'.join(out))

            try:
                answer = int(answer.strip())
            except ValueError:
                self.caller.msg("|xAborted.|n")
                return
    
            if answer-1 >= 0 and answer-1 < len(choices):
                ability = choices[answer-1]
            else:
                self.caller.msg("|xAborted.|n")
                return
            
            self.caller.msg(f"{ability} selected.")
    
        target.set_species(self.caller, mon, ability)

        self.caller.msg(f"{target.get_display_name(looker=self.caller)} updated.")


class CmdChargenSetNature(Command):
    """
    Usage: 
        setnature [nature]
    """
    key = 'setnature'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: setnature [nature]"

    def func(self):
        mondata = GLOBAL_SCRIPTS.mondata

        target = self.caller

        if not (target.access(self.caller, "control") or target.access(self.caller, "edit")):
            # Should never happen, but
            self.caller.msg(f"You don't have permission to work on {target.name}.")
            return

        args = self.args.strip() if self.args else ""
        
        if args:
            if args in mondata.natures:
                nature = args
            else:
                self.caller.msg(f"Nature '{args}' does not exist.")
                return
        else:
            choices = sorted(mondata.natures.keys())

            out = [f"|w -    - {'Nature':>8} - {'Favored Stat':<20} - {'Neglected Stat':<20}|n"]

            for idx, choice in enumerate(choices):
                favored = mondata.natures[choice]['favored_stat']
                neglected = mondata.natures[choice]['neglected_stat']
                if favored == neglected:
                    favored = ""
                    neglected = ""
                out.append(f" - {idx+1:2d} - {choice:>8} - |G{favored:<20}|n - |R{neglected:<20}|n")
                        
            out.append(f"Select [1-{len(choices)}]:")

            answer = yield('\n'.join(out))

            try:
                answer = int(answer.strip())
            except ValueError:
                self.caller.msg("|xAborted.|n")
                return
    
            if answer-1 >= 0 and answer-1 < len(choices):
                nature = choices[answer-1]
            else:
                self.caller.msg("|xAborted.|n")
                return
            
        self.caller.msg(f"{nature} selected.")

        target.set_nature(self.caller, mondata.natures[nature])

        self.caller.msg(f"{target.get_display_name(looker=self.caller)} updated.")


class CmdChargenBuyIVs(MuxCommand):
    """
    Usage:
        buyivs <stat> = <tokens to spend>
    """
    key = 'buyivs'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: buyivs <stat> = <tokens to spend>"

    def func(self):
        mondata = GLOBAL_SCRIPTS.mondata
    
        target = self.caller

        if not (target.access(self.caller, "control") or target.access(self.caller, "edit")):
            # Should never happen, but
            self.caller.msg(f"You don't have permission to work on {target.name}.")
            return
        
        remaining = target.ivtokens - target.ivtokens_spent
        if not remaining:
            self.caller.msg(f"{target.get_display_name(looker=self.caller)} has no IV tokens to spend.")
        
        stat = self.lhs
        amount = self.rhs

        if not (stat and amount):
            self.caller.msg(self._usage)
            return

        if stat not in mondata.lookup_statlist:
            self.msg(f"'{stat}' is not a valid stat.")
            return

        stat = mondata.lookup_statlist[stat]
        
        try:
            amount = int(amount)
        except ValueError:
            self.caller.msg(f"Tokens to spend must be a positive integer")
            return
        
        if not 0 <= amount:
            self.caller.msg(f"Tokens to spend must be a positive integer")
            return
        
        amount = min(amount,remaining)
        while amount and amount * 3 + target.ivs[stat] > 30:
            amount -= 1
        
        if not amount:
            self.caller.msg(f"{target}'s {stat} is already maxed out!")
            return
        
        question = (
            f"Spend {amount} of {target.get_display_name(looker=self.caller)}'s {remaining} " 
            f"remaining IV tokens to raise "
            f"{stat}'s IVs from {target.ivs[stat]} to {target.ivs[stat] + amount * 3}? [y/N]"
        )

        answer = yield question

        if not answer.strip().lower().startswith('y'):
            self.caller.msg("|xAborted.|n")
            return
        
        target.spend_iv_tokens(self.caller, stat, amount)

        self.caller.msg(f"{target.get_display_name(looker=self.caller)} updated.")


class CmdChargenResetIVs(MuxCommand):
    """
    Usage:
        resetivs
    """
    key = 'resetivs'
    locks = "cmd:all()"
    help_category = "Chargen"

    def func(self):

        target = self.caller

        if not any(target.ivs.values()):
            self.caller.msg(f"{target.get_display_name(self.caller)} has no ivs bought, no need to reset.")
            return

        target.reset_ivs(self.caller)

        self.caller.msg(f"{target.get_display_name(self.caller)} updated.")


class CmdChargenEquipMove(MuxCommand):
    """
    Usage:
        equipmove <move name>
    """
    key = 'equipmove'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: equipmove <move name>"

    def func(self):

        mondata = GLOBAL_SCRIPTS.mondata

        target = self.caller

        if len(target.moves_equipped) >= _MAX_EQUIPPED_MOVES:
            self.caller.msg(
                f"{target.get_display_name(self.caller)} already has "
                f"{len(target.moves_equipped)} out of {_MAX_EQUIPPED_MOVES} moves equipped."
            )
            return

        movename = self.args.strip()

        if not movename:
            self.caller.msg(self._usage)
            return
        
        movename = movename.lower()

        if movename in mondata.movelookup:
            actual_movename = mondata.movelookup[movename]
        else:
            suggestions = string_suggestions(movename, mondata.movenames)
            self.caller.msg(f"Could not find a move named '{movename}', did you mean one of {suggestions}?")
            return
        
        if actual_movename in target.moves_equipped:
            self.caller.msg(f"{target.get_display_name(self.caller)} already has {actual_movename} equipped.")
            return

        if not actual_movename in target.moves_known:
            if target.player_mode == "CG":
                target.learn_move(self.caller, actual_movename)
                self.caller.msg(
                    f"This is chargen, so {target.get_display_name(self.caller)} is "
                    f"also learning {actual_movename}."
                )
            else:
                self.caller.msg(f"{target.get_display_name(self.caller)} doesn't know the move {actual_movename}.")
                return
        
        target.equip_move(self.caller, actual_movename)
        self.caller.msg(f"{target.get_display_name(self.caller)} equipped {actual_movename}.")


class CmdChargenUnequipMove(MuxCommand):
    """
    Unequip move or show equipped moves if move name not given.

    Usage:
        unequipmove [move name]
    """
    key = 'unequipmove'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: unequipmove [move name]"

    def func(self):

        mondata = GLOBAL_SCRIPTS.mondata

        target = self.caller

        if not target.moves_equipped:
            self.caller.msg(f"No moves equipped by {target.get_display_name(self.caller)}.")
            return

        movename = self.args.strip()

        if not movename:
            self.caller.msg(
                f"{target.get_display_name(self.caller)} has these moves equipped: "
                f"{', '.join(sorted(target.moves_equipped.keys()))}."
            )
            return
        
        movename = movename.lower()

        if movename in mondata.movelookup:
            actual_movename = mondata.movelookup[movename]
        else:
            suggestions = string_suggestions(movename, mondata.movenames)
            self.caller.msg(
                f"Could not find a move named '{movename}'. "
                f"{target.get_display_name(self.caller)} has these moves equipped: "
                f"{', '.join(sorted(target.moves_equipped.keys()))}."
            )
            return
        
        if actual_movename not in target.moves_equipped:
            
            self.caller.msg(
                f"{target.get_display_name(self.caller)} doesn't have {actual_movename} equipped. "
                f"{target.get_display_name(self.caller)} has these moves equipped: "
                f"{', '.join(sorted(target.moves_equipped.keys()))}."
            )
            return

        target.unequip_move(self.caller, actual_movename)
        self.caller.msg(f"{target.get_display_name(self.caller)} unequipped {actual_movename}.")


class CmdChargenLearnMove(MuxCommand):
    """
    Usage:
        learnmove <move name>
    """
    key = 'learnmove'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: learnmove <move name>"

    def func(self):
        
        mondata = GLOBAL_SCRIPTS.mondata

        target = self.caller

        movename = self.args.strip()

        if not movename:
            self.caller.msg(self._usage)
            return
        
        movename = movename.lower()

        if movename in mondata.movelookup:
            actual_movename = mondata.movelookup[movename]
        else:
            suggestions = string_suggestions(movename, mondata.movenames)
            self.caller.msg(f"Could not find a move named '{movename}', did you mean one of {suggestions}?")
            return
        
        if actual_movename in target.moves_known:
            self.caller.msg(f"{target.get_display.name(self.caller)} doesn't know {actual_movename}")
            return

        target.learn_move(self.caller, actual_movename)
        self.caller.msg(f"{target.get_display_name(self.caller)} learned {actual_movename}.")


class CmdChargenForgetMove(MuxCommand):
    """
    Forget move or show known moves if move name not given.
    Usage:
        forgetmove [move name]
    """
    key = 'forgetmove'
    locks = "cmd:all()"
    help_category = "Chargen"

    _usage = "Usage: forgetmove [move name]"

    def func(self):

        mondata = GLOBAL_SCRIPTS.mondata

        target = self.caller

        if not target.moves_known:
            self.caller.msg(f"No moves known by {target.get_display_name(self.caller)}.")
            return

        movename = self.args.strip()

        if not movename:
            self.caller.msg(
                f"Moves {target.get_display_name(self.caller)} knows are: "
                f"{', '.join(sorted(target.moves_known))}."
            )
            return
        
        movename = movename.lower()

        if movename in mondata.movelookup:
            actual_movename = mondata.movelookup[movename]
        else:
            self.caller.msg(
                f"Could not find a move named '{movename}'. "
                f"Moves {target.get_display_name(self.caller)} knows are: {', '.join(sorted(target.moves_known))}."
            )
            return
        
        if actual_movename not in target.moves_known:
            self.caller.msg(
                f"{target.get_display_name(self.caller)} doesn't know {actual_movename}. "
                f"Moves {target.get_display_name(self.caller)} knows are: {', '.join(sorted(target.moves_known))}."
            )
            return
        
        if actual_movename in target.moves_equipped:
            target.unequip_move(self.caller, actual_movename)
            self.caller.msg(f"{target.get_display_name(self.caller)} unequips {actual_movename} to forget it.")

        target.forget_move(self.caller, actual_movename)
        self.caller.msg(f"{target.get_display_name(self.caller)} forgot {actual_movename}.")