# Datapacks

In addition to the built-in game of pente and its variants, it is possible to play many other games and variants using
this application. This is accomplished by defining them with datapacks. Once written, datapacks can be shared and
installed easily.

Datapacks are written in JSON, and this document assumes knowledge of JSON. It is intended to be read alongside the
datapack validation schema, which can be found in `resources/datapack/schema.yml`

## Installation

To play with a datapack:
- Put the datapack into `resources/datapack`
- Restart the game
- Type `play <name>`

## Understanding the game's structure

Datapacks work by defining features that affect the game's rules:
- Rules define what happens after a player places their stone for the turn, e.g. capturing stones or winning the game
- Restrictions define which moves are illegal
- Scores are numbers tracked for each player, and can be modified by the application of rules and checked as part of
rules and conditions

Datapacks can also define the dimensions of the board.

## Scores

Scores can be used to represent any integer associated with a player. Any number of types of score can be
declared in the `scores` array. See the schema for more detail.

## Rules

Rules define what happens after a player places their stone for the turn, e.g. capturing stones or winning the game.
Each rule defines certain conditions under which it applies, and certain actions that are taken if it does.

### Patterns

Each rule must have a pattern, which is a string, with each character representing a feature on the board. The pattern
is checked against the board in every possible orientation, and at every position that would cause the position of the
stone that was just placed for turn (hereafter, the centre) to be within the pattern.

If the pattern matches, the rule is applied with that match. If it matches multiple times, no actions are performed
until every match is found; then, each action in turn is performed for every match before the next action is considered.

The match used can determine how the rule applies.

#### Pattern syntax

The correspondence between characters and board features is as follows:

- `#` - A stone owned by any player
- `-` - An empty cell
- `.` - Any cell, whether empty or not
- Any letter `A-Z` - a stone; if a given capital letter is used multiple times, all stones matching that letter must be
owned by the same player
- Any letter `a-z` - a stone owned; if the corresponding capital letter is used, stones matching the lowercase letter
cannot be owned by the player who owns the stones matched by the capital letter

It is possible to define which cell in the match must be the centre. This is done by flanking the corresponding symbol
with square brackets (`[]`). If no such cell is specified, the pattern may match anywhere that causes it to contain the
centre.

Note that if other rules have already applied, the centre may no longer actually contain the stone placed for turn.

### Multimatch mode

Since the pattern is checked in every possible orientation, it is possible for a pattern to match multiple times. N.B. a
pattern *cannot* match multiple times with different centres in the same orientation.

`multimatch_mode` is a rule field which handles this situation:
- `all` - The rule will apply to each of its matches successively. If an application affects the board, that will be
reflected in determining whether and how the rule applies thereafter.
- `one` - The rule will only apply in the first orientation in which it matches.
- `half` (default) - If the rule has already matched in a given orientation, it won't match again in the reverse of that
orientation. This is generally preferred over `all` since `all` can cause the exact same match to occur twice for
palindromic patterns.

If conditions are present, matches that don't satisfy the conditions do not prevent other matches from being found.

The order in which orientations are checked is deterministic. Consider the difference between the coordinates of two
consecutive points on the line in which the pattern lies: e.g. for a line visiting (10, 8) immediately before (9, 8),
this difference is (-1, 0). Then the order in which orientations are checked is the ascending lexicographic order of
these difference tuples. This means that for `"multimatch_mode": "half"`, orientations pointing towards the top-left
corner are checked first.

### Conditions

Conditions restrict applications of the rule based on information outside the neighbourhood of the stone placed for
turn. The `conditions` field is a list of conditions. There are two types of conditions.

#### Score conditions

