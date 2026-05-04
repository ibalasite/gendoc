# Template Gap Analysis — 生成文件缺口清單

> 狀態：草稿，待知識補強後供作者評估確認，確認後才進行實作
> 建立日期：2026-05-05
> 來源：gendoc-auto + gendoc-flow 在 test 專案執行後的文件完整度評估

---

## 背景

在實驗專案執行完整 gendoc pipeline 後，評估發現以下文件缺口（前端 70%、後端 95%）。
根因是 template 的生成指令覆蓋不足，而非 AI 生成能力問題。

---

## 缺口清單

### G1 — VDD.gen.md：CSS 設計系統粒度不足

**缺失內容**：色彩 tokens 應用對照表、排版 Responsive 縮放規則

**現況**：
- §6 有要求 Design Token 三層架構，但缺「token → UI 元件/使用場景」對應表
- §5 有要求 Typography System，但缺「各斷點的字型縮放規則」

**建議做法**：
- 在 §6 追加 `§6.1 Token 應用矩陣`（token 名稱 → 使用場景對應表）
- 在 §5 追加 `§5.1 Responsive Typography`（mobile/tablet/desktop 字型尺寸表）

**改動 template**：`templates/VDD.gen.md`
**難度**：低

---

### G2 — SCHEMA.gen.md：Migration 缺實作清單

**缺失內容**：遷移檔案清單、執行順序表、Rollback 策略

**現況**：
- §8 有命名規則與 Expand-Contract Pattern，但只要求「策略說明」
- 未要求生成「實際遷移檔案清單」及「執行順序依賴關係」

**建議做法**：
- 在 §8 後追加 `§8.1 Migration 實作清單`（版本號/檔名/功能/依賴/Rollback）
- 要求標示哪些 migration 需 Data Backfill Job

**改動 template**：`templates/SCHEMA.gen.md`
**難度**：低

---

### G3 — CLIENT_IMPL.gen.md + PDD.gen.md：缺 Phaser.js 支援

**缺失內容**：Phaser 場景架構、精靈管理、物理引擎設定規範

**現況**：
- ENGINE routing 只有 Cocos / Unity / React / Vue / HTML5，Phaser 完全缺席
- 遊戲 UI 規範只涵蓋 Unity/Cocos Creator，無 Phaser Scene 架構要求

**建議做法**：
- CLIENT_IMPL.gen.md §2：新增 Phaser 路由分支 + 專用目錄結構
- CLIENT_IMPL.gen.md §3：新增 Phaser Scene 生命週期架構文件規範
- PDD.gen.md 遊戲 UI 章節：補充 Phaser Scene 層級架構描述要求

**改動 template**：`templates/CLIENT_IMPL.gen.md` + `templates/PDD.gen.md`
**難度**：中（需 Phaser 架構知識 → 見本文 §知識補強）

---

### G4 — EDD.gen.md：缺 Redis 鍵設計層

**缺失內容**：Redis 鍵命名規範、TTL 策略、限流鍵結構、資料結構選型

**現況**：
- §11 Performance Design 提及快取，但未展開到 Redis 層級
- Redis 只在 HA 章節出現（Sentinel 設定），無鍵設計規範要求

**建議做法**：
- 在 §11 追加 `§11.3 Redis 快取設計`
  - 鍵命名規範（namespace:entity:id:action 格式）
  - 業務場景 TTL 策略表
  - 限流鍵結構（滑動視窗 vs 令牌桶）
  - 資料結構選型表（String/Hash/Set/Sorted Set）
  - 記憶體預算估算指引

**改動 template**：`templates/EDD.gen.md`
**難度**：中（需 Redis 設計知識 → 見本文 §知識補強）

---

### G5 — PDD.gen.md + VDD.gen.md：缺 Mockup 交付清單

**缺失內容**：Figma 連結要求、狀態截圖清單、動效示意交付規範

**現況**：
- 兩個 template 都要求「文字描述」畫面，未要求附設計稿檔案
- Engineering Handoff 章節無 Mockup 資產交付清單

**建議做法**：
- PDD.gen.md：在 §13 追加「Mockup 資產交付清單」（Figma 連結、5 種狀態截圖、Empty/Loading/Error 示意）
- VDD.gen.md：在 §8 追加「設計稿截圖路徑或 Figma frame 連結」+ 動效示意清單

