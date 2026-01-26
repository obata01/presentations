"""部分和問題.

https://atcoder.jp/contests/tdpc/tasks/tdpc_contest


Problem Statement
N 問の問題があるコンテストがあり、i 問目の問題の配点は p_i点である。
コンテスタントは、この問題の中から何問か解き、解いた問題の配点の合計が得点となる。このコンテストの得点は何通り考えられるか。
"""

from pprint import pprint
import textwrap
import pytest

from utils import Input


CASES = [
    (
        textwrap.dedent(
            """\
            3
            2 3 5
            """
        ),
        7,
    ),
    (
        textwrap.dedent(
            """\
            10
            1 1 1 1 1 1 1 1 1 1
            """
        ),
        11,
    ),
]


@pytest.fixture(params=CASES, ids=[f"case{i}" for i in range(1, len(CASES) + 1)])
def case(request):
    return request.param

#############################################

"""
合計得点
s(score)
10                          10
9
8
7
6
5                  -->5      5
4                 |
3                 |
2             2 ----> 2 ----> 2  ※i-1に値があれば計算可能.
1
0      0      0       0      0
       -     問題1   問題2  問題3    i

※横軸にケース、縦軸に価値を置いた場合の図.
"""

def test_bubunnwa1(case):
    data, expected = case
    input = Input(data).input
    N = int(input())
    P = [0] + list(map(int, input().split()))

    P_sum = sum(P)

    score = []
    for i in range(P_sum+1):
        score.append([-1] * (N+1))

    score[0][0] = 0

    for i in range(P_sum+1):
        for j in range(1, N+1):
            if (before := score[i][j-1]) >= 0:
                score[i][j] = before
                score[i+P[j]][j] = before + P[j]

    ans = 0
    for k in score:
        if k[-1] >= 0:
            ans += 1

    print(score[:][-1])
    pprint(score[::-1][:])
    print(ans)
    assert ans == expected


def test_bubunnwa2(case):
    data, expected = case
    input = Input(data).input

    N = int(input())
    P = list(map(int, input().split()))

    score_max = sum(P)

    # 探索空間の箱の用意.
    search_space = []
    for i in range(N + 1):
        search_space.append([-1] * (score_max + 1))

    # 初期値の設定.
    search_space[0][0] = 0

    # 探索空間の更新.
    for i in range(1, N+1):  # 横軸.
        for j in range(score_max + 1):
            if search_space[i-1][j] >= 0:
                # 問題を解く場合.
                search_space[i][j+P[i-1]] = search_space[i-1][j] + P[i-1]
                # 問題を解かない場合.
                search_space[i][j] = search_space[i-1][j]

    ans = len([s for s in search_space[-1] if s >= 0])

    assert ans == expected


def test_bubunnwa3(case):
    """DFSで解く場合.

    計算量は
    - 動的計画法の場合: O(N*sum(P))
    - DFSの場合: O(2^N)
    となるが、Nが小さい場合はDFSの方が速い場合もある.

    【例】
    - N=20, sum(P)=2000の場合、動的計画法は約40,000の計算量に対し、DFSは最大1,048,576の計算量となる.
    - N=15, sum(P)=100の場合、動的計画法は約15,000の計算量に対し、DFSは最大32,768の計算量となる.
    - N=10, sum(P)=50の場合、動的計画法は約5,000の計算量に対し、DFSは最大1,024の計算量となり、DFSの方が速くなる.
    よって、Nとsum(P)の値によって適切なアルゴリズムを選択することが重要である.
    ここではDFSで解く場合のコードを示す.
    """
    data, expected = case
    input = Input(data).input

    N = int(input())
    P = list(map(int, input().split()))

    scores = [set() for _ in range(N)]

    def dfs(i, score):
        """DFS.

        Args:
            i: 問題番号.
            score: 現在の得点.
        """
        for next_score in [score, score + P[i]]:
            if next_score in scores[i]:  # 探索済みをスキップする.
                continue
            scores[i].add(next_score)
            if i + 1 < N:
                dfs(i + 1, next_score)
    
    dfs(0, 0)
    ans = len(scores[-1])
    assert ans == expected
