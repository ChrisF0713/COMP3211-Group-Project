"""Unit tests for the search-expression parser."""

import unittest

from model.expression import Token, tokenize
from model import (
    And,
    Event,
    Note,
    Not,
    Or,
    TextContains,
    TimeCompare,
    TypeIs,
    ValidationError,
    parse_criterion,
)


class TestExpressionTokens(unittest.TestCase):
    """Lexing: quotes, operators, comparison symbols."""

    def test_quoted_string_keeps_spaces(self):
        # A quoted value is one token even when it contains spaces.
        criterion = parse_criterion('content contains "buy milk"')
        self.assertIsInstance(criterion, TextContains)
        self.assertEqual(criterion.keyword, "buy milk")

    def test_unquoted_value_stops_at_space(self):
        # An unquoted value is a single word.
        criterion = parse_criterion("name contains Alice")
        self.assertEqual(criterion.keyword, "Alice")

    def test_single_quotes_are_accepted(self):
        criterion = parse_criterion("content contains 'x y'")
        self.assertEqual(criterion.keyword, "x y")

    def test_unclosed_quote_is_rejected(self):
        with self.assertRaises(ValidationError):
            parse_criterion('content contains "milk')

    def test_empty_expression_is_rejected(self):
        for text in ("", "   "):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    parse_criterion(text)

    def test_non_string_is_rejected(self):
        for value in (None, 42, []):
            with self.subTest(value=value):
                with self.assertRaises(ValidationError):
                    parse_criterion(value)


class TestExpressionLeaves(unittest.TestCase):
    """The three leaf kinds plus the bare-word shorthand."""

    def test_text_test(self):
        criterion = parse_criterion('description contains "report"')
        self.assertIsInstance(criterion, TextContains)
        self.assertEqual(criterion.field, "description")

    def test_time_test_operators(self):
        for symbol, operator in (("<", "before"), (">", "after"), ("=", "equal")):
            with self.subTest(symbol=symbol):
                criterion = parse_criterion(f"deadline {symbol} 2026-11-20 18:00")
                self.assertIsInstance(criterion, TimeCompare)
                self.assertEqual(criterion.operator, operator)

    def test_type_test_is_case_insensitive(self):
        # `type = task` and `type = Task` must mean the same thing.
        self.assertTrue(parse_criterion("type = task").matches(
            __import__("model").Task("x", "2026-11-20 18:00")))
        self.assertTrue(parse_criterion("type = Task").matches(
            __import__("model").Task("x", "2026-11-20 18:00")))

    def test_bare_word_matches_any_text_field(self):
        # The shorthand form searches all five text fields.
        criterion = parse_criterion("milk")
        self.assertTrue(criterion.matches(Note("buy milk")))
        self.assertFalse(criterion.matches(Note("buy bread")))

    def test_bare_word_does_not_match_times(self):
        # The shorthand is a text test only; it must not match a deadline.
        criterion = parse_criterion("2026-11-20")
        self.assertFalse(criterion.matches(
            __import__("model").Task("x", "2026-11-20 18:00")))

    def test_quoted_bare_string_is_a_text_test(self):
        criterion = parse_criterion('"buy milk"')
        self.assertTrue(criterion.matches(Note("I want to buy milk today")))


class TestExpressionComposition(unittest.TestCase):
    """Precedence, brackets and negation."""

    def test_and_needs_both(self):
        criterion = parse_criterion('type = Task && description contains report')
        self.assertIsInstance(criterion, And)

    def test_or_needs_either(self):
        criterion = parse_criterion("type = Task || type = Note")
        self.assertIsInstance(criterion, Or)

    def test_not_inverts(self):
        criterion = parse_criterion("!type = Note")
        self.assertIsInstance(criterion, Not)

    def test_double_negation_cancels(self):
        criterion = parse_criterion("!!type = Note")
        self.assertTrue(criterion.matches(Note("x")))

    def test_and_binds_tighter_than_or(self):
        # a || b && c  parses as  a || (b && c), so a lone `a` still matches.
        criterion = parse_criterion("type = Note || type = Task && type = Event")
        self.assertTrue(criterion.matches(Note("x")))

    def test_brackets_override_precedence(self):
        # (a || b) && c  requires c as well, so a lone note does not match.
        criterion = parse_criterion("(type = Note || type = Task) && type = Event")
        self.assertFalse(criterion.matches(Note("x")))

    def test_three_operands_chain(self):
        criterion = parse_criterion("type = Note || type = Task || type = Event")
        self.assertIsInstance(criterion, Or)
        self.assertEqual(len(criterion.operands), 3)

    def test_comparison_against_a_real_record(self):
        event = Event("meet", "2026-11-20 14:00", "2026-11-20 13:30")
        criterion = parse_criterion("starting_time > 2026-11-20 13:00")
        self.assertTrue(criterion.matches(event))


