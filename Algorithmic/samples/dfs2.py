"""深さ優先探索(DFS: Depth First Search).

以下のようなケースで有効.
- グラフの全探索
- 部分和問題

"""

from utils import Input
from pprint import pprint
import textwrap
import pytest


CASES = [
    (
        textwrap.dedent("""\
        10 12
        W........WW.
        .WWW.....WWW
        ....WW...WW.
        .........WW.
        .........W..
        ..W......W..
        .W.W.....WW.
        W.W.W.....W.
        .W.W......W.
        ..W.......W.
        """),
        3,
    ),
]


@pytest.fixture(params=CASES, ids=[f"case{i}" for i in range(1, len(CASES) + 1)])
def case(request):
    return request.param


###################################################


def test_1(case):
    data, expected = case
    input = Input(data).input

    H, W = map(int, input().split())
    F = [list(input()) for _ in range(H)]

    def dfs(h, w):
        F[h][w] = "."
        patterns = [
            (h + 1, w - 1),
            (h + 1, w),
            (h + 1, w + 1),
            (h, w + 1),
            (h - 1, w + 1),
            (h - 1, w),
            (h - 1, w - 1),
            (h, w - 1),
        ]
        for nh, nw in patterns:
            if not (0 <= nh < H and 0 <= nw < W):
                continue
            if F[nh][nw] == ".":
                continue
            dfs(nh, nw)

    dfs_count = 0
    for h in range(H):
        for w in range(W):
            if F[h][w] == "W":
                dfs(h, w)
                dfs_count += 1

    assert dfs_count == expected
