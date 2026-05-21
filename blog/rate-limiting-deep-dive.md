---
title: "深入理解限流：令牌桶、漏桶与分布式实现"
date: 2026-05-21
tags: [后端, 限流, Redis, 分布式, 高并发]
---

# 深入理解限流：令牌桶、漏桶与分布式实现

限流（Rate Limiting）是后端系统保护自身不被流量冲垮的核心手段。无论是 API 网关、微服务、还是消息队列，限流无处不在。

但"限流"两个字背后，实现方式五花八门，选错方案轻则用户体验差，重则系统雪崩。这篇文章把主流限流算法掰开揉碎讲清楚，重点说清楚**为什么这么设计**，以及**生产环境怎么实现**。

---

## 先理清一个核心问题：限流到底在限什么？

限流本质上是在回答一个问题：**"在某个时间窗口内，允许通过多少请求？"**

但不同的业务场景对"允许通过"的定义不一样：

| 场景 | 需求 | 适合的算法 |
|------|------|-----------|
| API 调用频率限制 | 每秒最多 N 次，但允许短暂突发 | **令牌桶** |
| 流量整形（匀速输出） | 严格匀速，不接受突发 | **漏桶** |
| 粗粒度窗口限制 | 每分钟/每小时不超过 N 次 | **固定窗口 / 滑动窗口** |
| 防刷 / 防爬 | 超限直接拒绝 | **计数器类** |

理解了需求，再看算法就不会迷路。

---

## 一、令牌桶（Token Bucket）

### 核心思想

想象一个桶，里面装令牌。系统以**恒定速率**往桶里放令牌（比如每秒放 10 个）。每个请求进来时，从桶里拿走一个令牌：

- 桶里有令牌 → 拿走，请求通过
- 桶里没令牌 → 请求被拒绝或排队

桶有**最大容量**（burst size）。桶满了，新产生的令牌被丢弃。

这意味着：如果系统空闲了一段时间，桶里会攒下一批令牌，允许**短暂的突发流量**。这是令牌桶最大的特点，也是它比漏桶灵活的地方。

```
时间线示意：

t=0s:  桶容量10, 令牌=10 → 请求来了拿1个, 令牌=9
t=1s:  补充2个, 令牌=10 → 来了8个请求, 令牌=2
t=2s:  补充2个, 令牌=4  → 来了5个请求? 只能过4个, 拒绝1个
```

### 关键参数

- **rate**：令牌产生速率（令牌/秒）
- **burst / max_tokens**：桶的最大容量，决定能容忍多大的突发

### 为什么叫"延迟计算"？

生产环境中，令牌桶**不会真的用定时器往桶里扔令牌**。而是用**延迟计算（lazy computation）**：

> 不维护一个"当前令牌数"的变量，而是在每次请求到来时，根据"距离上次补充过去了多久"来**计算当前应该有多少令牌**。

伪代码：

```python
def allow_request(key):
    now = current_time()
    record = get_record(key)  # { last_refill, tokens }

    if record is None:
        # 首次请求，桶满
        save_record(key, last_refill=now, tokens=burst - 1)
        return True

    # 计算自上次补充以来，应该产生多少令牌
    elapsed = now - record.last_refill
    new_tokens = elapsed * rate

    # 当前令牌数 = min(桶容量, 原有令牌 + 新产生的)
    current_tokens = min(burst, record.tokens + new_tokens)

    if current_tokens >= 1:
        save_record(key, last_refill=now, tokens=current_tokens - 1)
        return True
    else:
        # 更新 last_refill 但不扣令牌
        save_record(key, last_refill=now, tokens=current_tokens)
        return False
```

**延迟计算的好处**：
1. **不需要后台线程/定时器**，纯被动触发
2. **天然适配分布式存储**（Redis 等），把状态存远端，每次请求读写一次
3. **空闲时不消耗任何资源**——没有令牌在"白白产生"

### 分布式令牌桶：Redis + Lua 实现

单机令牌桶很简单，但生产环境通常是多实例部署，状态必须共享。Redis 是最常见的选择。

**为什么需要 Lua 脚本？** 因为"读取 → 计算 → 写回"不是原子操作。两个请求并发读取到相同的令牌数，都会认为自己能通过，导致超限。Lua 脚本在 Redis 中是**原子执行**的（单线程模型），完美解决这个问题。

