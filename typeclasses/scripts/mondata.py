"""
Mondata - the source for all IP-specific mon information. This expects the following CSVs to exist in world/mondata:

## Master-Type-Matrix.csv
Contains the type system for the game. Fromat is a square grid, left hand attacker, top defender.
The primary cells e.g. 1->2 below, the value for type 1 attacking type 2, are multipliers, typically 0.0, 0.5, 1.0, 2.0
Colors in ---- column are evennia color code strings.
Names in --- Column must match names across top.
Names in -- and - columns are short names (4-char capital, 2-char minimal) for tags and tables
```
---  , --  , - , Type1, Type2, Type3, ----
Type1, TYP1, To, 1->1 , 1->2 , 1->3 , Color1
Type2, TYP2, Tt, 2->1 , 2->2 , 2->3 , Color2
Type3, TYP3, Th, 3->1 , 3->2 , 3->3 , Color3
```

## Master-Mon-List.csv
Contains all of the mons that a player can choose. Asterisks mark rquired fields. 

Subtypes are prefixes to the species that are permanent.
Forms are prefixes to the species that are variable.
Types must match types from the master type list.

```
Dex No.*, Subtype, Form, Species Name*, Type1*, Type 2, 
Ability1*, Ability2, Hidden Ability,
Alt Ability1, Alt Ability2, Alt Hidden Ability,
[Stat Bases] Health*, Physical Attack*, Physical Defense*, Special Attack*, Special Defense*, Speed*
```

## Master-Move-List.csv
Containes all of the moves that can be created by players.
Types must match types from the master type list.
Category should be Physical, Special, Status, or ??? [Not Implemented].
Priority should be integers from around -10 to 10. It's zero if not listed.
Nonstandard Move Types include Z-Moves and Max Moves, as well as the unselectable move Struggle.
Special moves are currently ignored and not loaded into the move database.

It's unlikely special processing will ever be created for moves.
We can do basic calculations but you'll need to understand what the move is meant to do and how it works.

```
Move No.*, Move Name*, Priority [0 Default], Type*, Category*, Uses*, Potentcy, Accuracy, Nonstandard Move Type
```

## Master-Nature-List.csv
Fairly straightforward. If favored and neglected match nothing happens. If flavors match there's no preference.
Flavors are currently not implemented.
```
Nature Name*, Favored Stat, Neglected Stat*, Favored Flavor*, Disliked Flavor*
```
"""

import csv
import os

_TYPE_MATRIX_FILE = "world/mondata/Master-Type-Matrix.csv"
_MON_LIST_FILE = "xworld/mondata/Master-Mon-List.csv"
_MOVE_LIST_FILE = "xworld/mondata/Master-Move-List.csv"
_NATURE_LIST_FILE = "xworld/mondata/Master-Nature-List.csv"

_FALLBACK_TYPE_MATRIX = [
    ["---","--","-","Fire","Water","Grass","----"],
    ["Fire","FIRE","Fr",1.0,0.5,2.0,"|[#E62829|w"],
    ["Water","WATR","Wa",2.0,1.0,0.5,"|[#2980EF|w"],
    ["Grass","GRAS","Gs",0.5,2.0,1.0,"|[#3FA129|w"],
]

_FALLBACK_MON_LIST = [
    "1","","","Plant Monster","Grass","","Grass Ability","","Hidden Ability","","","","40","40","40","60","60","40"
    "2","","","Fire Winger","Fire","","Fire Ability","","Hidden Ability","","","","30","50","40","60","50","60"
    "3","","","Water Tank","Water","","Water Ability","","Secret Ability","","","","40","40","60","50","60","40"
]

from . import Script

class MonData(Script):
    key = 'mondata'

    def at_server_start(self):
        self.load_data()

    def load_data(self):
        if os.path.exists(_TYPE_MATRIX_FILE): 
            with open(_TYPE_MATRIX_FILE) as infile:
                self.load_type_matrix(csv.reader(infile))
        else:
            self.load_type_matrix(iter(_FALLBACK_TYPE_MATRIX))

        # if os.path.exists(_MON_LIST_FILE): 
        #     with open(_MON_LIST_FILE) as infile:
        #         self.load_mon_list(csv.reader(infile))
        # else:
        #     self.load_mon_list(iter(_FALLBACK_MON_LIST))
    
    def load_type_matrix(self, csvdata):
        types = {}
        typenames = []
        typelookup = {}

        header = [cell.strip() for cell in next(csvdata)]
        if not (header[0] == '---' and header[1] == '--' and header[2] == '-', header[-1] == '----'):
            raise ValueError("Type Matrix CSV Header Bad")
        
        for type in header[3:-1]:
            if type in ['-', '--', '---', '----']:
                raise ValueError("Type Matrix CSV Header Bad")
            typenames.append(type)
        
        curtype = 0
        for row in csvdata:
            name, token, short = row[:3]
            color = row [-1]
            if name != typenames[curtype]:
                raise ValueError("Type Matrix Types Don't Match")
            curtype += 1

            vs = {x:float(y) for x,y in zip(typenames, row[3:-1])}

            newtype = {'name':name, 'token':token, 'short':short, 'color':color, 'vs':vs,
                       'colortoken':f"{color}{token:^6}|n"}
            types[name] = newtype
            typelookup[name.lower()] = name
            typelookup[token.lower()] = name
            typelookup[short.lower()] = name

        if curtype != len(typenames):
            raise ValueError("Type Matrix Types Don't Match")
        
        self.types = types
        self.typenames = typenames
        self.typelookup = typelookup




        


        