**改動 template**：`templates/PDD.gen.md` + `templates/VDD.gen.md`
**難度**：低

---

### G6 — PDD.gen.md：Responsive 細節不足

**缺失內容**：Breakpoint 元件行為矩陣、Grid 規格表、Micro-interaction 最低覆蓋數量

**現況**：
- §7 有 5 個斷點定義，但缺「各斷點上主要元件的行為矩陣」
- §6 有 Micro-interaction Catalog，但無最低覆蓋數量要求

**建議做法**：
- 在 §7 追加 `§7.1 Breakpoint 元件行為矩陣`（Nav/Card/Button/Table 在各斷點的尺寸/排版變化）
- 在 §7 追加 `§7.2 Grid 系統規格表`（各斷點的欄數/Gutter/Max-Width）
- 在 §6 Micro-interaction Catalog 前明訂最低覆蓋要求

**改動 template**：`templates/PDD.gen.md`
**難度**：低

---

## 工作量彙整

| 編號 | 改動 template | 改動性質 | 難度 | 需要知識補強 |
|------|-------------|---------|------|------------|
| G1 | VDD.gen.md | 追加 2 個子節 | 低 | 否 |
| G2 | SCHEMA.gen.md | 追加 1 個子節 | 低 | 否 |
| G3 | CLIENT_IMPL.gen.md + PDD.gen.md | 新增 Phaser 分支 | 中 | **是** |
| G4 | EDD.gen.md | 追加 1 個子節 | 中 | **是** |
| G5 | PDD.gen.md + VDD.gen.md | 各追加 1 個子節 | 低 | 否 |
| G6 | PDD.gen.md | 追加 1 個子節 | 低 | 否 |

---

## 知識補強區（研究結果）

> 以下由 web survey + 專家分析填入，作為 template 實作的設計依據

### §KR-G3：Phaser.js 架構知識

> 來源：Web Survey（Phaser 官方文件、Rex Notes、Ourcade Blog、GitHub 模板），2026-05-05

#### 標準目錄結構

```
project-root/
├── public/
│   └── assets/
│       ├── images/
│       ├── audio/
│       ├── fonts/
│       └── atlases/        # TexturePacker 產生的 PNG + JSON
├── src/
│   ├── main.ts             # 建立 Phaser.Game 實例
│   ├── config.ts           # GameConfig 設定
│   ├── scenes/             # 每個 Scene 一個檔案
│   │   ├── BootScene.ts    # 最小啟動，載入 loading bar 資源
│   │   ├── PreloadScene.ts # 主要資源預載入
│   │   ├── MainMenuScene.ts
│   │   ├── GameScene.ts
│   │   └── UIScene.ts      # HUD，疊加在 GameScene 上
│   ├── objects/            # 繼承 Phaser.GameObjects.* 的 Prefab 類別
│   ├── systems/            # 可重用遊戲系統（ScoreSystem、InventorySystem）
│   ├── plugins/            # 自定義 Phaser Plugin
│   ├── utils/              # 純工具函式（不引入 Phaser 實例）
│   ├── constants/          # SceneKeys.ts / EventKeys.ts / PhysicsCategories.ts
│   └── types/              # TypeScript 介面與型別定義
```

**依賴方向**：`scenes/` → `objects/` + `systems/`；`systems/` 不引用 `scenes/`；`utils/` 無依賴

#### Scene 生命週期

```
PENDING → START → LOADING → CREATING → RUNNING → PAUSED
                                              ↓
                                     SLEEPING / SHUTDOWN → DESTROYED
```

| 方法 | 呼叫時機 | 主要職責 | 禁止操作 |
|------|---------|---------|---------|
| `init(data)` | 最先，assets 未載入 | 接收上一場景資料、重置狀態變數 | 呼叫 this.add.* |
| `preload()` | init 後 | 向 Loader 排隊所有資源 | 建立 Game Object |
| `create()` | 載入完畢後一次 | 建立 GO、設定物理、綁定事件 | — |
| `update(time, delta)` | 每幀（RUNNING 狀態） | 輸入處理、AI、移動 | 重量級資源操作 |
| `shutdown` | scene.stop() 後 | 停止 tweens/timers、解除事件監聽 | destroy GO |
| `destroy` | scene.remove() 後 | 釋放所有資源、取消外部訂閱 | — |

