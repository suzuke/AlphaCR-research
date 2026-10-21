# 繼續自我對打，為什麼沒有明顯變強？

**一句話：換輸入與出牌格式後，模型繼續練卻沒有明顯進步；測試三個解釋仍找不到原因，其中降低估計雜訊的方法因估值模型太弱，還不能判定。**


> AlphaCR 技術筆記 06。誠實的負面結果。數據：[official_ppo.json](../results/official_ppo.json)、[ppo_ema.json](../results/ppo_ema.json)、[vrpo_offline.json](../results/vrpo_offline.json)。

本文用語：PPO 是依對戰結果調整策略的訓練方法；IL 是模仿真人的學習；觀測合約是輸入與出牌格式。KL 衡量策略差異；EMA 是多輪權重的指數移動平均；critic 是估計局勢價值的模型。實驗組 PPO3／PPO4／PPO5 是同架構的不同訓練設定。

**Abstract.** After transferring the policy to a new observation contract, further self-play PPO stopped improving: three runs all stayed near 50-56% against their start point (about 52% in the 400-game final matches). We tested three explanations and rejected each. (1) "The KL limit holds the policy back": loosening it moved the policy further but strength did not rise. (2) "Averaging iterates (EMA) helps": none of three averaged models is distinguishable from the final iterate. (3) "Advantage variance is the bottleneck, so a Q-based variance-reduction estimator helps": an offline A/B failed all three gates, but the critic was too weak to draw a conclusion either way.

第三個假說沒有被否定：估值模型太弱，這個實驗還分不清方法效果與估值誤差。原英文摘要的概括不能取代這項限制。

## 背景

起點是轉移後的模型：自建模擬器線訓練出的 PPO 模型，權重逐位元組搬到新的觀測合約上（只改表頭），在新合約下對 IL 基準的勝率為 218/288 = 75.7%。之後三個 PPO run 從這裡繼續訓練，每輪 512 局 × 10 輪。

![PPO 評估](../figures/official_ppo.png)

## 現象

| Run | 設定差異 | 最終 400 局 vs 起點 |
|---|---|---|
| PPO3 | lr 3e-5、KL 0.05、熵 0 | 211/400 = 52.8% |
| PPO4 | 同上但熵 0.01 | 208/400 = 52.0% |
| PPO5 | lr 6e-5、KL 0.025 | 第 4 輪 50.5%，之後停止 |

期中 200 局評估偶爾出現 56.5%，但 400 局最終評估回到 52%：200 局的 95% 區間約 ±7 個百分點，單點看起來的進步多半是雜訊。

## 假說 1：KL 限制把模型綁住了

PPO3 與 PPO4 離 IL 起點的 KL 只有約 0.03（上限 0.1），所以懷疑是限制太緊。PPO5 放寬 lr 與 KL：每輪 KL 升到 0.046、0.053、0.059、0.060、0.065，模型確實走得更遠，但第 4 輪勝率 50.5%。

**否定**：放寬限制沒有帶來強度，問題不是「被綁住」。（附帶發現：熵獎勵 0.01 能避免策略熵持續下降，但同樣沒帶來強度。）

## 假說 2：對 PPO 迭代做事後平均（EMA）會更強

| 對戰（400 局） | 勝率 | 95% 區間 |
|---|---:|---|
| 迭代 5–9 等權平均 vs PPO4 final | 48.5% | [43.6, 53.4] |
| EMA（0.7）vs PPO4 final | 50.7% | [45.9, 55.6] |
| EMA（0.7）vs 轉移後的起點模型 | 50.5% | [45.6, 55.4] |

三個區間都涵蓋 50%。**否定**（在這個偵測力下）：400 局只能偵測約 ±5 個百分點以上的差距，平均沒有可辨識的好處。只試了一組 decay，也沒做訓練中即時 EMA。

## 假說 3：優勢估計雜訊太大，Q-based 降變異估計器會有幫助

離線 A/B：固定同一個策略，用 1,024 局訓練獨立 critic，在 512 局留出集上比較三種估計。預先設定三個門檻，**全部未通過**：

| 指標 | 基準 | Q-boost | 門檻 |
|---|---:|---:|---|
| advantage 標準差 | 0.164 | 0.170（+3.5%） | 至少降 20% |
| 兩半梯度 cosine | 0.208 | 0.192 | 要更高 |
| critic 解釋變異量（對 MC return） | 0.196 | 策略自帶 value 為 0.405 | 不低於策略 |

這不能解讀成「Q-boost 沒用」或「變異不是瓶頸」：critic 的解釋變異量（0.196）低於策略自己的 value head（0.405），表示 critic 太弱，估計器的效果與 critic 誤差分不開。

這個假說的狀態是「在此設定下未被支持，尚未判定」。另外，這 512 局留出集已被看過，日後調參必須換新的驗證集。

## 現在知道什麼

三個假說都沒有解釋停滯。剩下的候選是模型容量或輸入資訊的上限（例如缺少對手隱藏資訊的信念建模）。這一條線尚未驗證，也就是說：**我們不知道為什麼卡住**，只知道三個常見原因看起來不是。官方線上選單的預設仍是 轉移後的起點模型。

## 學到的事

1. 把「放寬限制後 KL 變大但勝率不升」當成診斷，比再調一輪參數有資訊量。
2. 200 局的單點進步不要當真；先算區間。
3. 負面結果要附上偵測力：「沒有差異」和「看不出差異」是兩件事。
