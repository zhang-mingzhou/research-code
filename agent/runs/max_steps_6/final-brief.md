# 視覺語言模型幻覺研究簡報

## 研究問題
如何區分評測分數變化與可由視覺證據支持的改善？

## 證據整理
- POPE 將影像中的物體存在性轉為是非問題，以不同負例採樣策略檢查物體幻覺。 [S01:E01]
- VCD 對比原始影像與擾動影像的輸出分數，再用原始分佈限制候選詞，無須重新訓練模型。 [S02:E01]
- 後續研究質疑 POPE 的分數增益是否代表幻覺改善，並分析輸出分佈調整與自適應合理性限制的影響。 [S03:E01]

## 限制與下一步
- 物體存在性測試不能完整涵蓋屬性、關係及開放式長文本中的事實錯誤。 [S01:E02]
- 方法需額外的擾動影像前向計算；不同模型、資料及解碼設定下的效果須分別驗證。 [S02:E02]
- 評估 VCD 時應同時檢查準確率與 Yes 回答比例，不能僅憑單一分數宣稱視覺依據改善。 [S03:E02]

來源：
S01：POPE 物體幻覺評估；https://aclanthology.org/2023.emnlp-main.20/
S02：VCD 推理階段緩解方法；https://openaccess.thecvf.com/content/CVPR2024/html/Leng_Mitigating_Object_Hallucinations_in_Large_Vision-Language_Models_through_Visual_Contrastive_CVPR_2024_paper.html
S03：對比解碼增益的批判性再評估；https://proceedings.neurips.cc/paper_files/paper/2025/hash/2f89a23a19d1617e7fb16d4f7a049ce2-Abstract-Conference.html
