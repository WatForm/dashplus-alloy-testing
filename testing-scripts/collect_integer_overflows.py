#!/usr/bin/env python3
"""Collect command-level integer-overflow observations without retaining routine logs."""

import argparse
import hashlib
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time

import config


class ReportWriter:
    """Append model checkpoints while leaving a valid JSON document between writes."""

    FOOTER = b"\n]}\n"

    def __init__(self, path, metadata):
        self.file = Path(path).open("w+b")
        self.file.write(b'{"schema_version":1,"configuration":')
        self.file.write(json.dumps(metadata, ensure_ascii=True).encode())
        self.file.write(b',"models":[')
        self.offset = self.file.tell()
        self.count = 0
        self.file.write(self.FOOTER)
        self.file.flush()

    def append(self, model):
        # Serialize before touching the last valid checkpoint.
        data = json.dumps(model, ensure_ascii=True, separators=(",", ":")).encode()
        self.file.seek(self.offset)
        self.file.write((b",\n" if self.count else b"\n") + data)
        self.offset = self.file.tell()
        self.file.write(self.FOOTER)
        self.file.truncate()
        self.file.flush()
        self.count += 1

    def close(self):
        self.file.close()


def read_tail(path, limit=8192):
    with path.open("rb") as stream:
        stream.seek(0, os.SEEK_END)
        stream.seek(max(0, stream.tell() - limit))
        return stream.read().decode("utf-8", errors="replace").strip()


def invoke(argv, directory, name, timeout, keep_artifacts=False):
    """Use argv (no shell), bounded diagnostic reads, and a process-group deadline."""
    stdout = directory / (name + ".stdout")
    stderr = directory / (name + ".stderr")
    telemetry = directory / (name + ".jsonl")
    started = time.perf_counter()
    timed_out = False
    launch_error = None
    process = None
    try:
        with stdout.open("wb") as out, stderr.open("wb") as err:
            process = subprocess.Popen(
                [*argv, "--telemetry=" + str(telemetry)],
                stdout=out, stderr=err, start_new_session=True,
            )
            try:
                process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
            except BaseException:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait()
                raise
    except OSError as error:
        launch_error = str(error)
    elapsed = time.perf_counter() - started
    events = []
    telemetry_error = None
    if telemetry.exists():
        with telemetry.open(encoding="utf-8", errors="replace") as stream:
            for line in stream:
                try:
                    event = json.loads(line)
                    if not isinstance(event, dict) or not isinstance(event.get("event"), str):
                        raise ValueError("invalid telemetry event")
                    events.append(event)
                except ValueError:
                    telemetry_error = "Malformed or interrupted telemetry"
    failures = [event for event in events if event["event"] == "failure"]
    results = [event for event in events if event["event"] == "result"]
    finished = any(event["event"] == "finished" for event in events)
    returncode = process.returncode if process else None
    reason = None
    if timed_out:
        status, reason = "timeout", f"Exceeded {timeout:g} seconds"
    elif launch_error:
        status, reason = "error", launch_error
    elif failures:
        status, reason = failures[-1]["status"], failures[-1]["reason"]
        if reason == "Parsing stopped.":
            reason = read_tail(stderr) or reason
    elif returncode != 0:
        status = "error"
        reason = read_tail(stderr) or read_tail(stdout) or f"Process exited with code {returncode}"
    elif telemetry_error or not finished:
        status, reason = "error", telemetry_error or "Missing completion telemetry; rebuild evaluation.jar"
    else:
        status = results[-1]["status"] if results else "complete"
    record = {
        "status": status, "wall_seconds": elapsed, "java_seconds": None,
        "exit_code": returncode,
    }
    if reason is not None:
        record["reason"] = reason[:2000]
    for event in events:
        if event["event"] == "timing":
            record["java_seconds"] = event["seconds"]
    output_tail = read_tail(stdout)
    if not keep_artifacts:
        for path in (stdout, stderr, telemetry):
            path.unlink(missing_ok=True)
    return record, events, output_tail


