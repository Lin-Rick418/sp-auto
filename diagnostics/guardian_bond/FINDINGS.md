# GuardianBond 調查結果（2026-09-11）

本次只調查與保存證據，未修改 bot、探針或遊戲檔，未執行實際施放。結論來自本機安裝版本的資源與 GameAssembly.dll 原生程式碼。

## 實際技能規格

GuardianBond.skill.json 是 sharedassets0.assets 中 path ID 88154 的 SkillConfig，依遊戲 metadata 生成型別樹解析，完整讀取長度檢查通過。TargetType=2（AllyNotSelf）、CastType=1（Target）、CanCastGround=false、Bond=true、基礎 Range=10、基礎 CastTime=1 秒。

因此技能指定自身以外的友方單位，並非限定召喚物。可以把自己的召喚物設為 checker 固定施放對象，但需驗證它的擁有者。

## 聚焦與施放 ID

1. PlayerController.FastCast(SkillState)，RVA 0xAC3180：客戶端讀取 enemy / player，經 SkillsComponent.CanHit 驗證後，將目標 ObjectId 寫進 Inputs.UnitId。
2. ProcessFastCast，RVA 0xAD2DA0：讀取 Inputs.UnitId，透過 Extensions.GetObjectById 找到單位，再呼叫 ProcessClickedUnit 和 ProcessTargeting。
3. ProcessClickedUnit，RVA 0xAD2A30：有 SkillReady 時檢查冷卻與 CanHit，設定 CastTarget，呼叫 CastOnTarget。
4. CastOnTarget，RVA 0xABF740：使用 CastTarget，處理接近目標與施放。

確實存在「對誰施放」的 ID：PlayerInputDto.UnitId = summon.ObjectId。UI 選取框不是最終施放契約；走完整輸入流程時，不必操作實體滑鼠。只有聚焦，或只有 ID 而未處理對應技能輸入，均不足以保證成功。

## 現有程式的問題

### 召喚物未驗證擁有者

SpiritValePositionProbe.cs 的 ResolveAnySummonUnit（約 7558 行）只排除敵方、木樁、死亡與未顯示單位，回傳第一個候選。7604 行的「Non-enemy team == the player's own summons」假設不成立，可能取到別人的召喚物或其他非敵方單位。

應使用 BaseUnitController.Summoning.Summoner，比較其 ObjectId 與本機玩家 ObjectId，再檢查存活、場景及可施放條件。遊戲 CanTargetAsAlly 流程也會讀取 Summoner。

現有快照的 SummonDisplays_C 列出 10 個召喚物，但 Primary 與 ActiveSummons 仍為空；不能將兩者為空當成客戶端沒有召喚物。scene_summon_unit_id=57044 只是舊篩選器的候選，未證實為本機玩家所有，且 ID 不可寫死。

### ClickSkill 不是立即施放

ClickSkill(int)，RVA 0xAC14F0，主要設定 PlayerController.ClickSkillIndex。下一次 CaptureInputs 才搬入 DTO 的 ClickSkillIndex，進一步 ProcessSkills / ReadySkill / FastCast。

現有 FireSkillKeyHotkeys 在 UpdatePostfix 修改 inputs、設定 player 後，只呼叫 ClickHotkeys → ClickSkill。因此本地目標設定與實際技能處理分離；下次輸入採樣可能換掉目標。

### 修改 DTO 後未重新寫回本地 Inputs

Interop 的 PlayerInputDto 包裝類別繼承 Il2CppSystem.ValueType；原生 ApplyInputs 也能看到整份結構複製。UpdatePostfix 約 1065–1066 行先設定 Inputs/currentInputs，FireSkillKeyHotkeys 約 1413 行才修改盒裝 inputs 的 UnitId、FastCast 與 Hotkeys，未重新寫回。

所以送出的 RPC 參數與本地 Inputs 可能不同。這是不一致，但 RPC 仍取得修改後的參數，不能只憑這點就宣稱伺服器必定施放失敗。完整失敗原因仍需同幀診斷及實際施放驗證。

## 修正方向

1. 找到本機玩家擁有且可施放的召喚物，取得當次 ObjectId；找不到則明確等待。
2. 建立同一份技能輸入：UnitId=召喚物 ObjectId、FastCast=true、指定技能 hotkey，排除殘留敵方與地面目標。
3. 修改後寫回 Inputs/currentInputs，在同一處理階段走正常技能處理。若走客戶端 FastCast，須同步合法友方 hover，避免它重新選錯目標；處理後讀回 Inputs，讓本地與送出內容一致。
4. 不要在此分支又排入下一幀 ClickSkill，避免重複施放與重新採樣目標。
5. 記錄 owner ID、summon ID、本地與送出 UnitId、CastTarget，最後以同步回來的連結確認成功。

以上是待實作與實測的修正方向，本次尚未改動執行中的程式。

## Checker 的成功判斷

目前 Python 查玩家 GuardianBond 狀態，不能因為 SkillConfig.SelfStatusEffects 是空的就判定查錯。Bond 完成回呼（bond_completion.asm，RVA 0x7F3B90）會對施法者也呼叫 ApplyBondStatus。

但自身狀態仍不能單獨證明「我對自己的召喚物建立 GuardianBond」。若要嚴格驗證此需求，可查 SkillsComponent.BondSync.Value.Entries，確認 SkillId=GuardianBond、Caster=true、Other 指向合格召喚物。BondEntry 的 Other / SkillId / Caster 與 DoBondBegin 新增雙向記錄的流程已確認存在。

## 證據檔

- GuardianBond.skill.json：實際技能設定。
- targeting.asm：ClickSkill / ProcessTargeting。
- fastcast.asm：FastCast / ProcessFastCast / CanTargetAsAlly。
- casting.asm：ApplyInputs / ProcessSkills / ReadySkill / CastOnTarget。
- input_and_validation.asm：CaptureInputs / ProcessClickedUnit / CanHit。
- bond.asm、bond_completion.asm：連結及狀態套用。
- inspect_native.py 與 methods.tsv：使用 BepInEx MethodAddressToToken.db 對照原生位址。部分多方法共用位址的通用函式標籤可能有別名，主要技能方法已交叉核對。
- inspect_assets.py：唯讀解析本機技能資源，使用 UnityPy / TypeTreeGeneratorAPI。反組譯使用 pefile / capstone。

本次沒有成功手動施放 GuardianBond 的紀錄，也沒有執行遊戲內施放測試，因此不宣稱已修復。
