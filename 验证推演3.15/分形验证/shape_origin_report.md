# `s_min` 景观形状的根源

## 1. 现在可以把“它为什么长这样”分成两层

这条景观的形状，不是凭空从“复杂数值扫描”里冒出来的，而是由两层结构叠加出来的：

1. **`k` 空间里的有理数骨架**
   `s_M(k)` 是有限个锯齿函数的下包络，而这个下包络可由 Farey 邻分数区间精确组织。
2. **从 `k` 到 `L/R` 的坐标拉伸**
   `L/R = sin^2(pi k)` 不是线性变换，所以同样宽的 `k` 区间，在图上的横向宽度会被重新分配。

前者决定“峰谷在哪里、峰多高、谁限制谁”；后者决定“为什么中心看起来更宽、更平缓、更容易做工程设计”。

---

## 2. 第一层根源：它本质上是 Farey 邻分数拼成的帐篷包络

对连续集合 `S_M = {1,2,...,M}`，

```math
s_M(k) = \min_{1 \le q \le M-1}\|qk\|.
```

令 `Q = M-1`。把区间 `[0,1/2]` 内所有分母不超过 `Q` 的既约分数排成 Farey 序列。
若其中相邻两项为

```math
\frac{a}{b} < \frac{c}{d},
```

则它们满足

```math
bc-ad=1,\qquad b,d \le Q,\qquad b+d>Q.
```

在这个 Farey 邻区间内，数值验算强烈表明并完全支持下面的精确公式：

```math
s_M(k)=\min(bk-a,\ c-dk), \qquad k\in\left[\frac{a}{b},\frac{c}{d}\right].
```

这意味着：

- `s_M(k)` 在每个 Farey 邻区间内就是一个**帐篷形**；
- 左边斜率是 `+b`；
- 右边斜率是 `-d`；
- 峰顶出现在两条直线相交处，也就是

```math
k_{\text{peak}}=\frac{a+c}{b+d},
```

即左右端点的 **mediant**；

- 峰高则是

```math
s_{\text{peak}}=\frac{1}{b+d}.
```

所以这条景观的每一座“山”，都不是随机长出来的，而是一对 Farey 邻分数围出来的。

---

## 3. 为什么全局最高峰恰好是 `1/M`

由上面这个局部公式，任何局部峰的高度都是

```math
\frac{1}{b+d}.
```

而 Farey 邻分数在 `Q=M-1` 阶时总满足 `b+d > Q = M-1`，因此

```math
b+d \ge M.
```

于是

```math
s_{\text{peak}} \le \frac{1}{M}.
```

只有当

```math
b+d=M
```

时，峰高才能真正达到 `1/M`。

这时峰顶正好是

```math
k^*=\frac{m}{M},\qquad \gcd(m,M)=1,
```

也就是你图里那些解析最优分支。

所以“最高峰是 `1/M`，并出现在互质 `m/M` 处”这件事，其实不是孤立公式，而是整个 Farey 骨架的直接结果。

---

## 4. 为什么 `M` 变大后会出现一层层细节

把 `M` 提高，相当于把可参与竞争的分母上界 `Q=M-1` 提高。

于是会发生三件事：

1. **新的低阶有理点被加入骨架**
   更多分母的既约分数进入 Farey 序列；
2. **旧区间被进一步细分**
   原来一整个 Farey 邻区间，现在会被新的中间有理点切成更小的子区间；
3. **旧帐篷下方长出新帐篷**
   新子区间各自再长出自己的 mediant 峰。

这就是“粗轮廓之下继续长细节”的真正来源。

所以这条曲线并不是在做严格分形复制，而是在做：

**有理数骨架逐阶加密导致的层级细化。**

---

## 5. 为什么很多局部峰还是偏斜的

在一个 Farey 邻区间里，左右斜率分别是 `b` 和 `-d`。
除非 `b=d`，否则这座峰天然就是偏斜的。

这也解释了为什么前一轮局部解析里会出现

```math
s_M(k^*+\varepsilon)
= \min\Bigl(\frac{1}{M}+a\varepsilon,\ \frac{1}{M}-(M-a)\varepsilon\Bigr).
```

那里出现的左右斜率 `a` 与 `M-a`，其实正对应于这对 Farey 邻分数的分母。

换句话说：

- “局部 skew tent” 不是偶然；
- 它正是 Farey 邻端点分母不对称的直接反映。

---

## 6. 第二层根源：为什么换成 `L/R` 后中心看起来更宽

图里真正画的横轴不是 `k`，而是

```math
L/R = \sin^2(\pi k).
```

这个映射的导数为

```math
\frac{d(L/R)}{dk} = \pi \sin(2\pi k).
```

它在

```math
k=\frac{1}{4}
```

附近最大，所以：

- 同样长度的一个 `k` 区间，
- 映射到 `L/R` 轴上时，
- 会在中心附近被拉得更宽，
- 在靠近 `0` 和 `1/2` 时被压得更窄。

这就是你图里“中间大轮廓更舒展、边缘更挤”的几何来源。

因此图形的“视觉风格”不是单一原因造成的，而是：

- `k` 空间里的 Farey 帐篷骨架，
- 再经过 `sin^2` 坐标变换后的横向非均匀拉伸。

---

## 7. 这次新增的验证文件

脚本：

- [verify_farey_skeleton.py](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/验证推演3.15/分形验证/verify_farey_skeleton.py)

输出：

- [farey_skeleton_summary.png](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/验证推演3.15/分形验证/outputs/farey_skeleton_summary.png)
- [farey_skeleton_verification.csv](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/验证推演3.15/分形验证/outputs/farey_skeleton_verification.csv)
- [farey_intervals_M9.csv](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/验证推演3.15/分形验证/outputs/farey_intervals_M9.csv)
- [farey_intervals_M15.csv](D:/自制软件/1.thesis/My_nju_thesis-master/thesis/验证推演3.15/分形验证/outputs/farey_intervals_M15.csv)

这些文件对应验证了三件事：

1. 数值曲线与 Farey 帐篷骨架逐点吻合；
2. `M=9` 的主要峰确实都落在 mediant 位置；
3. 同一批峰在 `L/R` 坐标下会被中心拉宽，从而形成你图里的视觉风格。

---

## 8. 目前最稳妥的一句话总结

如果现在要用一句最准确的话来描述这个形状根源，我会建议：

> `s_min` 景观的基本骨架由分母不超过 `M-1` 的 Farey 邻分数区间决定；在每个这样的区间内，景观是一个峰顶位于 mediant、峰高为 `1/(b+d)` 的偏斜帐篷。随着 `M` 增大，允许分母上界提高，Farey 骨架逐阶加密，原有粗轮廓被保留，而其下方不断生长出更细的子结构；再经 `L/R = sin^2(pi k)` 的非线性坐标变换后，就形成了图中这种中心舒展、边缘压缩的层级景观。`

这已经比“像分形”更接近真正的数学根源了。
