from __future__ import annotations

import itertools
import json
from collections.abc import Collection, Sequence
from dataclasses import dataclass

import jsonschema as jsonschema
import networkx as nx
import yaml

from pente.data import deserialize
from pente.data.deserialize import DataError, DatapackHeader
from pente.data.Language import Language
from pente.game.Game import Game
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

    @staticmethod
    def load_packs(names: Sequence[str], language: Language) -> Data:
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
                    restrictions[restr_dict["name"]] = deserialize.restriction(restr_dict, header, language, scores.keys())

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
        sorted_rules = [v for k, v in sorted(rules.items(), key=lambda k, v: priorities[k])]

        dimensions = tuple()
        for header in load_order:
            new_dimensions = header.dct.get("board", {}).get("dimensions", None)
            if new_dimensions is not None:
                dimensions = tuple(new_dimensions)

        return Data(display_name, list(scores.values()), list(restrictions.values()), sorted_rules, dimensions)

    def to_game(self) -> Game:
        return Game(self.dimensions, self.scores, self.restrictions, self.rules)


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
    :param language: The language in which to log errors
    :returns: Whether or not the name should be loaded
    """
    owner, _, name = qualname.rpartition(".")
    if owner == "" or name == "":
        language.print_key("error.datapack.unqualified_name")
        raise DataError

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
    try:
        with open("../../resources/datapack/schema.yml", 'r') as schema_file:
            return yaml.safe_load(schema_file)
    except (FileNotFoundError, PermissionError):
        language.print_key("error.file_absent.datapack_schema")
        raise


def _get_load_order(names: Sequence[str], schema: dict, language: Language) -> list[DatapackHeader]:
    # Record packs and dependencies
    # An edge from one pack to another means the first pack must be loaded first
    network = nx.DiGraph()
    for name in names:
        _register_pack_and_dependencies(network, name, schema, language)

    # Process load_afters
    for header1, header2 in itertools.permutations(network.nodes, 2):
        if header1.name in header2.load_after:
            network.add_edge(header1, header2)
            # Check for circular load_after
            if nx.simple_cycles(network):
                language.print_key("error.datapack.circular.load_after", pack=header1.name)
                raise DataError("error.datapack.circular.load_after")

    # Generate a load order by repeatedly removing initial nodes
    result = []
    while len(network.nodes) > 0:
        for header in network.nodes:
            # noinspection PyCallingNonCallable
            if network.in_degree(header) == 0:
                result.append(header)
                network.remove_node(header)
                break

    return result


# Side effects: modify `network` in place
def _register_pack_and_dependencies(network: nx.DiGraph, name: str, schema: dict, language: Language):
    header = _load_header(name, schema, language)
    network.add_node(header)

    # Record dependencies
    for other_header in network:
        if name in other_header.dependencies:
            network.add_edge(other_header, header)
        if other_header.name in header.dependencies:
            network.add_edge(header, other_header)

    # Check circular dependency
    cycles = nx.simple_cycles(network)
    if cycles:
        language.print_key("error.datapack.circular.dependency", pack=str(cycles[0][0]))
        raise DataError("error.datapack.circular.dependency")

    # Process dependencies
    for dependency in header.dependencies:
        _register_pack_and_dependencies(network, dependency, schema, language)


def _load_header(name: str, schema: dict, language: Language) -> DatapackHeader:
    try:
        with open(f"resources/lang/{name}.json", 'r') as file:
            try:
                dct = json.load(file)
            except json.JSONDecodeError:
                language.print_key("error.datapack.invalid_json", pack=name)
                raise
    except (FileNotFoundError, PermissionError):
        language.print_key("error.datapack.datapack_absent", pack=name)
        raise

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
