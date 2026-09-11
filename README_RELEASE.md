# SpiritVale Bot v2.22.0 快速開始

## 使用條件

- Windows 10／11、64 位元 Python 3.11 或更新版本。
- SpiritVale Steam 版。
- 遊戲已安裝 BepInEx 6 IL2CPP。
- 請只在遊戲規則允許自動化的情況下使用。

## 安裝

1. 將 ZIP 完整解壓縮到一般可寫入資料夾，不要直接在 ZIP 裡執行。
2. 完全關閉 SpiritVale。
3. 雙擊 `INSTALL.cmd`。首次安裝會建立 `.venv` 並從網路安裝 Python 套件。
4. 啟動 SpiritVale、登入角色並進入地圖；此時只載入輕量 Loader，不載入完整探針。
5. 雙擊 `RUN_PREVIEW.cmd`；Python 會按需載入探針並確認就緒，預覽不會送出移動或拾取按鍵。
6. 要正式執行時關閉預覽，再雙擊 `RUN_BOT.cmd`。

若遊戲不在 Steam 預設位置，請於本資料夾開啟 PowerShell 並執行：

```powershell
.\install_spiritvale_bot.ps1 -GameDirectory "D:\SteamLibrary\steamapps\common\SpiritVale"
```

## 快捷鍵

- F2：只列出同地圖的隊伍成員並切換獨立純跟隨；不再掃描全部玩家。同地圖隊員若在其他頻道，會先自動切頻，再接續跟隨。
- F4：正式 BOT 模式開啟常駐視窗；輸入必須保留的餘額與單卡價格上限後，持續大量購買單價嚴格小於上限的 Card。再次按 F4 只會帶回同一視窗。
- F5：顯示／隱藏背包價格視窗。
- F6：單次讀取最新背包並背景查價。
- F7：切換非裝備 Legendary 拾取。
- F8：暫停／繼續一般怪物與拾取導航；不會中斷 F2 純跟隨。
- Del：顯示／隱藏依裝備名稱區分的完整詞條表；232 種詞條均附中文說明並可中英文搜尋，每個名稱可獨立設定最低值與「至少符合 N 項」，也可按「此名稱一律分解」忽略所有素質。模式只在儲存後生效；既有收藏永遠安全略過，即使一律分解也不會取消收藏或拆解。
- F9：安全結束。

F4 固定搜尋 `Query=Card`、`ItemType=Card`，每次只送出一筆最低單價／listing ID 的上架，並一次買滿在保留餘額之上的可負擔數量。沒有符合項目時每 1 秒重查；價格或版本變動、已售出會重新搜尋。送出時附精確 listing ID、購買數量、預期單價與 listing 版本；餘額不足、背包滿、未授權或其他確定錯誤會停止，逾時或結果不明也會停止且不重送。停止、關閉視窗或 F9 不再建立新要求，已送出的單筆仍會等候結果。

F8 會避開場景中的傳送出口：怪物、掉落物或 NavMesh 路徑若進入「出口互動距離＋玩家碰撞半徑＋3 世界單位」的安全圈就會略過；角色若已在圈內只允許往外離開。可用 `spiritvale_bot_config.json` 的 `map_exit_avoidance_padding_world` 調整額外緩衝，F2 純跟隨不受影響。

F7 關閉時探針不再掃描一般掉落物；Mode 3 的王死亡拾取階段會自行開啟必要掃描。F7＋F8 同時開啟時，v2.22.0 會以每輪最多 24 件、約 2 ms 的預算增量處理地面道具，最多輸出 96 件最相關候選；目前拾取目標優先更新。掉落物生命週期、出口快取及背景狀態寫入會避免大量物件集中阻塞 Unity 主執行緒，因此道具增加主要影響完成一輪快取所需時間，不再等比例增加單幀耗時。

## F8 怪物滑鼠鎖定

`spiritvale_mode_config.json` 的 `lock_mouse_to_monster` 預設為 `false`。改成 `true` 並重新啟動 Python 後，正式執行模式會在 F8 一般導航追蹤畫面內怪物時將 Windows 游標移到怪物。所有 `job_type` 都完全依此設定，不會強制覆寫。

`lock_mouse_to_monster` 會用背景 `WM_MOUSEMOVE` 更新遊戲內游標位置，不再移動或占用 Windows 實體游標。`left_click_after_mouse_lock` 預設為 `false`；改成 `true` 後，每次取得新怪物目標並第一次成功送出背景游標位置時，會再對遊戲視窗送出一次背景左鍵。背景操作不切換焦點，且 v2.22.0 會要求 Unity 在失焦或最小化時繼續更新；預覽、F8 暫停、F2 跟隨、拾取、角色死亡及怪物位於畫面外時不送出滑鼠訊息。

