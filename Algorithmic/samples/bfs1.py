"""幅優先探索(BFS: Breadth First Search).

以下のようなケースで有効.
- 最短経路問題

https://atcoder.jp/contests/abc007/tasks/abc007_3
"""

from utils import Input
from pprint import pprint
import textwrap
import pytest


CASES = [
    (
        textwrap.dedent("""\
        7 8
        2 2
        4 5
        ########
        #......#
        #.######
        #..#...#
        #..##..#
        ##.....#
        ########
        """),
        11,
    ),
    (
        textwrap.dedent("""\
        5 8
        2 2
        2 4
        ########
        #.#....#
        #.###..#
        #......#
        ########
        """),
        10,
    ),
]


@pytest.fixture(params=CASES, ids=[f"case{i}" for i in range(1, len(CASES) + 1)])
def case(request):
    return request.param


###################################################


def test_1(case):
    data, expected = case
    input = Input(data).input

    from collections import deque

    def to_idx(x):
        return int(x) - 1

    H, W = map(int, input().split())
    S = tuple(map(to_idx, input().split()))
    G = tuple(map(to_idx, input().split()))
    print(S, G)

    F = [list(input()) for _ in range(H)]
    D = [[None] * W for _ in range(H)]

    D[S[0]][S[1]] = 0

    Q = deque()
    Q.append(S)

    def bfs():
        h, w = Q.popleft()

        for nh, nw in [(h + 1, w), (h - 1, w), (h, w + 1), (h, w - 1)]:
            if F[nh][nw] == "#":
                continue
            if D[nh][nw] is not None:
                continue
            Q.append((nh, nw))
            D[nh][nw] = D[h][w] + 1

    while len(Q) > 0:
        bfs()

    ans = D[G[0]][G[1]]
    assert ans == expected
