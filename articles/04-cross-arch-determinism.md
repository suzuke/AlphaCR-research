# 跨架構逐 tick 決定性：x86_64 與 ARM64 的 50 局完全一致

> AlphaCR 技術筆記 04。只談方法與結果，不談實作細節。數據：[results/parity.json](../results/parity.json)。

**Abstract.** We ran the same game logic natively on x86_64 (Intel, Linux VM) and ARM64 (Apple silicon) and compared full per-tick state dumps byte for byte. Across 50 games with 50 distinct deck pairs (227,770 ticks in total) there was not a single mismatch. The comparison uses no tolerance, no reordering and no skipped fields; a deliberately corrupted input is rejected by the comparer (negative control). Scope: fixed command logs, not every card or seed.

## 為什麼要做

[第 1 篇](01-determinism.md) 講過決定性是所有數字的地基。但「在我這台機器上可重現」還不夠：訓練可能跑在 ARM 筆電，大規模資料產生則可能搬到 x86 伺服器。浮點行為、執行順序、記憶體配置的差異，都可能讓兩個架構慢慢走歪，所以要實測，不能假設。

## 怎麼比

- **輸入固定**：同一份開局與同一份有序命令紀錄，兩邊讀入，不重排、不重送。
- **比整個狀態，不是比勝負**：每個 tick 輸出單位與塔（位置、血量、擁有者）、玩家（聖水原始值、手牌、換牌佇列）、單位狀態、護盾、buff、投射物、範圍效果、技能冷卻與終局資訊，整份 JSON 逐位元組比較。不認識的欄位不會被略過。
- **嚴格判準**：tick 必須從 0 連續到終局，兩邊長度相同，末筆為終局；任何缺列、多欄位、未終局都算失敗。
- **負控制**：刻意把某個 tick 的聖水加 1，比較工具必須失敗並指出是哪個 tick、哪個欄位。沒有這個步驟，「全部一致」可能只是比較器壞了。
- **觀測不改變狀態**：每次輸出狀態後重新讀 checksum，確認讀取本身沒有副作用。

## 結果

| 階段 | 內容 | 結果 |
|---|---|---|
| 初始 | 1 局含 99 筆命令 | 5,450 tick 完整狀態逐位元組一致 |
| 即時命令 | 在 tick 300／900／1500／2100 即時提交出牌 | 8/8 回條相同，3,602 tick 一致 |
| 同程序第二局 | 釋放並重建遊戲後再跑一局 | 第二局輸出與第一局逐位元組相同 |
| 擴大樣本 | 50 局、50 組不同雙方牌組 | **227,770 tick，0 不一致** |

擴大樣本的覆蓋度：46 局有進化單位實際上場、17 局有冠軍卡實際上場、25 局進入延長賽。這些條件都由場上實際出現的單位判定，不是看牌組宣告。樣本先依固定雜湊排序選定，選定後不因結果換樣本。

## 限制

- 這是固定命令紀錄的重演，不代表所有卡牌、所有種子、所有即時命令組合都已驗收。
- 兩台主機的 CPU 世代與核心數不同（Apple M3 Max；Intel Core i5-8500 上的 Docker Linux VM，原生指令執行、無指令轉譯），所以吞吐量比較不能解讀成純指令集優劣；本文只談正確性。
- 同程序重建只證明「同一開局」的釋放與重建，不證明不同開局交替或長時間無記憶體洩漏。

## 學到的事

1. 先寫負控制，再相信「全部一致」。
2. 比較要完整、嚴格、不留容差；容差會把真正的差異吞掉。
3. 樣本選擇規則要在看結果之前固定。
