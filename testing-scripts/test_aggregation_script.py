import contextlib
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from aggregation_script import filter_report, main, parse_value


class AggregationTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.report = {
            "schema_version": 1,
            "configuration": {"source_roots": ["archive"]},
            "models": [
                {"path": "a.als", "discovery": {"status": "complete"}, "commands": [
                    {"index": None, "dump": {"status": "sat"}, "evaluation": {"status": "false", "flag": False}},
                    {"index": 0, "dump": {"status": "sat"}, "evaluation": {"status": "true", "flag": True}},
                    {"index": 1, "dump": {"status": "unsat"}, "evaluation": {"status": "skipped"}},
                ]},
                {"path": "b.als", "commands": [
                    {"index": 2, "dump": {"status": "sat"}, "evaluation": {"status": "true"}},
                ]},
                {"path": "c.als", "discovery": {"status": "unsupported"}, "commands": []},
            ],
        }
        self.input = self.directory / "input report.json"
        self.input.write_text(json.dumps(self.report))
        self.output = self.directory / "output report.json"

    def run_cli(self, *arguments):
        stdout = io.StringIO()
        with contextlib.redirect_stdout(stdout):
            code = main([str(self.input), *arguments, str(self.output)])
        self.assertEqual(0, code)
        return json.loads(self.output.read_text()), stdout.getvalue()

    def test_combined_filters_prune_models_preserve_metadata_and_print_counts(self):
        result, stdout = self.run_cli("--command", "dump/status", "sat", "--command", "evaluation/status", "false")
        expected = copy.deepcopy(self.report)
        expected["models"][0]["commands"] = expected["models"][0]["commands"][:1]
        expected["models"] = expected["models"][:1]
        expected["counts"] = {"models": {"matched": 1, "total": 3}, "commands": {"matched": 1, "total": 4}}
        self.assertEqual(expected, result)
        self.assertEqual("Models: 1 matched out of 3\nCommands: 1 matched out of 4\n", stdout)

    def test_no_filters_preserve_all_data(self):
        result, stdout = self.run_cli()
        expected = {**self.report, "counts": {"models": {"matched": 3, "total": 3}, "commands": {"matched": 4, "total": 4}}}
        self.assertEqual(expected, result)
        self.assertIn("Models: 3 matched out of 3", stdout)
        self.assertIn("Commands: 4 matched out of 4", stdout)

    def test_no_matches_remove_every_model(self):
        result, stdout = self.run_cli("--command", "evaluation/status", "nonexistent")
        self.assertEqual([], result["models"])
        self.assertIn("Models: 0 matched out of 3", stdout)
        self.assertIn("0 matched out of 4", stdout)

    def test_discovery_filter_counts_models_without_commands(self):
        result, stdout = self.run_cli("--model", "discovery/status", "unsupported")
        self.assertEqual([self.report["models"][2]], result["models"])
        self.assertEqual({"models": {"matched": 1, "total": 3}, "commands": {"matched": 0, "total": 4}}, result["counts"])
        self.assertEqual("Models: 1 matched out of 3\nCommands: 0 matched out of 4\n", stdout)

    def test_model_filter_preserves_all_commands_of_matching_model(self):
        result, stdout = self.run_cli("--model", "path", "a.als")
        self.assertEqual(self.report["models"][:1], result["models"])
        self.assertIn("Models: 1 matched out of 3", stdout)
        self.assertIn("Commands: 3 matched out of 4", stdout)

    def test_discovery_and_command_filters_are_combined(self):
        self.report["models"][1]["discovery"] = {"status": "unsupported"}
        result, counts = filter_report(self.report, [("model", ["discovery", "status"], "unsupported"), ("command", ["dump", "status"], "sat")])
        self.assertEqual((3, 1, 1, 4), counts)
        self.assertEqual([self.report["models"][1]], result["models"])

    def test_scope_is_explicit_even_for_discovery(self):
        self.report["models"][0]["commands"][0]["discovery"] = {"status": "unsupported"}
        filtered, counts = filter_report(self.report, [("command", ["discovery", "status"], "unsupported")])
        self.assertEqual((3, 1, 1, 4), counts)
        self.assertEqual(self.report["models"][0]["commands"][:1], filtered["models"][0]["commands"])
        filtered, counts = filter_report(self.report, [("model", ["discovery", "status"], "unsupported")])
        self.assertEqual((3, 1, 0, 4), counts)
        self.assertEqual([self.report["models"][2]], filtered["models"])

    def test_arbitrary_model_path_and_repeated_scopes(self):
        result, stdout = self.run_cli(
            "--model", "path", "a.als",
            "--command", "dump/status", "sat",
            "--model", "discovery/status", "complete",
            "--command", "evaluation/status", "false",
        )
        self.assertEqual(self.report["models"][0]["commands"][:1], result["models"][0]["commands"])
        self.assertIn("Commands: 1 matched out of 4", stdout)
        filtered, counts = filter_report(self.report, [("command", ["path"], "a.als")])
        self.assertEqual((3, 0, 0, 4), counts)
        self.assertEqual([], filtered["models"])

    def test_counts_are_recomputed_for_the_current_input(self):
        self.report["counts"] = {"models": {"matched": 999, "total": 999}}
        filtered, _ = filter_report(self.report, [("command", ["evaluation", "status"], "false")])
        self.assertEqual({"models": {"matched": 1, "total": 3}, "commands": {"matched": 1, "total": 4}}, filtered["counts"])

    def test_missing_and_non_object_paths_do_not_match_null(self):
        for path in ["absent", "evaluation/absent", "index/absent"]:
            with self.subTest(path=path):
                result, counts = filter_report(self.report, [("command", path.split("/"), None)])
                self.assertEqual((3, 0, 0, 4), counts)
                self.assertEqual([], result["models"])
        result, _ = filter_report(self.report, [("command", ["index"], None)])
        self.assertEqual([self.report["models"][0]["commands"][0]], result["models"][0]["commands"])

    def test_types_and_recursive_equality(self):
        report = {"models": [{"commands": [{"v": v} for v in [
            "false", False, 0, True, 1, None, "null", {"a": [True]}, {"a": [1]}, 4,
        ]]}]}
        for argument, expected in [
            ("false", "false"), ("json:false", False), ("json:0", 0),
            ("json:true", True), ("json:1", 1), ("json:null", None),
            ("null", "null"), ('json:{"a":[true]}', {"a": [True]}), ("json:4.0", 4),
        ]:
            with self.subTest(argument=argument):
                filtered, counts = filter_report(report, [("command", ["v"], parse_value(argument))])
                self.assertEqual(1, counts[2])
                value = filtered["models"][0]["commands"][0]["v"]
                self.assertIs(type(expected), type(value))
                self.assertEqual(expected, value)
        self.assertEqual("json:null", parse_value("str:json:null"))
        self.assertEqual("str:value", parse_value("str:str:value"))

    def test_filtering_does_not_mutate_input(self):
        before = copy.deepcopy(self.report)
        filter_report(self.report, [("command", ["index"], None)])
        self.assertEqual(before, self.report)

    def test_invalid_arguments_and_reports_leave_no_output(self):
        cases = [
            ["--command", "dump/status"], ["--command", "dump//status", "sat"], ["--model", "/discovery/status", "unsupported"],
            ["--command", "index", "json:invalid"], ["--command", "index", "json:NaN"], ["--command", "index", "json:1e999"],
            ["dump/status", "sat"], ["--unknown", "dump/status", "sat"],
        ]
        for arguments in cases:
            with self.subTest(arguments=arguments), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main([str(self.input), *arguments, str(self.output)])
                self.assertEqual(2, error.exception.code)
                self.assertFalse(self.output.exists())
        for malformed in ['{broken', '[]', '{}', '{"models":[{}]}', '{"models":[{"commands":[null]}]}']:
            with self.subTest(report=malformed), contextlib.redirect_stderr(io.StringIO()):
                self.input.write_text(malformed)
                with self.assertRaises(SystemExit) as error:
                    main([str(self.input), str(self.output)])
                self.assertEqual(2, error.exception.code)
                self.assertFalse(self.output.exists())

    def test_existing_output_and_input_are_not_overwritten(self):
        self.output.write_text("keep this")
        for output in (self.output, self.input):
            before = output.read_bytes()
            with self.subTest(output=output), contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as error:
                    main([str(self.input), str(output)])
                self.assertEqual(2, error.exception.code)
                self.assertEqual(before, output.read_bytes())


if __name__ == "__main__":
    unittest.main()
