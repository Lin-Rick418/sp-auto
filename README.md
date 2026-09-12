# SpiritVale 內存／NavMesh 導航器

這個 Windows 工具由三部分組成：

- BepInEx 輕量 Loader 隨遊戲啟動，只檢查按需載入請求，不掃描場景。
- BepInEx 探針從遊戲已載入的 IL2CPP 物件讀取玩家、目前地圖分流、敵怪、掉落物與相機方向，並呼叫 Unity `NavMesh.CalculatePath` 計算路徑。
- Python 導航器讀取路徑，以背景 `PostMessage` 傳送 WASD；進入掉落物拾取範圍後則短按 V。

整個程式不擷取或分析遊戲畫面，也不再包含紫色／綠色光柱辨識程式碼。

> 請只在遊戲規則允許自動化的情況下使用。

## 需求

- Windows、Python 3.11+
- SpiritVale Steam 版
- BepInEx 6 IL2CPP（目前安裝於遊戲目錄）

安裝 Python 套件：

```powershell
python -m pip install -r requirements.txt
```

## 建置與安裝探針

在本目錄執行：

```powershell
.\build_position_probe.ps1 -Install
```

腳本會使用系統 C# 編譯器、已安裝的 .NET 6 runtime 與 BepInEx references，產生 `SpiritValeProbeLoader.dll` 與 `SpiritValePositionProbe.dll`，並分別安裝到：

```text
C:\Program Files (x86)\Steam\steamapps\common\SpiritVale\BepInEx\plugins\SpiritValeProbeLoader
C:\Program Files (x86)\Steam\steamapps\common\SpiritVale\BepInEx\ondemand\SpiritValePositionProbe
```

若遊戲當時正在執行，腳本會完成建置但延後安裝且不強制關閉遊戲。請關閉 SpiritVale、再次執行同一個 `-Install` 命令，再啟動遊戲。遊戲啟動後，`BepInEx\LogOutput.log` 應只先出現 `Loading [SpiritVale Probe Loader 2.11.0]`；執行任一 Python 工具後才會出現 `Loading [SpiritVale Position Probe 2.22.0]`、各 IPC 初始化訊息與 `Memory navigation probe v2.22.0 loaded on demand`。

要建立可傳給其他電腦的精簡發佈包：

```powershell
.\build_release.ps1
```

ZIP 會輸出至 `dist\SpiritValeBot-v2.23.4-win64.zip`，包含 Loader、按需探針、可攜式 LocalAppData IPC、一鍵安裝、Python 虛擬環境設定與啟動腳本，不包含測試、原始 C#、執行期 JSON、個人裝備篩選規則或本機報告。

## 執行

先重啟遊戲並進入角色地圖，再執行預覽模式。Python 會先要求 Loader 載入探針並等待完成：

```powershell
python spiritvale_red_dot_bot.py --no-loot
```

預覽模式會顯示純內存雷達，但不傳送按鍵。確認玩家、敵怪與黃色 NavMesh 路徑正常後，再使用：

```powershell
python spiritvale_red_dot_bot.py --run
```

若不需要自動拾取：

```powershell
python spiritvale_red_dot_bot.py --run --no-loot
```

其他選項：

```powershell
python spiritvale_red_dot_bot.py --list-windows
python spiritvale_red_dot_bot.py --title "SpiritVale" --run
```

舊版的 `--calibrate`、`--radius` 與 `--test-green-loot` 已移除；世界座標導航與內存拾取都不需要影像校正。

## 按需載入與休眠

遊戲啟動時不會載入完整探針；只有 10 KB 左右的 Loader 常駐。Python 會寫入 `spiritvale_probe_load_request.json`，Loader 確認請求在 15 秒內且尚未處理後，才從 `BepInEx\ondemand` 載入探針。Python 會等待相同 request ID 的 `spiritvale_probe_loader_state.json` 成功回覆，不會在探針未就緒時送出遊戲按鍵。

探針載入後也不會無條件掃描。導航／預覽以 `probe_active` 心跳控制一般世界快照；F2 使用獨立的 `party_follow_active` 輕量心跳，只讀取隊伍與單一目標。F8 與 F2 都關閉、Python 安全結束或心跳超過兩秒時，NavMesh 與狀態 JSON 都停止更新。F6／獨立拍賣與背包工具仍可透過各自的一次性 IPC 請求工作，不會因此啟動世界掃描。BepInEx 不支援可靠的執行期完整卸載，因此探針首次載入後會留在程序內，但保持休眠。

F7 狀態會以 `loot_scan_active` 心跳傳給探針；F7 關閉時完全不解析或輸出掉落物。F7 與 F8 同時開啟時採用增量快取：每 400 ms 最多處理 24 件，超過約 2 ms 就延至下一輪，最多輸出與玩家最相關的 96 件，正在追蹤的掉落物永遠優先更新。`LootDrop.OnEnable`／`Remove` 用來維護候選清單，完整 Unity 場景搜尋只用於每張地圖的初次補種或生命週期掛鉤不可用時的 10 秒節流 fallback。掉落物不再計算未使用的 viewport 座標，出口只在地圖身分變更時掃描，狀態檔則由背景執行緒合併寫入。

## 正常／火車／自動刷王模式

獨立設定檔 `spiritvale_mode_config.json`：

```json
{
  "mode": 3,
  "boss_name": "Scorpion King",
  "boss_summon_item_name": "Soldier Termite",
  "boss_spawn_timeout_sec": 10.0,
  "boss_death_confirm_sec": 1.0,
  "boss_loot_settle_sec": 3.0,
  "lock_mouse_to_monster": true,
  "left_click_after_mouse_lock": false
}
```

