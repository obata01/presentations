"""深さ優先探索(DFS: Depth First Search).

以下のようなケースで有効.
- グラフの全探索
- 部分和問題


https://atcoder.jp/contests/atc001/tasks/dfs_a
"""

from utils import Input
from pprint import pprint
import textwrap
import pytest


CASES = [
    (
        textwrap.dedent("""\
        4 5
        s####
        ....#
        #####
        #...g
        """),
        "No",
    ),
    (
        textwrap.dedent("""\
        4 4
        ...s
        ....
        ....
        .g..
        """),
        "Yes",
    ),
    (
        textwrap.dedent("""\
        10 10
        s.........
        #########.
        #.......#.
        #..####.#.
        ##....#.#.
        #####.#.#.
        g.#.#.#.#.
        #.#.#.#.#.
        ###.#.#.#.
        #.....#...
        """),
        "No",
    ),
    (
        textwrap.dedent("""\
        10 10
        s.........
        #########.
        #.......#.
        #..####.#.
        ##....#.#.
        #####.#.#.
        g.#.#.#.#.
        #.#.#.#.#.
        #.#.#.#.#.
        #.....#...
        """),
        "Yes",
    ),
    (
        textwrap.dedent("""\
        1 10
        s..####..g
        """),
        "No",
    ),
]

@pytest.fixture(params=CASES, ids=[f"case{i}" for i in range(1, len(CASES) + 1)])
def case(request):
    return request.param

#############################################

def test_dfs1(case):
    data, expected = case
    input = Input(data).input

    H, W = map(int, input().split())

    S = None
    G = None

    C = [list(input()) for _ in range(H)]

    for h in range(H):
        for w, v in enumerate(C[h]):
            if v == "s":
                S = (h, w)
            if v == "g":
                G = (h, w)

    visited = [[False] * W for _ in range(H)]

    def dfs(h, w):
        visited[h][w] = True
        for pos in [(h - 1, w), (h + 1, w), (h, w - 1), (h, w + 1)]:
            nh, nw = pos
            if not(0 <= nh < H and 0 <= nw < W):
                continue
            if visited[nh][nw]:
                continue
            if C[nh][nw] == "#":
                continue
            dfs(nh, nw)

    dfs(S[0], S[1])

    ans = "Yes" if visited[G[0]][G[1]] else "No"
    assert ans == expected
