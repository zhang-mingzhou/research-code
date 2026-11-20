# 視覺語言模型物體幻覺的簡化復現與證據分析

澳門城市大學「數據科學前沿分析研究」課程作業。作者：張銘洲；任課教師：劉文堅。

本倉庫同時支援 AT3 累積式大作業與 AT4 期末整合報告。兩份報告使用同一組可追溯實驗，分別呈現作業交付與研究論證。

## 報告

- [AT3 累積式大作業 PDF](reports/AT3-report.pdf) · [可編輯 Word](reports/AT3-report.docx)
- [AT4 期末整合論文 PDF](paper.pdf) · [可編輯 Word](reports/AT4-paper.docx)
- [一頁文獻綜述摘要](reports/AT3-literature-summary.pdf)
- [Agent 比較分析](reports/AT3-agent-analysis.pdf)
- [文獻知識地圖](literature/knowledge-map.md) · [五篇比較表](literature/comparison.md)

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
- Codex 協助程式、文獻核對和文稿整理；作者須於提交前核對內容與課程要求。

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
reports/        兩份報告、附件及可編輯來源
literature/     參考文獻庫、文獻比較表
src/            資料準備、模型推理、分析與驗證
data/           固定題目子集及來源 manifest
results/vcd/    真實模型輸出、指標、變更案例與 provenance
agent/          自建離線來源包、控制器、兩組完整紀錄
tests/          引用校驗與核心數值測試
docs/           模板格式、方法差異與來源紀錄
paper.pdf       AT4 論文
```

報告使用提供的 FDS 模板：繁體中文、正文兩端對齊、新細明體／Times New Roman、三線表及原款式封面。學號與電郵未提供，保留空欄。倉庫目前為私有，正式提交需確保教師擁有讀取權限。