- `mode: 1`（正常）：抵達目前內存敵怪後留在攻擊距離，等怪物死亡或失效才選下一隻。
- `mode: 2`（火車）：抵達目前內存敵怪後立刻將該 ObjectId 暫時略過，接著選距離最近的下一隻，不等待死亡。
- `mode: 3`（自動刷王）：先以遊戲正式 `PlayerSave.UseConsumable(ConsumableData)` 流程（背包 UI 點物品的同一條路）使用 `boss_summon_item_name`，只鎖定名稱符合 `boss_name` 的王且不自動換頻；王消失並確認死亡後等待 `boss_loot_settle_sec`，只拾取自己的 Legendary，全部清空才開始下一輪。F7 與 `--no-loot` 不會停用這個必要的刷王拾取階段。
- 使用召喚物品前會先放開所有按鍵（WASD 與左右 Shift）並沉澱 `boss_use_key_release_settle_sec`（預設 0.25 秒）才使用；因為 Shift 技能仍按住時使用消耗品會被遊戲拒絕。
- `boss_spawn_timeout_sec`：使用召喚物品後等待王生成的上限，預設 10 秒；物品不存在、數量不足、使用遭拒或逾時都會安全暫停，重新切換 F8 才重試。
- `boss_death_confirm_sec`：王從快照消失後持續多久才視為死亡，預設 1 秒。
- `boss_loot_settle_sec`：確認王死亡後保留的延遲掉落等待窗，預設 3 秒。
- `lock_mouse_to_monster: true`：以 `--run` 執行且 F8 一般導航正在追蹤畫面內怪物時，持續對遊戲視窗送出背景 `WM_MOUSEMOVE`，不會移動或占用 Windows 實體游標；預設為 `false`，所有 `job_type` 都完全依此設定，不會強制覆寫。
- `left_click_after_mouse_lock: true`：每次取得新的怪物目標後，第一次成功送出背景游標位置時，對遊戲視窗送出一次背景左鍵；點擊成功後等換怪或重新取得目標才再點一次。點擊失敗時後續迴圈會重試，預設為 `false`。

火車模式使用 `target_skip_cooldown_sec` 避免立刻選回同一隻怪。模式設定在 Python 啟動時讀取，修改後需重新啟動程式。預覽模式不會真的換怪、送出背景滑鼠訊息或點擊，只會顯示 `TRAIN PREVIEW ... WOULD SWITCH`。背景滑鼠與左鍵不切換焦點，也不移動實體游標；怪物離開畫面、F8 暫停、F2 跟隨、拾取、角色死亡或目標失效時停止控制，怪物重新可見後自動恢復。探針會要求 Unity 在失焦及最小化時繼續更新；WASD 會換算成世界方向，並在 `PlayerController.Update` 結束時直接呼叫遊戲的 `ProcessMovement` 與 `SendInputsToServer`，所以移動不再依賴遊戲視窗位於最上層。左右 Shift 會依遊戲目前的 Hotkey 綁定自動換算為 `PlayerInputDto.Hotkeys`／`HotkeysHeld`，支援持續按住及牧師短按。開啟 `lock_mouse_to_monster` 時，探針也會把畫面內怪物的 ObjectId 與世界座標寫入 `UnitId`、`ClickPosition` 與 `FastCastPosition`，再直接執行目標及技能處理，因此最小化時技能仍能對準目前怪物；舊的背景 `WM_MOUSEMOVE` 仍保留作前景視覺同步。V、9、0 與背景左鍵目前仍保留視窗訊息路徑。若目標被放棄後再次取得，即使 ObjectId 相同，也會視為新的目標取得並允許再點一次。

需要使用其他模式設定檔時可傳入：

```powershell
python spiritvale_red_dot_bot.py --mode-config .\spiritvale_mode_config.json --run
```

## 快捷鍵

只有 **一個** 快捷鍵：`F8`。按 `F8` 會跳出「控制選單」，所有功能都在選單內以按鈕挑選，一次只執行一項；不需再記憶多顆按鍵。選單會即時顯示各開關的目前狀態，未啟用的功能（例如未載入的查價或大量購買）不會出現對應按鈕。關閉選單（按「關閉選單」、關視窗或 `Esc`）不會執行任何動作。

`F8` 只有在**該實例的遊戲視窗位於前景時**才會回應：`GetAsyncKeyState` 是全域讀取，同時多開多個 BOT 時，若不限制前景會每個實例都各自彈出選單。因此請先點選要控制的遊戲視窗，再按 `F8`，就只會開那一個實例的選單。

啟動時一般導航預設為**開啟**（沿用 `--run` 即稼動的行為，等同以前按 `F8` 前就在跑）。若想改成啟動即待機、由選單手動開啟導航，在設定檔加入 `"start_paused": true`。

> 註：本文其他章節為沿用舊稱，仍以 `F2`（純跟隨）、`F5`（價格視窗）、`F6`（重新查價）、`F7`（內存拾取）、`F8`（一般導航）、`F9`（安全結束）、`F4`（大量購買）、`Del`（篩選表）指稱各功能；這些現在都改由上述 `F8` 選單的對應項目觸發。

選單項目：

