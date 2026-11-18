"""Parse a search expression into a Criterion tree.

The grammar is the one in the SRS, section 6.4:

    expression  ::= or-expr
    or-expr     ::= and-expr { "||" and-expr }
    and-expr    ::= not-expr { "&&" not-expr }
    not-expr    ::= "!" not-expr | primary
    primary     ::= "(" expression ")" | leaf
    leaf        ::= text-test | time-test | type-test | bare-word

    text-test   ::= field "contains" string
    time-test   ::= field ("<" | ">" | "=") timestamp
    type-test   ::= "type" "=" type-name

A bare word, or a bare quoted string, means "any text field contains this",
which keeps the common case short: `milk` instead of
`content contains "milk"`.
"""

from model.criteria import (
    TIME_FIELDS,
    And,
    Criterion,
    Not,
    Or,
    TextContains,
    TimeCompare,
    TypeIs,
)
from model.errors import ValidationError

#: Fields a text test may name.
TEXT_FIELDS = ("content", "description", "name", "address", "mobile_number")

#: Fields a time test may name; keys of the four record types.
TYPE_NAMES = ("Note", "Task", "Event", "Contact")

_OPERATORS = ("&&", "||")
_COMPARISONS = {"<": "before", ">": "after", "=": "equal"}
_WORD = "word"
_QUOTED = "quoted"
_SYMBOL = "symbol"


class Token:
    """One lexical unit: a word, a quoted string, or an operator."""

    __slots__ = ("kind", "text", "position")

    def __init__(self, kind, text, position):
        self.kind = kind
        self.text = text
        self.position = position

    def __repr__(self):
        return f"Token({self.kind}, {self.text!r})"


def tokenize(expression):
    """Turn an expression into a list of Tokens, or raise ValidationError."""
    tokens = []
    index = 0

    while index < len(expression):
        character = expression[index]

        if character.isspace():
            index += 1
            continue

        if character in ('"', "'"):
            quote = character
            start = index
            index += 1
            collected = []
            while index < len(expression) and expression[index] != quote:
                collected.append(expression[index])
                index += 1
            if index >= len(expression):
                raise ValidationError(
                    f"unclosed quote starting at position {start + 1}"
                )
            index += 1
            tokens.append(Token(_QUOTED, "".join(collected), start))
            continue

        pair = expression[index : index + 2]
        if pair in _OPERATORS:
            tokens.append(Token(_SYMBOL, pair, index))
            index += 2
            continue

        if character in "()<>=!":
            tokens.append(Token(_SYMBOL, character, index))
            index += 1
            continue

        start = index
        collected = []
        while index < len(expression):
            character = expression[index]
            if character.isspace() or character in '()<>=!"\'':
                break
            if expression[index : index + 2] in _OPERATORS:
                break
            collected.append(character)
            index += 1

        tokens.append(Token(_WORD, "".join(collected), start))

    return tokens


