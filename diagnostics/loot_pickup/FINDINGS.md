# 指定掉落物拾取修正（2026-09-12）

已建置、安裝並載入探針 v2.23.0。安裝 SHA256：
`726FB3CC86B4B8E25302668D42AEF8E960A0060084978C58DAFEBB30DD2AA646`。

## 根因與本機原生程式證據

舊版 `ApplyPendingLootPickup` 接收 `LootInteractObjectId`，但只用它啟動 200 ms 的 Pickup 熱鍵注入，沒有把它寫入 DTO。指定 ID 因而失去作用，實際仍等同 V 的範圍拾取。

本機 GameAssembly.dll 的路徑：

- `CaptureInputs` RVA `0xABCEC0` 的互動分支，在 `0xABE66F` 把網路 ObjectId 寫到 Inputs + `0x48`，然後呼叫 `ProcessClickedInteractable`。Click 位於 DTO + `0x3C`。
- `ApplyInputs` RVA `0xABA8C0` 在 Click 分支讀取 `InteractableId`（DTO + `0x48`）；`0xABAFC0` 解析 ObjectId，`0xABAFF0` 呼叫 `ProcessClickedInteractable`。
- `ProcessClickedInteractable` RVA `0xAD2450` 設定互動目標；`ProcessTargeting` 處理接近距離與互動。
- `LootDrop.Interact` RVA `0xAAEEA0` 先檢查 `App.IsServer`，只有伺服器才呼叫 `PickupSingle`（`0xAD1A10`）。這解釋了直接在客戶端呼叫無效。
- V 的 `Hotkey.Pickup` 是 47，由 `ApplyInputs` 的 `0xABB115` 起始分支呼叫 `PickupArea`（`0xAD16E0`），不是 ProcessSkills。
- `SendInputsToServer` RVA `0xAEA750` 序列化同一份 `PlayerInputDto` 並送出 RPC。

可用 `../guardian_bond/inspect_native.py` 重建上述反組譯；原始輸出保留在本機本資料夾的 asm 檔案。

## 新流程

每個有效拾取序號只送一次 `Click=true, InteractableId=掉落物 ObjectId`，同時清除 UnitId、LootId、移動、FastCast 與熱鍵。本機走 `ApplyInputs → ProcessTargeting`，同一份 DTO 送到伺服器。下一幀放開 Click；物品仍存在時沿用 Python 的 500 ms 重試。

重新檢查快取物件的 ID、activeInHierarchy、地圖、非裝備類型與 IsLocked；技能忙碌時跳過本次，等後續重試。停用 bot 或拾取時吸收舊序號，避免重新啟用時播放舊點擊。取消舊 V 策略檔與派發分支。Python 的稀有度、所有權、導航、預覽和消失判定規則沿用既有流程；訊息改為「已送出指定拾取」，不宣稱背包已收到。

## 驗證

- `python -m unittest discover -q`：213 項通過。
- `run_behavior_tests.ps1`：19 項通過（使用建好的探針 DLL 和假遊戲型別驗證 ID、鎖定、地圖、序號、同幀 DTO／RPC 與停用行為）。
- `../guardian_bond/run_behavior_tests.ps1`：13 項通過。
- 正常關閉遊戲與 bot 後安裝，安裝檔 hash 比對通過；重開後日誌確認載入 v2.23.0。
- 遊戲內單件測試：自己的 Tungsten，ObjectId `64472`，距離約 `0.693`、InteractionRange `1`、未鎖定。這是一次普通材料的診斷，正式設定仍為 Legendary。

實際探針紀錄：

```text
Targeted loot input sent: seq=1789151404 requested=64472 interactable_id=64472 unit_id=0 click=True hotkeys=0
```

送出後約 1.44 秒，連續三次快照觀察不到 `64472`；最後一份快照 timestamp `1789151405384`。鄰近 `19387 / 51757 / 27105 / 40975` 仍在，沒有被 V 範圍掃走。此證據包含指定輸入與目標消失，未另外量測背包材料數量增量。

`verify_live.py` 預設只掃描；`--pickup ID` 僅對原生範圍內、未鎖定的 Legendary 送一次請求。診斷普通材料需顯式加 `--test-common`。執行前拒絕搶占其他控制器的有效 IPC，結束時清除輸入。

## 後續 Common 完整流程實測

依使用者要求降低品質測試，以 `verify_common_flow.py` 執行真正的 `run_bot`，只在記憶體中的設定副本把最低品質設為 Common。未修改正式設定檔，也未再修改拾取程式或探針。

27.06 秒內自動選取、接近、發出指定 ID 拾取並確認五件自己的 Common Flax 消失：`46718 / 30177 / 42 / 28557 / 30327`。最遠的初始導航距離為 7.35，送出時均已在 1 單位的原生互動範圍內。每個目標均以三份不同時間戳的快照確認消失，耗時約 1.25–5.30 秒；同時探針日誌核對到指定 InteractableId、Click=True、UnitId=0、Hotkeys=0。

部分已消失目標在 Python 更新判定前有短暫 `missing cached loot` 重試，隨後皆正常換下一件，未見持續卡住。完整資料見 `common_full_flow_result.json`。測試結束由原本的 finally 流程停止輸入，正式設定檔逐位元組比對無變動，仍為 Legendary。原 bot 已依暫停狀態重新啟動。