- **一般導航（開/關）**：切換一般怪物／拾取導航；Mode Config 啟用 `lock_mouse_to_monster` 時也會切換怪物滑鼠鎖定。純跟隨啟用時不受此項影響，且不會鎖定滑鼠。
- **純跟隨模式（開/關）**：選擇後開啟角色名稱輸入視窗並啟用獨立純跟隨；再次選擇即關閉。
- **內存拾取（開/關）**：切換內存掉落物拾取。
- **拾取品質**：選擇 `Common`、`Rare`、`Unique` 或 `Legendary` 以上；選擇後立即套用並保存至設定檔。
- **裝備詞條篩選表**：顯示或隱藏依裝備名稱區分的詞條篩選表。先選裝備名稱，再替該名稱獨立填寫 232 種附有中文說明的 `StatType` 最低畫面值與「至少符合 N 項」，或按「此名稱一律分解」忽略全部素質；搜尋框同時支援英文代碼與中文名稱。
- **大量購買 Card**：僅在正式 BOT 模式出現，顯示常駐大量購買視窗；輸入必須保留的金幣餘額與單卡價格上限後，持續購買單價嚴格小於上限的 `Card`。再次選擇只會將同一視窗帶到前景。
- **價格視窗（顯示/隱藏）**：顯示或隱藏背包價格視窗（需啟用查價）。
- **重新查價**：單次在背景重新從遊戲內存讀取背包並查價，同時顯示價格視窗；已有查價工作時不會重複啟動。啟動腳本時不會自動查價或開窗。
- **安全結束程式**：安全結束程式並放開所有按鍵。

## 背包裝備自動篩選

按 `Del` 開啟 `spiritvale_equipment_filter.json` 的圖形化編輯器。上方名稱清單從目前背包與穿戴裝備讀取，並以不受翻譯或強化前綴影響的 `item_id` 保存；切換名稱後，下方 232 種詞條、最低值及「至少符合 N 項」都是該名稱自己的設定，不會與其他裝備共用。每列空白表示不使用；有填值的列以遊戲 `Formula.GetSubstats` 轉換後的畫面詞條做 `裝備值 >= 最低值` 比較。例如只替 Red Shell 的 `MATK% (MatkMult)` 填 `2`，Red Shell 的 `MATK +2%` 符合、`+1%` 不符合，其他名稱不會套用這條規則。`至少符合 N 項` 是每個名稱獨立的 N-of-M 規則。

選定名稱後按「此名稱一律分解」並確認，可讓該名稱忽略全部素質與 N 值；名稱清單會標示 `[一律分解]`，詞條欄位暫時停用。此模式可再按一次取消，原本的詞條規則會保留並恢復使用。模式只在按「儲存全部名稱」或「儲存並立即執行」後生效，而且只分解背包中未收藏的同名裝備；收藏品仍是硬性保護，不會取消收藏或分解。

勾選啟用並儲存後，程式每 100 秒重新從內存取得最新背包，依每件裝備的 `item_id` 只套用同名 profile。沒有建立有效規則或一律分解模式的裝備名稱會安全略過，絕不因別種裝備的規則而被分解。掃描當下已收藏的裝備也會無條件保護並略過，絕不自動取消收藏或分解；其餘已設定名稱的裝備符合自己的規則者會透過遊戲正式 RPC 設為收藏，不符合者才會逐件分解，而一律分解模式會直接分解未收藏的同名裝備。每次收藏及分解都以 UID、基礎物品 ID、所在位置、新鮮 request ID 與伺服器回寫結果驗證；分解端還會再次拒絕收藏或穿戴中的裝備，因此即使掃描後狀態改變也不會誤拆。可用「儲存並立即執行」先跑一次；沒有任何有效名稱 profile 時即使設定檔寫成啟用也不會執行。

本機角色死亡時，探針會以獨立的 25 ms 安全輪詢偵測 `Health.IsAlive=false`，不等待一般 250 ms 導航快照；Python 會立即放開 WASD、左右 Shift 及任何尚未釋放的按鍵，並封鎖 9、0、V 等所有後續遊戲按鍵，直到角色恢復存活。未提供本機存活狀態的舊探針也會進入安全停止，避免在死亡狀態下繼續操作。

## 跟隨玩家模式

F8／預覽從 `MapInstance.Players` 匯出其他玩家；清單不可用時才掃描目前 Unity 場景。F2 不使用這條全玩家掃描路徑，而是直接讀取 `CurrentParty.Members`，並只解析被鎖定隊友的 `CachedPlayer`／`GetPlayer()`。隊伍名單包含每位成員的地圖、伺服器實例與頻道索引。

按 F2 後會喚醒輕量隊伍快照，再跳出輸入框列出目前同地圖的隊伍成員。輸入完整角色名稱即可鎖定；非隊伍玩家無法選取。名稱不分大小寫，但必須唯一且完全一致。鎖定後以 PlayerId 保持身分，並直接從該隊伍成員取得單一玩家物件與 NavMesh 目標，不掃描全部玩家。

F2 會顯示隊伍成員所在的「第幾頻道」。目標與本機不在同一伺服器實例時先呼叫遊戲的 `TrySwitchToInstance`，實例相同但頻道不同時呼叫 `RequestChannelSwitch`；切換期間放開所有移動鍵並保留 PlayerId 鎖定。新分流出現同一玩家後，當輪就建立玩家 NavMesh 路徑並接續跟隨，不必再按 F2。

F2 是不依賴 F8 的純跟隨模式：每輪都以 `target_kind: player` 更新 NavMesh 路徑，超過雙方碰撞半徑加 `follow_player_stop_padding_world` 時送出 WASD，進入停靠距離後停止 WASD。`job_type = 1` 會先確認所有已啟用的召喚物／Buff；若有缺漏會放開 WASD 與左右 Shift、逐項補放，全部確認存在後才開始跟隨。路徑有效且玩家可用時會持續按住 Left Shift 與 Right Shift，即使已經停靠也不放開；此模式不選怪、不進入戰鬥流程、不追蹤掉落物，也不按 V。F7 與 F8 的切換狀態會保留，等再次按 F2 關閉後才套用於一般導航。

