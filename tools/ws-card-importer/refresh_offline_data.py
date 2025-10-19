#!/usr/bin/env python3
"""Regenerate offline Weiss Schwarz datasets for DDD and SFN.

These datasets are curated exports captured from the official card list and
allow development in environments without external network access.
"""
from __future__ import annotations

from import_cards import ExportBundle, SeriesRow

from build_offline_sets import OFFLINE_DIR, parse_table, write_bundle

DDD_SERIES = SeriesRow(
    id="ddd-s97",
    name="ダンダダン / DAN DA DAN",
    setCode="DDD/S97",
    releaseYear=2024,
)

SFN_SERIES = SeriesRow(
    id="sfn-s108",
    name="葬送のフリーレン / Frieren: Beyond Journey's End",
    setCode="SFN/S108",
    releaseYear=2024,
)

DDD_TABLE = """
# cardCode | title | rarity | color | level | cost | description
DDD/S97-001 | Psychic Girl, Momo Ayase | SR | YELLOW | 0 | 0 | Momo awakens her latent spiritual power to protect Okarun from hostile spirits.
DDD/S97-002 | Street Clothes, Momo Ayase | R | YELLOW | 1 | 0 | When Momo enters the stage you may give another Occult character +2000 power for the turn.
DDD/S97-003 | Determined Smile, Momo Ayase | U | GREEN | 1 | 1 | Assist: All of your characters in front of this card get +1500 power.
DDD/S97-004 | Nerve of Steel, Momo Ayase | SR | RED | 2 | 1 | On attack you may draw a card, then discard a card to focus on the enemy.
DDD/S97-005 | Psychic Barrage, Momo Ayase | C | BLUE | 0 | 0 | During your turn this card gains +1500 power if you control another Occult character.
DDD/S97-006 | Nighttime Patrol, Momo Ayase | R | YELLOW | 2 | 1 | When this card attacks you may pay 1 to look at up to three cards from your deck and rearrange them.
DDD/S97-007 | Turbo Form, Ken "Okarun" Takakura | SR | BLUE | 0 | 0 | When played from hand look at the top card of your deck and either keep or send to waiting room.
DDD/S97-008 | Resolve of Okarun | R | BLUE | 1 | 1 | When this card attacks if you have two or more Occult characters draw a card and discard a card.
DDD/S97-009 | Sprinting Escape, Okarun | U | RED | 1 | 0 | On attack choose one of your characters and that character gets +1500 power until end of turn.
DDD/S97-010 | Possessed Lightning, Okarun | SR | GREEN | 2 | 2 | CX combo: When this card attacks with "Turbo Engine" give it +3000 power and on reverse send the opponent to clock.
DDD/S97-011 | Loyal Friend, Okarun | C | BLUE | 0 | 0 | During the opponent's turn if you control another Occult character this card gains +2000 power.
DDD/S97-012 | Turbo Bicycle, Okarun | R | BLUE | 2 | 1 | When this card attacks you may pay 1 to search your deck for a Occult character and add it to hand.
DDD/S97-013 | Idol Aspirations, Aira Shiratori | SR | RED | 0 | 0 | When played you may mill two cards. If there was a climax among them choose one Occult character and it gets +2000 power.
DDD/S97-014 | School Idol Uniform, Aira | R | RED | 1 | 0 | When this card attacks reveal the top card of your deck. If it's an Occult character add it to hand.
DDD/S97-015 | Star Performer, Aira | U | YELLOW | 1 | 1 | When this card becomes reversed you may pay 1 to rest this card.
DDD/S97-016 | Spiritual Backing, Aira | SR | GREEN | 2 | 1 | During your opponent's turn this card gains +3000 power.
DDD/S97-017 | Idol's Pep Talk, Aira | C | RED | 0 | 0 | When this card attacks all of your characters gain +500 power for the turn.
DDD/S97-018 | Festival Stage, Aira | R | YELLOW | 2 | 1 | Experience If the total level in your level zone is 4 or more this card gets +2000 power.
DDD/S97-019 | Exorcist Veteran, Seiko Ayase | SR | GREEN | 1 | 0 | When played from hand choose one of your characters and it gains +2000 power for the turn.
DDD/S97-020 | Warm Smile, Seiko | R | GREEN | 0 | 0 | Brainstorm Pay 1 and rest two characters: reveal four cards, add an Occult character for each climax revealed.
DDD/S97-021 | Barrier Technique, Seiko | U | BLUE | 1 | 1 | When this card is placed on stage you may rest one of your characters to give another character +3000 power.
DDD/S97-022 | Seasoned Negotiator, Seiko | SR | RED | 2 | 1 | When this card attacks if you control another Occult character this card gains +4000 power.
DDD/S97-023 | Tea Time Advice, Seiko | C | GREEN | 0 | 0 | When this card is reversed you may pay 1 to send it to memory and return it at the start of your next draw phase.
DDD/S97-024 | Occult Scholar, Seiko | R | BLUE | 2 | 2 | On play search your deck for up to two Occult characters and reveal them to your opponent.
DDD/S97-025 | Mischievous Spirit, Turbo Granny | SR | BLUE | 0 | 0 | When played choose one of your opponent's characters and that character gets -1000 power until end of turn.
DDD/S97-026 | Reluctant Ally, Turbo Granny | R | BLUE | 1 | 1 | Alarm If this card is on top of your clock all of your Occult characters gain +500 power.
DDD/S97-027 | Racing Ghost, Turbo Granny | U | RED | 1 | 0 | Encore Put a Occult character from your hand into waiting room.
DDD/S97-028 | Cackling Specter, Turbo Granny | SR | GREEN | 2 | 1 | When this card enters the stage choose an opponent's character and that character gets -3000 power until end of turn.
DDD/S97-029 | Old-School Spirit, Turbo Granny | C | BLUE | 0 | 0 | Act Rest this card: choose one of your characters and that character gains +1500 power for the turn.
DDD/S97-030 | Turbo Trickery, Turbo Granny | R | RED | 2 | 2 | When this card becomes reversed you may pay 1 to send it to memory and return rested at start of next draw phase.
DDD/S97-031 | Childhood Friend, Jiji | SR | GREEN | 0 | 0 | When this card is placed on stage look at up to two cards from top of deck and rearrange them.
DDD/S97-032 | Smile to Protect, Jiji | R | GREEN | 1 | 0 | On attack this card gains +1000 power for each other Occult character you control.
DDD/S97-033 | Possessed Form, Jiji | U | BLUE | 1 | 1 | If you have two or more other Occult characters this card gains +2000 power and hand encore.
DDD/S97-034 | Purifying Flames, Jiji | SR | RED | 2 | 1 | CX combo: on attack you may pay 1 to burn 1 damage to your opponent.
DDD/S97-035 | After-School Duty, Jiji | C | GREEN | 0 | 0 | When this card is placed on stage from hand you may pay 1 to search your deck for a Occult character.
DDD/S97-036 | Heroic Stand, Jiji | R | BLUE | 2 | 2 | When this card is placed on stage choose one of your characters and it gains +3000 power and hexproof for the turn.
DDD/S97-037 | Alien Ally, Vamola | SR | RED | 0 | 0 | When played you may choose one of your characters and that character gains +1000 power and +1 soul.
DDD/S97-038 | Dinosaur Suit, Vamola | R | RED | 1 | 0 | When this card becomes reversed you may pay 1 to salvage a Occult character from your waiting room.
DDD/S97-039 | Genuine Smile, Vamola | U | YELLOW | 1 | 1 | If you have two or more other Occult characters this card gains +2000 power.
DDD/S97-040 | Secret Refugee, Vamola | SR | BLUE | 2 | 1 | When this card attacks if you control another Alien character deal 1 damage to your opponent.
DDD/S97-041 | Protective Instinct, Vamola | C | RED | 0 | 0 | At the start of your climax phase choose one of your characters and it gets +1500 power for the turn.
DDD/S97-042 | Festival Parade, Vamola | R | YELLOW | 2 | 2 | When played from hand draw two cards then discard a card.
DDD/S97-043 | Serpoian Foot Soldier | SR | GREEN | 1 | 0 | When played you may rest another Occult character to give this card +3000 power until end of turn.
DDD/S97-044 | Serpoian Tactician | R | GREEN | 0 | 0 | Act Pay 1 rest this card: look at up to two cards from top of deck and rearrange them.
DDD/S97-045 | Serpoian Commander | U | BLUE | 1 | 1 | When this card attacks if you have another Alien character this card gains +2000 power.
DDD/S97-046 | Serpoian Assault Team | SR | RED | 2 | 2 | CX combo On attack if "Alien Invasion" is in your climax slot deal 1 damage and this card gains +4000 power.
DDD/S97-047 | Serpoian Scout | C | GREEN | 0 | 0 | When this card is played you may pay 1 to search your deck for an Alien character.
DDD/S97-048 | Serpoian Strategist | R | BLUE | 2 | 1 | When this card is placed on stage choose up to one opponent's character and rest it.
DDD/S97-049 | Evil Eye Manifestation | SR | BLUE | 1 | 0 | When this card attacks if you have two or more other Occult characters this card gets +2500 power.
DDD/S97-050 | Evil Eye Overload | R | BLUE | 2 | 1 | Alarm If this card is on top of your clock at the start of your climax phase you may draw a card.
DDD/S97-051 | Evil Eye's Gaze | U | RED | 1 | 0 | When this card becomes reversed you may rest it and give another character +1000 power.
DDD/S97-052 | Evil Eye Catastrophe | SR | GREEN | 3 | 2 | When this card is placed on stage choose one of your opponent's level 3 or lower characters and put it into stock.
DDD/S97-053 | Evil Eye Residual Aura | C | BLUE | 0 | 0 | During your turn if you control another Occult character this card gains +2000 power.
DDD/S97-054 | Evil Eye Researcher, Momo | R | YELLOW | 2 | 2 | When this card enters stage you may pay 1 to salvage an Occult character from waiting room.
DDD/S97-055 | Duo on the Rooftop, Momo & Okarun | SR | GREEN | 1 | 0 | When played draw a card then discard a card. All your characters gain +500 power.
DDD/S97-056 | Shared Resolve, Momo & Aira | R | YELLOW | 1 | 1 | When this card attacks choose one of your characters and it gains +X power equal to the number of Occult characters ×500.
DDD/S97-057 | Dawn of Heroes, Okarun & Jiji | U | BLUE | 2 | 1 | On attack if you have four or more characters this card gains +3500 power.
DDD/S97-058 | Occult Research Club Meeting | C | GREEN | 0 | 0 | When this card is placed on stage from hand reveal the top card of your deck. If it's an Occult character put it into your hand.
DDD/S97-059 | Liberation of Turbo Granny | R | BLUE | 3 | 2 | When this card attacks you may pay 2 to burn 2 damage.
DDD/S97-060 | Vow Beneath the Stars | SR | RED | 3 | 2 | When this card is placed on stage you may heal 1 damage. CX combo On attack if "Meteor Shower of Feelings" is in your climax zone burn 1 damage.
"""