**Shutdown vs Destroy**：stop() → SHUTDOWN（可 restart）；remove() → DESTROYED（不可復用）

#### 場景管理

```typescript
// 並行啟動（HUD 疊在 Game 上）
this.scene.launch('UIScene', { score: this.score });

// 完整切換
this.scene.start('MainMenuScene');

// 帶過場
this.scene.transition({ target: 'Level2Scene', duration: 1000, data: { level: 2 } });

// 場景間通訊三種模式：
// A. init data 傳遞（啟動時一次）
// B. Game Registry（全域 DataManager，解耦）this.registry.set('key', value)
// C. scene.get('TargetScene') 直接引用（強耦合，慎用）
```

#### Game Object 管理

| 需求 | 方案 |
|------|------|
| 單一獨特物件（玩家、Boss） | 直接 Sprite |
| 同類大量物件（子彈、粒子） | Group + Object Pool（killAndHide 回池） |
| 複合顯示結構（角色+血條+名稱） | Container（繼承 transform） |
| 需要 Physics 批次碰撞 | Physics Group（runChildUpdate: true） |

**Object Pool 設計原則**：maxSize 按峰值需求設定；get() 回傳 null 時不再建立；回池用 killAndHide() + body.reset()

#### 物理引擎選擇

| | Arcade Physics | Matter.js |
|---|---|---|
| 形狀 | 矩形/圓形 | 任意多邊形 |
| 效能 | 極高（AABB） | 中 |
| 旋轉碰撞 | 不支援 | 支援 |
| 適用場景 | 橫向捲軸、彈幕、Tilemap | 物理解謎、Ragdoll、不規則地形 |

**碰撞分類**：PhysicsCategories.ts 集中管理 Bitmask（PLAYER=0x0001, ENEMY=0x0002...）；Matter 用 setCollisionCategory + setCollidesWith

#### 資源管理策略

**三段式預載入**：
```
BootScene      → 只載入 loading bar 資源（幾 KB）
PreloadScene   → 載入所有共用資源（顯示進度條）
GameScene      → 按關卡載入私有資源；shutdown 時釋放
```

**跨場景共用資源**：不在 Scene shutdown 時釋放；Scene 私有資源在 shutdown 中 textures.remove() + cache.audio.remove()

**Texture Atlas**：相比多張散圖大幅減少 draw call；由 TexturePacker 產生 PNG+JSON

#### 輸入系統架構

```
瀏覽器 DOM 事件 → InputManager（全域）→ InputPlugin（每 Scene 一個）→ GO callbacks
```

- `createCursorKeys()` / `addKey()` / `once('keydown-ESC')` — 鍵盤三種模式
- Pointer API 統一滑鼠與觸控（setInteractive() + pointerdown/over/out/drag）
- Scene shutdown 時呼叫 `this.input.keyboard?.removeAllKeys()` 防洩漏

#### 音效系統

| | WebAudio（預設） | HTML5 Audio（fallback） |
|---|---|---|
| 位置音效 | 支援 | 不支援 |
| 多重同步播放 | 支援 | 需 audio tag pool |
| 行動裝置解鎖 | 需使用者互動 | 同上 |

**格式**：OGG + MP3 雙格式（涵蓋所有瀏覽器）；BGM 音量控制透過 WebAudio GainNode

#### 相機系統

- `setScrollFactor(0)` — HUD 元素固定在螢幕（不隨世界捲動）
- `startFollow(target, true, lerpX, lerpY)` — lerpX/Y 越小越平滑但延遲越大
- `cam.ignore(layer)` — 多相機時控制各相機可見圖層
- `cam.shake(200, 0.02)` / `cam.fadeIn(500)` / `cam.fadeOut(500)` — 常用效果

#### 架構模式建議

| 規模 | 推薦架構 |
|------|---------|
| 小型原型（< 1 個月） | Scene 組裝 + 簡單 GO 繼承 |
| 中型遊戲 | Scene 組裝 + Component Pattern |
| 大型 / 效能敏感 | bitECS（Phaser 4 官方路線） |