玩家消失、死亡、隱藏、切圖、快照失效或路徑未就緒時會顯示 `FOLLOW LOST`／`FOLLOW WAIT PATH` 並立即放開 WASD 與左右 Shift；同一 PlayerId 重現且路徑恢復後才繼續。召喚坐騎維護仍優先執行，等待 9、0 與坐騎確認期間也會安全放開移動鍵。

## 斷線自動重登

以 `--run` 執行且 F8 一般導航或 F2 純跟隨任一啟用時，Python 會持續送出有效期兩秒的自動化心跳。角色斷線後會立即放開 WASD、Shift 與 V，探針先讓遊戲內建重連接手；若仍未恢復，便透過遊戲的 `UILogin` 與 `UICharacterSelect` 介面重新連線並選回斷線前的角色 UID，不使用固定螢幕座標。

單次登入逾時後預設等待 10 秒，最多嘗試五次。五次都失敗時會顯示 `PAUSED AFTER 5 ATTEMPTS` 並停止操作登入介面；手動登入成功仍會自動恢復導航，也可先關閉 F2 並暫停 F8，再重新啟用需要的模式以重置重試次數。預覽模式、F2 與 F8 都停用、F9 結束、Python 心跳消失或遊戲程序退出時都不會自動登入。此功能不會重啟已關閉或崩潰的遊戲，也不會產生第二份 Python 程序。

## 導航規則

1. 探針透過 `App.Game.Map.Get(player.NetworkObject)` 取得玩家所在的 `MapInstance`。
2. 只匯出 `CombatTeam.Enemy`、存活且顯示中的怪物，並排除訓練假人。
3. Python 鎖定最近敵怪的 FishNet ObjectId；正常模式在死亡、消失、追蹤逾時、路徑失效或脫困失敗時換怪，火車模式則會在抵達後立即換怪。
4. 探針對鎖定怪物計算完整 NavMesh path；Python 只接受 schema、時間戳、request id 與 target id 全部相符的完整路徑。
5. 路徑失效、探針超過 750 ms 未更新、切換地圖、選單／斷線或資料破損時立即停鍵。
6. 抵達距離由玩家與怪物碰撞半徑加 `arrival_padding_world` 決定；進入距離後停止 WASD。`job_type` 0/1 保留 F8 的長按 Shift 組合，`job_type` 2 在滑鼠成功鎖定怪物後改為隨機間隔短按 Left Shift。
7. 探針會匯出目前場景的 `MapExit` 傳送出口。F8 會略過位於出口安全圈內的怪物與掉落物，也會拒絕穿越安全圈的 NavMesh 路徑；角色若一開始已在圈內，只允許沿路徑往外離開。F2 純跟隨不套用此限制。
7. 近身後以怪物最低 `health_ratio` 監測戰鬥進展；停滯時脫離重接一次，第二次停滯會封鎖該 ObjectId 並換怪。

NavMesh 只處理靜態可行走區域。舊版透過小地圖顏色偵測的藍色動態危險區已移除。

## 內存掉落物拾取

1. 探針優先從目前 `MapInstance.Loots` 取得掉落物，清單不可用時使用 `LootDrop` 生命週期快取；只在每張地圖初次需要補種時掃描一次 Unity 場景。清單以固定批次與時間預算增量更新，不會因地面道具總數增加而讓單輪工作無上限。
2. 探針在建立掉落物快照前排除 `Equip`／`Equipment`；不再讀取地面 `LootDrop.ItemData`、轉換詞條、查拍賣或嘗試拾取裝備。
3. 對保留的非裝備掉落物，探針將 `LockDto.PlayerId` 與本機 `PlayerController.PlayerId` 比對，輸出本人、外人與公開物品的所有權，並以遊戲的 `IsLocked(player)` 標示本機目前是否可互動。
4. F7 開啟時，非裝備掉落物維持稀有度規則；外人或公開的 Legendary 只有自然進入 `InteractionRange + padding`（不再加玩家碰撞半徑）且不超過硬上限後才會互動。伺服器判定拾取只看玩家「中心點」是否在 `InteractionRange` 內、不採計碰撞半徑，因此 `memory_loot_range_padding_world` 可為負值把按鍵點內縮到範圍內（預設 -0.2，讓角色貼近才按）。
5. 合格的遠距自有非裝備掉落物會優先於怪物導航；Python 以 `target_kind: loot` 要求探針計算 NavMesh 路徑。同一 ObjectId 連續出現兩個 snapshot 後才開始追蹤或拾取。進入有效範圍後會先放開 WASD 與 Shift，再以 `loot_interact` 序號與 `loot_interact_object_id` 要求探針點選指定掉落物；物品仍存在時每 500 ms 重試。
6. 預覽模式顯示 `WOULD PICK UP TARGET`，不送任何輸入或拾取意圖。

拾取透過遊戲原本的指定互動流程：探針把掉落物的 ObjectId 寫入 `PlayerInputDto.InteractableId`，同一份 DTO 設定 `Click=true`、`UnitId=0`，清除移動與技能熱鍵，先執行本機 `ApplyInputs → ProcessTargeting`，再經 `SendInputsToServer` 傳送。伺服器解析指定 ID，依正常距離、鎖定、背包與分配規則執行 `LootDrop.Interact → PickupSingle`。探針會重新檢查快取物件的 ID、存活顯示狀態、地圖、類型與鎖定；技能施放中或等待技能選取目標時，留待下次請求重試。

