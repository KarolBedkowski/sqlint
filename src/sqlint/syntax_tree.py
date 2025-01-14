from __future__ import annotations

from typing import List, Optional, Generator

from .parser import Token
from .parser import parse as parse_sql


class Node:
    def __init__(self, line_num: int, tokens: List[Token] = None):
        if tokens is None:
            tokens = []

        self.line_num = line_num
        self.tokens = tokens

    @property
    def line_num(self) -> int:
        return self._line_num

    @line_num.setter
    def line_num(self, value: int):
        if value < 0:
            raise ValueError(f"line_num must be ≧ 0, but {value}")
        self._line_num = value

    @property
    def text(self):
        return "".join([x.word for x in self.tokens])

    @property
    def indent(self):
        """Returns indent size

        If this is a blank line or whitespaces does not exist at head of line,
        returns 0.

        Returns:
            indent size
        """
        if len(self.tokens) == 0:
            return 0

        head = self.tokens[0]
        if head.kind == Token.WHITESPACE:
            return len(head)

        return 0

    def __len__(self):
        return len(self.tokens)

    def __str__(self):
        return " ".join([str(tkn) for tkn in self.tokens])

    def get_position(self, index: int):
        """Returns length of texts before Nth token.

        Args:
            index: the number of tokens

        Returns:
            length of texts
        """
        index = max(index, 0)
        return sum([len(token) for token in self.tokens[0:index]]) + 1

    def append(self, token: Token):
        self.tokens.append(token)

    def extend(self, token: List[Token]):
        self.tokens.extend(token)

    def insert(self, index: int, token: Token):
        self.tokens.insert(index, token)

    def trip_kind(self, *args) -> Node:
        return self.ltrip_kind(*args).rtrip_kind(*args)

    def ltrip_kind(self, *args) -> Node:
        """

        Args:
            *args:

        Returns:

        """
        cut = -1
        for token in self.tokens:
            if token.kind in args:
                cut += 1
            else:
                break

        return Node(line_num=self.line_num, tokens=self.tokens[cut + 1 :])

    def rtrip_kind(self, *args) -> Node:
        """

        Args:
            *args:

        Returns:

        """
        cut = len(self.tokens)
        for token in reversed(self.tokens):
            if token.kind in args:
                cut -= 1
            else:
                break

        return Node(line_num=self.line_num, tokens=self.tokens[0:cut])


class SyntaxTree:
    def __init__(
        self,
        depth: int,
        line_num: int,
        tokens: List[Token] = None,
        parent: Optional[SyntaxTree] = None,
        is_abstract: bool = False,
    ):
        """

        Args:
            depth: tree depth
            parent: parent tree node
            line_num: the number of line in source sql this tokens belongs to.
            tokens: a list of tokens which is tokenized sql statemnt.
            is_abstract: If this is True, this tree is constructed abstractly.
                          Abstract tree ignores whitespaces and blank lines.

        Returns:

        """

        self._depth = depth
        self.leaves: List[SyntaxTree] = []
        self.parent: Optional[SyntaxTree] = parent
        self.node: Node = Node(line_num=line_num, tokens=tokens)
        self.is_abstract: bool = is_abstract

    @property
    def depth(self) -> int:
        return self._depth

    @depth.setter
    def depth(self, value: int) -> None:
        if value < 0:
            raise ValueError(f"depth must be ≧ 0, but {value}")
        self._depth = value

    @property
    def line_num(self) -> int:
        return self.node.line_num

    @property
    def tokens(self) -> List[Token]:
        return self.node.tokens

    @tokens.setter
    def tokens(self, value: List[Token]) -> None:
        self.node.tokens = value

    @property
    def text(self):
        return self.node.text

    @property
    def indent(self):
        """Returns indent size

        If this is a blank line or whitespaces does not exist at head of line,
        returns 0.

        Returns:
            indent size
        """

        return self.node.indent

    @classmethod
    def sqlptree(
        cls, sql: str, is_abstract: bool = False, sql_type: str = "StandardSQL"
    ) -> "SyntaxTree":
        """Returns SyntaxTree by parsing sql statement.

        Args:
            sql: sql statemtnt
            is_abstract: If this is True, this tree is constructed abstractly.
                          Abstract tree ignores whitespaces, comments and blank
                          lines.
            sql_type: target sql type (StandardSQL only now)

        Returns:
            SyntaxTree instance
        """

        # TODO: deals with other sql type.
        if sql_type != "StandardSQL":
            raise NotImplementedError(
                'this linter can parses only "StandardSQL" right now, '
                f"but {sql_type}"
            )

        token_list: List[List[Token]] = parse_sql(sql)

        # creates empty syntax tree as guard
        parent_vertex = SyntaxTree(
            depth=0, line_num=0, is_abstract=is_abstract
        )
        result = parent_vertex

        for line_num, tokens in enumerate(token_list):
            # skips the line having only whitespaces or which is blank
            if is_abstract:
                tokens = cls._ignore_token(tokens)
                if not tokens:
                    continue

            # if line is not blank, get indent size
            indent = 0
            if tokens and tokens[0].kind == Token.WHITESPACE:
                indent = len(tokens[0].word)

            # check whether parent_node is root node
            while indent <= parent_vertex.indent and 0 < parent_vertex.depth:
                assert parent_vertex.parent
                parent_vertex = parent_vertex.parent

            _tree = SyntaxTree(
                depth=parent_vertex.depth + 1,
                line_num=line_num + 1,
                tokens=tokens,
                parent=parent_vertex,
                is_abstract=is_abstract,
            )
            parent_vertex.add_leaf(_tree)
            parent_vertex = _tree

        return result

    @staticmethod
    def _ignore_token(tokens: List[Token]) -> List[Token]:
        """Returns tokens exclueded ones in abstract tree"""

        if len(tokens) == 0:
            return []

        ignore_kinds = [Token.WHITESPACE]

        return [token for token in tokens if token.kind not in ignore_kinds]

    def sqlftree(self) -> str:
        """Returns sql statement

        Returns:
            sql stetement
        """

        return "\n".join(SyntaxTree._sqlftree(self))

    @staticmethod
    def _sqlftree(tree: SyntaxTree) -> Generator[str, None, None]:
        """Returns sql statement

        Returns:
            sql statement
        """

        for leaf in tree.leaves:
            yield leaf.text
            yield from SyntaxTree._sqlftree(leaf)

    def add_leaf(self, leaf: "SyntaxTree"):
        self.leaves.append(leaf)

    def insert_leaf(self, index: int, leaf: "SyntaxTree"):
        self.leaves.insert(index, leaf)

    def get_position(self, index: int):
        """Returns length of texts at head of Nth token.

        Args:
            index: the number of tokens

        Returns:
            length of texts
        """
        return self.node.get_position(index)