class TestExpressionErrors(unittest.TestCase):
    """Every malformed form must raise ValidationError, never crash."""

    def test_malformed_forms_are_rejected(self):
        forms = [
            "type =",
            "type = Alien",
            "type Task",
            'content "milk"',
            "deadline contains x",
            "deadline <",
            "deadline < tomorrow",
            "(type = Task",
            "type = Task)",
            "&&",
            "||",
            "content contains",
            "type = Task &&",
            "!",
            'content contains ""',
        ]
        for text in forms:
            with self.subTest(text=text):
                with self.assertRaises(ValidationError):
                    parse_criterion(text)

    def test_misspelled_field_names_are_reported_as_such(self):
        # A typo used to read as a bare-word search, so the operator after it was
        # reported as "trailing input" - a message that names nothing useful.
        for text, word in (
            ("alram < 2030-10-29 11:11", "alram"),
            ("dealines < 2030-10-29 11:11", "dealines"),
            ("starting_tim > 2030-10-29 11:11", "starting_tim"),
            ("descriptoin contains x", "descriptoin"),
            ("nmae contains Ali", "nmae"),
        ):
            with self.subTest(text=text):
                with self.assertRaises(ValidationError) as caught:
                    parse_criterion(text)
                message = str(caught.exception)
                self.assertIn(word, message)
                self.assertIn("not a field name", message)
                # The message lists what is accepted, so the typo can be fixed.
                self.assertIn("deadline", message)
                self.assertIn("starting_time", message)

    def test_a_bare_word_followed_by_nothing_still_searches(self):
        # The shorthand must not be broken by the field-name check above.
        for text in ("milk", "bread", '"buy milk"', "milk || bread"):
            with self.subTest(text=text):
                parse_criterion(text)

    def test_time_field_rejects_contains(self):
        # `contains` belongs to text fields only.
        with self.assertRaises(ValidationError):
            parse_criterion("deadline contains x")

    def test_unbalanced_closing_bracket(self):
        # A stray ')' where a condition is expected is reported, not ignored.
        with self.assertRaises(ValidationError):
            parse_criterion("type = Task && )")

    def test_value_missing_after_contains(self):
        # `content contains` with nothing after it must be an error.
        with self.assertRaises(ValidationError):
            parse_criterion("content contains ")

    def test_description_is_a_resolved_description(self):
        # describe() renders back in the grammar notation for display.
        criterion = parse_criterion('type = Task && content contains "x"')
        rendered = criterion.describe()
        self.assertIn("&&", rendered)
        self.assertIn("contains", rendered)

    def test_operators_need_no_spaces(self):
        # `milk&&bread` must lex as three tokens, not one word.
        criterion = parse_criterion("milk&&bread")
        self.assertIsInstance(criterion, And)
        self.assertEqual(len(criterion.operands), 2)

    def test_missing_comparator_after_time_field(self):
        # A time field followed by a value but no operator is reported.
        with self.assertRaises(ValidationError):
            parse_criterion("deadline 2026-11-20 18:00")

    def test_symbol_where_a_value_is_expected(self):
        # `deadline < && x` has an operator where the timestamp should be.
        with self.assertRaises(ValidationError):
            parse_criterion("deadline < && x")

    def test_token_repr_names_its_text(self):
        # Token carries a readable repr for debugging.

        self.assertIn("milk", repr(tokenize("milk")[0]))
        self.assertIn("symbol", repr(Token("symbol", "&&", 0)))


if __name__ == "__main__":
    unittest.main()