`UnitId` 用於技能／戰鬥單位；`InteractableId` 才是此處的網路互動目標。舊實作雖收到掉落物 ID，實際只注入 `Hotkey.Pickup`（V），由伺服器 `ApplyInputs` 執行範圍拾取。直接在客戶端呼叫 `LootDrop.Interact` 則被遊戲的 `App.IsServer` 檢查擋下。新版不再使用 V、200 ms 按住或 `loot_pickup_strategy.txt`；每個序號只送一次指定點擊，物品仍存在時由 Python 的 500 ms 冷卻重試。

紀錄 `Targeted loot input sent` 會列出請求序號、目標 `interactable_id`、`unit_id`、`click` 與熱鍵值。這只表示輸入已送出，並非拾取成功；消失判定仍沿用掉落物快照。實際遊戲可能因背包滿、鎖定或掉落物已被其他玩家取走而拒絕。調查與測試位於 `diagnostics/loot_pickup/`。

地面裝備拾取前估價功能已廢棄並移除；原因是伺服器不會在拾取前同步可供完全一致比價的完整 `EquipData`。背包 F6 查價不受影響。

## F4 持續限價大量購買 Card

F4 只在 `--run` 正式 BOT 模式啟用。非阻塞視窗會要求兩個金額：「必須保留的金幣餘額」與「單張 Card 價格上限」。按「開始大量購買」後，BOT 以查詢文字 `Card`、`ItemType=Card` 持續監看，單價必須嚴格小於上限；沒有符合項目時每 1 秒重新搜尋，成交後則立即搜尋下一筆。視窗會顯示已購數量、總花費、最新餘額、最後成交與目前狀態。

每次只處理一筆上架，並依單價、listing ID 選擇最低項目。探針在送出前重新讀取 `PlayerSave.PlayerData.Coins`，購買量為 `min(上架數量, floor((目前餘額－保留金額) / 單價))`，再附上精確 listing ID、數量、查詢時的單價與 listing 版本呼叫遊戲的 `PlayerSave.VendingPurchase` 完整購買流程；不能從客戶端直接呼叫底層 `VendingClient.PurchaseAsync`，否則拍賣服務只會回覆未解析的 `OperationPending`。價格或版本變動、已售出等確定未成交狀態會在 1 秒後重查；餘額不足、背包滿、未授權等錯誤會停止。購買逾時或結果不明時會立即停止且不重送，避免重複成交。

按「停止」、關閉 F4 視窗或按 F9 都會阻止建立新要求。若已有一筆交易送出，狀態會顯示「停止中」並等候該筆結果；它仍可能完成。餘額等於保留金額時自動停止；若仍有可用餘額但目前買不起上架項目，則繼續等待更便宜的新上架。保留金額保證假設監看期間沒有其他程式或手動操作同時花費；若偵測到實際餘額低於保留值，BOT 會立即停止。

## 不開拍賣 UI 查價

探針 v2.22.0 可在遊戲登入角色後按需載入，直接呼叫遊戲既有的 `RequestVendorItemList` 搜尋流程；不需要開啟或操作一般拍賣 UI。它沿用目前登入連線與遊戲的請求限制；裝備收藏與分解只透過有 UID 防護的獨立 IPC 開放。Mode 3 的消耗品使用同樣只接受新鮮、正式執行且角色存活的導航 IPC，先確認背包數量，再經 `PlayerController.Save` 呼叫遊戲的 `PlayerSave.UseConsumable(ConsumableData)`（背包 UI 使用物品的同一條路），不直接修改背包。

查詢名稱並列出價格，以及單價超過 5 萬的項目：

```powershell
python spiritvale_auction_query.py "Mind Resonant Headphones"
```

套用精煉、價格或其他 filter：

```powershell
python spiritvale_auction_query.py "Mind Resonant Headphones" --min-refine 6 --max-refine 6
python spiritvale_auction_query.py "Mind Resonant Headphones" --max-price 50000 --has-gem
```

基礎能力用可重複的 `--stat TYPE=VALUE` 指定，所有條件必須同時符合。例如圖片中的 `INT +3`、`MATK +2`、`MATK +2%`：

```powershell
python spiritvale_auction_query.py "Double Mind Sapphire Crown" --stat Int=3 --stat Matk=2 --stat "Matk%=2"
```

其中 `Matk%` 會轉成遊戲內部的 `MatkMult`。這些條件只送出裝備本體的基礎能力，不會加入精煉值、每精煉加成、卡片或卡片效果。遊戲的拍賣 API 只提供能力的 `MinimumValue`，因此條件語意為 `INT >= 3`、`MATK >= 2`、`MATK% >= 2`。

可用 filter 包含 `--min-price`／`--max-price`、等級、精煉、潛力、數量、寶石、卡片、物品類型、裝備類型、職業與物品分類。`--page-size` 上限為 100；有下一頁時，輸出會提供可傳給 `--cursor` 的值。需要完整資料（包含伺服器回傳的物品 payload）時加上 `--json`。

查詢器會寫入 `spiritvale_auction_request.json`，並只接受 `spiritvale_auction_results.json` 中相同 request ID 的結果。請求 30 秒後失效，一次只會執行一筆。這組一般查價 IPC 維持唯讀；F4 使用下述獨立且有額外限價防護的購買 IPC。

要單獨讀取背包裝備並依畫面詞條完全一致查價：

```powershell
python spiritvale_inventory_pricer.py
```

主導航腳本不會在啟動時查背包或打開價格視窗；需要時按 F6 執行一次，導航不會等待查價完成。價格視窗把名稱與詞條相同的裝備合併成 `x數量`，超過 50,000 的最低價排在最前面；可用滑鼠滾輪或 Previous／Next 換頁。