**設計原則**：Scene 負責組裝，不寫業務邏輯；優先組合而非多層繼承；ECS 不應過早引入

#### Phaser 專案文件必要章節（gendoc template 參考）

```
1. 專案概覽（遊戲類型、技術選型、目標平台）
2. 目錄結構說明（各 src/ 子目錄職責、命名規範）
3. Scene 架構圖（所有 Scene、切換關係、並行 Scene、資料傳遞方式）
4. Game Object 清單（自定義類別、繼承關係、哪些用 Object Pool）
5. 物理設計（引擎選擇理由、Collision Category 表格、碰撞矩陣）
6. 資源清單 Asset Manifest（所有 Atlas/Audio/Tilemap 的 key/路徑/載入 Scene）
7. 輸入映射表（Desktop/Mobile 操作對應）
8. 音效設計（BGM/SFX 列表、觸發條件、音量分層架構）
9. 效能策略（Pool 大小設定、Atlas 合圖策略、目標 FPS、最低裝置規格）
10. 開發環境與建置（啟動/建置命令、環境變數）
```

**必填欄位**：Scene 架構圖（標明入口 Scene）、Collision 碰撞矩陣、Asset Manifest（標明共用 vs Scene 私有）、輸入映射同時涵蓋 Desktop 與 Mobile

#### 參考連結
- 官方文件：https://docs.phaser.io/phaser/concepts/scenes
- Rex Notes（詳盡非官方）：https://rexrainbow.github.io/phaser3-rex-notes/docs/site/
- 官方 Vite+TS 模板：https://github.com/phaserjs/template-vite-ts
- Matter 碰撞插件：https://github.com/mikewesthad/phaser-matter-collision-plugin

---

### §KR-G4：Redis 快取設計知識

> 來源：Web Survey（Redis 官方文件、AWS Whitepaper、Martin Kleppmann、Games24x7），2026-05-05

#### 鍵命名規範

**標準格式**：`{env}:{service}:{entity}:{id}:{field}`

```
prod:auth:session:u123456:token
prod:game:leaderboard:season2026:global
staging:rate:api:u123456:login
```

**四層結構**：環境 → 服務（Bounded Context）→ 實體類型 → 識別子 → 欄位（選填）

**命名規則**：
- 全小寫，冒號 `:` 分隔，禁止空格
- 長度 20-40 字元（100 萬個 key，每多 30 字元 = 多 30MB）
- 避免通用名（`cache`、`user`、`data` 易衝突）
- 多租戶系統加 `tenant:{id}:` 前綴

**避免 Hot Key**：分片前綴（`leaderboard:shard:{uid%16}:`）、L1 本地快取（5-10 秒）、讀取路由至 replica

#### 資料結構選型表

| 資料結構 | 最適場景 | 記憶體 | 時間複雜度 |
|---------|---------|--------|-----------|
| **String** | 單值快取、計數器、Session Token、分散式鎖 | 最低（56 bytes 起） | O(1) |
| **Hash** | 物件多欄位（User Profile）；< 512 欄位用 ziplist 省記憶體 | 低（ziplist）→ 中（hashtable） | O(1) hget |
| **List** | FIFO/LIFO 佇列、最近活動紀錄、工作佇列 | 中 | O(1) lpush/rpop |
| **Set** | 不重複集合、標籤、線上用戶 | 中 | O(1) sadd/sismember |
| **Sorted Set** | 排行榜、優先佇列、滑動視窗限流 | 最高（~160 bytes/成員） | O(log N) zadd/zrank |
| **Stream** | 可靠消息、事件溯源、跨服務通知（需 ACK） | 高（~500 bytes/條） | O(1) XADD |

**選型決策樹**：
- 單值 → String；多欄位物件 → Hash；排序+分數 → Sorted Set
- 可靠消息（需 ACK/重放）→ Stream；廣播通知（不需確認）→ Pub/Sub

#### TTL 策略表

