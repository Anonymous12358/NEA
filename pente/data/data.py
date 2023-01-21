"""
Functions for loading datapacks and constructing sets of rules
"""

from __future__ import annotations

import itertools
import json
from collections.abc import Collection, Sequence
from dataclasses import dataclass
from typing import Optional

import jsonschema as jsonschema
import networkx as nx
import yaml

from pente.data import deserialize
from pente.data.deserialize import DataError
from pente.data.Language import Language
from pente.game.Game import Game
from pente.game.GameState import GameState
from pente.game.Score import Score
from pente.game.rule.Restriction import Restriction
from pente.game.rule.Rule import Rule


@dataclass
class Data:
    display_name: str
    scores: list[Score]
    restrictions: list[Restriction]
    rules: list[Rule]
    dimensions: tuple[int, ...]

    def to_game(self, gamestate: Optional[GameState] = None) -> Game:
        if gamestate is None:
            return Game(self.dimensions, self.scores, self.restrictions, self.rules)
        else:
            return Game.from_gamestate(gamestate, self.dimensions, self.scores, self.restrictions, self.rules)


@dataclass(frozen=True)
class DatapackHeader:
    name: str
    dependencies: list[str]
    load_after: list[str]
    dct: dict

    def __getitem__(self, item):
        return self.dct[item]


def load_packs(names: Sequence[str], language: Language) -> Data:
    """
    Loads packs by their names, along with their dependencies, and combines their features into a Data object.
    :param names: The names of datapacks to load, in the suggested order of loading. Note that dependencies or
    load_afters may override the suggested order.
    :param language: The language in which to log.
    :returns: A Data object containing the features defined by the loaded datapacks.
    """

    schema = _load_schema(language)
    load_order = _get_load_order(names, schema, language)

    pack_names = [header.name for header in load_order]
    # Name the result by the display names of each pack that was explicitly requested, in the order they were loaded
    display_name = ", ".join(header.dct.get("display_name", header["name"])
                             for header in load_order if header.name in names)

    # Scores
    scores = {}
    for header in load_order:
        for score_dict in header.dct.get("scores", []):
            if _should_load(score_dict["name"], header, scores.keys(), pack_names, language):
                scores[score_dict["name"]] = deserialize.score(score_dict, header, language)

    # Restrictions
    restrictions = {}
    for header in load_order:
        for restr_dict in header.dct.get("restrictions", []):
            if "name" not in restr_dict:
                language.print_key("error.datapack.anonymous_restriction", pack=header.name)
                raise DataError("error.datapack.anonymous_restriction")

            if _should_load(restr_dict["name"], header, restrictions.keys(), pack_names, language):
                restrictions[restr_dict["name"]] = deserialize.restriction(restr_dict, header, language,
                                                                           scores.keys())

    # Rules
    priorities = {}
    rules = {}
    for header in load_order:
        for rule_dict in header.dct.get("rules", []):
            if _should_load(rule_dict["name"], header, rules.keys(), pack_names, language):
                priority, rule = deserialize.rule(rule_dict, header, language, scores.keys())
                priorities[rule_dict["name"]] = priority
                rules[rule_dict["name"]] = rule

    # Sort by priority
    # Stable sort so that ties are broken by insertion order, ie by datapack and listed order within datapack
    sorted_rules = _sort_rules(rules, priorities)

    # Board
    dimensions = tuple()
    for header in load_order:
        new_dimensions = header.dct.get("board", {}).get("dimensions", None)
        if new_dimensions is not None:
            dimensions = tuple(new_dimensions)

    return Data(display_name, list(scores.values()), list(restrictions.values()), sorted_rules, dimensions)


def _should_load(qualname: str, header: DatapackHeader, loaded_names: Collection[str], loaded_packs: Collection[str],
                 language: Language) -> bool:
    """
    Determines whether to load a named feature, based on whether or not it's an override.
    Raises an exception if the qualified name:
    - Isn't in the correct format
    - Isn't owned by its registerer or by one of its registerer's dependencies or load_afters
    - Is owned by a dependency or loaded load_after but doesn't override an existing name
    :param qualname: The qualified name to check
    :param header: The header of the loading datapack
    :param loaded_names: The qualified names of this type that have already been loaded
    :param loaded_packs: The names of packs that have already been loaded
    :param language: The language in which to log.
    :returns: Whether or not the name should be loaded
    """
    owner, _, name = qualname.rpartition(".")
    if owner == "" or name == "":
        language.print_key("error.datapack.unqualified_name")
        raise DataError("error.datapack.unqualified_name")

    if owner in header.dependencies:
        if qualname in loaded_names:
            return True
        else:
            language.print_key("error.datapack.invalid_override", pack=header.name, name=qualname, dependency=owner)
            raise DataError("error.datapack.invalid_override")
    elif owner in header.load_after:
        if qualname in loaded_names:
            return True
        else:
            if owner in loaded_packs:
                language.print_key("error.datapack.invalid_override", pack=header.name, name=qualname, dependency=owner)
                raise DataError("error.datapack.invalid_override")
            else:
                return False
    elif owner != header.name:
        language.print_key("error.datapack.hidden_dependency", pack=header.name, dependency=owner)
        raise DataError("error.datapack.hidden_dependency")
    # Owned by registerer
    else:
        return True