程式以內存取得最新背包，再讓背包與拍賣物品都通過遊戲自己的 `Formula.GetSubstats` 轉成畫面屬性；本機以基礎物品名稱／ID，以及無視順序的完整顯示詞條集合過濾。精煉、卡片、潛力與數量不參與詞條比對；`favorite: true` 的收藏裝備會在拍賣查詢前排除。沒有完全相同上架樣本的裝備會明確標示，不會套用相近詞條價格。完整 schema 2 結果寫入 `spiritvale_inventory_price_report.json`，包含收藏略過、已定價、無樣本及高價數量。

## 首領迴避

`avoid_boss: true` 時，程式會在解析每份內存快照時判定當前地圖的首領：**取所有存活敵怪中等級（由 `display_name` 的 `Lv.NN` 解析）最高、且該最高等級只有唯一一隻的怪物**。遊戲對所有怪物（含首領）都回報 rank 為 `Normal`，無法用 rank 區分，因此改以「等級最高且全場唯一」判定，例如一群 Lv.31–35 雜怪中唯一的 Lv.40 Scorpion King。若最高等級平手（兩隻以上）或完全沒有等級資訊，就不標記，避免誤判。

判定為首領的怪物會在快照模型上被標記 `avoid = true`（其餘為 `false`）。一般與 F2 跟隨的選目標都會排除 `avoid` 的怪物，**永遠不把首領當攻擊目標**。除此之外的反應由 `boss_response` 決定：

- **`switch_channel`（預設）**：偵測到首領就換頻道。探針把當前頻道與頻道總數寫進快照（`channel_index` 0-based、`channel_count`），程式算 `下一頻道 = (channel_index + 1) % channel_count`（到最後一個頻道會繞回第一個），透過 IPC 請探針呼叫遊戲的 `RequestChannelSwitch`。因為王不是每個頻道都刷，換一次通常就落到乾淨的頻道。換頻後會等 `boss_channel_switch_settle_sec` 秒讓新頻道快照重填，才重新判定，避免用切換前的舊畫面重複換頻。狀態列顯示 `BOSS CHANNEL SWITCH - 首領 <ObjectId> Lv.<等級> → 頻道 <號碼>`。
- **`flee`**：不換頻，改用「主動保持距離」。每幀在選目標前檢查，若首領進入 `boss_flee_radius_world`（世界單位）內，清掉當前攻擊目標、朝「玩家→首領的反方向」換算 WASD 走開，該幀跳過戰鬥，狀態列顯示 `BOSS FLEE - 遠離首領 <ObjectId> Lv.<等級> (<距離>m)`。

`switch_channel` 在任一幀若頻道資料尚未取得（`channel_count` 為 0）會自動退回 `flee` 那幀的行為當保底。頻道清單由伺服器在**登入／換圖／換頻**時推送，探針以 Harmony hook 掛在 `UIServerDisplay.DrawChannels` 攔截並寫進 `channel_index`/`channel_count`。因為 bot 跑圖時本來就會在地圖間移動（走進 boss 圖前必經換圖），實際運作時頻道資料在需要換頻前就已備妥；只有在「探針按需載入後、尚未經過任何一次伺服器推送就先遇到首領」的少數情況才會落到 `flee` 保底。

`avoid_boss` 預設為 `false`（關閉，首領照打）；`avoid = false` 即代表玩家可以打該怪。此判定與行為只在 `--run` 的一般戰鬥導航生效，F2 純跟隨只套用「不鎖定首領」的排除。

## IPC 檔案

- `spiritvale_navigation_request.json`：Python 寫入版本、request id、`target_kind`（`none`／`monster`／`loot`／`player`）、鎖定 ObjectId、Unix 毫秒時間戳、`movement_keys`、相機換算後的 `movement_world`、`shift_keys`，以及可選的怪物聚焦 `focus_target_object_id`／`focus_target_world`；另含 `probe_active`、`party_follow_active`、`bot_active` 與自動重登設定。`movement_keys` 只允許 `w`、`a`、`s`、`d`；`movement_world` 是探針寫入 `PlayerInputDto.Move` 的世界座標 `Vector3Int`。`skill_key_request_id` 與 `skill_key`（`numpad0`～`numpad9`）用於一次性的背景技能觸發，探針只接受新的 request id。`probe_active` 控制一般世界掃描；`party_follow_active` 只允許隊伍限定跟隨資料；`bot_active` 只授權正式執行與自動重登。超過兩秒的檔案不授權任何操作，且探針會送出零移動向量停步；召喚坐騎及檢查按鍵完全由 Python 控制。
- `spiritvale_probe_load_request.json`／`spiritvale_probe_loader_state.json`：Python 與常駐 Loader 的一次性載入握手；request ID 必須相符且請求不可超過 15 秒。
- `spiritvale_memory_state.json`：探針以原子替換方式輸出本機玩家、其他玩家、敵怪（包含滑鼠鎖定使用的 viewport 座標）、非裝備掉落物、地圖／分流及對應 NavMesh corners；斷線時以可選的 `relogin` 物件回報等待、連線、選角、錯誤或暫停狀態。
- `spiritvale_auction_request.json`／`spiritvale_auction_results.json`：唯讀拍賣搜尋的單次請求與結果，使用 request ID 避免讀到舊資料。
- `spiritvale_card_purchase_request.json`／`spiritvale_card_purchase_result.json`：F4 每輪的一次性 Card 搜尋／購買 IPC；包含保留金額、嚴格單價上限、request ID 與大量購買確認值。搜尋與購買共用拍賣 IPC lock，單筆以預期單價和 listing 版本防止成交條件變動；結果會回傳成交量、花費及前後餘額，不明結果不會重送。
- `spiritvale_inventory_request.json`／`spiritvale_inventory_equips.json`：一次性分列背包與穿戴中裝備，並匯出原始詞條及遊戲轉換後的畫面詞條；讀取本身不修改背包。
- `spiritvale_favorite_request.json`／`spiritvale_favorite_result.json`：以 UID、物品 ID、背包／穿戴位置及目標布林值切換收藏；請求必須在 15 秒內且結果需驗證實際狀態。
- `spiritvale_dismantle_request.json`／`spiritvale_dismantle_result.json`：只接受精確 UID、物品 ID 與明確確認字串的單件背包分解；收藏或穿戴中裝備會被拒絕，結果需驗證 UID 已從背包消失。