Lua 脚本实现：

```lua
-- KEYS[1] = 限流 key
-- ARGV[1] = 令牌产生速率（令牌/秒）
-- ARGV[2] = 桶最大容量（burst）
-- ARGV[3] = 当前时间戳（秒或毫秒，由调用方决定精度）
-- ARGV[4] = 本次请求消耗的令牌数（通常为1）

local key = KEYS[1]
local rate = tonumber(ARGV[1])
local burst = tonumber(ARGV[2])
local now = tonumber(ARGV[3])
local requested = tonumber(ARGV[4])

-- 获取当前状态
local record = redis.call("HMGET", key, "tokens", "last_time")
local tokens = tonumber(record[1])
local last_time = tonumber(record[2])

-- 初始化：桶满
if tokens == nil then
    tokens = burst
    last_time = now
end

-- 延迟计算：根据时间差补充令牌
local elapsed = math.max(0, now - last_time)
local new_tokens = elapsed * rate
tokens = math.min(burst, tokens + new_tokens)

local allowed = false

if tokens >= requested then
    tokens = tokens - requested
    allowed = true
end

-- 写回状态
redis.call("HMSET", key, "tokens", tokens, "last_time", now)
-- 设置过期时间，避免无用 key 永远存在（2 倍填满桶的时间就够了）
local fill_time = math.ceil(burst / rate)
redis.call("EXPIRE", key, fill_time * 2)

if allowed then
    return 1  -- 允许
else
    return 0  -- 拒绝
end
```

调用方（以 Python 为例）：

```python
import time
import redis

r = redis.Redis()

TOKEN_BUCKET_SCRIPT = """...上面那段 lua..."""
script = r.register_script(TOKEN_BUCKET_SCRIPT)

def is_allowed(key: str, rate: float = 10.0, burst: int = 20) -> bool:
    now = time.time()
    result = script(keys=[f"ratelimit:{key}"], args=[rate, burst, now, 1])
    return result == 1
```

**实现要点**：

1. **时间戳由调用方传入**，不用 Redis 的 `TIME` 命令。因为 `TIME` 在 Lua 脚本中被调用会被标记为 non-deterministic（Redis 7.0 前），影响主从复制。调用方传时间还能避免 Redis 服务器与应用服务器时钟不一致的问题。
2. **EXPIRE 不能忘**。不设过期，大量已停止使用的 key 会占满 Redis 内存。
3. **精度选择**：如果 rate 很高（比如每秒 10000），用毫秒级时间戳，否则误差太大。

---

## 二、漏桶（Leaky Bucket）

### 核心思想

想象一个底部有洞的桶，水（请求）从上面倒进去，从下面以**恒定速率**流出来。

- 桶没满 → 请求进入桶中排队，等待被"漏出"（处理）
- 桶满了 → 新请求直接溢出（被拒绝）

和令牌桶最大的区别：**漏桶的输出速率是严格恒定的**，不管你瞬间倒进去多少水，流出来的速度永远不变。

```
时间线示意（每秒处理2个请求）：

t=0s:  桶里0个 → 来了5个请求, 桶里5个 → 漏出2个, 桶里3个
t=1s:  漏出2个, 桶里1个 → 来了4个, 桶里5个（满）→ 漏出2个, 桶里3个
t=2s:  来了3个, 桶里6个? 桶容量5 → 拒绝1个, 桶里5个 → 漏出2个, 桶里3个
```

### 实现方案一：消息队列模拟

最直觉的实现——用消息队列当桶：

```
请求 → [写入队列] → [定时消费者以固定速率取出] → 处理
```

```python
import queue
import threading
import time

class LeakyBucketQueue:
    def __init__(self, rate: float, capacity: int):
        """
        rate: 每秒处理请求数
        capacity: 桶容量（队列最大长度）
        """
        self.rate = rate
        self.interval = 1.0 / rate  # 两个请求之间的最小间隔
        self.bucket = queue.Queue(maxsize=capacity)

        # 启动消费者线程，匀速取请求
        self._consumer = threading.Thread(target=self._drain, daemon=True)
        self._consumer.start()

    def _drain(self):
        """以恒定速率从桶中取出请求并处理"""
        while True:
            request = self.bucket.get()  # 阻塞等待
            self._process(request)
            time.sleep(self.interval)  # 控制速率

    def submit(self, request) -> bool:
        """提交请求，桶满则拒绝"""
        try:
            self.bucket.put_nowait(request)
            return True
        except queue.Full:
            return False  # 溢出，拒绝

    def _process(self, request):
        # 实际业务处理
        pass
```