def integer_observations(events, complete):
    integer_phases = {e["phase"] for e in events if e["event"] == "integer"}
    overflow_events = [e for e in events if e["event"] == "overflow"]
    finished = next((e for e in reversed(events) if e["event"] == "finished"), None)
    # First-occurrence events survive termination. Final counts, when present, are exact.
    counts = finished["overflow_counts"] if finished else {}
    if finished is None:
        for event in overflow_events:
            counts.setdefault(event["phase"], {})[event["direction"]] = 1

    def observed(value):
        return True if value else (False if complete else None)

    integer_in_constraints = "constraints" in integer_phases
    overflow_in_constraints = any(e["phase"] == "constraints" for e in overflow_events)

    return {
        # Either kind of atom creation is integer activity; initialization is excluded.
        "integer_activity_in_constraints": observed(integer_in_constraints or overflow_in_constraints),
        "overflow_creation_observed": observed(bool(overflow_events)),
        "overflow_creation_in_constraints": observed(overflow_in_constraints),
        "overflow_counts_by_phase": counts,
        "counts_complete": finished is not None,
        "observations_complete": complete,
    }


def collect_model(model, root_index, root, directory, java_command, timeout, keep_artifacts=False):
    record = {"source_root": root_index, "path": str(model.relative_to(root)), "commands": []}
    base = [*java_command, str(model)]
    discovery, events, _ = invoke([*base, "--list-commands"], directory, "discovery", timeout, keep_artifacts)
    commands_event = next((e for e in events if e["event"] == "commands"), None)
    record["discovery"] = discovery
    if discovery["status"] != "complete" or commands_event is None:
        if discovery["status"] == "complete":
            discovery.update(status="error", reason="Missing command-discovery telemetry")
        return record
    for command in commands_event["commands"]:
        index = command["index"]
        name = "default" if index is None else f"command-{index}"
        command_dir = directory / name
        command_dir.mkdir()
        entry = {**command, "bitwidth": None}
        record["commands"].append(entry)
        selection = ["--default-only"] if index is None else [f"-cmd={index}"]
        dump, dump_events, _ = invoke(
            [*base, "-dumpInstance", *selection, "-dumpDir=" + str(command_dir)],
            command_dir, "dump", timeout, keep_artifacts,
        )
        entry["dump"] = dump
        for event in dump_events:
            if event["event"] == "instance":
                entry["bitwidth"] = event["bitwidth"]
        if dump["status"] not in {"sat", "unsat", "unsupported", "error", "timeout"}:
            dump.update(status="error", reason="Missing or invalid dump result")
        if dump["status"] != "sat":
            entry["evaluation"] = {"status": "skipped", "reason": "dump_" + dump["status"]}
            continue
        dumped = next((e for e in dump_events if e["event"] == "result" and "xml" in e), None)
        xml = Path(dumped["xml"]) if dumped else None
        if xml is None or not xml.is_file():
            dump.update(status="error", reason="SAT reported without a generated XML file")
            entry["evaluation"] = {"status": "skipped", "reason": "dump_error"}
            continue
        evaluate_selection = [] if index is None else [f"-cmd={index}"]
        evaluation, eval_events, _ = invoke(
            [*base, "-evalConstraints", "-xml=" + str(xml), *evaluate_selection],
            command_dir, "evaluation", timeout, keep_artifacts,
        )
        if evaluation["status"] not in {"true", "false", "unknown", "unsupported", "error", "timeout"}:
            evaluation.update(status="error", reason="Missing or invalid evaluation result")
        complete = evaluation["status"] in {"true", "false", "unknown"}
        evaluation["integers"] = integer_observations(eval_events, complete)
        entry["evaluation"] = evaluation
        if not keep_artifacts:
            xml.unlink()
    return record


def positive_seconds(value):
    result = float(value)
    if not math.isfinite(result) or result <= 0:
        raise argparse.ArgumentTypeError("must be a finite positive number")
    return result