| 場景 | 建議 TTL | 失效策略 | 注意 |
|------|---------|---------|------|
| Web Session | 1800 秒，每次存取後 EXPIRE 延長（滑動） | 惰性過期 | 閒置超時 |
| Game Session | 300-600 秒 + KEEPALIVE ping | TTL + Pub/Sub 踢線 | 短 TTL 防僵屍連線 |
| API 快取 | 60-300 秒 + jitter | Cache-Aside + 隨機擾動 | 防雪崩 |
| 靜態參考資料 | 3600-86400 秒 | Write-through 更新 | 資料不常變動 |
| 限流計數器 | = 視窗大小（60/3600 秒） | 固定 TTL | 視窗結束自動清除 |
| 排行榜 | 無 TTL 或賽季末手動 DEL | 手動管理 | 長期資料 |
| OTP/驗證碼 | 120-300 秒 | 使用後立即 DEL（用後即焚）| NX 防重複發送 |
| 分散式鎖 | 業務操作預估時間 × 2 | 持有者主動 DEL，TTL 防 deadlock | PX 毫秒精度 |

**TTL Jitter（防雪崩必要技術）**：`ttl = base_ttl + random(0, base_ttl × 0.2)`

#### 限流設計

| 演算法 | Redis 結構 | 特性 | 適用場景 |
|--------|-----------|------|---------|
| 固定視窗 | String + INCR | 最簡單，有邊界突刺 | 簡單 API 保護 |
| **滑動視窗** | **Sorted Set** | **精準無突刺，記憶體較高** | **嚴格限流（支付、登入）** |
| 令牌桶 | Hash | 允許短暫突發，平均流量穩定 | 允許突發的 API |
| 漏桶 | List + 後台消費 | 嚴格均勻輸出 | 保護下游固定速率 |

**滑動視窗 Lua 腳本（原子性必要）**：
```lua
-- 移除視窗外舊記錄 → 計算當前數量 → 若未超限則 ZADD 當前請求
local window_start = now - window_ms
redis.call('ZREMRANGEBYSCORE', key, '-inf', window_start)
local count = redis.call('ZCARD', key)
if count < limit then
    redis.call('ZADD', key, now, now .. '-' .. math.random())
    redis.call('PEXPIRE', key, window_ms)
    return 1  -- allowed
end
return 0  -- rejected
```

**分散式鎖（Lua 釋放保證原子性）**：
```lua
-- 只有持有者能釋放（比對 unique_token）
if redis.call('GET', KEYS[1]) == ARGV[1] then
    return redis.call('DEL', KEYS[1])
end
return 0
```

#### 快取失效策略

| 模式 | 一致性 | 適用場景 | Spring Boot |
|------|--------|---------|------------|
| **Cache-Aside**（最常用） | 最終一致 | 讀多寫少 | `@Cacheable` + `@CacheEvict` |
| Write-Through | 強一致 | 讀寫均衡 | `@CachePut` |
| Write-Behind | 最終一致（有丟失風險） | 高寫入吞吐（計數、日誌） | 需自行實作 |

**Cache-Aside 寫入流程**：更新 DB → `DEL cache:key`（刪除而非更新，避免競態）

**Cache Stampede 防護**：分散式鎖 + 只讓一個請求回源 DB；或提前非同步重建快取

#### 遊戲/SaaS 常見場景

**排行榜（Sorted Set）**：
```
Key: leaderboard:{season}:{scope}
操作: ZADD（更新分數）、ZREVRANGE 0 99 WITHSCORES（前100）、ZREVRANK uid（個人排名）
多維排行榜: ZUNIONSTORE 合併週榜 + 月榜
```

**Session 管理（Hash）**：
```
session:{sid}        → Hash（儲存 uid/role/created 等欄位）
user:session:{uid}   → String（儲存 session_id，用於踢線）
踢線: GET old_sid → DEL session:{old_sid} → 建立新 session
```

**Pub/Sub vs Stream**：
- 廣播通知（遊戲實時事件）→ Pub/Sub
- 可靠消息（充值/訂單，需 ACK/重放）→ Stream + Consumer Group

#### 記憶體預算估算

**公式**：`Total = key_count × (88 + avg_key_len + avg_value_size) × fragmentation(1.1~1.3)`

| 資料結構 | 單個 key 大小（含 88 bytes key overhead） |
|---------|---------------------------------------|
| String | 88 + key_len + value_len |
| Hash（ziplist < 512 欄位） | 88 + Σ(field+value) × 1.2 |
| Sorted Set（skiplist） | 88 + 成員數 × (160 + member_len) |

