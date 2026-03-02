# It's a prototype!

This is an early prototype of a MUSH/MUCK game built on the [evennia](https://github.com/evennia/evennia/) engine.
Not much here for public consumption as of yet.
I'm just making this public to make things easier.

---Weaver

# Todo list!

- Transform %r and co into evennia |/ and such before they get stored in the database. Also parse
  them more globally.
- Probably need to customize all of the emitting functions anyway.
    - Third person command output for everyone
    - Name colors on command output
    - Semicolon command for portability
    - Spoof command
    - Change RP trap system to use time since someone emitted text into a room rather than their unidle presence
    - Implement separate comms idle time perhaps
- Character creation system
- Stats.
    - Pokémon type
    - Pokémon 6 stats
        - Base Stats
        - Level 
        - IVs
        - EVs
        - Nature
        - Computed Stats
    - Elemental Types
    - Known moves
    - Equipped moves
        - Move object?
    - IC Wordcount
    - Affiliation
- Read Pokémon data from a CSV
    - Couple of basic emergency failovers in case can't find CSV
    - But don't want IP stuff in the repo
- Nature matrix? Also CSV?
- Type matrix (CSV?)



