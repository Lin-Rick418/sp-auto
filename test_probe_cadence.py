from pathlib import Path
import unittest


SOURCE_PATH = Path(__file__).with_name("SpiritValePositionProbe.cs")


class ProbeCadenceTests(unittest.TestCase):
    def test_navigation_and_general_work_use_independent_intervals(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "NavigationUpdateIntervalMilliseconds = 250", source
        )
        self.assertIn("GeneralUpdateIntervalMilliseconds = 400", source)
        self.assertIn("PlayerSafetyUpdateIntervalMilliseconds = 25", source)
        self.assertIn("LootScanBatchSize = 24", source)
        self.assertIn("LootScanBudgetMilliseconds = 2", source)
        self.assertIn("LootCacheLimit = 384", source)
        self.assertIn("LootExportLimit = 96", source)
        self.assertIn("WriteSnapshot(player, generalDue, _cachedRequest)", source)
        self.assertIn(
            "RefreshGeneralSnapshot(player, _cachedRequest)", source
        )
        self.assertNotIn("WriteIntervalMilliseconds = 400", source)

    def test_world_scans_require_a_fresh_probe_active_heartbeat(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        request_index = source.index("_cachedRequest = ReadRequest(")
        gate_index = source.index("if (!_probeActive)\n                    return;")
        scan_index = source.index("WriteSnapshot(player, generalDue, _cachedRequest)")
        self.assertLess(request_index, gate_index)
        self.assertLess(gate_index, scan_index)
        self.assertIn(
            "_probeActive = _cachedRequest != null\n"
            "                        && (_cachedRequest.ProbeActive\n"
            "                            || _cachedRequest.PartyFollowActive);",
            source,
        )

    def test_party_follow_uses_only_party_target_and_skips_world_collections(
        self,
    ) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('diagnostics.Source = "party_target"', source)
        self.assertIn("CollectFollowedPartyPlayer(", source)
        self.assertIn('monsterScan.Source = "disabled_party_follow"', source)
        self.assertIn('lootScan.Source = "disabled_party_follow"', source)
        self.assertIn('partyMemberType, "CachedPlayer"', source)
        self.assertIn('partyMemberType, "GetPlayer", 0', source)

    def test_loot_scan_is_f7_gated_incremental_and_bounded(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("internal bool LootScanActive;", source)
        self.assertIn("LootScanActivePattern", source)
        self.assertIn('lootScan.Source = "disabled_f7"', source)
        self.assertIn("CollectLootsIncremental(", source)
        self.assertIn("batchProcessed < LootScanBatchSize", source)
        self.assertIn("ElapsedMilliseconds(startedTicks)", source)
        self.assertIn("result.Count > LootExportLimit", source)
        self.assertIn("result.Count > LootCacheLimit", source)
        self.assertIn("EnsureTrackedLootSeed(", source)
        self.assertIn("LootLifecyclePatch", source)

        start = source.index(
            "private static List<LootSnapshot> CollectLootsIncremental("
        )
        end = source.index(
            "private static List<MapExitSnapshot> CollectMapExits()", start
        )
        loot_scan = source[start:end]
        self.assertNotIn("_worldToViewportPoint", loot_scan)
        self.assertNotIn("LootClickPosition", source)

    def test_probe_uses_single_game_update_and_async_state_writer(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('FindLoadedType("Game")', source)
        self.assertIn(
            'Log.LogInfo("Memory navigation hook installed (Game.Update)")', source
        )
        self.assertNotIn(
            'Log.LogInfo("Memory navigation hook installed (PlayerController.Update)")',
            source,
        )
        self.assertIn("ThreadPool.QueueUserWorkItem(StateWriterLoop)", source)
        self.assertIn("WriteStateFileNow(contents)", source)

    def test_probe_keeps_unity_updating_without_window_focus(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('"UnityEngine.Application"', source)
        self.assertIn('"runInBackground"', source)
        self.assertIn("runInBackground.SetValue(null, true, null)", source)

    def test_background_movement_overrides_capture_input_move_axis(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('playerController, "CaptureInputs"', source)
        self.assertIn("class BackgroundMovementPatch", source)
        self.assertIn("request.MovementKeys", source)
        self.assertIn("CreateMoveVector(horizontal, vertical, depth)", source)
        self.assertIn("ConvertMoveComponent(x, _moveXField.FieldType)", source)
        self.assertIn('_request.BackgroundInputMode == "both"', source)
        self.assertIn('_request.BackgroundInputMode == "apply"', source)
        self.assertIn("__result = true", source)
        self.assertIn('playerController, "Update"', source)
        self.assertIn('FindMethod(playerType, "ProcessMovement", 1)', source)
        self.assertIn('playerType, "SendInputsToServer", 1', source)
        self.assertIn('FindProperty(_inputDtoType, "Hotkeys")', source)
        self.assertIn('FindProperty(_inputDtoType, "HotkeysHeld")', source)
        self.assertIn('"HotkeyManager"', source)
        self.assertIn(
            "ApplyShiftHotkeys(inputs, injectedShiftKeys, _lastShiftKeys)", source
        )
        self.assertIn(
            "ApplyCapturedShiftHotkeys(\n"
            "                    inputs, requestedShiftKeys",
            source,
        )
        self.assertIn('FindProperty(_inputDtoType, "UnitId")', source)
        self.assertIn('FindProperty(_inputDtoType, "ClickPosition")', source)
        self.assertIn('_inputDtoType, "FastCastPosition"', source)
        self.assertIn('FindMethod(playerType, "ProcessTargeting", 0)', source)
        self.assertIn('FindMethod(playerType, "ProcessSkills", 0)', source)
        self.assertIn("_processTargeting.Invoke(__instance, null)", source)
        self.assertIn("_processSkills.Invoke(__instance, null)", source)
        self.assertIn("FindEnemyUnitByObjectId", source)
        self.assertIn("ApplyResolvedFocus(__instance)", source)
        self.assertIn("ApplyResolvedHover(__instance)", source)
        self.assertIn('_enemy.SetValue(playerController, _resolvedFocusTarget', source)
        self.assertIn('_castTarget.SetValue(playerController, _resolvedFocusTarget', source)
        self.assertIn(
            "ClickNewShiftSkills(__instance, injectedShiftKeys)", source
        )
        self.assertIn("Background capture input ", source)
        self.assertIn("Captured manual input: ", source)
        self.assertIn("_lastCaptureShiftKeys", source)
        self.assertIn("CapturePressDurationMilliseconds = 50", source)
        self.assertIn("leftHeld && !leftPressed", source)
        self.assertIn("rightHeld && !rightPressed", source)
        self.assertIn("_fastCast.SetValue(inputs, shiftActive, null)", source)
        self.assertIn("shiftActive && shiftInHoldPhase", source)
        self.assertIn("_unitId.SetValue(inputs, 0, null)", source)
        self.assertIn("CreateScaledWorldVector(", source)
        self.assertIn("x * 100f", source)
        self.assertIn("if (!IsLocalPlayer(__instance))", source)
        self.assertIn("Injected capture DTO: ", source)
        hover_method = source.split(
            "private static void ApplyResolvedHover", 1
        )[1].split("private static void ClickNewShiftSkills", 1)[0]
        self.assertNotIn("_castTarget.SetValue", hover_method)

    def test_map_exits_are_cached_until_map_identity_changes(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("if (!_mapExitCacheReady", source)
        self.assertIn("_mapExitCacheMapId != mapId", source)
        self.assertIn("_mapExitCacheInstanceId != instanceId", source)

    def test_death_transition_bypasses_navigation_snapshot_interval(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            "bool deathTransition = !playerAlive", source
        )
        self.assertIn("if (navigationDue || deathTransition)", source)
        self.assertIn('json.Append(",\\\"alive\\\":")', source)

    def test_probe_exports_mount_controller_state_without_casting(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn(
            'RequireProperty(\n                summoningType, "MountController_C"',
            source,
        )
        self.assertNotIn('summoningType, "IsMountedSummon"', source)
        self.assertIn('json.Append(",\\\"is_mounted_summon\\\":")', source)
        self.assertIn(
            'json, "summon_mount_state_source", "mount_controller"', source
        )
        self.assertNotIn("MaintainMountedSummon", source)
        self.assertNotIn("FindSummonActionSkills", source)
        self.assertNotIn("FindSummonClickSkill", source)
        self.assertNotIn("FindSummonFastCast", source)
        self.assertNotIn("GetAnySkill", source)

    def test_probe_exports_current_summon_display_items(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('summoningType, "SummonDisplays_C"', source)
        self.assertIn('summonSkillDataType, "SkillId"', source)
        self.assertIn('summonSkillDataType, "Id"', source)
        self.assertIn('summonSkillDataType, "Level"', source)
        self.assertIn('json.Append(",\\\"summon_displays\\\":{")', source)

    def test_probe_exports_wallet_coins_without_gating_the_snapshot(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('_playerType, "Save"', source)
        self.assertIn('_playerSave.PropertyType, "PlayerData"', source)
        self.assertIn('_savePlayerData.PropertyType, "Coins"', source)
        self.assertIn('json.Append(",\\\"wallet_coins_available\\\":")', source)
        self.assertIn('AppendNumber(json, "wallet_coins", walletCoins.Coins)', source)
        self.assertIn('AppendString(json, "wallet_coins_error", walletCoins.Error)', source)
        self.assertIn("private static WalletCoinsSnapshot ReadWalletCoins", source)

    def test_probe_exports_active_status_displays_separately_from_catalogs(
        self,
    ) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn('statusComponentType, "StatusDisplays_C"', source)
        self.assertNotIn("fanaticism", source.lower())
        self.assertIn('FindLoadedType("StatusComponent")', source)
        self.assertIn('statusComponentType, "Effects"', source)
        self.assertIn('statusComponentType, "Buffs"', source)
        self.assertIn('statusComponentType, "Debuffs"', source)
        self.assertIn('json.Append(",\\\"status_component\\\":{")', source)
        self.assertIn("active_status_ids\\\":[", source)

    def test_probe_supports_edge_triggered_numpad_skill_requests(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("SkillKeyRequestIdPattern", source)
        self.assertIn("FireSkillKeyHotkeys", source)
        self.assertIn('Enum.Parse(keyCodeType, "Keypad" + number)', source)
        self.assertIn("requestId == _lastSkillKeyRequestId", source)

    def test_card_bulk_purchase_preserves_reserve_and_is_server_guarded(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("internal static class CardPurchaseService", source)
        self.assertIn('SetNullableEnum(search, "ItemType", "Card")', source)
        self.assertIn('"MaximumUnitPrice",\n                request.UnitPriceLimitExclusive - 1', source)
        self.assertIn("unitPrice >= request.UnitPriceLimitExclusive", source)
        self.assertIn("currentBalance - request.ReserveCoins", source)
        self.assertIn("string.CompareOrdinal", source)
        self.assertIn("candidate.PurchaseQuantity", source)
        self.assertIn('RequireProperty(\n                _savePlayerData.PropertyType, "Coins"', source)
        self.assertIn('_playerSave.PropertyType, "VendingPurchase", 5', source)
        self.assertIn("candidate.ListingId,", source)
        self.assertIn("candidate.UnitPrice,", source)
        self.assertIn("candidate.ListingVersion,", source)
        self.assertIn("VendingPurchaseResultPrefix", source)
        self.assertNotIn('clientType, "PurchaseAsync"', source)
        self.assertIn("BULK_BUY_CARD_WITH_RESERVE", source)
        self.assertIn('"purchase_may_have_completed"', source)
        self.assertIn("BOT 不會自動重試", source)

    def test_consumable_use_ipc_is_guarded_deduped_and_reported(self) -> None:
        source = SOURCE_PATH.read_text(encoding="utf-8")
        self.assertIn("internal static class ConsumableUseService", source)
        self.assertIn("ConsumableUseRequestIdPattern", source)
        self.assertIn("ConsumableNamePattern", source)
        self.assertIn(
            "request.ConsumableUseRequestId == _lastRequestId", source
        )
        self.assertIn("if (!request.BotActive || !playerAlive)", source)
        self.assertIn('RequireProperty(runtimeType, "Consumables")', source)
        self.assertIn('RequireProperty(inventoryType, "Consumables")', source)
        self.assertIn('methods[index].Name == "UseConsumable"', source)
        self.assertIn("_useConsumable.Invoke(player", source)
        self.assertIn('result.Status = "out_of_stock"', source)
        self.assertIn('result.Status = accepted ? "accepted" : "rejected"', source)
        self.assertIn('json.Append(",\\\"consumable_use\\\":{")', source)


if __name__ == "__main__":
    unittest.main()