**maxmemory 建議**：設為可用 RAM 的 75-80%；淘汰策略用 `allkeys-lru` 或 `volatile-lru`

**估算工具**：`MEMORY USAGE {key}`（線上查詢）；`redis-cli --bigkeys`（掃描大 key）

#### 部署模式選擇

| 模式 | HA | Scale | 適用場景 |
|------|----|----|---------|
| Standalone | 無 | 無 | 開發/低流量 |
| Sentinel | 是 | 讀 | 中等規模，資料量 < 50GB |
| **Cluster** | **是** | **讀+寫** | **大規模，資料量 > 50GB 或需橫向擴寫** |

**最小 Sentinel 配置**：1 master + 1 replica + 1 sentinel（共 3 節點）
**最小 Cluster 配置**：3 master + 3 replica（共 6 節點）

**Cluster Hash Tag**：`{user:u123}:session` 與 `{user:u123}:wallet` 同一 shard（只算 `{}` 內的 hash）

#### EDD 文件 Redis 章節必要內容（gendoc template 參考）

**A 類（必要，缺少設計不完整）**：
```
1. Key Schema 表（Key Pattern / 資料結構 / 業務說明 / TTL / 預估大小）
2. 資料結構選型說明（說明選用理由，不只列名稱）
3. TTL 策略表（每類 key 的 TTL 值 / jitter / 過期 fallback）
4. 限流設計（每個端點的演算法 / 參數 / Lua 腳本說明）
5. 快取模式（Cache-Aside 或 Write-Through，含 Cache Stampede 防護）
6. 記憶體預算表（各類 key 數量 × 大小，加總對比 instance 規格）
7. HA / 部署模式（Sentinel / Cluster 選型及節點數）
```

**B 類（生產系統標配）**：
```
8. maxmemory-policy 設定值與理由
9. 命名空間隔離設計（多服務/多租戶防碰撞）
10. 分散式鎖設計（如有：lock key 格式 / TTL / 釋放 Lua 腳本）
11. Pub/Sub 或 Stream 設計（channel/stream 定義 / consumer group）
12. 監控指標（cache hit ratio / memory usage / connected_clients / slow log）
```

**品質門檻 Checklist**：
- □ 每個 Key Pattern 均有 TTL 說明
- □ 所有限流端點明確說明演算法與 Lua 原子性保證
- □ 分散式鎖使用 NX + PX + Lua 釋放
- □ 記憶體預算估算存在（哪怕粗估）
- □ HA 模式及節點數說明
- □ maxmemory-policy 設定說明
- □ Cache-aside 有 Cache Stampede 防護

#### 參考連結
- Redis 鍵設計：https://redis.io/blog/5-key-takeaways-for-developing-with-redis/
- 限流教學：https://redis.io/tutorials/howtos/ratelimiting/
- AWS 快取策略：https://docs.aws.amazon.com/whitepapers/latest/database-caching-strategies-using-redis/caching-patterns.html
- 分散式鎖：https://redis.io/docs/latest/develop/clients/patterns/distributed-locks/
- 排行榜設計：https://redis.io/tutorials/howtos/leaderboard/
- 記憶體優化：https://redis.io/docs/latest/operate/oss_and_stack/management/optimization/memory-optimization/
- Sentinel 指南：https://redis.io/docs/latest/operate/oss_and_stack/management/sentinel/

---

## 評估確認記錄

- [x] 作者確認缺口清單正確
- [x] 作者確認知識補強內容足夠
- [x] 作者確認建議做法方向
- [x] 進入實作

---

## Fix Action List（具體實作清單）

> 原則：每個 Action 只改動 template 的生成指令，不涉及人工素材。
> 所有要求必須通過測試：「AI 在只有 PRD + EDD 的情況下能否獨立填滿這個欄位？」

