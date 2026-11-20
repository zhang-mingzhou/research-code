# 方法與第三方來源

本專案 `src/run_vcd.py` 的視覺擾動排程、雙路 logits 對比及 adaptive plausibility constraint 參考 Leng 等（CVPR 2024）與 [DAMO-NLP-SG/VCD](https://github.com/DAMO-NLP-SG/VCD) 的 `vcd_utils/vcd_add_noise.py`、`vcd_utils/vcd_sample.py`。上游採 Apache-2.0，授權全文保存在 [VCD-LICENSE.txt](VCD-LICENSE.txt)。原作者及貢獻者保留其權利。

學生實作改為 SmolVLM-256M、固定 POPE 小子集、貪婪解碼與 Yes／No 停止規則；自行撰寫資料準備、快取、逐題記錄、分析及驗證程式。這些變更使結果只構成方法的簡化移植，不構成原論文結果表的重現。

POPE 題目來自 [AoiDragon/POPE](https://github.com/AoiDragon/POPE)，影像來自 COCO 官方 S3；題目、版本與影像雜湊見 `data/manifest.json`。模型來源為 [HuggingFaceTB/SmolVLM-256M-Instruct](https://huggingface.co/HuggingFaceTB/SmolVLM-256M-Instruct)，版本及下載雜湊另見模型 manifest。上游資料及權重各依其原有授權使用，沒有改授權為本專案作品。

Agent 來源卡是本專案對文獻的中文整理，不是論文逐字引文或教師來源包。Word 封面來自使用者提供的課程模板。
