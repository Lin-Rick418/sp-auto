# 空白輸入誤觸第一格技能（v2.23.5）

2026-09-12 使用者回報補 Buff 前仍會先施放 Left Shift。執行中的 Python 啟動時間晚於 `5de4e5e` 修正；探針紀錄在維護期間顯示 `shift=-:focus=0`，技能綁定紀錄為 `left=Skill1_1(0)`。

`BackgroundMovementPatch.UpdatePostfix` 每幀以 `Activator.CreateInstance` 建立輸入 DTO，但未初始化 `ClickSkillIndex`，因此為 `0`。無熱鍵不等於無技能：歷史原生程式碼證據 `84bbf07:diagnostics/guardian_bond/casting.asm` 中，`ProcessSkills` 的 `0xAD3351` 檢查熱鍵後，`0xAD335A` 另外比較 Inputs.ClickSkillIndex，任一符合都會在 `0xAD3382` 呼叫 `ReadySkill`。遊戲正常無點擊的紀錄使用 `click_skill=-1`。

這使 Buff 檢查的空白心跳仍可能指定第一格技能；當遊戲尚未提供 CaptureInputs 時，新建 DTO 的另一條路徑也有相同問題。Python 層無法靠清空 `shift_keys` 修正這個欄位。

修正以 `CreateNeutralInputs` 統一建立 DTO，將 `ClickSkillIndex` 明確設為 `-1`。只初始化新建 DTO，保留遊戲已捕捉的 NumPad 技能點擊，避免把前一幀 `ClickSkill` 排入的 Buff 一併清掉。

驗證：擴充現有 DLL 行為測試，舊 DLL 在「startup upkeep heartbeat cannot select Left Shift skill zero」失敗。新版測試涵蓋啟動空白心跳、NumPad 召喚請求、等待確認、停止、明確左右 Shift、攻擊釋放、CaptureInputs 無輸入及保留真實 Buff 點擊。測試使用假遊戲物件和實際建置 DLL，未操控執行中的遊戲。

需在關閉 Bot 與遊戲後安裝新版 DLL；只重啟 Python 不會替換已載入的 v2.23.4。