| Action | 目標檔案 | 插入位置 | 改動性質 | 狀態 |
|--------|---------|---------|---------|------|
| G1-A | VDD.gen.md | §5 末尾（~272 行後） | 新增 §5.1 斷點字型縮放表 | [x] done |
| G1-B | VDD.gen.md | §6 末尾（~501 行後） | 新增 §6.1 Token 應用矩陣 | [x] done |
| G2-A | SCHEMA.gen.md | Migration 策略末尾（~201 行後） | 新增 §8.1 Migration 實作清單 | [x] done |
| G3-A | CLIENT_IMPL.gen.md | HTML5 路由後（~293 行後） | 新增 Phaser.js 目錄結構分支 | [x] done |
| G3-B | CLIENT_IMPL.gen.md | HTML5 場景結構後（~383 行後） | 新增 Phaser Scene 生命週期表 | [x] done |
| G3-C | PDD.gen.md | §5 Scene Architecture（~311 行後） | 新增 Phaser Camera/Pool 規格 | [x] done |
| G4-A | EDD.gen.md | §11.2 末尾（~1191 行後） | 新增 §11.3 Redis 完整設計 | [ ] |
| G5-A | PDD.gen.md | 替換 §13.1（221–232 行） | 改為 Component State Spec Table | [ ] |
| G5-B | PDD.gen.md | §13.1 之後 | 新增 §13.2 Mermaid stateDiagram | [ ] |
| G5-C | VDD.gen.md | §8 開頭（~503 行後） | 新增 §8.1 Animation Spec Table | [ ] |
| G6-A | PDD.gen.md | §7 末尾（~175 行後） | 新增 §7.1 Breakpoint 元件行為矩陣 | [ ] |
| G6-B | PDD.gen.md | §7.1 之後 | 新增 §7.2 Grid 系統規格表 | [ ] |
| G6-C | PDD.gen.md | §6.5 前（~183 行前） | 加入 Micro-interaction 最低覆蓋要求 | [ ] |

---

### Action 詳細規格

#### G1-A：VDD.gen.md — §5.1 Responsive Typography

插入於 §5 字型載入策略末尾（`---` 分隔線前，約第 272 行後）。

要求 AI 生成表格，行 = §5 Type Scale 各層級，列 = 320/375/768/1024/1440 五個斷點：
- 每格填具體 font-size（從 clamp() 公式計算）+ line-height
- 值從 §5 已有的 clamp() 示範推導，不得留 placeholder

---

#### G1-B：VDD.gen.md — §6.1 Token 應用矩陣

插入於 §6 Design Token 三層架構末尾（§8 Screen Visual Specs 開頭前，約第 501 行後）。

要求 AI 生成表格：Token 名稱 | 值 | 適用元件/場景 | 禁用場景：
- 覆蓋 color / spacing / radius / shadow 四類，每類 ≥ 4 個 token
- 所有值從 §6 Layer 1–3 推導，不得出現「請設計師填入」

---

#### G2-A：SCHEMA.gen.md — §8.1 Migration 實作清單

插入於 Migration 策略說明末尾（「資料量估算」節開始前，約第 201 行後）。

要求 AI 生成表格：版本號 | 檔名 | 操作說明 | 依賴版本 | Expand/Contract 階段 | 需要 Backfill Job：
- 依 EDD 功能模組完整列出，禁止留空
- 標示需要 Maintenance Window 的 migration（ADD NOT NULL / DROP COLUMN / 建唯一索引）
- Rollback 方式寫在 migration 檔末尾 `-- Rollback: <SQL>` 注解

---

#### G3-A：CLIENT_IMPL.gen.md — Phaser.js 目錄結構分支

插入於 HTML5 路由命名規範末尾（`---` 前，約第 293 行後）。

新增 `client_type == "phaser"` 條件分支，生成標準目錄結構：
- src/scenes/ src/objects/ src/systems/ src/constants/ src/utils/ src/types/
- constants/ 必須含 SceneKeys.ts / EventKeys.ts / PhysicsCategories.ts
- main.ts：Phaser.Game 實例建立；config.ts：GameConfig 定義
- 命名規範：Scene 檔 PascalCaseScene.ts；常數 UPPER_SNAKE_CASE

---

#### G3-B：CLIENT_IMPL.gen.md — Phaser Scene 生命週期表

插入於 Step 4 §3.2 HTML5 場景結構末尾（約第 383 行後）。