def arguments(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sources", nargs="*", type=Path, help="Archive roots (default: config.sources)")
    parser.add_argument("--jar", type=Path, default=Path(__file__).resolve().parent / "../../dashplus/app/build/libs/evaluation.jar")
    parser.add_argument("--java", default="java", help="Java executable")
    parser.add_argument("--output", type=Path, default=Path("integer-overflows.json"))
    parser.add_argument("--timeout", type=positive_seconds, default=60, help="Seconds per subprocess, including discovery (default: 60)")
    parser.add_argument("--limit", type=int, help="Collect only the first N models")
    parser.add_argument("--keep-artifacts", action="store_true", help="Retain logs, telemetry and XML for diagnosis")
    args = parser.parse_args(argv)
    args.sources = [p.resolve() for p in (args.sources or map(Path, config.sources))]
    args.jar = args.jar.resolve()
    args.output = args.output.resolve()
    if not args.jar.is_file():
        parser.error(f"JAR not found: {args.jar}")
    if any(not p.is_dir() for p in args.sources):
        parser.error("Every source must be an existing directory")
    if args.limit is not None and args.limit <= 0:
        parser.error("--limit must be positive")
    if args.output.exists():
        parser.error(f"Output already exists (choose a new path): {args.output}")
    return args


def main(argv=None):
    args = arguments(argv)
    java_command = [args.java, "-ea", "-jar", str(args.jar)]
    # Fail before scanning an archive when an old JAR is accidentally selected.
    try:
        help_run = subprocess.run([*java_command, "--help"], capture_output=True, text=True, timeout=args.timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        print(f"Cannot launch evaluator: {error}", file=sys.stderr)
        return 2
    if help_run.returncode or any(flag not in help_run.stdout for flag in ("--telemetry", "--list-commands", "--default-only")):
        print("Evaluator lacks collector CLI support; rebuild evaluation.jar.", file=sys.stderr)
        return 2
    jar_digest = hashlib.sha256()
    with args.jar.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            jar_digest.update(chunk)
    metadata = {
        "source_roots": [str(root) for root in args.sources], "jar": str(args.jar),
        "jar_sha256": jar_digest.hexdigest(),
        "timeout_seconds": args.timeout, "workers": 1, "instances_per_command": 1,
        "java": args.java, "java_assertions": True,
        "solver": None, "no_overflow": None, "keep_artifacts": args.keep_artifacts,
        "model_limit": args.limit,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="integer-overflows-") as temporary:
        scratch = Path(temporary)
        # Use an empty, temporary model to obtain the actual Java solver options.
        probe_model = scratch / "settings.als"
        probe_model.write_text("run {}\n")
        probe, events, _ = invoke([*java_command, str(probe_model), "--list-commands"], scratch, "settings", args.timeout)
        settings = next((e for e in events if e["event"] == "settings"), None)
        if probe["status"] != "complete" or settings is None:
            print("Evaluator telemetry probe failed: " + probe.get("reason", probe["status"]), file=sys.stderr)
            return 2
        metadata.update(solver=settings["solver"], no_overflow=settings["no_overflow"])
        artifacts = args.output.with_suffix(".artifacts") if args.keep_artifacts else scratch / "models"
        artifacts.mkdir(exist_ok=False)
        if args.keep_artifacts:
            metadata["artifact_directory"] = str(artifacts)
        writer = ReportWriter(args.output, metadata)
        seen = set()
        try:
            for root_index, root in enumerate(args.sources):
                for model in sorted(root.rglob("*.als")):
                    if not model.is_file() or model.resolve() in seen:
                        continue
                    seen.add(model.resolve())
                    if args.limit is not None and writer.count >= args.limit:
                        return 0
                    if args.keep_artifacts:
                        directory = artifacts / str(writer.count)
                        directory.mkdir()
                        result = collect_model(model, root_index, root, directory, java_command, args.timeout, True)
                        result["artifact_directory"] = str(directory)
                    else:
                        with tempfile.TemporaryDirectory(dir=artifacts) as model_temporary:
                            result = collect_model(model, root_index, root, Path(model_temporary), java_command, args.timeout)
                    writer.append(result)
                    print(f"Collected {writer.count}: {model.relative_to(root)}", flush=True)
        except KeyboardInterrupt:
            print(f"Interrupted; {writer.count} complete models saved to {args.output}", file=sys.stderr)
            return 130
        finally:
            writer.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