Score conditions examine a score of a player and check it against a range. See [Scores](#Scores)

The player to use is determined by the `player_index` field.
- If 0 or more, the value is used as an index into the match. The player used is the player who owns a stone at that
position. Datapacks should use the pattern to ensure there is always a stone at that position; if there isn't, an error
is thrown.
- If -1, the player used is the player who owns a stone at the centre of the match. This may not be the active player.
- If -2, the active player is used.

The `memo` field specifies the name of the score to use.

The `minimum` and `maximum` fields specify a range in which the score must lie in order for the match to apply. Each can
be omitted in order to not restrict the score in that direction, but at least one must be specified.

#### Coords conditions

Coords conditions examine the coordinates of the stone placed for turn and check them against a range.

The `axes` field is a list specifying which dimensions of the coordinates to check. For 2-dimensional boards,
the vertical dimension is 0 and the horizontal is 1.

The `minimum` and `maximum` fields specify a range in which each ordinate must lie for the match to apply. Each can be
omitted in order to not restrict the coordinates in that direction, but at least one must be specified.

### Active player

The `active_player` field specifies which player must be the active player for the rule to apply. If unspecified, the
rule can apply on any player's turn.

### Score actions

Score actions modify a player's score, either setting it to a value, increasing it by a value, or multiplying it by a
value. Since the value must be an integer, division is impossible, but subtraction is possible.

When depending on the match for an action, note that the actual stones present may have changed since the pattern was
checked, due to previous applications of the same rule.

### Board actions

Board actions place or remove a single stone on the board. Any piece already on the board is overwritten.

Score actions and board actions are stored in separate lists because, while similar, they have separate purposes.

## Restrictions

Restrictions define which moves are legal. In order for a move to be legal, it must satisfy all top-level restrictions.
Restrictions cannot make moves legal that would otherwise be illegal, such as placing a stone where one is already
present.

Top-level restrictions must be named in order to interact properly with other overrides. Child restrictions can never be
overriden so don't need to be named.

### Pattern restrictions

Pattern restrictions are similar to rules, in that they attempt to match a pattern and check conditions, and they use
the same syntax where applicable.

A pattern restriction is satisfied if the pattern matches and conditions are satisfied in at least one orientation. If
`negate` is `true`, the restriction is instead satisfied if the pattern doesn't match with conditions satisfied in any
orientation.

In the case that a restriction only needs to check conditions, it is recommended to set the pattern to `"."`. Note that
the empty pattern, `""`, cannot match because it cannot contain the center.

### Disjunction restrictions

Disjunction restrictions combine multiple restrictions through boolean logic. The `conjunctions` field is an array of
arrays of sub-restrictions. The disjunction restriction matches if and only if at least one of the sub-arrays has all of
its restrictions match. In other words, the sub-restrictions are `and`ed within each sub-array, and then the sub-arrays
are `or`ed to yield the final result.

A disjunction restriction with only one sublist in `conjunctions` can be used to group related rules under a single name
for convenience.

## Boards

The `dimensions` property defines the dimensions of the board. Any natural number of dimensions can be specified,
including 0. Support for infinitely many dimensions is planned for a future release.

The `topology` property is unused. Support for topologies is planned for a future release.

## Interaction of datapacks

Any number of datapacks can be loaded at the same time. Datapacks can affect the order of loading, cause other datapacks
to be loaded, and interact with and override features specified by other datapacks.

### load_after

Datapacks can specify other datapacks by name within the `load_after` list. If both datapacks are loaded, the specifying
datapack must load after the specified datapack. If this is not possible, loading fails. If the specified datapack is
not being loaded, `load_after` has no effect.

`load_after` should be used when a datapack contains an override for a feature registered by another datapack for
compatibility, in order to guarantee that the override is applied if needed.

### Dependencies

Specifying a datapack within the `dependencies` list has the same effect as `load_after`, and also forces the specified
datapack to load, even if it otherwise wouldn't.

Dependency should be used when a datapack builds on another, and only makes sense in the context of the other.

### Qualified named and overrides

Most features specified by datapacks are named. For scores, this allows them to be referenced by score conditions and
score actions. For all named features, this also allows them to be overriden.

Names should contain a dot (`.`), with the text before the first dot being the name of the datapack that first registers
the feature, ie the owner. For most features, the owner should be the enclosing datapack. Otherwise, the feature is
considered an override. Datapacks should only specify overrides for features owned by their dependencies or load_afters.

Overrides are only loaded if the owning datapack has already loaded a feature of that name. The overriden feature is
removed and entirely replaced with the new feature. To change only certain attributes of a feature, the entire feature
must be rewritten as an override with the changes effected.

The board is not named. The dimensions are determined by whichever datapack is last to specify them.

### Priorities

Since rules can affect which other rules apply, and datapacks do not in general know which other datapacks might be
loaded concurrently, it is useful to be able to control the order in which rules are invoked.

Rules have a `priority` field to guide the order in which they are applied. Rules are first ordered by priority;
then within each priority bracket, by the order in which the datapacks were loaded; then within each datapack, by the
order in which the rules are listed. See the schema for a list of priority tiers.

It is recommended to be as humble as possible, not using priority tiers beyond what is necessary for a datapack to work.