新增 Phaser 分支，生成 Scene 生命週期規格表：Scene 名稱 | init 職責 | preload 載入資源 | create 建立物件 | shutdown 釋放：
- 從 EDD 功能模組推斷所有 Scene
- 聲明 Scene Manager 切換策略（start/launch/sleep/wake 適用條件）
- 聲明 Scene 間資料傳遞方式（init data / registry / EventEmitter 三選一）

---

#### G3-C：PDD.gen.md — Phaser §5 Scene Architecture

插入於 §5 Scene Architecture Design 說明文字後（約第 311 行後），§6 UI Component 清單前。

新增 Phaser 條件分支：
- 物理引擎選型聲明（Arcade 或 Matter.js，需附理由）
- Camera 設計：World Camera（跟隨 Player）+ UI Camera（fixed，ignoreWorldCamera）
- Object Pool 設計表格：Pool 名稱 | GO 類別 | maxSize | 回池方式

---

#### G4-A：EDD.gen.md — §11.3 Redis 快取設計

插入於 §11.2 Capacity Planning Math 末尾（約第 1191 行後），§12.2 前。

分五部分：
- A. 鍵命名規範 + 鍵清單表（鍵模板/資料結構/TTL/TTL Jitter/用途）
- B. 資料結構選型規則表（場景/選用結構/理由）
- C. 限流鍵 Lua 腳本（滑動視窗原子操作）+ 端點清單
- D. 記憶體預算估算公式 + Top 3 場景表
- E. 快取穿透/擊穿/雪崩對策聲明（三種必填）

---

#### G5-A：PDD.gen.md — §13.1 改為 Component State Spec Table

替換現有 §13.1 Figma Handoff Checklist（第 221–232 行）。

改為要求 AI 生成互動元件狀態規格表：元件名稱 | Default | Hover | Focus | Active | Disabled | Loading | Error：
- 每格填具體 CSS property + value（使用 Design Token 名稱）
- 禁止填「顏色改變」等模糊描述
- 依 PDD §4 所有互動元件完整列出

---

#### G5-B：PDD.gen.md — §13.2 畫面狀態轉換圖

插入於 §13.1 之後。

要求 AI 為每個 PRD P0 功能對應的主要畫面生成 Mermaid stateDiagram-v2：
- state 名稱對應 §13.1 狀態欄位（Loading/Empty/Loaded/Error）
- 每個 P0 畫面一張圖

---

#### G5-C：VDD.gen.md — §8.1 Animation Spec Table

插入於 §8 Screen Visual Specs 開頭（第 503 行後），SCR 個別畫面規格前。

要求 AI 生成動畫規格表：動效名稱 | 觸發條件 | CSS Property | Duration | Easing | 代碼形式：
- 所有 §6.5 Micro-interaction 對應的 CSS 實作規格
- 複雜動效必須附 @keyframes 代碼片段

---

#### G6-A：PDD.gen.md — §7.1 Breakpoint 元件行為矩陣

插入於 §7 斷點清單末尾（第 175 行後），§8 Accessibility 前。

要求 AI 生成主要元件在各斷點的行為規格表：元件 | 320px | 375px | 768px | 1024px | 1440px：
- 禁止填「responsive」等模糊描述，每格需填具體尺寸/欄數/顯隱規則
- 必填元件：Navigation / Card Grid / Data Table / CTA Button / Modal

---

#### G6-B：PDD.gen.md — §7.2 Grid 系統規格表

插入於 §7.1 之後。

要求 AI 生成 Grid 規格表：斷點 | 欄數 | Gutter | Margin | Max-Width | 實作方式：
- 必填 5 個斷點，Max-Width 與設計一致
- 必須聲明統一使用 CSS Grid 或 Flexbox（不得混用）
- Container class 具體 CSS 代碼附在表格後

---

#### G6-C：PDD.gen.md — §6.5 Micro-interaction 最低覆蓋要求

插入於 §6.5 Micro-interaction Catalog 標題前（約第 183 行前）。

前置聲明最低覆蓋數量（低於此視為文件不完整）：
- 表單類 ≥ 3 個 / 導覽類 ≥ 2 個 / 資料回饋類 ≥ 2 個 / 遊戲類 ≥ 2 個（若適用）
- 以下 Catalog 表格必須全部填滿，不得留空白列
