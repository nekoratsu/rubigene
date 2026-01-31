# Rubigene GUI「NGSLレベル」「CEFRレベル」ドロップダウン真っ黒問題の詳細解析

## 現象
- 「NGSLレベル」「CEFRレベル」のQComboBox（ドロップダウン）が真っ黒に表示され、中身の選択肢が見えない。
- 他のQComboBoxやQWidgetは正常に表示されている。

## コード・スタイルシート調査
### 1. QComboBoxの生成箇所
- `rubigene/gui/components.py` で `self.ngsl_combo = QComboBox()` および `self.cefr_combo = QComboBox()` を生成。
- `addItems` で選択肢を追加し、setCurrentIndexで初期値も設定。
- 追加のsetStyleSheetは行っていない。

### 2. QSS（スタイルシート）
- `rubigene/gui/style.qss` でQComboBoxに対し以下のスタイルが適用：
  - `background-color: white;`（通常）
  - `color`指定なし（親のQWidget/QLabelは`#333`）
  - QComboBox QAbstractItemView（ドロップダウンリスト）も `background-color: white; selection-background-color: #4a90d9; selection-color: white;` で黒指定はなし。
- 他の箇所でQComboBoxに対し `setStyleSheet` で黒色や背景色を上書きしている箇所は見当たらない。

### 3. 現象の推定原因
- QComboBox自体・QAbstractItemViewともに `background-color: white;` で黒指定はない。
- しかし「真っ黒」になる場合、**OSのダークモード**や**Qtのテーマ自動適用**、または**QComboBoxの親Widget/GroupBoxのsetStyleSheet**が影響している可能性が高い。
- 特に `criteria_group.setStyleSheet()` でQGroupBox全体にカスタム背景色やborderを指定しているため、QComboBoxの子要素にも影響が及ぶ場合がある。
- もしくは、QComboBoxのテキスト色（color）が明示的に指定されていないため、ダークモード時に背景白＋文字白（見えない）となることも。

## まとめ
- QComboBox自体のQSSは「白背景」だが、親GroupBoxやOSテーマの影響で「黒背景」や「文字色が背景と同化」している可能性が高い。
- **親GroupBoxのsetStyleSheetやOSダークモード、QComboBoxのcolor未指定**が主な原因候補。
- 修正にはQComboBoxのcolor, background-colorを明示的に指定し、親のsetStyleSheetの影響を受けないようにする必要がある。

---
（このファイルは自動生成されました）