上述 JSON 與 IPC lock 都存放在 `%LOCALAPPDATA%\SpiritValeBot`，因此程式資料夾可放在任意可寫入位置，也能直接移到不同 Windows 使用者。舊影像辨識使用的 `spiritvale_memory_position.json`、`blocked_areas.jsonl`、`blocked_captures`、測試截圖與歷史 bot 日誌已從工作區清理，現在的內存／NavMesh 版本不再讀寫它們。

## 常用設定

`spiritvale_bot_config.json` 的導航設定使用 Unity 世界單位：

有效的 `probe_active` 心跳會每 250 ms 更新一般導航資料，其他玩家每 400 ms 更新；只有 `loot_scan_active` 同時有效時才會在每個 400 ms 週期內以 24 件／約 2 ms 上限增量更新非裝備掉落物。`party_follow_active` 則只更新隊伍名單、單一跟隨目標及其 NavMesh 路徑，不建立全玩家、怪物、掉落物或出口快照。拍賣／背包 IPC 維持低成本的 400 ms 請求檢查，不會啟動世界掃描。

- `memory_snapshot_timeout_ms`：探針資料最大有效時間，預設 750 ms。
- `arrival_padding_world`：碰撞半徑之外的停靠距離。
- `map_exit_avoidance_padding_world`：F8 在傳送出口互動距離與玩家碰撞半徑之外再保留的安全緩衝，預設 3.0 世界單位；同時套用於怪物與掉落物路徑，F2 不套用。
- `path_waypoint_tolerance_world`：略過已抵達 NavMesh corner 的容差。
- `target_max_chase_sec` / `target_skip_cooldown_sec`：追蹤逾時與略過時間。
- `combat_health_progress_epsilon` / `combat_no_progress_sec`：有效掉血幅度與近身無進展門檻。
- `combat_reengage_back_ms` / `combat_reengage_side_ms`：疑似不死怪第一次停滯時的脫離動作。
- `combat_blacklist_absence_reset_sec`：封鎖 ObjectId 持續消失多久後允許再次選取。
- `stuck_position_epsilon_world` / `stuck_timeout_sec`：以真實世界座標判斷卡住。
- `memory_loot_min_rarity`：最低拾取稀有度，可設為 `Common`、`Rare`、`Unique` 或 `Legendary`。
- `memory_loot_range_padding_world`：在掉落物 `InteractionRange` 之上的拾取容差（不再加玩家碰撞半徑），預設 **-0.2** 世界單位；伺服器只看玩家中心點是否在 `InteractionRange` 內，故用負值把按鍵點內縮到範圍內、確保生效。
- `memory_loot_pickup_hysteresis_world`：開始放開按鍵後的退出遲滯，預設 0.25 世界單位；只會擴到物品真正的 `InteractionRange`，避免邊界抖動反覆重算放鍵等待，又不會站在伺服器範圍外送撿取。
- `memory_loot_max_distance_world`：允許按拾取鍵互動的絕對距離上限，預設 3.0；更遠的合格自有物品會透過 NavMesh 接近，外人與公開物品只在自然進入範圍後處理。
- `memory_loot_confirm_frames` / `memory_loot_clear_confirm_frames`：掉落物出現與消失的穩定確認幀數。
- `memory_loot_interact_cooldown_ms`：物品仍存在時重試拾取鍵的間隔，預設 500 ms。
- `memory_loot_release_settle_ms`：進入拾取距離後先放開 WASD、Left Shift、Right Shift，至少經過一個完全無按鍵迴圈才送撿取；預設 50 ms。指定拾取封包本身也會清空移動與技能鍵。
- `memory_loot_chase_timeout_sec`：單次主動追蹤 Legendary 的時間上限，預設 20 秒。
- `memory_loot_retry_cooldown_sec`：Legendary 路徑無效、逾時或脫困失敗後的重試冷卻，預設 15 秒。
- `auto_relogin_enabled`：是否允許執行模式在 F8 一般導航或 F2 純跟隨啟用時自動重登，預設開啟。
- `auto_relogin_disconnect_grace_sec`：玩家消失後確認斷線的時間，預設 3 秒。
- `auto_relogin_builtin_wait_max_sec`：等待遊戲內建重連的最長時間，預設 30 秒；內建流程提早結束時會立即接手。
- `auto_relogin_attempt_timeout_sec` / `auto_relogin_retry_delay_sec`：每次登入上限與失敗後的間隔，預設 30／10 秒。
- `auto_relogin_max_attempts`：自動登入次數上限，預設 5；F8 關閉再開啟可重置。
- `debug_window` / `radar_size_px`：內存雷達開關與大小；預設關閉，需要雷達時將 `debug_window` 設為 `true`。
- `pricing_enabled` / `pricing_auto_start`：是否啟用背包查價，以及舊版自動啟動設定；目前預設 `pricing_auto_start: false`，按 F6 才查詢。
- `pricing_window_enabled` / `pricing_page_rows`：價格視窗及每頁列數，預設開啟且每頁 8 組。
- `pricing_high_value_threshold`：高價門檻，預設 50,000；只有嚴格大於門檻才標示為高價。
- `pricing_timeout_sec` / `pricing_request_delay_sec`：單次 IPC 等待上限及拍賣頁面間隔，預設 25／0.2 秒。
- `follow_player_enabled`：是否提供 F2 跟隨玩家模式，預設開啟。
- `follow_monster_radius_world`：舊版跟隨打怪半徑，為相容既有設定檔而保留；F2 純跟隨不使用此值。
- `job_type`：`0` 為未滿 64 等、F8 持續按住 Left Shift；`1` 為召喚、F8 持續按住 Left Shift 與 Right Shift；`2` 為牧師，滑鼠成功鎖定怪物後會立即短按 Left Shift，之後依 `priest_left_shift_tap_min_interval_ms` 與 `priest_left_shift_tap_max_interval_ms`（預設 300–1300 ms）的隨機間隔重複，每次按住時間由 `priest_left_shift_tap_hold_ms`（預設 50 ms）決定。牧師短按只在 F8 正式追蹤且滑鼠成功鎖怪時發生，不用於掉落物。滑鼠鎖定與點擊仍完全依 mode config。只有 `1` 會在 F8 一般導航或 F2 純跟隨啟用時持續確認 `MountController_C`；若尚未騎乘，Python 固定短按 `summon_reanimation_key`（預設 `9`），等待 `summon_reanimation_delay_ms`（預設 750 ms）後短按 `summon_mount_key`（預設 `0`）。若尚未確認騎乘，會依 `summon_mount_key_retry_delay_ms`（預設 400 ms）只重試 `0`，4 秒總確認期限不會因重試而延長；逾時後才等待 2.5 秒重新從 `9` 開始。確認坐騎控制器出現前會放開移動鍵並暫停所有導航。F2 的 Shift 規則完全獨立，三種職業都固定同時按住左右 Shift。舊設定中的 `always_hold_lshift` 會被忽略。預設為 `1`。
- `summoner_checks`：套用於 `job_type = 1` 的正式 F8 導航與 F2 純跟隨。F8 選單可個別啟用召喚物與 Buff，並指定右側 NumPad 0–9。召喚物依目前 `SummonDisplays_C` 判斷，一般 Buff 依目前 `StatusDisplays_C` 判斷；`GuardianBond` 需要探針 v2.22.1，會驗證召喚物擁有者、在同一處理階段指定目標並施放，再以同步的對外連結確認成功。自身有別人提供的 GuardianBond 不算完成。沒有自己的存活召喚物時等待；GuardianBond 每次至少等待 2500 ms 再重試，其餘技能依 `summoner_check_settle_ms` 與 `summoner_check_retry_delay_ms` 設定。缺少項目時會先放開 WASD 與左右 Shift，每次只觸發一項；全部確認存在後才接續坐騎確認與導航。預設各項關閉。
- 正式執行時，每次開啟一般導航都會開始一筆運行時間與金幣總收入統計。金幣由 `PlayerSave.PlayerData.Coins` 讀取，只累加餘額上升的差額，支出不扣除；純跟隨期間完全排除。手動關閉導航、Mode 3 安全暫停或安全結束時，主控台會顯示運行時間、總收入與目前餘額。金幣資料中斷時會採最後有效值並警告收入可能低估，不顯示彈窗或保存歷史。
- `follow_player_stop_padding_world`：跟隨停靠距離在雙方碰撞半徑外增加的 padding，預設 2.0。
- `follow_player_rejoin_distance_world`：舊版回跟門檻，為相容既有設定檔而保留；F2 現在會持續追蹤玩家，不使用此值。
- `avoid_boss`：是否啟用首領迴避，預設 `false`。設為 `true` 後，會把當前地圖「等級最高且全場唯一」的怪物視為首領並排除鎖定；詳見「首領迴避」。
- `boss_response`：偵測到首領後的反應，`switch_channel`（預設，換頻道）或 `flee`（保持距離）。
- `boss_channel_switch_settle_sec`：`switch_channel` 換頻後等待新頻道快照重填的秒數，預設 6.0，必須為非負值。
- `boss_flee_radius_world`：`flee` 模式的逃離半徑，預設 15.0；首領進入此距離內才會主動走開，必須為非負值。

