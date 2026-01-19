"""部分和問題.

https://atcoder.jp/contests/tdpc/tasks/tdpc_contest


Problem Statement
N 問の問題があるコンテストがあり、i 問目の問題の配点は p_i点である。
コンテスタントは、この問題の中から何問か解き、解いた問題の配点の合計が得点となる。このコンテストの得点は何通り考えられるか。
"""

from utils import Input
from pprint import pprint



data1 = """
3
2 3 5
"""

expected1 = 7

data = [
    data1,
]

expected = [
    expected1,
]

idx_ = 0

input = Input(data[idx_]).input

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
"""

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
assert ans == expected[idx_]