class _Parser:
    """Recursive descent over the token list."""

    def __init__(self, tokens, source):
        self.tokens = tokens
        self.source = source
        self.position = 0

    # -- token helpers ----------------------------------------------------

    def peek(self, offset=0):
        index = self.position + offset
        return self.tokens[index] if index < len(self.tokens) else None

    def at_symbol(self, text):
        token = self.peek()
        return token is not None and token.kind == _SYMBOL and token.text == text

    def take_symbol(self, text):
        if self.at_symbol(text):
            self.position += 1
            return True
        return False

    def expect_symbol(self, text):
        if not self.take_symbol(text):
            self.fail(f"expected {text!r}")

    def at_word(self):
        token = self.peek()
        return token is not None and token.kind == _WORD

    def take_word(self):
        token = self.peek()
        if token is not None and token.kind == _WORD:
            self.position += 1
            return token.text
        return None

    def fail(self, message):
        token = self.peek()
        if token is None:
            raise ValidationError(f"{message}, but the expression ended")
        raise ValidationError(f"{message} at position {token.position + 1}")

    # -- grammar ----------------------------------------------------------

    def parse(self):
        criterion = self.parse_or()
        if self.peek() is not None:
            self.fail("unexpected trailing input")
        return criterion

    def parse_or(self):
        operands = [self.parse_and()]
        while self.take_symbol("||"):
            operands.append(self.parse_and())
        return operands[0] if len(operands) == 1 else Or(*operands)

    def parse_and(self):
        operands = [self.parse_not()]
        while self.take_symbol("&&"):
            operands.append(self.parse_not())
        return operands[0] if len(operands) == 1 else And(*operands)

    def parse_not(self):
        if self.take_symbol("!"):
            return Not(self.parse_not())
        return self.parse_primary()

    def parse_primary(self):
        if self.take_symbol("("):
            criterion = self.parse_or()
            self.expect_symbol(")")
            return criterion

        if self.at_symbol(")"):
            self.fail("unbalanced ')'")

        return self.parse_leaf()

    def parse_leaf(self):
        token = self.peek()

        if token is None:
            self.fail("expected a condition")

        if token.kind == _QUOTED:
            self.position += 1
            return self.any_text(token.text)

        if token.kind != _WORD:
            self.fail(f"unexpected {token.text!r}")

        word = token.text
        lowered = word.lower()

        # `type = Task`
        if lowered == "type":
            self.position += 1
            self.expect_symbol("=")
            type_name = self.take_word()
            if type_name is None:
                self.fail("expected a record type after 'type ='")
            return self.build_type(type_name)

        # `!` handled by parse_not; anything else that is a known field
        # followed by a comparator is a leaf test.
        if lowered in TIME_FIELDS:
            self.position += 1
            token = self.peek()
            if token is not None and token.kind == _WORD and token.text.lower() == "contains":
                self.fail(f"{word!r} is a time field; use <, > or =")
            return self.build_time(word)

        if lowered in TEXT_FIELDS:
            self.position += 1
            if not self.at_word() or (self.peek().text or "").lower() != "contains":
                self.fail(f"expected 'contains' after {word!r}")
            self.position += 1
            value = self.take_quoted_or_word()
            return self.any_text(value, field=word)

        # A bare word: shorthand for "any text field contains it".
        self.position += 1
        return self.any_text(word)

    def build_time(self, field):
        token = self.peek()
        if token is None or token.kind != _SYMBOL or token.text not in _COMPARISONS:
            self.fail(f"expected one of '<', '>', '=' after {field!r}")
        self.position += 1
        target = self.take_timestamp()
        return TimeCompare(field, _COMPARISONS[token.text], target)

    def build_type(self, type_name):
        for known in TYPE_NAMES:
            if known.lower() == type_name.lower():
                return TypeIs(known)
        raise ValidationError(
            f"{type_name!r} is not a record type; expected one of "
            f"{list(TYPE_NAMES)}"
        )

    def take_timestamp(self):
        """Read the rest of a timestamp: `YYYY-MM-DD HH:MM` is two tokens."""
        first = self.take_quoted_or_word()
        if not first:
            self.fail("expected a timestamp")
        if len(first) == 10 and "-" in first:
            # Date and time are separate tokens because of the space between.
            second = self.take_word()
            if second is None:
                self.fail(
                    f"expected a time after {first!r}; timestamps need "
                    f"YYYY-MM-DD HH:MM"
                )
            return f"{first} {second}"
        return first

    def take_quoted_or_word(self):
        token = self.peek()
        if token is None:
            return None
        if token.kind in (_QUOTED, _WORD):
            self.position += 1
            return token.text
        return None

    def any_text(self, value, field=None):
        """One text test when a field is named, otherwise any of the five."""
        if value is None or not value.strip():
            self.fail("the text to search for must not be empty")

        if field is not None:
            return TextContains(field, value)

        tests = [TextContains(name, value) for name in TEXT_FIELDS]
        return tests[0] if len(tests) == 1 else _AnyText(tests)


class _AnyText(Criterion):
    """Matches when any text field of a record contains the text.

    This is the shorthand form (`milk`), and it is not one of the five grammar
    leaves, so it is kept here rather than in model/criteria.py.
    """

    def __init__(self, tests):
        self.tests = tuple(tests)

    def matches(self, record):
        return any(test.matches(record) for test in self.tests)

    def describe(self):
        return f'any text contains {self.tests[0].keyword!r}'


def parse_criterion(expression):
    """Parse `expression` into a Criterion, or raise ValidationError."""
    if not isinstance(expression, str) or not expression.strip():
        raise ValidationError("a search expression must not be empty")

    tokens = tokenize(expression)
    return _Parser(tokens, expression).parse()