**这种方案的优缺点**：

- ✅ 语义清晰，真正"匀速流出"
- ✅ 天然支持异步/排队处理
- ❌ 需要后台线程/协程，有调度开销
- ❌ 不太好做分布式（需要分布式队列，引入 Kafka/Redis Stream 等）
- ❌ 队列内存占用（请求体大时更明显）

适合场景：下游处理能力有限，需要严格匀速输入（比如调用第三方 API 有频率限制）。

### 实现方案二：延迟计算（和令牌桶类似的思路）

漏桶也能用延迟计算！不需要队列，不需要后台线程。

核心逻辑：**记录"下一次允许请求通过的时间"**。每次请求到来时：

1. 算出当前时间与"上次漏水时间"之间，漏出了多少个请求的量
2. 推算出"下一个可以放行的时间点"
3. 如果当前时间 ≥ 这个时间点，放行并更新；否则拒绝或等待

```python
import time

class LeakyBucketLazy:
    def __init__(self, rate: float, capacity: int):
        """
        rate: 每秒漏出（处理）的请求数
        capacity: 桶容量（最大排队数）
        """
        self.rate = rate
        self.capacity = capacity
        self.interval = 1.0 / rate

        # 状态
        self.water = 0          # 当前桶中水量（排队请求数）
        self.last_leak = time.time()  # 上次漏水时间

    def allow(self) -> bool:
        now = time.time()

        # 先漏水：计算这段时间漏出了多少
        elapsed = now - self.last_leak
        leaked = elapsed * self.rate
        self.water = max(0, self.water - leaked)
        self.last_leak = now

        # 尝试加水（请求进入桶）
        if self.water < self.capacity:
            self.water += 1
            return True
        else:
            return False  # 桶满，拒绝
```

**等一下，这和令牌桶有什么区别？**

看起来很像，但语义不同：

| 对比项 | 令牌桶（延迟计算） | 漏桶（延迟计算） |
|--------|-------------------|-----------------|
| 状态变量 | `tokens`（可用令牌数） | `water`（桶中积水量） |
| 通过条件 | `tokens >= 1` | `water < capacity` |
| 通过操作 | `tokens -= 1`（消耗令牌） | `water += 1`（加水入桶） |
| 补充方向 | 时间流逝 → 令牌**增加** | 时间流逝 → 水量**减少** |
| 突发处理 | 允许突发（攒令牌） | 不允许突发（匀速漏出） |

实际上，令牌桶和漏桶在延迟计算形式下，代码结构几乎对称，区别在于**计数方向**和**语义**。

同样地，漏桶的分布式版本也可以用 Redis + Lua 实现，结构和令牌桶几乎一样，只是把 `tokens` 换成 `water`，判断条件反过来。

---

## 三、其他限流思路

### 3.1 固定窗口计数器（Fixed Window）

最简单的限流：把时间划分为固定窗口（比如每分钟），每个窗口内维护一个计数器。

```
|---- 0:00 ~ 0:59 ----|---- 1:00 ~ 1:59 ----|
      count = 47            count = 0
```

```python
import time
import redis

r = redis.Redis()

def fixed_window_limit(key: str, limit: int, window_seconds: int) -> bool:
    now = int(time.time())
    window_key = f"fw:{key}:{now // window_seconds}"

    count = r.incr(window_key)
    if count == 1:
        r.expire(window_key, window_seconds)

    return count <= limit
```

**致命问题：边界突发（Boundary Burst）**。

```
假设限制每分钟 100 次：

0:00:00 ~ 0:00:59 → 来了 100 个请求（窗口内合法）
0:01:00 ~ 0:01:59 → 又来了 100 个请求（窗口内也合法）

但在 0:00:30 ~ 0:01:30 这 1 分钟里，实际通过了 200 个请求！
```

### 3.2 滑动窗口计数器（Sliding Window Log）

为了解决边界突发问题，记录每个请求的精确时间戳，统计"最近 N 秒内"的请求数。

用 Redis 的 Sorted Set 实现，**时间戳同时作为 score**：