## 驗證

執行單元測試：

```powershell
python -m unittest discover -v
```

查看探針即時位置與怪物數：

```powershell
python spiritvale_position_reporter.py
```

若雷達顯示 `SAFE STOP`：

1. 確認遊戲已在安裝 v2.22.0 後重新啟動，BepInEx 日誌先顯示 Loader；啟動 Python 後再顯示 Position Probe、`run_in_background=enabled`、`incremental_loot=lifecycle` 與 `auto_relogin=enabled`。
2. 查看 `BepInEx\LogOutput.log` 是否有探針載入或反射錯誤。
3. 確認已進入角色地圖，而不是登入、載入或選單畫面。
4. 確認 `spiritvale_memory_state.json` 的時間戳仍持續更新。
5. 若曾看到 `Permission denied` 或「無法移除要被取代的檔案」，代表仍在使用 v2.0.0；關閉遊戲並重新執行 `-Install`，讓 Python 與探針兩端都使用允許原子替換的共享模式。
6. `monster_scan` 會列出 `Monsters`／`Units`／Unity 場景原始數量及每個敵怪過濾階段的計數，可用來判斷 `NO LIVING ENEMY` 的原因。
7. `loot_scan` 會列出 `source`、`batch_limit`、`processed`、`cached`、`exported`、場景補種數量、`accepted_local`／`accepted_foreign` 與最後一個讀取錯誤；正常增量模式的 `incremental` 應為 `true`、`exported` 不超過 96，若終端看不到外人物品則確認 `ownership_filter` 是 `all`。
