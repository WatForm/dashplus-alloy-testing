"""Collector orchestration tests; no archive or Java build is required."""

import json
from pathlib import Path
import sys
import tempfile
import time
import unittest

from collect_integer_overflows import ReportWriter, collect_model, integer_observations, invoke


class CollectorTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="collector test ")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)

    def program(self, body):
        script = self.directory / "fake evaluator.py"
        script.write_text(
            "import json, pathlib, sys, time, subprocess\n"
            "telemetry = pathlib.Path(next(a.split('=', 1)[1] for a in sys.argv if a.startswith('--telemetry=')))\n"
            "stream = telemetry.open('w')\n"
            "def emit(event, **fields):\n"
            " stream.write(json.dumps(dict(event=event, **fields)) + '\\n'); stream.flush()\n"
            "emit('started')\n" + body
        )
        return [sys.executable, str(script)]

    def test_integer_activity_includes_overflows_and_excludes_initialization(self):
        initialization = [
            {"event": "integer", "phase": "initialization"},
            {"event": "overflow", "phase": "initialization", "direction": "OVERFLOW_UP"},
        ]
        for complete in (False, True):
            for integer, overflow in ((False, False), (True, False), (False, True), (True, True)):
                with self.subTest(complete=complete, integer=integer, overflow=overflow):
                    events = list(initialization)
                    if integer:
                        events.append({"event": "integer", "phase": "constraints"})
                    if overflow:
                        events.append({"event": "overflow", "phase": "constraints", "direction": "OVERFLOW_UP"})
                    evidence = integer_observations(events, complete)
                    expected = True if integer or overflow else (False if complete else None)
                    self.assertIs(expected, evidence["integer_activity_in_constraints"])

    def test_timeout_preserves_signals_and_kills_descendants(self):
        marker = self.directory / "child survived"
        command = self.program(
            "emit('integer', phase='initialization')\n"
            "emit('overflow', phase='constraints', direction='OVERFLOW_UP')\n"
            f"subprocess.Popen([sys.executable, '-c', {('import time, pathlib; time.sleep(0.8); pathlib.Path(' + repr(str(marker)) + ').touch()')!r}])\n"
            "time.sleep(10)\n"
        )
        result, events, _ = invoke(command, self.directory, "timeout", 0.4)
        self.assertEqual("timeout", result["status"])
        self.assertGreaterEqual(result["wall_seconds"], 0.4)
        self.assertLess(result["wall_seconds"], 3)
        self.assertIsNone(result["java_seconds"])
        evidence = integer_observations(events, False)
        self.assertTrue(evidence["overflow_creation_in_constraints"])
        self.assertTrue(evidence["integer_activity_in_constraints"])
        self.assertFalse(evidence["counts_complete"])
        self.assertFalse(list(self.directory.glob("timeout.*")))
        time.sleep(0.9)
        self.assertFalse(marker.exists(), "descendant survived the process-group timeout")

    def test_each_command_gets_independent_dump_and_evaluation(self):
        command = self.program(
            "if '--list-commands' in sys.argv:\n"
            " emit('commands', commands=[dict(index=None, text='run {}', kind='run'), dict(index=0, text='run { false }', kind='run'), dict(index=1, text='check p', kind='check')])\n"
            "elif '-dumpInstance' in sys.argv:\n"
            " emit('instance', bitwidth=4)\n"
            " if '-cmd=0' in sys.argv: emit('result', status='unsat')\n"
            " else:\n"
            "  xml = telemetry.parent / 'instance.xml'; xml.touch()\n"
            "  emit('result', status='sat', xml=str(xml))\n"
            " emit('timing', phase='generation', seconds=0.2)\n"
            "else:\n"
            " emit('integer', phase='initialization')\n"
            " if '-cmd=1' in sys.argv:\n"
            "  emit('overflow', phase='constraints', direction='OVERFLOW_UP')\n"
            "  emit('result', status='unknown')\n"
            " else: emit('result', status='true')\n"
            " emit('timing', phase='evaluation', seconds=0.1)\n"
            "emit('finished', integer_counts={'initialization': 46}, overflow_counts={})\n"
        )
        model = self.directory / "model with spaces.als"
        model.touch()
        result = collect_model(model, 0, self.directory, self.directory, command, 5)
        default, unsat, check = result["commands"]
        self.assertEqual("true", default["evaluation"]["status"])
        self.assertFalse(default["evaluation"]["integers"]["integer_activity_in_constraints"])
        self.assertEqual("unsat", unsat["dump"]["status"])
        self.assertEqual("skipped", unsat["evaluation"]["status"])
        self.assertEqual("unknown", check["evaluation"]["status"])
        self.assertTrue(check["evaluation"]["integers"]["overflow_creation_observed"])
        self.assertEqual(4, check["bitwidth"])
        self.assertEqual(0.2, check["dump"]["java_seconds"])
        self.assertEqual(0.1, check["evaluation"]["java_seconds"])
        self.assertFalse(list(self.directory.rglob("*.xml")))
        self.assertFalse(list(self.directory.rglob("*.jsonl")))

    def test_failure_reason_survives_without_retaining_logs(self):
        command = self.program(
            "emit('failure', status='unsupported', reason='unsupported expression')\n"
            "emit('finished', integer_counts={}, overflow_counts={})\n"
            "sys.exit(1)\n"
        )
        result, _, _ = invoke(command, self.directory, "unsupported", 5)
        self.assertEqual("unsupported", result["status"])
        self.assertEqual("unsupported expression", result["reason"])
        self.assertFalse(list(self.directory.glob("unsupported.*")))

    def test_malformed_telemetry_is_an_error(self):
        command = self.program("stream.write('{broken'); stream.flush()\n")
        result, _, _ = invoke(command, self.directory, "malformed", 5)
        self.assertEqual("error", result["status"])
        self.assertIn("telemetry", result["reason"])

    def test_crash_diagnostics_are_bounded(self):
        command = self.program("sys.stderr.write('x' * 100000); sys.exit(9)\n")
        result, _, _ = invoke(command, self.directory, "crash", 5)
        self.assertEqual("error", result["status"])
        self.assertEqual(9, result["exit_code"])
        self.assertLessEqual(len(result["reason"]), 2000)

    def test_keep_artifacts_is_opt_in(self):
        command = self.program("emit('finished', integer_counts={}, overflow_counts={})\n")
        invoke(command, self.directory, "retained", 5, keep_artifacts=True)
        self.assertEqual(3, len(list(self.directory.glob("retained.*"))))

    def test_missing_executable_is_recorded(self):
        result, _, _ = invoke([str(self.directory / "missing")], self.directory, "launch", 5)
        self.assertEqual("error", result["status"])
        self.assertIsNone(result["exit_code"])
        self.assertIn("reason", result)

    def test_each_model_checkpoint_is_valid_json(self):
        path = self.directory / "report.json"
        writer = ReportWriter(path, {"workers": 1})
        self.addCleanup(writer.close)
        self.assertEqual([], json.loads(path.read_text())["models"])
        models = [{"path": "a/model.als"}, {"path": "b/model.als"}]
        for index, model in enumerate(models):
            writer.append(model)
            self.assertEqual(models[:index + 1], json.loads(path.read_text())["models"])

    def test_built_evaluator_integration(self):
        jar = (Path(__file__).resolve().parent / "../../dashplus/app/build/libs/evaluation.jar").resolve()
        if not jar.is_file():
            self.skipTest("Build the sister project's evaluation.jar for CLI integration coverage")
        model = self.directory / "real model.als"
        model.write_text(
            "sig A {}\n"
            "run { some A } for 2\n"
            "run { some A and no A } for 2\n"
            "assert empty { no A }\n"
            "check empty for 2\n"
            "run { plus[7, 1] = -8 } for 4 Int\n"
            "run { plus[7, 1] = plus[7, 1] } for 4 Int\n"
            "run { #Int = #Int } for 4 Int\n"
            "run { some s: set A | some s } for 2\n"
        )
        result = collect_model(model, 0, self.directory, self.directory, ["java", "-ea", "-jar", str(jar)], 60)
        self.assertEqual("complete", result["discovery"]["status"])
        default, sat, unsat, check, overflow, unknown, overflow_only, unsupported = result["commands"]
        self.assertIsNone(default["index"])
        self.assertEqual("true", default["evaluation"]["status"])
        self.assertFalse(default["evaluation"]["integers"]["integer_activity_in_constraints"])
        self.assertEqual("sat", sat["dump"]["status"])
        self.assertEqual("true", sat["evaluation"]["status"])
        self.assertEqual("unsat", unsat["dump"]["status"])
        self.assertEqual("skipped", unsat["evaluation"]["status"])
        self.assertEqual("check", check["kind"])
        self.assertEqual("true", check["evaluation"]["status"])
        self.assertEqual("sat", overflow["dump"]["status"])
        self.assertEqual("false", overflow["evaluation"]["status"])
        self.assertEqual(4, overflow["bitwidth"])
        self.assertEqual({"constraints": {"OVERFLOW_UP": 1}}, overflow["evaluation"]["integers"]["overflow_counts_by_phase"])
        self.assertEqual("unknown", unknown["evaluation"]["status"])
        self.assertEqual("unknown", overflow_only["evaluation"]["status"])
        self.assertTrue(overflow_only["evaluation"]["integers"]["overflow_creation_in_constraints"])
        self.assertTrue(overflow_only["evaluation"]["integers"]["integer_activity_in_constraints"])
        self.assertEqual("unsupported", unsupported["evaluation"]["status"])
        self.assertIn("multiplicity", unsupported["evaluation"]["reason"])
        self.assertGreater(overflow["dump"]["java_seconds"], 0)
        self.assertGreater(overflow["evaluation"]["wall_seconds"], overflow["evaluation"]["java_seconds"])
        self.assertFalse(list(self.directory.rglob("*.xml")))
        self.assertFalse(list(self.directory.rglob("*.jsonl")))


if __name__ == "__main__":
    unittest.main()
