# 視覺語言模型物體幻覺的簡化復現與證據分析

澳門城市大學「數據科學前沿分析研究」課程作業。作者：張銘洲；學號：D26092110377；任課教師：劉文堅。
電郵：D2609210377@cityu.eu.mo。

本專案研究視覺語言模型的物體幻覺，包含文獻比較、視覺對比解碼實驗與離線工具迴圈分析。

## 報告與閱讀入口

- [期末整合論文 PDF（paper.pdf）](paper.pdf)。
- [文獻知識地圖](literature/knowledge-map.md) · [五篇比較表](literature/comparison.md)
- [完整實驗指標](results/vcd/metrics.csv) · [逐題預測](results/vcd/predictions.jsonl)
- [Agent 兩組執行紀錄](agent/runs/) · [比較表](agent/runs/comparison.csv)

## 結果與解讀

真實模型：`HuggingFaceTB/SmolVLM-256M-Instruct`，修訂 `d039ab0d4b9311b617e8ffec1d06c8464364aeb3`。

從 POPE 的 COCO 子集固定抽取 12 張影像，Random／Adversarial 各 72 題。三個條件共 432 筆模型回答。兩子集共享 36 道正例，合計 108 個不重複的影像—問題配對。

| 子集 | 一般解碼 Accuracy | VCD Accuracy | FP 一般／VCD | FN 一般／VCD |
|---|---:|---:|---:|---:|
| Random | 80.56% | 81.94% | 0／0 | 14／13 |
| Adversarial | 79.17% | 80.56% | 1／1 | 14／13 |

增益來自同一個重複正例，不代表兩次獨立驗證。假陽性未下降，因此不能宣稱已證明一般性的幻覺緩解。完整指標、逐題改變與影像群集 bootstrap 見 `results/vcd/`。

## 資料與來源邊界

- VCD：學生移植核心公式及擾動排程，實際執行小型模型；不是原論文表格的數值重現。
- Agent：學生自建來源卡片、固定規則工具迴圈及 validator；未使用 LLM、API 或教師 fixture。尚未取得教師指定來源包及 validator，也未取得教師對替代版本的認可。
- W01–W10：用於選題與證據記錄方法；教師預設樣例分數沒有混入模型實驗。

## 快速重跑

只核對已有結果或重跑 Agent，使用 Python 3.10 以上標準函式庫即可：

```bash
python src/analyze_results.py
python agent/run_agent.py --output rerun
python -m unittest discover -s tests -p test_core.py
python src/verify_artifacts.py
```

重跑模型推理，先建立獨立環境（本次實際使用 Python 3.10.22）：

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install torch==2.5.1 --index-url https://download.pytorch.org/whl/cu121
pip install -r requirements.txt
python src/prepare_pope.py
python src/run_vcd.py
python src/analyze_results.py
python -m unittest discover -s tests
```

沒有 NVIDIA GPU 時可安裝 CPU 版 PyTorch；推理會較慢。模型權重約 513 MB，不存入 GitHub。下載需連網，執行時不使用付費 API。本次主站連線不穩，公開權重經 `hf-mirror.com` 下載；模型版本及檔案雜湊見 `docs/model-download-manifest.json`。可用 `--model /path/to/local/model` 指定本地權重。

影像不隨倉庫上傳；`prepare_pope.py` 從 COCO 官方 S3 下載固定 12 張影像。題目版本固定為 POPE commit `08d957b917e5a378a2f99d35b6293c536a66298b`。請遵守原資料與模型的授權，來源位置及 SHA-256 見 `data/manifest.json`。

## 實驗設定

`alpha=1.0`、`beta=0.1`、noise step `500`；擾動沿用官方 sigmoid 排程。每張影像使用由檔名決定的固定雜訊種子，模型採 float16／eager attention／貪婪解碼，首次得到明確 Yes／No 即停止，最多 8 token。APC-only 在貪婪解碼下應保持原始 argmax，屬實作正確性檢查。

程式對相同影像、問題及前綴快取前向 logits；執行時間不能作為三種方法的速度基準。硬體及實際執行時間見 `results/vcd/provenance.json`。

## Agent 證據

`agent/runs/max_steps_3/` 保存未完成的失敗狀態，空白簡報不作人工補寫。
`agent/runs/max_steps_6/` 保存完成簡報、合約、schema、工具軌跡、觀測結果、評估、錯誤分析及來源聲明。

固定流程需搜尋 1 次、讀取 3 次、組合 1 次、校驗 1 次。六步成功只適用於此工具拆分；校驗器檢查來源卡片一致性，不獨立判定論文科學結論。外部評分不計入 Agent 工具預算。

## 目錄

```text
literature/     參考文獻庫、文獻比較表
src/            資料準備、模型推理、分析與驗證
data/           固定題目子集及來源 manifest
results/vcd/    真實模型輸出、指標、變更案例與 provenance
agent/          自建離線來源包、控制器、兩組完整紀錄
tests/          引用校驗與核心數值測試
docs/           方法差異、第三方授權與模型來源紀錄
paper.pdf       AT4 論文
```
