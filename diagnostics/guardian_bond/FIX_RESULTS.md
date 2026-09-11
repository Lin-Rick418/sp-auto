# GuardianBond 修正（探針 2.22.1）

已修改、編譯並安裝到本機 SpiritVale 的 on-demand 探針目錄。原始程式與 DLL 備份在 before_fix/。

## 已修改

- 只選擇 Summoning.Summoner 屬於本機玩家、仍存活且顯示中的召喚物；排除已知其他地圖，優先最近單位。
- 檢查實際 NumPad 技能欄是否為 GuardianBond；若探針比按鍵設定更早載入，收到空綁定技能請求時重新解析。
- 設定召喚物 UnitId、友方目標與單次技能輸入後，重新寫回值型別 Inputs/currentInputs，立即 ProcessSkills，再讀回供 RPC 使用的 Inputs。
- GuardianBond 不再使用延遲到下幀的 ClickSkill，也不會在找不到召喚物時退回無目標施放；尊重 CanHit、詠唱中與冷卻檢查。
- Python 以 BondSync 的 GuardianBond、Caster=true、Other=自己的存活召喚物確認成功。自身有別人提供的 buff 不算完成。
- GuardianBond 請求至少等待 2.5 秒再重試，以容納詠唱及同步；沒有召喚物時等待，旧探針缺少資料時提示更新。
- F8 進入補召喚物／Buff 階段時同時清除敵方聚焦，避免等待詠唱期間，下一次探針更新又把 CastTarget 改回怪物。

## 驗證

- 167 項 Python/探針回歸測試通過（tests.log）。
- 13 項直接執行編譯後 C# DLL 的行為檢查通過（native_tests.log）；使用值型別 DTO 與模擬遊戲單位，驗證擁有者、同幀處理、原生修改讀回、去重、無目標、錯誤綁定、冷卻、施法中與連結方向。
- 安裝後 DLL 雜湊相符，遊戲日誌確認載入 v2.22.1。
- 遊戲內實測成功：先送出使用者設定的 numpad5 召喚，讀到自己的召喚物 ObjectId=33086，再送出一次 GuardianBond。約一秒後同步回報 has_owned_bond=true、linked_unit_id=33086、error 與 cast_error 皆空（live_result.json）。
- 驗證結束已關閉測試控制（bot_active=false / probe_active=false），保留遊戲與成功建立的連結，沒有啟動打怪導航。

## 重現指令

在專案目錄執行：

```powershell
.\build_position_probe.ps1
.\.venv\Scripts\python.exe -m unittest test_guardian_bond test_spiritvale_red_dot_bot test_probe_cadence -q
.\diagnostics\guardian_bond\run_behavior_tests.ps1
```

關閉正式 bot 後，角色已進入遊戲時，可執行一次受限的施放驗證（結束後自動停止控制，不啟動打怪導航）：

```powershell
.\.venv\Scripts\python.exe diagnostics\guardian_bond\verify_live.py --cast --summon-key numpad5 --seconds 25
```

此處 numpad5 來自目前 SummonSkeleton 的使用者設定。測試只在沒有候選召喚物時送出一次召喚按鍵，再於合格候選出現後送出一次 GuardianBond。成功證據應為同步回來的 has_owned_bond=true 與 linked_unit_id，而非只有「input processed」日誌。
