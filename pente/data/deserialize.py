from dataclasses import dataclass
from enum import IntEnum
from typing import Collection

from pente.data.Language import Language
from pente.game.Score import Score
from pente.game.rule.BoardAction import BoardAction
from pente.game.rule.Condition import Condition, ScoreCondition, CoordsCondition
from pente.game.rule.Pattern import Pattern
from pente.game.rule.Restriction import PatternRestriction, DisjunctionRestriction, Restriction
from pente.game.rule.Rule import Rule
from pente.game.rule.ScoreAction import ScoreAction


class DataError(RuntimeError):
    pass


@dataclass(frozen=True)
class DatapackHeader:
    name: str
    dependencies: list[str]
    load_after: list[str]
    dct: dict

    def __getitem__(self, item):
        return self.dct[item]


class RulePriority(IntEnum):
    EARLIEST = 0
    EARLIER = 1
    EARLY = 2
    DEFAULT = 3
    LATE = 4
    LATER = 5
    LATEST = 6


def score(dct: dict, header: DatapackHeader, language: Language) -> Score:
    return Score(dct["name"], dct.get("display_name", None), dct.get("threshold", None))


def condition(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]) -> Condition:
    if "minimum" not in dct and "maximum" not in dct:
        language.print_key("error.datapack.no_min_or_max", pack=header["name"])
        raise DataError("error.datapack.no_min_or_max")

    return score_condition(dct, header, language, scores) if dct["type"] == "score" \
        else _coords_condition(dct, header, language)


def score_condition(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]) -> ScoreCondition:
    if dct["memo"] not in scores:
        language.print_key("error.datapack.unregistered_score", pack=header["name"], name=dct["memo"])
        raise DataError("error.datapack.unregistered_score")

    return ScoreCondition(dct["player_index"], dct["memo"], dct.get("minimum", None), dct.get("maximum", None))


def _coords_condition(dct: dict, header: DatapackHeader, language: Language) -> CoordsCondition:
    return CoordsCondition(dct["axes"], dct.get("minimum", None), dct.get("maximum", None))


def pattern(string: str, header: DatapackHeader, language: Language) -> Pattern:
    try:
        return Pattern(string)
    except ValueError:
        language.print_key("error.datapack.invalid_pattern", pack=header["name"], pattern=string)
        raise DataError("error.datapack.invalid_pattern")


def pattern_restriction(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]
                        ) -> PatternRestriction:
    pattern_ = pattern(dct["pattern"], header, language)
    conditions = [
        condition(condition_dict, header, language, scores) for condition_dict in dct.get("conditions", [])
    ]
    active_player = dct.get("active_player", None)
    negate = dct.get("negate", False)

    return PatternRestriction(pattern_, conditions, active_player, negate)


def disjunction_restriction(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]
                            ) -> DisjunctionRestriction:
    conjunctions = [
        [restriction(restriction_dict, header, language, scores) for restriction_dict in conjunction]
        for conjunction in dct["conjunctions"]
    ]
    return DisjunctionRestriction(conjunctions)


def restriction(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]) -> Restriction:
    return pattern_restriction(dct, header, language, scores) if dct["type"] == "pattern" \
        else disjunction_restriction(dct, header, language, scores)


def _score_action(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str], pattern_len: int
                  ) -> ScoreAction:
    if dct["memo"] not in scores:
        language.print_key("error.datapack.unregistered_score", pack=header["name"], name=dct["memo"])
        raise DataError("error.datapack.unregistered_score")

    if dct["player_index"] > pattern_len:
        language.print_key("error.datapack.index_out_of_pattern", pack=header.name)
        raise DataError("error.datapack.index_out_of_pattern")

    return ScoreAction(dct["player_index"], dct["memo"], dct["operation"], dct["value"])


def board_action(dct: dict, header: DatapackHeader, language: Language, pattern_len: int) -> BoardAction:
    if dct["location_index"] > pattern_len or dct["player_index"] > pattern_len:
        language.print_key("error.datapack.index_out_of_pattern", pack=header.name)
        raise DataError("error.datapack.index_out_of_pattern")

    return BoardAction(dct["location_index"], dct["player_index"])


def rule(dct: dict, header: DatapackHeader, language: Language, scores: Collection[str]) -> tuple[RulePriority, Rule]:
    pattern_ = pattern(dct["patter"], header, language)
    pattern_len = len(dct["pattern"])
    multimatch_mode = Rule.Mode[dct.get("multimatch_mode", "half").upper()]
    conditions = [
        condition(condition_dict, header, language, scores) for condition_dict in dct.get("conditions", [])
    ]
    score_actions = [_score_action(action_dict, header, language, scores, pattern_len)
                     for action_dict in dct.get("score_actions", [])]
    board_actions = [board_action(action_dict, header, language, pattern_len)
                     for action_dict in dct.get("board_actions", [])]
    active_player = dct.get("active_player", None)
    priority = RulePriority[dct.get("priority", "default").upper()]

    return priority, Rule(pattern_, multimatch_mode, conditions, score_actions, board_actions, active_player)
