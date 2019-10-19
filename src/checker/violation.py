from typing import Dict
from enum import Enum

from src.parser.token import Token
from src.parser.syntax_tree import SyntaxTree


class Code(Enum):
    # E1: Indentation
    INDENT_STEPS = ('E101', 'indent steps must be {expected} multiples, but {actual} spaces')
    # E2: Whitespaces
    WHITESPACE_MULTIPLE = ('E201', 'there are multiple whitespaces')
    WHITESPACE_AFTER_COMMA = ('E202', 'whitespace must be after comma: {target}')
    WHITESPACE_BEFORE_COMMA = ('E203', 'whitespace must not be before comma: ,')
    WHITESPACE_AFTER_BRACKET = ('E204', 'whitespace must not be after bracket: {target}')
    WHITESPACE_BEFORE_BRACKET = ('E205', 'whitespace must not be before bracket: {target}')
    WHITESPACE_AFTER_OPERATOR = ('E206', 'whitespace must be after binary operator: {target}')
    WHITESPACE_BEFORE_OPERATOR = ('E207', 'whitespace must be before binary operator: {target}')
    # E3: Comma
    COMMA_HEAD = ('E301', 'comma must be head of line')
    COMMA_END = ('E302', 'comma must be end of line')
    # E4: Reserved Keyword
    KEYWORD_UPPER = ('E401', 'reserved keywords must be upper case: {actual} -> {expected}')
    KEYWORD_UPPER_HEAD = ('E402', 'a head of reserved keywords must be upper case: {actual} -> {expected}')
    KEYWORD_LOWER = ('E403', 'reserved keywords must be lower case: {actual} -> {expected}')
    # E5: Join Context
    JOIN_TABLE = ('E501', 'table_name must be at the same line as join context')
    JOIN_CONTEXT = ('E502', 'join context must be fully: {actual} -> {expected}')
    # E6: lines
    LINE_BlANK_MULTIPLE = ('E601', 'there are multiple blank lines')
    LINE_ONLY_WHITESPACE = ('E602', 'this line has only whitespace')
    LINE_BREAK_BEFORE = ('E603', 'expected to break line after: {target}')
    LINE_BREAK_AFTER = ('E604', 'expected to break line after: {target}')

    def __init__(self, code: str, template: str):
        """
        Args:
            code: violation code
            template: violation template message
        """
        self.code = code
        self.template = template

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, value: str):
        self._code = value

    @property
    def template(self):
        return self._template

    @template.setter
    def template(self, value: str):
        self._template = value


class Violation:
    def __init__(self, tree: SyntaxTree, pos: int, code: Code, **kwargs):
        self.tree: SyntaxTree = tree
        self.pos: int = pos
        self.code: Code = code
        self.params: Dict = kwargs

    def get_message(self):
        _template = '(L{line}, {pos}): ' + self.code.template

        return _template.format(
            line=self.tree.node.line_num,
            pos=self.pos,
            **self.params)


class IndentStepsViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.INDENT_STEPS, **kwargs)


class KeywordStyleViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        if 'style' not in kwargs:
            raise KeyError(f'style must be passed.')

        style = kwargs['style']

        if style == 'upper-all':
            _code = Code.KEYWORD_UPPER
        elif style == 'upper-head':
            _code = Code.KEYWORD_UPPER_HEAD
        elif style == 'lower':
            _code = Code.KEYWORD_LOWER
        else:
            raise ValueError('keyword style must be in [upper-all, upper-head, lower]')

        super().__init__(tree, pos, _code, **kwargs)


class CommaPositionViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, comma_position: str, **kwargs):
        self.comma_position = comma_position

        if comma_position == 'head':
            _code = Code.COMMA_HEAD
        elif comma_position == 'end':
            _code = Code.COMMA_END
        else:
            raise ValueError('position must be in [head, end]')

        super().__init__(tree, pos, _code, **kwargs)


class MultiSpacesViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.WHITESPACE_MULTIPLE, **kwargs)


class WhitespaceViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        if 'token' not in kwargs:
            raise KeyError(f'token must be passed.')
        if 'position' not in kwargs:
            raise KeyError(f'position must be passed.')

        token = kwargs['token']
        position = kwargs['position']

        # TODO: modify more simple, maybe it is better to split several classes.
        if token == Token.COMMA:
            if position == 'before':
                _code = Code.WHITESPACE_BEFORE_COMMA
            elif position == 'after':
                _code = Code.WHITESPACE_AFTER_COMMA
            else:
                raise ValueError('whitespace position must be in [before, after]')
        elif token == Token.BRACKET_LEFT:
            _code = Code.WHITESPACE_AFTER_BRACKET
        elif token == Token.BRACKET_RIGHT:
            _code = Code.WHITESPACE_BEFORE_BRACKET
        elif token == Token.OPERATOR:
            if position == 'before':
                _code = Code.WHITESPACE_BEFORE_OPERATOR
            elif position == 'after':
                _code = Code.WHITESPACE_AFTER_OPERATOR
            else:
                raise ValueError('whitespace position must be in [before, after]')
        else:
            raise ValueError('token kind must be in [{}, {}, {}, {}]'.format(
                Token.COMMA, Token.BRACKET_LEFT, Token.BRACKET_RIGHT, Token.OPERATOR))

        super().__init__(tree, pos, _code, **kwargs)


class JoinTableViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.JOIN_TABLE, **kwargs)


class JoinContextViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.JOIN_CONTEXT, **kwargs)


class MultiBlankLineViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.LINE_BlANK_MULTIPLE, **kwargs)


class OnlyWhitespaceViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, **kwargs):
        super().__init__(tree, pos, Code.LINE_ONLY_WHITESPACE, **kwargs)


class BreakingLineViolation(Violation):
    def __init__(self, tree: SyntaxTree, pos: int, position: int, **kwargs):
        if position == 'before':
            _code = Code.BREAK_LINE_BEFORE
        elif position == 'after':
            _code = Code.BREAK_LINE_AFTER
        else:
            raise ValueError('position must be in [before, after]')

        super().__init__(tree, pos, _code, **kwargs)