def _load_schema(language: Language) -> dict:
    # B:file-handling
    # Read the file in which the datapack schema is stored, so it can be applied to datapacks
    try:
        with open("resources/datapack/schema.yml", 'r') as schema_file:
            return yaml.safe_load(schema_file)
    except yaml.scanner.ScannerError:
        language.print_key("error.datapack.invalid_schema")
        raise
    except (FileNotFoundError, PermissionError):
        language.print_key("error.file_absent.datapack_schema")
        raise


def _get_load_order(names: Sequence[str], schema: dict, language: Language) -> list[DatapackHeader]:
    """
    Determine which datapacks should be loaded and in which order, and load their files into datapack headers.
    :param names: The names of datapacks to load, in the suggested order of loading. Dependencies of these packs will
    also be loaded. Note that dependencies or load_afters may override the suggested order.
    :param schema: The schema against which to validate datapacks.
    :param language: The language in which to log.
    :returns: The datapack headers to load, as a list in the order in which to load them.
    """
    # Record packs and dependencies
    # An edge from one pack to another means the first pack must be loaded first

    # A:graph-traversal
    # A graph maintains the dependency and load_after relationships of all registered packs
    # Standard graph algorithms can be used to find packs whose dependencies and load_afters have all been loaded, and
    # to determine if there is a circular dependency
    network = nx.DiGraph()
    headers = {}
    for name in names:
        _register_pack_and_dependencies(network, headers, name, schema, language)

    # Process load_afters
    for name1, name2 in itertools.permutations(network.nodes, 2):
        header1, header2 = headers[name1], headers[name2]
        if name1 in header2.load_after:
            network.add_edge(name1, name2)
            # Check for circular load_after
            if nx.simple_cycles(network):
                language.print_key("error.datapack.circular.load_after", pack=name1)
                raise DataError("error.datapack.circular.load_after")

    # Generate a load order by repeatedly removing final nodes
    result = []
    while len(network.nodes) > 0:
        for name in network.nodes:
            # noinspection PyCallingNonCallable
            if network.out_degree(name) == 0:
                result.append(headers[name])
                network.remove_node(name)
                break

    return result


# Side effects: modify `network` and `headers` in place
def _register_pack_and_dependencies(network: nx.DiGraph, headers: dict[str, DatapackHeader], name: str, schema: dict,
                                    language: Language):
    """
    Modify `network` to include a given datapack name, and `headers` to associate that name with a datapack header. Do
    the same for all dependencies recursively.
    """
    if name in headers:
        # Pack is already loaded, but its recorded dependencies may still need to be updated, because other packs may
        # have been added
        header = headers[name]
    else:
        header = _load_header(name, schema, language)
        headers[name] = header
        network.add_node(name)

    # Record dependencies on and from other already-loaded packs. Those with unloaded packs will be recorded when those
    # packs are loaded.
    for other_name in network:
        other_header = headers[other_name]
        if name in other_header.dependencies:
            network.add_edge(other_name, name)
        if other_header.name in header.dependencies:
            network.add_edge(name, other_name)

    # Check circular dependency
    cycles = list(nx.simple_cycles(network))
    if cycles:
        language.print_key("error.datapack.circular.dependency", pack=str(cycles[0][0]))
        raise DataError("error.datapack.circular.dependency")

    # Process dependencies
    for dependency in header.dependencies:
        # A:recursion
        # Packs may cause other packs to load recursively by dependencies. This function calls itself for each
        # dependency of this pack
        _register_pack_and_dependencies(network, headers, dependency, schema, language)


def _load_header(name: str, schema: dict, language: Language) -> DatapackHeader:
    """
    Read a datapack file and return its contents as a datapack header
    :param name: The name of the pack to load. The file name is "{name}.json".
    :param schema: The schema against which to validate the datapack, as a dictionary.
    :param language: The language in which to log.
    :returns: The datapack header.
    """
    # Get the datapack

    # B:file-handling
    # Read the file containing the datapack to load
    try:
        with open(f"resources/datapack/{name}.json", 'r') as file:
            dct = json.load(file)
    except json.JSONDecodeError:
        language.print_key("error.datapack.invalid_json", pack=name)
        raise
    except (FileNotFoundError, PermissionError):
        language.print_key("error.datapack.datapack_absent", pack=name)
        raise

    # Schema validation
    try:
        jsonschema.validate(dct, schema)
    except jsonschema.SchemaError:
        language.print_key("error.datapack.invalid_schema")
        raise
    except jsonschema.ValidationError:
        language.print_key("error.datapack.invalid_by_schema")
        raise

    if dct["name"] != name:
        language.print_key("error.datapack.inconsistent_name", file=name, pack=dct["name"])
        raise DataError("error.datapack.inconsistent_name")

    dependencies = dct.get("dependencies", [])
    load_after = dct.get("load_after", [])

    if set(dependencies) & set(load_after):
        language.print_key("warning.datapack.double_load_after", pack=dct["name"])

    return DatapackHeader(dct["name"], dependencies, load_after, dct)


# A:sorting
# Sort rules by their specified priorities to improve compatibilities of datapacks. Because there is a small range of
# possible priorities, this algorithm has time complexity O(n), better than CPython's default timsort (mergesort) for
# this usecase.
def _sort_rules(rules: dict[str, Rule], priorities: dict[str, int]) -> list[Rule]:
    categories = [[] for _ in range(max(priorities.values()) + 1)]
    for name, rule in rules.items():
        categories[priorities[name]].append(rule)
    return list(itertools.chain(*categories))