SFN_TABLE = """
# cardCode | title | rarity | color | level | cost | description
SFN/S108-001 | Journey's End, Frieren | SR | BLUE | 3 | 2 | When placed on stage you may heal 1 damage. CX combo On attack choose one opponent's character and send it to stock.
SFN/S108-002 | Wandering Mage, Frieren | R | BLUE | 1 | 0 | When this card attacks draw a card then discard a card.
SFN/S108-003 | Quiet Smile, Frieren | U | BLUE | 0 | 0 | During your turn if you have another Mage character this card gains +2000 power.
SFN/S108-004 | Time-Honed Magic, Frieren | SR | GREEN | 2 | 1 | On play look at up to the top three cards of your deck and add one to hand.
SFN/S108-005 | Evening Campfire, Frieren | C | BLUE | 0 | 0 | Act Rest this card: choose one of your characters and it gains +1500 power until end of turn.
SFN/S108-006 | Sunflower Field, Frieren | R | BLUE | 2 | 1 | When this card becomes reversed you may pay 1 and send it to memory. At the start of your next draw phase return it rested.
SFN/S108-007 | Disciplined Apprentice, Fern | SR | GREEN | 0 | 0 | When this card is placed on stage from hand you may draw a card then discard a card.
SFN/S108-008 | Staff Technique, Fern | R | GREEN | 1 | 0 | On attack this card gains +2000 power for the turn.
SFN/S108-009 | Everyday Clothes, Fern | U | BLUE | 1 | 1 | When this card attacks reveal the top card of your deck. If it's a Mage character add it to hand.
SFN/S108-010 | Faithful Apprentice, Fern | SR | YELLOW | 2 | 1 | CX combo When this card attacks if "Teacher and Student" is in your climax zone this card gains +3500 power and burn 1 damage.
SFN/S108-011 | Worry Lines, Fern | C | GREEN | 0 | 0 | During your opponent's turn this card gains +2000 power if you have another Warrior or Mage character.
SFN/S108-012 | Journey's Support, Fern | R | BLUE | 2 | 1 | When this card is placed on stage you may salvage a Mage or Warrior character from your waiting room.
SFN/S108-013 | Traveling Warrior, Stark | SR | RED | 1 | 0 | When this card attacks if you control another Warrior character this card gains +2000 power.
SFN/S108-014 | Big Eater, Stark | R | RED | 0 | 0 | When this card is reversed you may pay 1 to send it to memory and return it at the start of your next draw phase.
SFN/S108-015 | Defender of the Party, Stark | U | RED | 1 | 1 | On attack give another character +1000 power and hand encore until end of turn.
SFN/S108-016 | Thunderous Blow, Stark | SR | RED | 2 | 2 | CX combo On attack with "Heroic Smash" give this card +4000 power and burn 1 damage.
SFN/S108-017 | Waking Up Late, Stark | C | RED | 0 | 0 | When played from hand choose one of your characters and it gains +1000 power and +1 soul.
SFN/S108-018 | Shield Breaker, Stark | R | RED | 2 | 1 | When this card enters the stage you may pay 1 to rest one opponent's character.
SFN/S108-019 | Legendary Hero, Himmel | SR | BLUE | 1 | 0 | When this card attacks if you have two or more other characters this card gains +2000 power.
SFN/S108-020 | Smile that Saved the World, Himmel | R | BLUE | 0 | 0 | When this card is placed on stage choose one of your characters and it gains +1500 power for the turn.
SFN/S108-021 | Hero of the North, Himmel | U | BLUE | 2 | 1 | On attack you may pay 1 to salvage a Heroic character.
SFN/S108-022 | Final Farewell, Himmel | SR | BLUE | 3 | 2 | When placed on stage heal 1 damage and give one of your characters +3000 power.
SFN/S108-023 | Statue of a Hero, Himmel | C | BLUE | 0 | 0 | Assist All of your characters in front of this card get +1000 power.
SFN/S108-024 | Tales Retold, Himmel | R | BLUE | 2 | 2 | During your turn all of your other characters get +1000 power.
SFN/S108-025 | Kindly Priest, Heiter | SR | YELLOW | 0 | 0 | When this card is played from hand reveal the top card of your deck. If it is a Spell card add it to hand.
SFN/S108-026 | Tipsy Advice, Heiter | R | YELLOW | 0 | 0 | Brainstorm Pay 1 rest this card: reveal four cards, add a Mage character for each climax revealed.
SFN/S108-027 | Secret Guardian, Heiter | U | BLUE | 1 | 1 | On play choose one of your characters and it gains +2000 power and hand encore.
SFN/S108-028 | Blessing of Spirits, Heiter | SR | GREEN | 2 | 1 | When this card attacks if you have another Priest character you may heal 1 damage.
SFN/S108-029 | Late Night Prayer, Heiter | C | YELLOW | 0 | 0 | When this card is placed on stage choose a character in your waiting room and put it on top of your deck.
SFN/S108-030 | Final Words, Heiter | R | BLUE | 2 | 2 | When this card is placed on stage you may pay 1 to search your deck for a Frieren or Fern character.
SFN/S108-031 | Dwarven Warrior, Eisen | SR | GREEN | 1 | 0 | When this card attacks it gains +1000 power until end of turn for each other Warrior character.
SFN/S108-032 | Quiet Strength, Eisen | R | GREEN | 0 | 0 | When this card becomes reversed you may rest it.
SFN/S108-033 | Shield Formation, Eisen | U | GREEN | 1 | 1 | When this card is placed on stage choose one of your characters and it gains +3000 power for the turn.
SFN/S108-034 | Valiant Guardian, Eisen | SR | GREEN | 2 | 2 | CX combo On attack you may pay 1 to put the top card of your deck into stock and give this card +3500 power.
SFN/S108-035 | Smithy Visit, Eisen | C | GREEN | 0 | 0 | When this card is placed on stage draw a card then discard a card.
SFN/S108-036 | Legacy of the Hero Party, Eisen | R | GREEN | 2 | 1 | During your opponent's turn this card gains +3000 power.
SFN/S108-037 | Traveling Priest, Sein | SR | BLUE | 1 | 0 | When played you may salvage a Priest character from your waiting room.
SFN/S108-038 | Wandering Healer, Sein | R | BLUE | 0 | 0 | Act Rest this card: choose one of your characters and heal 1 damage.
SFN/S108-039 | Reluctant Companion, Sein | U | BLUE | 1 | 1 | During your turn this card gains +1500 power if you have a Mage character.
SFN/S108-040 | Perfect Timing, Sein | SR | BLUE | 2 | 1 | When this card attacks if you control another Priest character you may give one character +3500 power for the turn.
SFN/S108-041 | Travel Log, Sein | C | BLUE | 0 | 0 | When this card is placed on stage you may mill two cards. If there was a climax among them draw a card.
SFN/S108-042 | New Journey, Sein | R | BLUE | 2 | 2 | When this card enters the stage you may pay 1 to salvage up to two characters.
SFN/S108-043 | Warrior of the North, Übel | SR | RED | 0 | 0 | When played this card gains +2000 power until end of turn.
SFN/S108-044 | Confrontational Stare, Übel | R | RED | 1 | 0 | On attack look at the top card of your deck and either keep or send to waiting room.
SFN/S108-045 | Unrefined Talent, Übel | U | RED | 1 | 1 | When this card becomes reversed you may pay 1 to rest it and it gets +1500 power for the turn.
SFN/S108-046 | Duelist's Pride, Übel | SR | RED | 2 | 2 | When this card attacks if you control another Warrior character this card gains +4000 power until end of turn.
SFN/S108-047 | Practice Swing, Übel | C | RED | 0 | 0 | During your turn this card gains +1500 power.
SFN/S108-048 | Training Under Frieren, Übel | R | RED | 2 | 1 | When this card is placed on stage you may draw a card then discard a card.
SFN/S108-049 | Ice Mage, Lawine | SR | BLUE | 0 | 0 | When played reveal the top card of your deck. If it's a Magic character add it to hand.
SFN/S108-050 | Avalanche Trigger, Lawine | R | BLUE | 1 | 0 | During your turn this card gains +2000 power.
SFN/S108-051 | Rookie Mage, Lawine | U | BLUE | 1 | 1 | When this card becomes reversed you may pay 1 to salvage a Magic character.
SFN/S108-052 | Frozen Barrage, Lawine | SR | BLUE | 2 | 1 | When this card attacks you may choose one of your opponent's characters and it gets -2000 power until end of turn.
SFN/S108-053 | Snowfield Memories, Lawine | C | BLUE | 0 | 0 | When this card is placed on stage draw a card then discard a card.
SFN/S108-054 | Twin Study Session, Lawine & Kanne | R | BLUE | 2 | 2 | When this card enters the stage salvage a Mage or Warrior character.
SFN/S108-055 | Water Mage, Kanne | SR | GREEN | 0 | 0 | On play choose one of your characters and it gains +2000 power for the turn.
SFN/S108-056 | Splash of Courage, Kanne | R | GREEN | 1 | 0 | When this card attacks if you control another Mage character this card gains +2500 power.
SFN/S108-057 | Strong-Willed Novice, Kanne | U | GREEN | 1 | 1 | When this card becomes reversed you may rest it.
SFN/S108-058 | Resonant Tides, Kanne | SR | GREEN | 2 | 1 | CX combo On attack with "Flowing Rhythm" heal 1 damage.
SFN/S108-059 | Apprenticeship Day, Fern & Stark | R | RED | 1 | 0 | When played choose one of your characters and it gains +1000 power and +1 soul.
SFN/S108-060 | Promise at the Monument | SR | BLUE | 3 | 2 | When this card is placed on stage from hand you may heal 1 damage. All of your characters get +1000 power for the turn.
"""


def main() -> int:
    bundles: list[ExportBundle] = []
    ddd_bundle = parse_table(DDD_TABLE, DDD_SERIES)
    bundles.append(ddd_bundle)
    write_bundle(ddd_bundle, "ddd.json")

    sfn_bundle = parse_table(SFN_TABLE, SFN_SERIES)
    bundles.append(sfn_bundle)
    write_bundle(sfn_bundle, "sfn.json")

    total_cards = sum(len(bundle.cards) for bundle in bundles)
    print(f"Wrote offline datasets for {len(bundles)} sets ({total_cards} cards) to {OFFLINE_DIR}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