```python
def sliding_window_limit(key: str, limit: int, window_seconds: int) -> bool:
    now = time.time()
    window_start = now - window_seconds
    zk = f"sw:{key}"

    pipe = r.pipeline()
    # 1. 移除窗口外的旧记录
    pipe.zremrangebyscore(zk, 0, window_start)
    # 2. 统计当前窗口内的请求数
    pipe.zcard(zk)
    # 3. 如果未超限，加入当前请求
    pipe.zadd(zk, {str(now): now})
    pipe.expire(zk, window_seconds + 1)
    results = pipe.execute()

    count = results[1]
    if count < limit:
        return True
    else:
        return False
```

**优点**：精确，无边界问题。
**缺点**：每个请求都要存一条记录，内存开销大（高 QPS 场景下 Sorted Set 会很大）。

### 3.3 滑动窗口（合并方案）

折中方案：用**两个相邻的固定窗口做加权平均**，既避免了固定窗口的边界问题，又不需要存储每个请求。

```
假设窗口大小 1 分钟，当前时间是 0:30（在 0:00~1:00 窗口的 50% 处）：

加权计数 = 前一窗口计数 × (1 - 50%) + 当前窗口计数
         = 前一窗口计数 × 0.5 + 当前窗口计数
```

```python
def sliding_window_merged(key: str, limit: int, window_seconds: int) -> bool:
    now = int(time.time())
    current_window = now // window_seconds
    previous_window = current_window - 1

    # 当前窗口的偏移比例
    elapsed = now - current_window * window_seconds
    weight = 1 - elapsed / window_seconds

    previous_count = int(r.get(f"swm:{key}:{previous_window}") or 0)
    estimated = previous_count * weight

    current_count = r.incr(f"swm:{key}:{current_window}")
    r.expire(f"swm:{key}:{current_window}", window_seconds * 2)

    return estimated + current_count <= limit
```

**优点**：内存极小（只存两个计数器），近似滑动窗口效果。
**缺点**：是**估算值**，不如 Log 方案精确，但大多数场景够用。

### 3.4 令牌桶变体：预热 / 冷启动

Guava RateLimiter 实现了带**预热（warmup）** 的令牌桶。核心思想：

- 系统刚启动或长时间空闲后，桶是"冷"的，令牌产生速率较慢
- 随着请求持续到来，系统"热起来"，令牌产生速率逐渐提升到正常水平
- 防止冷系统突然被大流量冲垮

```
      速率
       ↑
rate ──┤         ┌────────────── 正常速率
       │        ╱
       │       ╱  ← 预热期：速率逐渐上升
       │      ╱
       ├─────╱
       └──────────────────────→ 时间
           ↑
         cold
```

适用场景：需要保护下游服务的冷启动场景（如数据库连接池未预热时）。

---

## 四、算法选型速查表

| 算法 | 突发容忍 | 内存开销 | 实现复杂度 | 精确度 | 典型场景 |
|------|---------|---------|-----------|--------|---------|
| **令牌桶** | ✅ 允许 | 低 | 中 | 高 | API 限流（大多数场景首选） |
| **漏桶** | ❌ 匀速 | 中 | 中 | 高 | 流量整形、调用第三方 API |
| **固定窗口** | ❌ 边界突发 | 极低 | 极低 | 低 | 简单场景、粗粒度限制 |
| **滑动窗口 Log** | ✅ 精确 | 高 | 中 | 最高 | 精确计费、审计 |
| **滑动窗口合并** | ⚠️ 近似 | 极低 | 低 | 中 | 高 QPS + 近似够用 |
| **预热令牌桶** | ✅ 渐进 | 低 | 高 | 高 | 冷启动保护 |

---

## 五、分布式限流的额外考量

### 5.1 时钟问题

延迟计算依赖时间戳。分布式环境下：

- **Redis 与应用服务器时钟不同步** → 计算的 elapsed 不准确
- 解决方案：时间戳由应用方统一传入，所有实例用同一套时钟（NTP 同步）
- 更好的方案：使用 Redis 的 `TIME` 命令（Redis 7.0+ 支持 effect replication，Lua 脚本中调用 `TIME` 不再影响主从复制）

### 5.2 性能优化

