#!/usr/bin/env python3
"""Filter a collector report: INPUT [--model PATH VALUE | --command PATH VALUE ...] OUTPUT.

Each filter explicitly selects the model or command to search. Bare values are
strings; json:VALUE parses a JSON value, and str:VALUE forces a literal string.
Reports include matched and total counts.
Model-only filters retain matching models with no commands. Command filters
remove models with no surviving commands. No filters preserve the entire report.
"""

import argparse
import json
import math
from pathlib import Path


MISSING = object()


def reject_constant(value):
    raise ValueError(f"Invalid JSON constant: {value}")


def check_finite(value):
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("JSON numbers must be finite")
    if isinstance(value, dict):
        for item in value.values():
            check_finite(item)
    elif isinstance(value, list):
        for item in value:
            check_finite(item)


def parse_value(value):
    if value.startswith("str:"):
        return value[4:]
    if value.startswith("json:"):
        parsed = json.loads(value[5:], parse_constant=reject_constant)
        check_finite(parsed)
        return parsed
    return value


def lookup(command, path):
    value = command
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return MISSING
        value = value[key]
    return value


def json_equal(left, right):
    # JSON has one number type; Python's bool must not compare equal to 0 or 1.
    if type(left) in (int, float) and type(right) in (int, float):
        return left == right
    if type(left) is not type(right):
        return False
    if isinstance(left, dict):
        return left.keys() == right.keys() and all(
            json_equal(left[key], right[key]) for key in left
        )
    if isinstance(left, list):
        return len(left) == len(right) and all(
            json_equal(a, b) for a, b in zip(left, right)
        )
    return left == right


def filter_report(report, filters):
    if not isinstance(report, dict) or not isinstance(report.get("models"), list):
        raise ValueError("Report must be an object containing a models list")
    models = []
    model_filters = []
    command_filters = []
    for scope, path, value in filters:
        if scope == "model":
            model_filters.append((path, value))
        elif scope == "command":
            command_filters.append((path, value))
        else:
            raise ValueError(f"Unknown filter scope: {scope}")
    total_models = len(report["models"])
    total_commands = matched_commands = 0
    for index, model in enumerate(report["models"]):
        if not isinstance(model, dict) or not isinstance(model.get("commands"), list):
            raise ValueError(f"Model {index} must be an object containing a commands list")
        model_matches = all(json_equal(lookup(model, path), value) for path, value in model_filters)
        kept = []
        for command in model["commands"]:
            if not isinstance(command, dict):
                raise ValueError(f"Model {index} contains a non-object command")
            total_commands += 1
            if model_matches and all(json_equal(lookup(command, path), value) for path, value in command_filters):
                kept.append(command)
        matched_commands += len(kept)
        # Model-only filters can match models that have no commands at all.
        if model_matches and (kept or not command_filters):
            models.append({**model, "commands": kept})
    matching_models = len(models)
    filtered = {
        **report,
        "models": models,
        "counts": {
            "models": {"matched": matching_models, "total": total_models},
            "commands": {"matched": matched_commands, "total": total_commands},
        },
    }
    counts = (total_models, matching_models, matched_commands, total_commands)
    return filtered, counts


def main(argv=None):
    parser = argparse.ArgumentParser(
        description=__doc__,
        usage="%(prog)s INPUT [--model PATH VALUE | --command PATH VALUE ...] OUTPUT",
        allow_abbrev=False,
    )
    parser.add_argument("input", type=Path, help="Collector JSON report")
    parser.add_argument("--model", nargs=2, action="append", default=[], metavar=("PATH", "VALUE"), help="Match a model field; may be repeated")
    parser.add_argument("--command", nargs=2, action="append", default=[], metavar=("PATH", "VALUE"), help="Match a command field; may be repeated")
    parser.add_argument("output", type=Path, help="New output filepath")
    args = parser.parse_args(argv)
    output = args.output
    filters = []
    for scope, criteria in (("model", args.model), ("command", args.command)):
        for parameter, argument in criteria:
            path = parameter.split("/")
            if any(not key for key in path):
                parser.error(f"Invalid parameter path: {parameter!r}; empty segments are not allowed")
            try:
                value = parse_value(argument)
            except ValueError as error:
                parser.error(f"Invalid value for {parameter!r}: {error}")
            filters.append((scope, path, value))
    try:
        if output.exists():
            raise ValueError(f"Output already exists: {output}")
        with args.input.open(encoding="utf-8") as stream:
            report = json.load(stream, parse_constant=reject_constant)
        check_finite(report)
        filtered, counts = filter_report(report, filters)
        # Exclusive creation also prevents overwriting a file created during filtering.
        with output.open("x", encoding="utf-8") as stream:
            json.dump(filtered, stream, indent=2, allow_nan=False)
            stream.write("\n")
    except (OSError, UnicodeError, ValueError) as error:
        parser.error(str(error))
    models, matching_models, commands, total_commands = counts
    print(f"Models: {matching_models} matched out of {models}")
    print(f"Commands: {commands} matched out of {total_commands}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