Python 雷達預設關閉；需要時把 `spiritvale_bot_config.json` 的 `debug_window` 改成 `true`。F8／預覽會按需更新世界資料；F2 只更新隊伍名單、被鎖定的單一隊友與 NavMesh 路徑，不掃描全部玩家、怪物、掉落物或傳送出口。F8/F2 都關閉或 Python 心跳消失後，探針會在最多約兩秒內休眠；F6 背包查價仍可獨立工作。

本機角色死亡時會由獨立的 25 ms 安全輪詢立即觸發快照，放開 WASD、左右 Shift 與其他仍按住的按鍵，並封鎖 9、0、V 等所有遊戲按鍵，直到角色復活；舊探針若沒有提供本機存活狀態也會安全停鍵。

F2 純跟隨只以指定隊伍成員為 NavMesh 目標，不打怪、不拾取或按 V。不同伺服器實例先切實例，同實例不同頻道則直接切頻。切換期間放開所有移動鍵並保留 PlayerId 鎖定，目標在新分流出現後立即建立路徑。到達雙方碰撞半徑加 2 世界單位的停靠距離後會停止 WASD，但仍按住左右 Shift；玩家或路徑失效、斷線、關閉 F2 或按 F9 時會立即放開所有移動鍵。

`spiritvale_bot_config.json` 的 `job_type` 使用 `0` 代表未滿 64 等、F8 持續按住 Left Shift；`1` 代表召喚、F8 持續按住 Left Shift 與 Right Shift；`2` 代表牧師，滑鼠成功鎖定怪物後立即短按 Left Shift，之後每 300–1300 ms 隨機短按一次（預設按住 50 ms），且不用於掉落物。滑鼠鎖定與點擊完全依 mode config。只有召喚會在 F8 或 F2 啟用後以 `MountController_C` 持續確認坐騎；未騎乘時 Python 固定先按 `9`、等待 750 ms 再按 `0`，尚未確認騎乘時每 400 ms 只重試 `0`，最多持續 4 秒，之後才等待 2.5 秒重新從 `9` 開始。確認坐騎控制器出現前會放開移動鍵並暫停導航。F2 完全獨立，三種職業都固定同時按住左右 Shift；舊設定中的 `always_hold_lshift` 會被忽略。本發佈包預設為 `1`。

`job_type = 1` 時，F8 控制選單會顯示「召喚／Buff 檢查設定」。可分別選擇是否維持 `SummonSkeleton`、`SummonAbomination`、`SummonSkeletonMage`、`Invoker` 與 `Conjurer`，並指定右側 NumPad 0–9 的技能鍵；預設全部關閉。已選項目缺少時會停止一般導航、每次只背景觸發一個技能，狀態完整後自動繼續；F2 純跟隨不執行這項檢查。召喚物依 `SummonDisplays_C` 判斷至少一隻，Buff 只依目前 `StatusDisplays_C` 判斷，不使用可用 Buff 目錄。

正式 BOT 模式下，每次開啟一般導航會開始計時並取樣 `PlayerSave.PlayerData.Coins`。停止導航時主控台顯示導航時間、只累加正向餘額變化的金幣總收入，以及目前餘額；支出不扣除收入，純跟隨期間不計時也不取樣。金幣資料短暫失效時會使用最後有效值並提示收入可能低估。

探針與 Python 的執行期 JSON 存放在 `%LOCALAPPDATA%\SpiritValeBot`，發佈包可解壓縮到任意可寫入位置。

`spiritvale_mode_config.json` 預設使用 Mode 3：`Scorpion King` 搭配 `Soldier Termite`。程式只攻擊該王、不自動換頻；王死亡後等待 3 秒並撿完所有自己的 Legendary 才再次召喚。物品不足、使用失敗、王未生成或 Legendary 拾取失敗時會安全暫停，重新切換 F8 才重試。

若遊戲仍載入舊版探針，而舊資料夾中的 `spiritvale_memory_state.json` 正在持續更新，Python 會暫時自動使用同一舊路徑；安裝 v2.22.0 發行包並重啟遊戲後會優先回到 LocalAppData。安裝程式會移除舊的開機載入探針，改裝 Loader 至 `BepInEx\plugins`，完整探針則放在 `BepInEx\ondemand`。也可用環境變數 `SPIRITVALE_BOT_IPC_DIR` 明確指定 IPC 資料夾。