- **管道化（Pipeline）**：批量检查多个 key 时，用 pipeline 减少网络往返
- **本地缓存 + 远端同步**：Guava 有 `RateLimiter` + Redis 的组合方案，本地先做一次粗粒度限流，减少 Redis 压力
- **分片**：按用户/租户分 key，天然分散热点

### 5.3 超限后的策略

限流拒绝请求后，可以有不同的策略：

| 策略 | 行为 | 适用场景 |
|------|------|---------|
| **直接拒绝** | 返回 429 / 503 | 保护系统优先 |
| **排队等待** | 请求阻塞，等令牌可用 | 用户体验优先（但要注意超时） |
| **降级返回** | 返回缓存/默认值 | 可用性优先 |
| **预热等待** | 返回 `Retry-After` 头 | 客户端友好（REST API 常见） |

---

## 六、代码汇总：Redis + Lua 分布式令牌桶完整实现

```lua
-- ratelimit_token_bucket.lua
-- 分布式令牌桶限流器
--
-- KEYS[1]: 限流 key
-- ARGV[1]: rate（令牌/秒）
-- ARGV[2]: burst（桶容量）
-- ARGV[3]: now（当前时间戳，秒级浮点数）
-- ARGV[4]: cost（本次消耗令牌数，默认1）
--
-- 返回:
--   [1] = 是否允许（1=允许, 0=拒绝）
--   [2] = 剩余令牌数

local key       = KEYS[1]
local rate      = tonumber(ARGV[1])
local burst     = tonumber(ARGV[2])
local now       = tonumber(ARGV[3])
local cost      = tonumber(ARGV[4]) or 1

-- 读取状态
local data = redis.call("HMGET", key, "tokens", "last_time")
local tokens    = tonumber(data[1])
local last_time = tonumber(data[2])

-- 首次请求初始化
if tokens == nil then
    tokens = burst
    last_time = now
end

-- 延迟补充令牌
local elapsed = math.max(0, now - last_time)
local refill  = elapsed * rate
tokens = math.min(burst, tokens + refill)
last_time = now

-- 判断是否允许
local allowed = 0
if tokens >= cost then
    tokens = tokens - cost
    allowed = 1
end

-- 持久化
redis.call("HMSET", key, "tokens", tokens, "last_time", now)
local ttl = math.ceil(burst / rate) * 2
redis.call("EXPIRE", key, ttl)

return { allowed, tostring(tokens) }
```

Python 调用封装：

```python
import time
import redis

class DistributedTokenBucket:
    def __init__(self, redis_client: redis.Redis,
                 rate: float, burst: int):
        self.redis = redis_client
        self.rate = rate
        self.burst = burst
        self._script = self.redis.register_script(LUA_SCRIPT)

    def is_allowed(self, key: str, cost: int = 1) -> tuple[bool, float]:
        """
        返回 (是否允许, 剩余令牌数)
        """
        now = time.time()
        result = self._script(
            keys=[f"rl:{key}"],
            args=[self.rate, self.burst, now, cost]
        )
        return bool(result[0]), float(result[1])

    def wait_for_permit(self, key: str, cost: int = 1,
                        timeout: float = 30.0) -> bool:
        """
        阻塞等待直到获取令牌，或超时
        """
        deadline = time.time() + timeout
        while time.time() < deadline:
            allowed, remaining = self.is_allowed(key, cost)
            if allowed:
                return True
            # 计算大约需要等多久
            wait = max(0.01, (cost - remaining) / self.rate)
            time.sleep(min(wait, deadline - time.time()))
        return False


# 使用示例
bucket = DistributedTokenBucket(
    redis_client=redis.Redis(),
    rate=10,    # 每秒 10 个令牌
    burst=20    # 最大容量 20
)

if bucket.is_allowed("user:123")[0]:
    handle_request()
else:
    return_too_many_requests()
```

---

## 总结

限流不是一个"随便加个计数器"的问题。选对算法，理解它的边界，在生产环境中正确实现（原子性、过期清理、时钟同步），才能真正做到保护系统。

**大多数场景下，令牌桶是最优选择**：它允许合理的突发，实现简洁，且天然适配分布式。漏桶适合需要严格匀速的场景。固定/滑动窗口适合粗粒度的调用频率限制。

记住一点：**限流是保护，不是惩罚**。好的限流设计应该让正常用户无感，只在真正危险时才触发。
