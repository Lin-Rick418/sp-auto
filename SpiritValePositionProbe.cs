using System;
using System.Collections;
using System.Collections.Generic;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using System.Threading;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;

namespace SpiritValePositionProbe
{
    [BepInPlugin("local.spiritvale.positionprobe", "SpiritVale Position Probe", "2.23.5")]
    public sealed class Plugin : BasePlugin
    {
        internal const int SchemaVersion = 1;
        internal static readonly string IpcDirectory = Path.Combine(
            Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
            "SpiritValeBot"
        );
        internal static readonly string StatePath = Path.Combine(
            IpcDirectory, "spiritvale_memory_state.json"
        );
        internal static readonly string RequestPath = Path.Combine(
            IpcDirectory, "spiritvale_navigation_request.json"
        );
        internal static readonly string AuctionRequestPath = Path.Combine(
            IpcDirectory, "spiritvale_auction_request.json"
        );
        internal static readonly string AuctionResultPath = Path.Combine(
            IpcDirectory, "spiritvale_auction_results.json"
        );
        internal static readonly string CardPurchaseRequestPath = Path.Combine(
            IpcDirectory, "spiritvale_card_purchase_request.json"
        );
        internal static readonly string CardPurchaseResultPath = Path.Combine(
            IpcDirectory, "spiritvale_card_purchase_result.json"
        );
        internal static readonly string InventoryRequestPath = Path.Combine(
            IpcDirectory, "spiritvale_inventory_request.json"
        );
        internal static readonly string InventoryResultPath = Path.Combine(
            IpcDirectory, "spiritvale_inventory_equips.json"
        );
        internal static readonly string DismantleRequestPath = Path.Combine(
            IpcDirectory, "spiritvale_dismantle_request.json"
        );
        internal static readonly string DismantleResultPath = Path.Combine(
            IpcDirectory, "spiritvale_dismantle_result.json"
        );
        internal static readonly string FavoriteRequestPath = Path.Combine(
            IpcDirectory, "spiritvale_favorite_request.json"
        );
        internal static readonly string FavoriteResultPath = Path.Combine(
            IpcDirectory, "spiritvale_favorite_result.json"
        );

        public override void Load()
        {
            Directory.CreateDirectory(IpcDirectory);
            bool runInBackgroundEnabled = EnableRunInBackground(Log);
            PlayerUpdatePatch.Initialize(Log);
            Type game = PlayerUpdatePatch.FindLoadedType("Game");
            MethodInfo update = RequireZeroParameterMethod(game, "Update");
            MethodInfo postfix = AccessTools.Method(typeof(PlayerUpdatePatch), "Postfix");
            new Harmony("local.spiritvale.positionprobe").Patch(
                update,
                null,
                new HarmonyMethod(postfix),
                null,
                null,
                null
            );
            Log.LogInfo("Memory navigation hook installed (Game.Update)");

            bool backgroundMovementEnabled = false;
            try
            {
                BackgroundMovementPatch.Initialize(Log);
                Type playerController = PlayerUpdatePatch.FindLoadedType(
                    "PlayerController"
                );
                MethodInfo captureInputs = RequireZeroParameterMethod(
                    playerController, "CaptureInputs"
                );
                new Harmony(
                    "local.spiritvale.positionprobe.backgroundmovement"
                ).Patch(
                    captureInputs,
                    null,
                    new HarmonyMethod(AccessTools.Method(
                        typeof(BackgroundMovementPatch), "Postfix"
                    )),
                    null,
                    null,
                    null
                );
                MethodInfo playerUpdate = RequireZeroParameterMethod(
                    playerController, "Update"
                );
                new Harmony(
                    "local.spiritvale.positionprobe.backgroundmovement.update"
                ).Patch(
                    playerUpdate,
                    null,
                    new HarmonyMethod(AccessTools.Method(
                        typeof(BackgroundMovementPatch), "UpdatePostfix"
                    )),
                    null,
                    null,
                    null
                );
                backgroundMovementEnabled = true;
                Log.LogInfo(
                    "Background movement hooks installed "
                    + "(PlayerController.CaptureInputs + Update RPC)"
                );
            }
            catch (Exception error)
            {
                Log.LogWarning(
                    "Background movement hook unavailable: "
                    + error.GetType().Name + ": " + error.Message
                );
            }

            bool lootLifecycleEnabled = false;
            try
            {
                Type lootDrop = PlayerUpdatePatch.FindLoadedType("LootDrop");
                MethodInfo onEnable = RequireZeroParameterMethod(lootDrop, "OnEnable");
                MethodInfo remove = RequireZeroParameterMethod(lootDrop, "Remove");
                Harmony lootHarmony = new Harmony(
                    "local.spiritvale.positionprobe.lootlifecycle"
                );
                lootHarmony.Patch(
                    onEnable,
                    null,
                    new HarmonyMethod(AccessTools.Method(
                        typeof(LootLifecyclePatch), "OnEnablePostfix"
                    )),
                    null,
                    null,
                    null
                );
                lootHarmony.Patch(
                    remove,
                    new HarmonyMethod(AccessTools.Method(
                        typeof(LootLifecyclePatch), "RemovePrefix"
                    )),
                    null,
                    null,
                    null,
                    null
                );
                PlayerUpdatePatch.SetLootLifecycleTrackingAvailable(true);
                lootLifecycleEnabled = true;
                Log.LogInfo("Incremental loot lifecycle hooks installed");
            }
            catch (Exception error)
            {
                PlayerUpdatePatch.SetLootLifecycleTrackingAvailable(false);
                Log.LogWarning(
                    "Loot lifecycle hooks unavailable; using throttled scene fallback: "
                    + error.GetType().Name + ": " + error.Message
                );
            }

            bool autoReloginEnabled = false;
            try
            {
                ReconnectPatch.Initialize(Log);
                Type uiManager = PlayerUpdatePatch.FindLoadedType("UIManager");
                MethodInfo lateUpdate = RequireZeroParameterMethod(
                    uiManager, "LateUpdate"
                );
                MethodInfo reconnectPostfix = AccessTools.Method(
                    typeof(ReconnectPatch), "Postfix"
                );
                new Harmony("local.spiritvale.positionprobe.reconnect").Patch(
                    lateUpdate,
                    null,
                    new HarmonyMethod(reconnectPostfix),
                    null,
                    null,
                    null
                );
                autoReloginEnabled = true;
                Log.LogInfo("Auto relogin hook installed (UIManager.LateUpdate)");
            }
            catch (Exception error)
            {
                Log.LogError(
                    "Auto relogin disabled: failed to install "
                    + "UIManager.LateUpdate hook: "
                    + error.GetType().Name + ": " + error.Message
                );
            }

            bool channelListEnabled = false;
            try
            {
                Type uiServerDisplay = PlayerUpdatePatch.FindLoadedType(
                    "UIServerDisplay"
                );
                MethodInfo drawChannels = AccessTools.Method(
                    uiServerDisplay, "DrawChannels"
                );
                if (drawChannels == null)
                    throw new MissingMethodException(
                        "UIServerDisplay", "DrawChannels"
                    );
                new Harmony("local.spiritvale.positionprobe.channellist").Patch(
                    drawChannels,
                    null,
                    new HarmonyMethod(AccessTools.Method(
                        typeof(ChannelListPatch), "Postfix"
                    )),
                    null,
                    null,
                    null
                );
                channelListEnabled = true;
                Log.LogInfo(
                    "Channel list hook installed (UIServerDisplay.DrawChannels)"
                );
            }
            catch (Exception error)
            {
                Log.LogWarning(
                    "Channel list hook unavailable; channel_index/channel_count "
                    + "will be reported as unknown: "
                    + error.GetType().Name + ": " + error.Message
                );
            }

            Log.LogInfo(
                "Memory navigation probe v2.23.5 loaded on demand; auto_relogin="
                + (autoReloginEnabled ? "enabled" : "disabled")
                + "; run_in_background="
                + (runInBackgroundEnabled ? "enabled" : "unavailable")
                + "; background_movement="
                + (backgroundMovementEnabled ? "enabled" : "unavailable")
                + "; incremental_loot="
                + (lootLifecycleEnabled ? "lifecycle" : "throttled_fallback")
                + "; channel_list="
                + (channelListEnabled ? "enabled" : "unavailable")
                + "; state=" + StatePath
                + "; request=" + RequestPath
                + "; auction_request=" + AuctionRequestPath
                + "; auction_results=" + AuctionResultPath
                + "; card_purchase_request=" + CardPurchaseRequestPath
                + "; card_purchase_result=" + CardPurchaseResultPath
                + "; inventory_request=" + InventoryRequestPath
                + "; inventory_results=" + InventoryResultPath
                + "; dismantle_request=" + DismantleRequestPath
                + "; dismantle_result=" + DismantleResultPath
                + "; favorite_request=" + FavoriteRequestPath
                + "; favorite_result=" + FavoriteResultPath
            );
        }

        private static bool EnableRunInBackground(ManualLogSource log)
        {
            try
            {
                Type application = PlayerUpdatePatch.FindLoadedType(
                    "UnityEngine.Application"
                );
                PropertyInfo runInBackground = application.GetProperty(
                    "runInBackground",
                    BindingFlags.Public | BindingFlags.Static
                );
                if (runInBackground == null || !runInBackground.CanWrite)
                    throw new MissingMemberException(
                        application.FullName, "runInBackground"
                    );
                runInBackground.SetValue(null, true, null);
                bool enabled = Convert.ToBoolean(
                    runInBackground.GetValue(null, null),
                    CultureInfo.InvariantCulture
                );
                log.LogInfo(
                    "Unity Application.runInBackground="
                    + (enabled ? "true" : "false")
                );
                return enabled;
            }
            catch (Exception error)
            {
                Exception actual = error is TargetInvocationException
                    && error.InnerException != null
                        ? error.InnerException
                        : error;
                log.LogWarning(
                    "Could not enable Unity background updates: "
                    + actual.GetType().Name + ": " + actual.Message
                );
                return false;
            }
        }

        private static MethodInfo RequireZeroParameterMethod(Type type, string name)
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && !methods[index].IsGenericMethodDefinition
                    && methods[index].GetParameters().Length == 0)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name + "()");
        }
    }

    internal sealed class NavigationRequest
    {
        internal long RequestId;
        internal string TargetKind;
        internal int TargetObjectId;
        internal long FollowChannelRequestId;
        internal string FollowPlayerId = string.Empty;
        internal long ChannelSwitchRequestId;
        internal int ChannelSwitchIndex = -1;
        internal long ConsumableUseRequestId;
        internal string ConsumableName = string.Empty;
        internal long TimestampMilliseconds;
        internal bool ProbeActive;
        internal bool LootScanActive;
        internal bool PartyFollowActive;
        internal bool BotActive;
        internal string MovementKeys = string.Empty;
        internal int MovementWorldX;
        internal int MovementWorldY;
        internal int MovementWorldZ;
        internal string ShiftKeys = string.Empty;
        internal string SummonAction = string.Empty;
        internal long SkillKeyRequestId;
        internal string SkillKey = string.Empty;
        internal bool SkillKeyTargetSummon;
        internal int LootInteract;
        internal int LootInteractObjectId;
        internal int FocusTargetObjectId;
        internal float FocusTargetWorldX;
        internal float FocusTargetWorldY;
        internal float FocusTargetWorldZ;
        internal string BackgroundInputMode = "inputs";
        internal string BackgroundSkillMode = "capture";
        internal bool AutoReloginEnabled;
        internal float AutoReloginDisconnectGraceSeconds = 3f;
        internal float AutoReloginBuiltinWaitMaxSeconds = 30f;
        internal float AutoReloginAttemptTimeoutSeconds = 30f;
        internal float AutoReloginRetryDelaySeconds = 10f;
        internal int AutoReloginMaxAttempts = 5;
    }

    internal sealed class ConsumableUseSnapshot
    {
        internal long RequestId;
        internal string Status = "idle";
        internal string ItemId = string.Empty;
        internal string DisplayName = string.Empty;
        internal int RemainingCount = -1;
        internal string Error = string.Empty;
    }

    internal static class ConsumableUseService
    {
        private static ManualLogSource _log;
        private static long _lastRequestId;
        private static PropertyInfo _appServerRuntime;
        private static PropertyInfo _runtimeConsumables;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _characterInventory;
        private static PropertyInfo _inventoryConsumables;
        private static PropertyInfo _configId;
        private static PropertyInfo _configDisplayName;
        private static PropertyInfo _consumableId;
        private static PropertyInfo _consumableCount;
        private static MethodInfo _useConsumable;
        private static MethodInfo _useConsumableData;
        private static PropertyInfo _playerSave;
        private static ConsumableUseSnapshot _result = new ConsumableUseSnapshot();

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type appType = PlayerUpdatePatch.FindLoadedType("App");
            Type runtimeType = PlayerUpdatePatch.FindLoadedType("GameServerRuntime");
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            Type characterType = PlayerUpdatePatch.FindLoadedType("CharacterData");
            Type inventoryType = PlayerUpdatePatch.FindLoadedType("InventoryData");
            Type configType = PlayerUpdatePatch.FindLoadedType("ConsumableConfig");
            Type dataType = PlayerUpdatePatch.FindLoadedType("ConsumableData");
            _appServerRuntime = RequireProperty(appType, "ServerRuntime");
            _runtimeConsumables = RequireProperty(runtimeType, "Consumables");
            _playerCharacterData = RequireProperty(playerType, "CharacterData");
            _characterInventory = RequireProperty(characterType, "Inventory");
            _inventoryConsumables = RequireProperty(inventoryType, "Consumables");
            _configId = RequireProperty(configType, "Id");
            _configDisplayName = RequireProperty(configType, "DisplayName");
            _consumableId = RequireProperty(dataType, "Id");
            _consumableCount = RequireProperty(dataType, "Count");
            // Preferred path: PlayerSave.UseConsumable(ConsumableData) is the exact
            // method the inventory UI invokes when a player clicks a bag consumable.
            // It takes the owned stack instance and drives the normal client->server
            // (UseConsumable_S ServerRpc) flow. PlayerController.Save exposes the
            // PlayerSave instance for the local player.
            Type saveType = PlayerUpdatePatch.FindLoadedType("PlayerSave");
            _playerSave = RequireProperty(playerType, "Save");
            MethodInfo[] saveMethods = saveType.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance
            );
            for (int index = 0; index < saveMethods.Length; index++)
            {
                ParameterInfo[] parameters = saveMethods[index].GetParameters();
                if (saveMethods[index].Name == "UseConsumable"
                    && parameters.Length == 1
                    && parameters[0].ParameterType == dataType)
                {
                    _useConsumableData = saveMethods[index];
                    break;
                }
            }
            // Fallback: PlayerController.UseConsumable(ConsumableConfig) -> bool.
            // This rejects (returns false) when handed a config instance the client
            // does not recognize, so it is only used when the ConsumableData overload
            // cannot be resolved.
            MethodInfo[] methods = playerType.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == "UseConsumable"
                    && methods[index].ReturnType == typeof(bool)
                    && parameters.Length == 1
                    && parameters[0].ParameterType == configType)
                {
                    _useConsumable = methods[index];
                    break;
                }
            }
            if (_useConsumableData == null && _useConsumable == null)
                throw new MissingMethodException(
                    saveType.FullName,
                    "UseConsumable(ConsumableData) or PlayerController.UseConsumable(ConsumableConfig)"
                );
            log.LogInfo(
                "Guarded consumable-use navigation IPC initialized"
                + " (data-overload=" + (_useConsumableData != null)
                + ", config-overload=" + (_useConsumable != null) + ")"
            );
        }

        internal static void SetUnavailable(Exception error)
        {
            _result.Status = "unavailable";
            _result.Error = error.GetType().Name + ": " + error.Message;
        }

        internal static void Tick(
            object player, NavigationRequest request, bool playerAlive
        )
        {
            if (request == null || request.ConsumableUseRequestId <= 0
                || request.ConsumableUseRequestId == _lastRequestId)
                return;
            _lastRequestId = request.ConsumableUseRequestId;
            ConsumableUseSnapshot result = new ConsumableUseSnapshot();
            result.RequestId = request.ConsumableUseRequestId;
            _result = result;
            if (!request.BotActive || !playerAlive)
            {
                result.Status = "unauthorized";
                result.Error = !request.BotActive
                    ? "bot_active is false" : "player is not alive";
                return;
            }
            string query = (request.ConsumableName ?? string.Empty).Trim();
            if (query.Length == 0)
            {
                result.Status = "not_found";
                result.Error = "consumable name is empty";
                return;
            }
            try
            {
                object runtime = _appServerRuntime.GetValue(null, null);
                object configs = runtime == null
                    ? null : _runtimeConsumables.GetValue(runtime, null);
                List<object> matches = new List<object>();
                foreach (KeyValuePair<object, object> entry in Entries(configs))
                {
                    object config = entry.Value;
                    string key = Convert.ToString(
                        entry.Key, CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    string id = ReadString(_configId, config);
                    string name = ReadString(_configDisplayName, config);
                    if (EqualsQuery(query, key)
                        || EqualsQuery(query, id)
                        || EqualsQuery(query, name))
                    {
                        if (!matches.Contains(config))
                            matches.Add(config);
                    }
                }
                if (matches.Count == 0)
                {
                    result.Status = "not_found";
                    result.Error = "consumable was not found: " + query;
                    return;
                }
                if (matches.Count != 1)
                {
                    result.Status = "ambiguous";
                    result.Error = "multiple consumables match: " + query;
                    return;
                }
                object selected = matches[0];
                result.ItemId = ReadString(_configId, selected);
                result.DisplayName = ReadString(_configDisplayName, selected);
                object character = _playerCharacterData.GetValue(player, null);
                object inventory = character == null
                    ? null : _characterInventory.GetValue(character, null);
                object values = inventory == null
                    ? null : _inventoryConsumables.GetValue(inventory, null);
                object owned = null;
                foreach (KeyValuePair<object, object> entry in Entries(values))
                {
                    object data = entry.Value;
                    string key = Convert.ToString(
                        entry.Key, CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    string id = ReadString(_consumableId, data);
                    if (EqualsQuery(result.ItemId, key)
                        || EqualsQuery(result.ItemId, id))
                    {
                        owned = data;
                        break;
                    }
                }
                int count = owned == null
                    ? 0 : Convert.ToInt32(
                        _consumableCount.GetValue(owned, null),
                        CultureInfo.InvariantCulture
                    );
                result.RemainingCount = count;
                if (count <= 0)
                {
                    result.Status = "out_of_stock";
                    result.Error = "consumable count is zero";
                    return;
                }
                bool accepted;
                object save = _playerSave == null
                    ? null : _playerSave.GetValue(player, null);
                if (_useConsumableData != null && save != null)
                {
                    // Replicate the inventory UI's own "use this bag item" call:
                    // PlayerSave.UseConsumable(ConsumableData). The overload returns
                    // void, so success is inferred from the absence of an exception;
                    // the owned stack count is re-read for reporting (it may only
                    // settle after the server round-trip).
                    _useConsumableData.Invoke(save, new object[] { owned });
                    accepted = true;
                }
                else if (_useConsumable != null)
                {
                    accepted = Convert.ToBoolean(
                        _useConsumable.Invoke(player, new object[] { selected }),
                        CultureInfo.InvariantCulture
                    );
                }
                else
                {
                    result.Status = "error";
                    result.Error = _useConsumableData != null
                        ? "PlayerController.Save returned null"
                        : "no usable UseConsumable overload";
                    _log.LogWarning("Consumable use failed: " + result.Error);
                    return;
                }
                result.RemainingCount = Math.Max(
                    0,
                    Convert.ToInt32(
                        _consumableCount.GetValue(owned, null),
                        CultureInfo.InvariantCulture
                    )
                );
                result.Status = accepted ? "accepted" : "rejected";
                if (!accepted)
                    result.Error = "PlayerController.UseConsumable returned false";
                _log.LogInfo(
                    "Consumable use " + result.Status + " id=" + result.ItemId
                    + " via=" + (_useConsumableData != null ? "data" : "config")
                    + " request=" + result.RequestId
                );
            }
            catch (Exception error)
            {
                TargetInvocationException invocation = error as TargetInvocationException;
                Exception actual = invocation != null && invocation.InnerException != null
                    ? invocation.InnerException : error;
                result.Status = "error";
                result.Error = actual.GetType().Name + ": " + actual.Message;
                _log.LogWarning("Consumable use failed: " + result.Error);
            }
        }

        internal static void AppendJson(StringBuilder json)
        {
            ConsumableUseSnapshot result = _result ?? new ConsumableUseSnapshot();
            json.Append(",\"consumable_use\":{");
            json.Append("\"request_id\":");
            json.Append(result.RequestId.ToString(CultureInfo.InvariantCulture));
            AppendString(json, "status", result.Status);
            AppendString(json, "item_id", result.ItemId);
            AppendString(json, "display_name", result.DisplayName);
            json.Append(",\"remaining_count\":");
            json.Append(result.RemainingCount.ToString(CultureInfo.InvariantCulture));
            AppendString(json, "error", result.Error);
            json.Append('}');
        }

        private static IEnumerable<KeyValuePair<object, object>> Entries(object dictionary)
        {
            if (dictionary == null)
                yield break;
            MethodInfo getEnumerator = dictionary.GetType().GetMethod("GetEnumerator", Type.EmptyTypes);
            if (getEnumerator == null)
                yield break;
            object enumerator = getEnumerator.Invoke(dictionary, null);
            MethodInfo moveNext = enumerator.GetType().GetMethod("MoveNext", Type.EmptyTypes);
            PropertyInfo current = enumerator.GetType().GetProperty("Current");
            while (moveNext != null && current != null
                && Convert.ToBoolean(moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture))
            {
                object pair = current.GetValue(enumerator, null);
                PropertyInfo key = pair.GetType().GetProperty("Key");
                PropertyInfo value = pair.GetType().GetProperty("Value");
                if (key != null && value != null)
                    yield return new KeyValuePair<object, object>(
                        key.GetValue(pair, null), value.GetValue(pair, null)
                    );
            }
        }

        private static bool EqualsQuery(string left, string right)
        {
            return string.Equals(
                (left ?? string.Empty).Trim(),
                (right ?? string.Empty).Trim(),
                StringComparison.OrdinalIgnoreCase
            );
        }

        private static string ReadString(PropertyInfo property, object target)
        {
            return target == null ? string.Empty : Convert.ToString(
                property.GetValue(target, null), CultureInfo.InvariantCulture
            ) ?? string.Empty;
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static void AppendString(StringBuilder json, string name, string value)
        {
            json.Append(",\"");
            json.Append(name);
            json.Append("\":\"");
            string text = value ?? string.Empty;
            for (int index = 0; index < text.Length; index++)
            {
                char character = text[index];
                if (character == '\\' || character == '"')
                    json.Append('\\');
                if (character == '\n')
                    json.Append("\\n");
                else if (character == '\r')
                    json.Append("\\r");
                else if (character == '\t')
                    json.Append("\\t");
                else
                    json.Append(character);
            }
            json.Append('"');
        }
    }

    internal static class BackgroundMovementPatch
    {
        private const long RequestRefreshIntervalMilliseconds = 25;
        private const long ErrorLogIntervalMilliseconds = 5000;
        private const long CapturePressDurationMilliseconds = 50;

        private static ManualLogSource _log;
        private static PropertyInfo _inputs;
        private static PropertyInfo _currentInputs;
        private static PropertyInfo _move;
        private static PropertyInfo _hotkeys;
        private static PropertyInfo _hotkeysHeld;
        private static PropertyInfo _unitId;
        private static PropertyInfo _clickPosition;
        private static PropertyInfo _fastCastPosition;
        private static PropertyInfo _click;
        private static PropertyInfo _altClick;
        private static PropertyInfo _fastCast;
        private static PropertyInfo _clickSkillIndex;
        private static PropertyInfo _skillHold;
        private static PropertyInfo _enemy;
        private static PropertyInfo _targetPlayer;
        private static PropertyInfo _interactable;
        private static PropertyInfo _samplePosition;
        private static PropertyInfo _lastTarget;
        private static PropertyInfo _castTarget;
        private static PropertyInfo _castPosition;
        private static PropertyInfo _appPlayer;
        private static PropertyInfo _objectId;
        private static MethodInfo _applyInputs;
        private static MethodInfo _processMovement;
        private static MethodInfo _processTargeting;
        private static MethodInfo _processSkills;
        private static MethodInfo _clickSkill;
        private static MethodInfo _getAssignedSkill;
        internal static string GuardianBondCastError = string.Empty;
        private static MethodInfo _sendInputsToServer;
        private static Type _inputDtoType;
        private static Type _moveType;
        private static ConstructorInfo _moveConstructor;
        private static FieldInfo _moveXField;
        private static FieldInfo _moveYField;
        private static FieldInfo _moveZField;
        private static PropertyInfo _moveXProperty;
        private static PropertyInfo _moveYProperty;
        private static PropertyInfo _moveZProperty;
        private static NavigationRequest _request;
        private static long _lastRequestReadMilliseconds;
        private static long _lastErrorLogMilliseconds;
        private static bool _wasControlling;
        private static bool _wasSending;
        private static string _lastShiftKeys = string.Empty;
        private static string _lastCaptureShiftKeys = string.Empty;
        private static string _lastManualInputSignature = string.Empty;
        private static string _lastInjectedInputSignature = string.Empty;
        private static string _lastCaptureSuccessSignature = string.Empty;
        private static long _leftCapturePressStartedMilliseconds;
        private static long _rightCapturePressStartedMilliseconds;
        private static int _resolvedFocusTargetObjectId;
        private static object _resolvedFocusTarget;
        private static string _lastSuccessSignature = string.Empty;
        private static readonly List<int> LeftShiftHotkeys = new List<int>();
        private static readonly List<int> RightShiftHotkeys = new List<int>();
        private static readonly List<int> SummonHotkeys = new List<int>();
        private static readonly List<int> MountHotkeys = new List<int>();
        private static readonly Dictionary<string, List<int>> NumpadHotkeys =
            new Dictionary<string, List<int>>(StringComparer.OrdinalIgnoreCase);
        private static string _lastSummonAction = string.Empty;
        private static long _lastSkillKeyRequestId;
        private static int _lastLootClickSeq;
        private static PropertyInfo _interactableId;
        private static PropertyInfo _lootId;
        private static PropertyInfo _skillReady;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType(
                "PlayerController"
            );
            Type appType = PlayerUpdatePatch.FindLoadedType("App");
            _inputDtoType = PlayerUpdatePatch.FindLoadedType("PlayerInputDto");
            _inputs = FindProperty(playerType, "Inputs");
            _currentInputs = FindProperty(playerType, "currentInputs");
            _move = FindProperty(_inputDtoType, "Move");
            _hotkeys = FindProperty(_inputDtoType, "Hotkeys");
            _hotkeysHeld = FindProperty(_inputDtoType, "HotkeysHeld");
            _unitId = FindProperty(_inputDtoType, "UnitId");
            _interactableId = FindProperty(_inputDtoType, "InteractableId");
            _lootId = FindProperty(_inputDtoType, "LootId");
            _skillReady = FindProperty(playerType, "SkillReady");
            _clickPosition = FindProperty(_inputDtoType, "ClickPosition");
            _fastCastPosition = FindProperty(
                _inputDtoType, "FastCastPosition"
            );
            _click = FindProperty(_inputDtoType, "Click");
            _altClick = FindProperty(_inputDtoType, "AltClick");
            _fastCast = FindProperty(_inputDtoType, "FastCast");
            _clickSkillIndex = FindProperty(_inputDtoType, "ClickSkillIndex");
            _skillHold = FindProperty(_inputDtoType, "SkillHold");
            _enemy = FindProperty(playerType, "enemy");
            _targetPlayer = FindProperty(playerType, "player");
            _interactable = FindProperty(playerType, "interactable");
            _samplePosition = FindProperty(playerType, "position");
            _lastTarget = FindProperty(playerType, "LastTarget");
            _castTarget = FindProperty(playerType, "CastTarget");
            _castPosition = FindProperty(playerType, "CastPosition");
            _appPlayer = FindProperty(appType, "Player");
            _objectId = FindProperty(playerType, "ObjectId");
            _applyInputs = FindMethod(playerType, "ApplyInputs", 1);
            _processMovement = FindMethod(playerType, "ProcessMovement", 1);
            _processTargeting = FindMethod(playerType, "ProcessTargeting", 0);
            _processSkills = FindMethod(playerType, "ProcessSkills", 0);
            _clickSkill = FindMethod(playerType, "ClickSkill", 1);
            _getAssignedSkill = FindMethod(playerType, "GetAssignedSkill", 1);
            _sendInputsToServer = FindMethod(
                playerType, "SendInputsToServer", 1
            );
            if (!_inputs.CanRead || !_inputs.CanWrite || !_move.CanWrite)
            {
                throw new MissingMemberException(
                    playerType.FullName,
                    "writable Inputs and PlayerInputDto.Move"
                );
            }
            _moveType = _move.PropertyType;
            _moveConstructor = _moveType.GetConstructor(new Type[] {
                typeof(float), typeof(float)
            });
            _moveXField = _moveType.GetField(
                "x", BindingFlags.Public | BindingFlags.Instance
            );
            _moveYField = _moveType.GetField(
                "y", BindingFlags.Public | BindingFlags.Instance
            );
            _moveZField = _moveType.GetField(
                "z", BindingFlags.Public | BindingFlags.Instance
            );
            _moveXProperty = _moveType.GetProperty(
                "x", BindingFlags.Public | BindingFlags.Instance
            );
            _moveYProperty = _moveType.GetProperty(
                "y", BindingFlags.Public | BindingFlags.Instance
            );
            _moveZProperty = _moveType.GetProperty(
                "z", BindingFlags.Public | BindingFlags.Instance
            );
            if (_moveConstructor == null
                && (_moveXField == null || _moveYField == null)
                && (_moveXProperty == null || !_moveXProperty.CanWrite
                    || _moveYProperty == null || !_moveYProperty.CanWrite))
            {
                throw new MissingMemberException(
                    _moveType.FullName,
                    ".ctor(float,float) or writable x/y"
                );
            }
            log.LogInfo(
                "Background movement DTO initialized: input="
                + _inputDtoType.FullName + "; move=" + _moveType.FullName
            );
            try
            {
                ResolveShiftHotkeys(log);
            }
            catch (Exception error)
            {
                Exception actual = error is TargetInvocationException
                    && error.InnerException != null
                        ? error.InnerException
                        : error;
                log.LogWarning(
                    "Background Shift binding discovery failed: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
        }

        internal static void Postfix(object __instance, ref bool __result)
        {
            long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            try
            {
                RefreshRequest(now);
                if (!IsLocalPlayer(__instance))
                    return;
                ObserveManualInput(__instance, __result);

                bool requestAuthorized = _request != null
                    && _request.BotActive;
                bool sendMode = requestAuthorized
                    && IsSendMode(_request.BackgroundInputMode);
                bool authorized = requestAuthorized
                    && (!sendMode
                        || (_request.BackgroundSkillMode == "capture"
                            && (_request.FocusTargetObjectId > 0
                                || _request.ShiftKeys.Length > 0
                                || _lastCaptureShiftKeys.Length > 0)));
                if (!authorized && !_wasControlling)
                    return;

                float horizontal = 0f;
                float vertical = 0f;
                float depth = 0f;
                if (authorized)
                {
                    horizontal = _request.MovementWorldX;
                    vertical = _request.MovementWorldY;
                    depth = _request.MovementWorldZ;
                }

                bool capturedByGame = __result;
                object inputs = capturedByGame
                    ? _inputs.GetValue(__instance, null)
                    : null;
                if (inputs == null)
                    inputs = CreateNeutralInputs();
                _move.SetValue(
                    inputs,
                    CreateMoveVector(horizontal, vertical, depth),
                    null
                );
                string requestedShiftKeys = authorized
                    ? _request.ShiftKeys
                    : string.Empty;
                UpdateCaptureShiftTiming(
                    now, requestedShiftKeys, _lastCaptureShiftKeys
                );
                ApplyCapturedShiftHotkeys(
                    inputs, requestedShiftKeys, now
                );
                int focusTargetObjectId = authorized
                    ? _request.FocusTargetObjectId
                    : 0;
                bool focusResolved = ResolveFocusTarget(focusTargetObjectId);
                _unitId.SetValue(inputs, 0, null);
                _clickPosition.SetValue(
                    inputs, CreateMoveVector(0f, 0f, 0f), null
                );
                if (focusTargetObjectId > 0)
                {
                    VectorData focusAim = focusResolved
                        ? PlayerUpdatePatch.GetUnitAimPosition(
                            _resolvedFocusTarget
                        )
                        : new VectorData(
                            _request.FocusTargetWorldX,
                            _request.FocusTargetWorldY,
                            _request.FocusTargetWorldZ
                        );
                    object fastCastPosition = CreateScaledWorldVector(
                        focusAim.X, focusAim.Y, focusAim.Z
                    );
                    _fastCastPosition.SetValue(
                        inputs, fastCastPosition, null
                    );
                }
                bool shiftActive = requestedShiftKeys.Length > 0;
                bool shiftInHoldPhase = AnyCapturedShiftInHoldPhase(
                    requestedShiftKeys, now
                );
                _fastCast.SetValue(inputs, shiftActive, null);
                _skillHold.SetValue(
                    inputs, shiftActive && shiftInHoldPhase, null
                );
                _inputs.SetValue(__instance, inputs, null);
                if (focusResolved)
                    ApplyResolvedHover(__instance);
                LogCapturedInjection(
                    __instance, inputs, requestedShiftKeys, focusResolved
                );
                if (authorized
                    && (_request.BackgroundInputMode == "both"
                        || _request.BackgroundInputMode == "apply"))
                {
                    _currentInputs.SetValue(__instance, inputs, null);
                }
                if (authorized && _request.BackgroundInputMode == "apply")
                {
                    _applyInputs.Invoke(__instance, new object[] { inputs });
                }
                __result = true;
                _wasControlling = authorized;
                _lastCaptureShiftKeys = requestedShiftKeys;
                string signature = authorized
                    ? _request.BackgroundInputMode
                        + ":shift=" + (requestedShiftKeys.Length == 0
                            ? "-" : requestedShiftKeys)
                        + ":focus=" + focusTargetObjectId
                        + (focusTargetObjectId > 0
                            ? (focusResolved ? "(resolved)" : "(missing)")
                            : string.Empty)
                    : "stopped";
                if (signature != _lastCaptureSuccessSignature)
                {
                    _lastCaptureSuccessSignature = signature;
                    _log.LogInfo("Background capture input " + signature);
                }
            }
            catch (Exception error)
            {
                _wasControlling = false;
                LogError(now, error);
            }
        }

        internal static void UpdatePostfix(object __instance)
        {
            long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            try
            {
                RefreshRequest(now);
                string mode = _request == null
                    ? string.Empty
                    : _request.BackgroundInputMode;
                bool authorized = _request != null
                    && _request.BotActive
                    && IsSendMode(mode);
                if (!IsLocalPlayer(__instance))
                    return;
                if (_request != null && (!authorized || !_request.LootScanActive))
                    _lastLootClickSeq = _request.LootInteract;
                if (!authorized && !_wasSending)
                    return;

                float x = authorized ? _request.MovementWorldX : 0f;
                float y = authorized ? _request.MovementWorldY : 0f;
                float z = authorized ? _request.MovementWorldZ : 0f;
                object inputs = CreateNeutralInputs();
                _move.SetValue(inputs, CreateMoveVector(x, y, z), null);
                string requestedShiftKeys = authorized
                    ? _request.ShiftKeys
                    : string.Empty;
                bool captureHandlesSkills = authorized
                    && _request.BackgroundSkillMode == "capture";
                string injectedShiftKeys = captureHandlesSkills
                    ? string.Empty : requestedShiftKeys;
                ApplyShiftHotkeys(inputs, injectedShiftKeys, _lastShiftKeys);
                int focusTargetObjectId = authorized
                    ? _request.FocusTargetObjectId
                    : 0;
                bool focusResolved = ResolveFocusTarget(focusTargetObjectId);
                _unitId.SetValue(inputs, focusTargetObjectId, null);
                if (focusTargetObjectId > 0)
                {
                    object focusPosition = CreateMoveVector(
                        _request.FocusTargetWorldX,
                        _request.FocusTargetWorldY,
                        _request.FocusTargetWorldZ
                    );
                    _clickPosition.SetValue(inputs, focusPosition, null);
                    _fastCastPosition.SetValue(inputs, focusPosition, null);
                }
                bool lootPickupActive = authorized
                    && ApplyPendingLootPickup(__instance, inputs);
                if (lootPickupActive)
                {
                    focusTargetObjectId = 0;
                    focusResolved = false;
                    injectedShiftKeys = string.Empty;
                }
                _inputs.SetValue(__instance, inputs, null);
                _currentInputs.SetValue(__instance, inputs, null);
                if (focusResolved)
                    ApplyResolvedFocus(__instance);

                if (lootPickupActive)
                {
                    // Use the same local targeting path as a normal click and
                    // send this exact DTO to the server below. LootDrop.Interact
                    // itself is server-only; ProcessSkills does not consume V.
                    _applyInputs.Invoke(__instance, new object[] { inputs });
                    _processTargeting.Invoke(__instance, null);
                }
                else if (authorized && mode == "send_apply")
                    _applyInputs.Invoke(__instance, new object[] { inputs });
                else if (authorized && mode == "send_process")
                {
                    _processMovement.Invoke(__instance, new object[] { inputs });
                    if (focusTargetObjectId > 0 && !captureHandlesSkills)
                    {
                        _processTargeting.Invoke(__instance, null);
                        if (focusResolved)
                            ApplyResolvedFocus(__instance);
                    }
                    if (!captureHandlesSkills
                        && (injectedShiftKeys.Length > 0
                            || _lastShiftKeys.Length > 0))
                    {
                        string skillMode = _request.BackgroundSkillMode;
                        if (skillMode == "process"
                            || skillMode == "process_click")
                        {
                            _processSkills.Invoke(__instance, null);
                        }
                        if (skillMode == "click"
                            || skillMode == "process_click")
                        {
                            ClickNewShiftSkills(__instance, injectedShiftKeys);
                        }
                    }
                }

                if (authorized && !lootPickupActive)
                {
                    FireSummonActionHotkeys(__instance, _request.SummonAction);
                    FireSkillKeyHotkeys(
                        __instance,
                        ref inputs,
                        _request.SkillKeyRequestId,
                        _request.SkillKey,
                        _request.SkillKeyTargetSummon
                    );
                }
                else if (!authorized)
                {
                    _lastSummonAction = string.Empty;
                    _lastSkillKeyRequestId = _request.SkillKeyRequestId;
                    // Absorb any pending loot pulse while unauthorized so a stale
                    // pickup click does not fire the moment control resumes.
                    _lastLootClickSeq = _request.LootInteract;
                }

                _sendInputsToServer.Invoke(__instance, new object[] { inputs });
                if (lootPickupActive)
                    _log.LogInfo("Targeted loot input sent: seq=" + _lastLootClickSeq
                        + " requested=" + _request.LootInteractObjectId
                        + " interactable_id=" + _interactableId.GetValue(inputs, null)
                        + " unit_id=" + _unitId.GetValue(inputs, null)
                        + " click=" + _click.GetValue(inputs, null)
                        + " hotkeys=" + _hotkeys.GetValue(inputs, null));
                _wasSending = authorized;
                _lastShiftKeys = injectedShiftKeys;

                string signature = authorized
                    ? mode + ":" + x + "," + y + "," + z
                        + ":shift=" + (requestedShiftKeys.Length == 0
                            ? "-" : requestedShiftKeys)
                        + ":focus=" + focusTargetObjectId
                        + (focusTargetObjectId > 0
                            ? (focusResolved ? "(resolved)" : "(missing)")
                            : string.Empty)
                        + ":skill=" + _request.BackgroundSkillMode
                    : "stopped";
                if (signature != _lastSuccessSignature)
                {
                    _lastSuccessSignature = signature;
                    _log.LogInfo("Background movement RPC " + signature);
                }
            }
            catch (Exception error)
            {
                _wasSending = false;
                LogError(now, error);
            }
        }

        private static void RefreshRequest(long now)
        {
            if (now - _lastRequestReadMilliseconds
                < RequestRefreshIntervalMilliseconds)
                return;
            _lastRequestReadMilliseconds = now;
            _request = PlayerUpdatePatch.ReadRequest(now);
        }

        private static bool IsSendMode(string mode)
        {
            return mode == "send"
                || mode == "send_apply"
                || mode == "send_process";
        }

        private static bool ResolveFocusTarget(int objectId)
        {
            if (objectId <= 0)
            {
                _resolvedFocusTargetObjectId = 0;
                _resolvedFocusTarget = null;
                return false;
            }
            if (_resolvedFocusTarget != null
                && _resolvedFocusTargetObjectId == objectId)
                return true;
            _resolvedFocusTarget = PlayerUpdatePatch.FindEnemyUnitByObjectId(
                objectId
            );
            _resolvedFocusTargetObjectId = _resolvedFocusTarget == null
                ? 0 : objectId;
            return _resolvedFocusTarget != null;
        }

        private static void ObserveManualInput(
            object playerController,
            bool captured
        )
        {
            if (!captured)
                return;
            object inputs = _inputs.GetValue(playerController, null);
            if (inputs == null)
                return;
            ulong hotkeys = Convert.ToUInt64(
                _hotkeys.GetValue(inputs, null), CultureInfo.InvariantCulture
            );
            ulong hotkeysHeld = Convert.ToUInt64(
                _hotkeysHeld.GetValue(inputs, null), CultureInfo.InvariantCulture
            );
            if (hotkeys == 0UL && hotkeysHeld == 0UL)
            {
                _lastManualInputSignature = string.Empty;
                return;
            }
            int unitId = Convert.ToInt32(
                _unitId.GetValue(inputs, null), CultureInfo.InvariantCulture
            );
            object enemy = _enemy.GetValue(playerController, null);
            object castTarget = _castTarget.GetValue(playerController, null);
            string signature = "hotkeys=" + hotkeys
                + "; held=" + hotkeysHeld
                + "; click=" + FormatValue(_click.GetValue(inputs, null))
                + "; alt_click=" + FormatValue(_altClick.GetValue(inputs, null))
                + "; fast_cast=" + FormatValue(_fastCast.GetValue(inputs, null))
                + "; click_skill="
                + FormatValue(_clickSkillIndex.GetValue(inputs, null))
                + "; skill_hold=" + FormatValue(_skillHold.GetValue(inputs, null))
                + "; unit=" + unitId
                + "; click_position="
                + FormatVector(_clickPosition.GetValue(inputs, null))
                + "; fast_cast_position="
                + FormatVector(_fastCastPosition.GetValue(inputs, null))
                + "; enemy=" + PlayerUpdatePatch.GetUnitObjectId(enemy)
                + "; cast_target="
                + PlayerUpdatePatch.GetUnitObjectId(castTarget)
                + "; last_target=" + PlayerUpdatePatch.GetUnitObjectId(
                    _lastTarget.GetValue(playerController, null))
                + "; target_player=" + PlayerUpdatePatch.GetUnitObjectId(
                    _targetPlayer.GetValue(playerController, null))
                + "; interactable=" + PlayerUpdatePatch.GetUnitObjectId(
                    _interactable.GetValue(playerController, null));
            if (signature == _lastManualInputSignature)
                return;
            _lastManualInputSignature = signature;
            _log.LogInfo("Captured manual input: " + signature);
        }

        private static void LogCapturedInjection(
            object playerController,
            object inputs,
            string shiftKeys,
            bool focusResolved
        )
        {
            ulong hotkeys = Convert.ToUInt64(
                _hotkeys.GetValue(inputs, null), CultureInfo.InvariantCulture
            );
            ulong hotkeysHeld = Convert.ToUInt64(
                _hotkeysHeld.GetValue(inputs, null), CultureInfo.InvariantCulture
            );
            string signature = "shift="
                + (shiftKeys.Length == 0 ? "-" : shiftKeys)
                + "; hotkeys=" + hotkeys
                + "; held=" + hotkeysHeld
                + "; fast_cast=" + FormatValue(
                    _fastCast.GetValue(inputs, null)
                )
                + "; skill_hold=" + FormatValue(
                    _skillHold.GetValue(inputs, null)
                )
                + "; unit=" + FormatValue(_unitId.GetValue(inputs, null))
                + "; click_position=" + FormatVector(
                    _clickPosition.GetValue(inputs, null)
                )
                + "; fast_cast_position=" + FormatVector(
                    _fastCastPosition.GetValue(inputs, null)
                )
                + "; enemy=" + PlayerUpdatePatch.GetUnitObjectId(
                    _enemy.GetValue(playerController, null)
                )
                + "; focus_resolved=" + focusResolved;
            if (signature == _lastInjectedInputSignature)
                return;
            _lastInjectedInputSignature = signature;
            _log.LogInfo("Injected capture DTO: " + signature);
        }

        private static string FormatValue(object value)
        {
            return Convert.ToString(value, CultureInfo.InvariantCulture)
                ?? string.Empty;
        }

        private static string FormatVector(object value)
        {
            if (value == null)
                return "null";
            Type type = value.GetType();
            return ReadVectorComponent(type, value, "x") + ","
                + ReadVectorComponent(type, value, "y") + ","
                + ReadVectorComponent(type, value, "z");
        }

        private static string ReadVectorComponent(
            Type type,
            object value,
            string name
        )
        {
            FieldInfo field = type.GetField(
                name, BindingFlags.Public | BindingFlags.Instance
            );
            object component = field == null ? null : field.GetValue(value);
            if (field == null)
            {
                PropertyInfo property = type.GetProperty(
                    name, BindingFlags.Public | BindingFlags.Instance
                );
                component = property == null
                    ? null : property.GetValue(value, null);
            }
            return FormatValue(component);
        }

        private static void ApplyResolvedFocus(object playerController)
        {
            object targetPosition = PlayerUpdatePatch.GetUnitPositionValue(
                _resolvedFocusTarget
            );
            _enemy.SetValue(playerController, _resolvedFocusTarget, null);
            _targetPlayer.SetValue(playerController, null, null);
            _interactable.SetValue(playerController, null, null);
            _samplePosition.SetValue(playerController, targetPosition, null);
            _lastTarget.SetValue(playerController, _resolvedFocusTarget, null);
            _castTarget.SetValue(playerController, _resolvedFocusTarget, null);
            _castPosition.SetValue(playerController, targetPosition, null);
        }

        private static void ApplyResolvedHover(object playerController)
        {
            object targetPosition = PlayerUpdatePatch.GetUnitAimPositionValue(
                _resolvedFocusTarget
            );
            _enemy.SetValue(playerController, _resolvedFocusTarget, null);
            _targetPlayer.SetValue(playerController, null, null);
            _interactable.SetValue(playerController, null, null);
            _samplePosition.SetValue(playerController, targetPosition, null);
        }

        private static void ClickNewShiftSkills(
            object playerController,
            string shiftKeys
        )
        {
            if (HasShiftKey(shiftKeys, "lshift")
                && !HasShiftKey(_lastShiftKeys, "lshift"))
            {
                ClickHotkeys(playerController, LeftShiftHotkeys);
            }
            if (HasShiftKey(shiftKeys, "rshift")
                && !HasShiftKey(_lastShiftKeys, "rshift"))
            {
                ClickHotkeys(playerController, RightShiftHotkeys);
            }
        }

        private static void FireSummonActionHotkeys(
            object playerController, string action
        )
        {
            string normalized = action ?? string.Empty;
            if (normalized == _lastSummonAction)
                return;
            _lastSummonAction = normalized;
            if (normalized == "reanimation")
                ClickHotkeys(playerController, SummonHotkeys);
            else if (normalized == "mount")
                ClickHotkeys(playerController, MountHotkeys);
        }

        private static void FireSkillKeyHotkeys(
            object playerController, ref object inputs, long requestId,
            string key, bool targetSummon
        )
        {
            if (requestId <= 0L || requestId == _lastSkillKeyRequestId)
                return;
            _lastSkillKeyRequestId = requestId;
            string normalized = (key ?? string.Empty).ToLowerInvariant();
            List<int> hotkeys;
            if (!NumpadHotkeys.TryGetValue(normalized, out hotkeys))
                return;
            // On-demand loading may happen before the player's bindings arrive.
            // Resolve again when an actual skill request finds an empty binding.
            if (hotkeys.Count == 0)
            {
                ResolveShiftHotkeys(_log);
                if (!NumpadHotkeys.TryGetValue(normalized, out hotkeys))
                    return;
            }
            if (targetSummon)
            {
                GuardianBondCastError = string.Empty;
                // Validate the actual binding before sending any target-required skill.
                int guardianHotkey = -1;
                object skill = null;
                for (int i = 0; i < hotkeys.Count; i++)
                {
                    object assigned = _getAssignedSkill.Invoke(
                        playerController, new object[] { hotkeys[i] });
                    if (assigned != null && string.Equals(
                        FindProperty(assigned.GetType(), "Id").GetValue(assigned, null)
                            as string, "GuardianBond", StringComparison.Ordinal))
                    {
                        guardianHotkey = hotkeys[i];
                        skill = assigned;
                        break;
                    }
                }
                if (inputs == null || guardianHotkey < 0 || guardianHotkey >= 64)
                {
                    GuardianBondCastError = "Selected NumPad key is not bound to GuardianBond";
                    _log.LogWarning(GuardianBondCastError);
                    return;
                }
                object summon = PlayerUpdatePatch.ResolveSummonUnit(
                    playerController
                );
                int summonId = PlayerUpdatePatch.GetUnitObjectId(summon);
                if (summon != null && summonId > 0)
                {
                    object skills = FindProperty(playerController.GetType(), "Skills")
                        .GetValue(playerController, null);
                    bool canHit = Convert.ToBoolean(FindMethod(skills.GetType(), "CanHit", 2)
                        .Invoke(skills, new object[] { skill, summon }));
                    bool busy = Convert.ToBoolean(FindProperty(skills.GetType(), "IsCasting")
                        .GetValue(skills, null));
                    bool cooldown = Convert.ToBoolean(FindProperty(skill.GetType(), "IsOnCooldown")
                        .GetValue(skill, null));
                    if (!canHit || busy || cooldown)
                    {
                        GuardianBondCastError = !canHit ? "Owned summon is not a valid GuardianBond target"
                            : "Waiting for cast or cooldown";
                        return;
                    }
                    _hotkeys.SetValue(inputs, 1UL << guardianHotkey, null);
                    _hotkeysHeld.SetValue(inputs, 0UL, null);
                    _unitId.SetValue(inputs, summonId, null);
                    _fastCast.SetValue(inputs, true, null);
                    _click.SetValue(inputs, false, null);
                    _altClick.SetValue(inputs, false, null);
                    _clickSkillIndex.SetValue(inputs, -1, null);
                    _skillHold.SetValue(inputs, false, null);
                    _clickPosition.SetValue(inputs, CreateMoveVector(0f, 0f, 0f), null);
                    _fastCastPosition.SetValue(inputs, CreateMoveVector(0f, 0f, 0f), null);
                    // FastCast reads the friendly hover and writes Inputs.UnitId.
                    _enemy.SetValue(playerController, null, null);
                    _targetPlayer.SetValue(playerController, summon, null);
                    _interactable.SetValue(playerController, null, null);
                    _samplePosition.SetValue(playerController,
                        PlayerUpdatePatch.GetUnitAimPositionValue(summon), null);
                    // DTO is a value type: write AFTER editing, then process now.
                    _inputs.SetValue(playerController, inputs, null);
                    _currentInputs.SetValue(playerController, inputs, null);
                    _processSkills.Invoke(playerController, null);
                    inputs = _inputs.GetValue(playerController, null);
                    _currentInputs.SetValue(playerController, inputs, null);
                    _log.LogInfo(
                        "GuardianBond input processed: owner="
                        + PlayerUpdatePatch.GetUnitObjectId(playerController)
                        + " summon=" + summonId
                        + " sent_unit=" + _unitId.GetValue(inputs, null)
                        + " cast_target=" + PlayerUpdatePatch.GetUnitObjectId(
                            _castTarget.GetValue(playerController, null))
                        + " key=" + normalized
                    );
                    return;
                }
                GuardianBondCastError = "No living summon owned by the local player";
                return;
            }
            ClickHotkeys(playerController, hotkeys);
        }

        // One click per IPC sequence, with its network target in the same DTO.
        // The server resolves InteractableId and runs the normal locked/range/
        // inventory checks. UnitId addresses combat units, not ground loot.
        private static bool ApplyPendingLootPickup(object player, object inputs)
        {
            if (_request == null || !_request.BotActive || !_request.LootScanActive)
                return false;
            int seq = _request.LootInteract;
            int objectId = _request.LootInteractObjectId;
            if (seq <= 0 || seq == _lastLootClickSeq)
                return false;
            _lastLootClickSeq = seq;
            if (objectId <= 0)
                return false;
            string rejection;
            if (!PlayerUpdatePatch.CanInteractWithCachedLoot(player, objectId, out rejection))
            {
                _log.LogInfo("Targeted loot input skipped: id=" + objectId + " reason=" + rejection);
                return false;
            }
            object skills = FindProperty(player.GetType(), "Skills").GetValue(player, null);
            if (skills == null || Convert.ToBoolean(FindProperty(skills.GetType(), "IsCasting")
                .GetValue(skills, null)) || _skillReady.GetValue(player, null) != null)
            {
                _log.LogInfo("Targeted loot input skipped: id=" + objectId + " reason=skill busy");
                return false;
            }
            _move.SetValue(inputs, CreateMoveVector(0f, 0f, 0f), null);
            _hotkeys.SetValue(inputs, 0UL, null);
            _hotkeysHeld.SetValue(inputs, 0UL, null);
            _unitId.SetValue(inputs, 0, null);
            _lootId.SetValue(inputs, 0, null);
            _interactableId.SetValue(inputs, objectId, null);
            _click.SetValue(inputs, true, null);
            _altClick.SetValue(inputs, false, null);
            _fastCast.SetValue(inputs, false, null);
            _skillHold.SetValue(inputs, false, null);
            _clickSkillIndex.SetValue(inputs, -1, null);
            _clickPosition.SetValue(inputs, CreateMoveVector(0f, 0f, 0f), null);
            _fastCastPosition.SetValue(inputs, CreateMoveVector(0f, 0f, 0f), null);
            return true;
        }

        private static ulong ToUInt64(object value)
        {
            if (value == null)
                return 0UL;
            return Convert.ToUInt64(value, CultureInfo.InvariantCulture);
        }

        private static void ClickHotkeys(
            object playerController,
            List<int> hotkeys
        )
        {
            for (int index = 0; index < hotkeys.Count; index++)
            {
                int hotkey = hotkeys[index];
                if (hotkey >= 0 && hotkey < 40)
                    _clickSkill.Invoke(playerController, new object[] { hotkey });
            }
        }

        private static void ResolveShiftHotkeys(ManualLogSource log)
        {
            LeftShiftHotkeys.Clear();
            RightShiftHotkeys.Clear();
            SummonHotkeys.Clear();
            MountHotkeys.Clear();
            NumpadHotkeys.Clear();
            Type hotkeyType = PlayerUpdatePatch.FindLoadedType("Hotkey");
            Type hotkeyManagerType = PlayerUpdatePatch.FindLoadedType(
                "HotkeyManager"
            );
            Type bindingType = PlayerUpdatePatch.FindLoadedType("HotkeyBinding");
            Type keyCodeType = PlayerUpdatePatch.FindLoadedType(
                "UnityEngine.KeyCode"
            );
            MethodInfo getBinding = FindMethod(
                hotkeyManagerType, "Get", 1
            );
            FieldInfo mainKey = bindingType.GetField(
                "Main", BindingFlags.Public | BindingFlags.Instance
            );
            if (mainKey == null)
                throw new MissingMemberException(bindingType.FullName, "Main");
            int leftShift = Convert.ToInt32(
                Enum.Parse(keyCodeType, "LeftShift"),
                CultureInfo.InvariantCulture
            );
            int rightShift = Convert.ToInt32(
                Enum.Parse(keyCodeType, "RightShift"),
                CultureInfo.InvariantCulture
            );
            int summonKey = Convert.ToInt32(
                Enum.Parse(keyCodeType, "Alpha9"),
                CultureInfo.InvariantCulture
            );
            int mountKey = Convert.ToInt32(
                Enum.Parse(keyCodeType, "Alpha0"),
                CultureInfo.InvariantCulture
            );
            int[] numpadKeys = new int[10];
            for (int number = 0; number < numpadKeys.Length; number++)
            {
                numpadKeys[number] = Convert.ToInt32(
                    Enum.Parse(keyCodeType, "Keypad" + number),
                    CultureInfo.InvariantCulture
                );
                NumpadHotkeys["numpad" + number] = new List<int>();
            }
            Array values = Enum.GetValues(hotkeyType);
            for (int index = 0; index < values.Length; index++)
            {
                object hotkey = values.GetValue(index);
                int hotkeyValue = Convert.ToInt32(
                    hotkey, CultureInfo.InvariantCulture
                );
                if (hotkeyValue < 0 || hotkeyValue >= 64)
                    continue;
                object binding = getBinding.Invoke(null, new object[] { hotkey });
                int configuredKey = Convert.ToInt32(
                    mainKey.GetValue(binding), CultureInfo.InvariantCulture
                );
                if (configuredKey == leftShift)
                    LeftShiftHotkeys.Add(hotkeyValue);
                if (configuredKey == rightShift)
                    RightShiftHotkeys.Add(hotkeyValue);
                if (configuredKey == summonKey)
                    SummonHotkeys.Add(hotkeyValue);
                if (configuredKey == mountKey)
                    MountHotkeys.Add(hotkeyValue);
                for (int number = 0; number < numpadKeys.Length; number++)
                {
                    if (configuredKey == numpadKeys[number])
                        NumpadHotkeys["numpad" + number].Add(hotkeyValue);
                }
            }
            log.LogInfo(
                "Background Shift bindings: left="
                + FormatHotkeys(hotkeyType, LeftShiftHotkeys)
                + "; right=" + FormatHotkeys(hotkeyType, RightShiftHotkeys)
            );
            log.LogInfo(
                "Background Summon bindings: reanimation(Alpha9)="
                + FormatHotkeys(hotkeyType, SummonHotkeys)
                + "; mount(Alpha0)=" + FormatHotkeys(hotkeyType, MountHotkeys)
            );
            for (int number = 0; number < numpadKeys.Length; number++)
            {
                log.LogInfo(
                    "Background skill binding Keypad" + number + "="
                    + FormatHotkeys(
                        hotkeyType, NumpadHotkeys["numpad" + number]
                    )
                );
            }

        }

        private static int TryGetHotkeyValue(Type hotkeyType, string name)
        {
            try
            {
                return Convert.ToInt32(
                    Enum.Parse(hotkeyType, name), CultureInfo.InvariantCulture
                );
            }
            catch
            {
                return -1;
            }
        }

        private static string FormatHotkeys(Type hotkeyType, List<int> values)
        {
            if (values.Count == 0)
                return "none";
            string[] names = new string[values.Count];
            for (int index = 0; index < values.Count; index++)
            {
                names[index] = Enum.GetName(hotkeyType, values[index])
                    + "(" + values[index] + ")";
            }
            return string.Join(",", names);
        }

        private static object CreateNeutralInputs()
        {
            object inputs = Activator.CreateInstance(_inputDtoType);
            // Zero is a real skill slot (normally Left Shift), not "no click".
            // ProcessSkills checks this index independently of Hotkeys/Held.
            // Only initialize newly allocated DTOs: a DTO captured by the game
            // may carry the NumPad buff queued by ClickSkill on the last frame.
            _clickSkillIndex.SetValue(inputs, -1, null);
            return inputs;
        }

        private static void ApplyShiftHotkeys(
            object inputs,
            string shiftKeys,
            string previousShiftKeys
        )
        {
            bool leftHeld = HasShiftKey(shiftKeys, "lshift");
            bool rightHeld = HasShiftKey(shiftKeys, "rshift");
            bool leftWasHeld = HasShiftKey(previousShiftKeys, "lshift");
            bool rightWasHeld = HasShiftKey(previousShiftKeys, "rshift");
            ulong pressed = 0UL;
            ulong held = 0UL;
            AddHotkeyMasks(
                LeftShiftHotkeys,
                leftHeld && !leftWasHeld,
                leftHeld,
                ref pressed,
                ref held
            );
            AddHotkeyMasks(
                RightShiftHotkeys,
                rightHeld && !rightWasHeld,
                rightHeld,
                ref pressed,
                ref held
            );
            _hotkeys.SetValue(inputs, pressed, null);
            _hotkeysHeld.SetValue(inputs, held, null);
        }

        private static void ApplyCapturedShiftHotkeys(
            object inputs,
            string shiftKeys,
            long now
        )
        {
            bool leftHeld = HasShiftKey(shiftKeys, "lshift");
            bool rightHeld = HasShiftKey(shiftKeys, "rshift");
            bool leftPressed = leftHeld
                && now - _leftCapturePressStartedMilliseconds
                    < CapturePressDurationMilliseconds;
            bool rightPressed = rightHeld
                && now - _rightCapturePressStartedMilliseconds
                    < CapturePressDurationMilliseconds;
            ulong pressed = 0UL;
            ulong held = 0UL;
            AddHotkeyMasks(
                LeftShiftHotkeys,
                leftPressed,
                leftHeld && !leftPressed,
                ref pressed,
                ref held
            );
            AddHotkeyMasks(
                RightShiftHotkeys,
                rightPressed,
                rightHeld && !rightPressed,
                ref pressed,
                ref held
            );
            _hotkeys.SetValue(inputs, pressed, null);
            _hotkeysHeld.SetValue(inputs, held, null);
        }

        private static void UpdateCaptureShiftTiming(
            long now,
            string shiftKeys,
            string previousShiftKeys
        )
        {
            bool leftHeld = HasShiftKey(shiftKeys, "lshift");
            bool rightHeld = HasShiftKey(shiftKeys, "rshift");
            if (leftHeld
                && !HasShiftKey(previousShiftKeys, "lshift"))
                _leftCapturePressStartedMilliseconds = now;
            else if (!leftHeld)
                _leftCapturePressStartedMilliseconds = 0L;
            if (rightHeld
                && !HasShiftKey(previousShiftKeys, "rshift"))
                _rightCapturePressStartedMilliseconds = now;
            else if (!rightHeld)
                _rightCapturePressStartedMilliseconds = 0L;
        }

        private static bool AnyCapturedShiftInHoldPhase(
            string shiftKeys,
            long now
        )
        {
            bool leftHeld = HasShiftKey(shiftKeys, "lshift");
            bool rightHeld = HasShiftKey(shiftKeys, "rshift");
            return (leftHeld
                    && now - _leftCapturePressStartedMilliseconds
                        >= CapturePressDurationMilliseconds)
                || (rightHeld
                    && now - _rightCapturePressStartedMilliseconds
                        >= CapturePressDurationMilliseconds);
        }

        private static bool HasShiftKey(string value, string key)
        {
            if (string.IsNullOrEmpty(value))
                return false;
            string[] keys = value.Split(',');
            for (int index = 0; index < keys.Length; index++)
            {
                if (string.Equals(keys[index], key, StringComparison.Ordinal))
                    return true;
            }
            return false;
        }

        private static void AddHotkeyMasks(
            List<int> hotkeys,
            bool pressedNow,
            bool heldNow,
            ref ulong pressed,
            ref ulong held
        )
        {
            for (int index = 0; index < hotkeys.Count; index++)
            {
                ulong bit = 1UL << hotkeys[index];
                if (pressedNow)
                    pressed |= bit;
                if (heldNow)
                    held |= bit;
            }
        }

        private static bool IsLocalPlayer(object instance)
        {
            object localPlayer = _appPlayer.GetValue(null, null);
            if (localPlayer == null || instance == null)
                return false;
            if (ReferenceEquals(localPlayer, instance))
                return true;
            int localId = Convert.ToInt32(
                _objectId.GetValue(localPlayer, null),
                CultureInfo.InvariantCulture
            );
            int instanceId = Convert.ToInt32(
                _objectId.GetValue(instance, null),
                CultureInfo.InvariantCulture
            );
            return localId > 0 && localId == instanceId;
        }

        private static void LogError(long now, Exception error)
        {
            if (now - _lastErrorLogMilliseconds < ErrorLogIntervalMilliseconds)
                return;
            _lastErrorLogMilliseconds = now;
            Exception actual = error is TargetInvocationException
                && error.InnerException != null
                    ? error.InnerException
                    : error;
            _log.LogWarning(
                "Background movement injection failed: "
                + actual.GetType().Name + ": " + actual.Message
            );
        }

        private static object CreateMoveVector(float x, float y, float z)
        {
            if (_moveConstructor != null)
                return _moveConstructor.Invoke(new object[] { x, y });
            object value = Activator.CreateInstance(_moveType);
            if (_moveXField != null && _moveYField != null)
            {
                _moveXField.SetValue(
                    value, ConvertMoveComponent(x, _moveXField.FieldType)
                );
                _moveYField.SetValue(
                    value, ConvertMoveComponent(y, _moveYField.FieldType)
                );
                if (_moveZField != null)
                {
                    _moveZField.SetValue(
                        value, ConvertMoveComponent(z, _moveZField.FieldType)
                    );
                }
            }
            else
            {
                _moveXProperty.SetValue(
                    value,
                    ConvertMoveComponent(x, _moveXProperty.PropertyType),
                    null
                );
                _moveYProperty.SetValue(
                    value,
                    ConvertMoveComponent(y, _moveYProperty.PropertyType),
                    null
                );
                if (_moveZProperty != null && _moveZProperty.CanWrite)
                {
                    _moveZProperty.SetValue(
                        value,
                        ConvertMoveComponent(z, _moveZProperty.PropertyType),
                        null
                    );
                }
            }
            return value;
        }

        private static object CreateScaledWorldVector(
            float x,
            float y,
            float z
        )
        {
            return CreateMoveVector(
                (float)Math.Round(x * 100f, MidpointRounding.AwayFromZero),
                (float)Math.Round(y * 100f, MidpointRounding.AwayFromZero),
                (float)Math.Round(z * 100f, MidpointRounding.AwayFromZero)
            );
        }

        private static object ConvertMoveComponent(float value, Type targetType)
        {
            return Convert.ChangeType(
                value, targetType, CultureInfo.InvariantCulture
            );
        }

        private static PropertyInfo FindProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo FindMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }
    }

    internal static class LootLifecyclePatch
    {
        internal static void OnEnablePostfix(object __instance)
        {
            PlayerUpdatePatch.TrackLoot(__instance);
        }

        internal static void RemovePrefix(object __instance)
        {
            PlayerUpdatePatch.ForgetLoot(__instance);
        }
    }

    // Captures the authoritative channel list the server pushes to the client.
    // UIServerDisplay.DrawChannels(int[] channels, int currentIndex, string
    // instanceId) fires whenever the channel list is (re)sent, including right
    // after a channel switch, so the last-seen values stay current without the
    // channel window being open. CurrentIndex/Count are list positions, the same
    // space UIServerDisplay.OnChannelSelected(int) expects.
    internal static class ChannelListPatch
    {
        internal static volatile bool Available;
        internal static int CurrentIndex = -1;
        internal static int Count;
        internal static string InstanceId = string.Empty;
        internal static object Instance;

        internal static void Postfix(
            object __instance, object __0, object __1, object __2
        )
        {
            try
            {
                Instance = __instance;
                Count = ReadArrayLength(__0);
                CurrentIndex = Convert.ToInt32(
                    __1, CultureInfo.InvariantCulture
                );
                InstanceId = __2 == null
                    ? string.Empty
                    : (Convert.ToString(__2, CultureInfo.InvariantCulture)
                        ?? string.Empty);
                Available = true;
            }
            catch
            {
                // Never let a capture failure break the game's UI callback.
            }
        }

        private static int ReadArrayLength(object array)
        {
            if (array == null)
                return 0;
            Type type = array.GetType();
            PropertyInfo length = type.GetProperty("Length");
            if (length == null)
                length = type.GetProperty("Count");
            if (length == null)
                return 0;
            return Convert.ToInt32(
                length.GetValue(array, null), CultureInfo.InvariantCulture
            );
        }
    }

    internal sealed class AuctionQueryRequest
    {
        internal long RequestId;
        internal long TimestampMilliseconds;
        internal string Query = string.Empty;
        internal string Cursor = string.Empty;
        internal int PageSize = 50;
        internal long? MinimumUnitPrice;
        internal long? MaximumUnitPrice;
        internal int? MinimumLevel;
        internal int? MaximumLevel;
        internal int? MinimumRefine;
        internal int? MaximumRefine;
        internal int? MinimumPotential;
        internal int? MaximumPotential;
        internal int? MinimumQuantity;
        internal bool? HasGem;
        internal bool? HasCard;
        internal string ItemType = string.Empty;
        internal string EquipType = string.Empty;
        internal string Archetype = string.Empty;
        internal string ItemCategory = string.Empty;
        internal readonly List<AuctionStatFilter> StatFilters =
            new List<AuctionStatFilter>();
    }

    internal sealed class AuctionStatFilter
    {
        internal string Type = string.Empty;
        internal int MinimumValue;
    }

    internal static class EquipmentDisplayStatService
    {
        private static Type _equipType;
        private static MethodInfo _formulaGetSubstats;
        private static MethodInfo _snapshotToInventoryItem;
        private static MethodInfo _tryCastEquip;
        private static MethodInfo _castEquip;
        private static PropertyInfo _statName;
        private static PropertyInfo _statType;
        private static PropertyInfo _statValue;
        private static PropertyInfo _scaledValue;
        private static PropertyInfo _scaledValueLevel;
        private static PropertyInfo _scaledValueString;
        private static PropertyInfo _scaledValueString2;

        internal static void Initialize(ManualLogSource log)
        {
            Type equipType = PlayerUpdatePatch.FindLoadedType("EquipData");
            _equipType = equipType;
            Type formulaType = PlayerUpdatePatch.FindLoadedType("Formula");
            Type snapshotType = PlayerUpdatePatch.FindLoadedType(
                "SpiritVale.Vending.Contracts.ItemSnapshot"
            );
            Type extensionsType = PlayerUpdatePatch.FindLoadedType(
                "_App.Scripts.Service.VendingUnityExtensions"
            );
            Type objectBaseType = PlayerUpdatePatch.FindLoadedType(
                "Il2CppInterop.Runtime.InteropTypes.Il2CppObjectBase"
            );
            Type statValueType = PlayerUpdatePatch.FindLoadedType("StatValue");
            Type scaledValueType = PlayerUpdatePatch.FindLoadedType("ScaledValue");

            _formulaGetSubstats = RequireMethod(
                formulaType, "GetSubstats", equipType, 1
            );
            _snapshotToInventoryItem = RequireMethod(
                extensionsType, "ToInventoryItemData", snapshotType, 1
            );
            _tryCastEquip = RequireGenericMethod(
                objectBaseType, "TryCast", 0
            ).MakeGenericMethod(equipType);
            _castEquip = RequireGenericMethod(
                objectBaseType, "Cast", 0
            ).MakeGenericMethod(equipType);
            _statName = RequireProperty(statValueType, "Name");
            _statType = RequireProperty(statValueType, "Type");
            _statValue = RequireProperty(statValueType, "Value");
            _scaledValue = RequireProperty(scaledValueType, "Value");
            _scaledValueLevel = RequireProperty(scaledValueType, "ValueLv");
            _scaledValueString = RequireProperty(scaledValueType, "ValueStr");
            _scaledValueString2 = RequireProperty(scaledValueType, "ValueStr2");
            log.LogInfo("Equipment display stat conversion initialized");
        }

        internal static void AppendForEquip(StringBuilder json, object equip)
        {
            AppendForEquip(json, equip, string.Empty);
        }

        private static void AppendForEquip(
            StringBuilder json, object equip, string conversionError
        )
        {
            json.Append(",\"display_substats\":");
            if (_formulaGetSubstats == null || equip == null)
            {
                json.Append("null");
                AuctionQueryService.AppendString(
                    json,
                    "display_substats_error",
                    conversionError.Length > 0
                        ? conversionError
                        : "EquipData is unavailable"
                );
                return;
            }
            try
            {
                object stats = _formulaGetSubstats.Invoke(
                    null, new object[] { equip }
                );
                AppendStats(json, stats);
            }
            catch (Exception error)
            {
                json.Append("null");
                AuctionQueryService.AppendString(
                    json,
                    "display_substats_error",
                    "Formula.GetSubstats failed: " + Describe(error)
                );
            }
        }

        internal static void AppendForSnapshot(
            StringBuilder json, object snapshot
        )
        {
            object item = null;
            string conversionError = string.Empty;
            try
            {
                item = _snapshotToInventoryItem.Invoke(
                    null, new object[] { snapshot }
                );
            }
            catch (Exception error)
            {
                conversionError = "snapshot conversion failed: " + Describe(error);
            }
            if (item != null)
            {
                object equip = ConvertEquip(item, out conversionError);
                AppendForEquip(json, equip, conversionError);
            }
            else
            {
                AppendForEquip(json, null, conversionError);
            }
        }

        private static object ConvertEquip(object item, out string error)
        {
            error = string.Empty;
            if (item == null)
            {
                error = "ItemData is null";
                return null;
            }
            if (_equipType != null && _equipType.IsInstanceOfType(item))
                return item;
            Exception tryCastError = null;
            try
            {
                object equip = _tryCastEquip.Invoke(item, null);
                if (equip != null)
                    return equip;
            }
            catch (Exception caught)
            {
                tryCastError = caught;
            }
            try
            {
                object equip = _castEquip.Invoke(item, null);
                if (equip != null)
                    return equip;
            }
            catch (Exception caught)
            {
                error = "Cast<EquipData> failed for "
                    + (item.GetType().FullName ?? item.GetType().Name)
                    + ": " + Describe(caught);
                if (tryCastError != null)
                    error += "; TryCast: " + Describe(tryCastError);
                return null;
            }
            error = "ItemData is not EquipData: "
                + (item.GetType().FullName ?? item.GetType().Name);
            return null;
        }

        private static string Describe(Exception error)
        {
            TargetInvocationException invocation =
                error as TargetInvocationException;
            Exception actual = invocation != null
                && invocation.InnerException != null
                    ? invocation.InnerException
                    : error;
            return actual.GetType().Name + ": " + actual.Message;
        }

        private static void AppendStats(StringBuilder json, object stats)
        {
            json.Append('[');
            int count = CollectionCount(stats);
            for (int index = 0; index < count; index++)
            {
                if (index > 0)
                    json.Append(',');
                object stat = CollectionItem(stats, index);
                object type = _statType.GetValue(stat, null);
                object scaled = _statValue.GetValue(stat, null);
                json.Append('{');
                AuctionQueryService.AppendString(
                    json, "name", ReadString(_statName, stat), false
                );
                AuctionQueryService.AppendString(
                    json,
                    "type",
                    Convert.ToString(type, CultureInfo.InvariantCulture)
                );
                AuctionQueryService.AppendNumber(
                    json,
                    "type_value",
                    Convert.ToInt64(type, CultureInfo.InvariantCulture)
                );
                AuctionQueryService.AppendString(
                    json, "value", ReadFloatString(_scaledValue, scaled)
                );
                AuctionQueryService.AppendString(
                    json,
                    "value_lv",
                    ReadFloatString(_scaledValueLevel, scaled)
                );
                AuctionQueryService.AppendString(
                    json, "value_str", ReadString(_scaledValueString, scaled)
                );
                AuctionQueryService.AppendString(
                    json, "value_str2", ReadString(_scaledValueString2, scaled)
                );
                json.Append('}');
            }
            json.Append(']');
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            PropertyInfo count = RequireProperty(collection.GetType(), "Count");
            return Convert.ToInt32(
                count.GetValue(collection, null), CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = RequireProperty(collection.GetType(), "Item");
            return item.GetValue(collection, new object[] { index });
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            if (instance == null)
                return string.Empty;
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static string ReadFloatString(
            PropertyInfo property, object instance
        )
        {
            if (instance == null)
                return "0";
            float value = Convert.ToSingle(
                property.GetValue(instance, null), CultureInfo.InvariantCulture
            );
            return value.ToString("R", CultureInfo.InvariantCulture);
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name
                    && parameters.Length == parameterCount
                    && parameters[0].ParameterType == firstParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireGenericMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
                if (methods[index].Name == name
                    && methods[index].IsGenericMethodDefinition
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            throw new MissingMethodException(type.FullName, name);
        }
    }

    internal static class AuctionQueryService
    {
        private const long RequestMaxAgeMilliseconds = 30000;
        private const long RequestTimeoutMilliseconds = 20000;
        private const int FileOperationAttempts = 5;

        private static ManualLogSource _log;
        private static Type _searchRequestType;
        private static Type _searchPageType;
        private static MethodInfo _requestVendorItems;
        private static PropertyInfo _pageItems;
        private static PropertyInfo _pageNextCursor;
        private static PropertyInfo _pageHasMore;
        private static PropertyInfo _pageSuccess;
        private static PropertyInfo _pageCode;
        private static PropertyInfo _pageMessage;
        private static long _lastSeenRequestId;
        private static long _activeRequestId;
        private static long _activeStartedElapsed;
        private static AuctionQueryRequest _activeRequest;
        private static object _activeIl2CppCallback;
        private static Delegate _activeManagedCallback;

        internal static bool IsBusy
        {
            get { return _activeRequestId != 0; }
        }

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            _searchRequestType = PlayerUpdatePatch.FindLoadedType(
                "SpiritVale.Vending.Contracts.SearchRequest"
            );
            _searchPageType = PlayerUpdatePatch.FindLoadedType(
                "VendingManager+VendingSearchPage"
            );
            _requestVendorItems = RequireMethod(
                playerType, "RequestVendorItemList", _searchRequestType, 2
            );
            _pageItems = RequireProperty(_searchPageType, "Items");
            _pageNextCursor = RequireProperty(_searchPageType, "NextCursor");
            _pageHasMore = RequireProperty(_searchPageType, "HasMore");
            _pageSuccess = RequireProperty(_searchPageType, "Success");
            _pageCode = RequireProperty(_searchPageType, "Code");
            _pageMessage = RequireProperty(_searchPageType, "Message");
            log.LogInfo("Auction query IPC initialized (read-only search)");
        }

        internal static void Tick(object player, long elapsedMilliseconds)
        {
            if (_requestVendorItems == null || player == null)
                return;

            if (_activeRequestId != 0)
            {
                if (elapsedMilliseconds - _activeStartedElapsed
                    > RequestTimeoutMilliseconds)
                {
                    AuctionQueryRequest timedOut = _activeRequest;
                    ClearActive();
                    WriteFailure(timedOut, "timeout", "Auction search timed out");
                }
                return;
            }

            if (CardPurchaseService.IsBusy)
                return;

            AuctionQueryRequest request = ReadRequest();
            if (request == null || request.RequestId == _lastSeenRequestId)
                return;

            _lastSeenRequestId = request.RequestId;
            _activeRequestId = request.RequestId;
            _activeStartedElapsed = elapsedMilliseconds;
            _activeRequest = request;
            try
            {
                object search = BuildSearchRequest(request);
                Action<object> handler = delegate(object page)
                {
                    Complete(request.RequestId, page);
                };
                _activeIl2CppCallback = CreateIl2CppCallback(handler);
                WritePending(request);
                _requestVendorItems.Invoke(
                    player, new object[] { search, _activeIl2CppCallback }
                );
                _log.LogInfo(
                    "Auction search requested id=" + request.RequestId
                    + " query=" + request.Query
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                ClearActive();
                WriteFailure(
                    request,
                    "error",
                    actual.GetType().Name + ": " + actual.Message
                );
                _log.LogWarning(
                    "Auction search request failed: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
        }

        private static void Complete(long requestId, object page)
        {
            if (_activeRequestId != requestId || _activeRequest == null)
                return;
            AuctionQueryRequest request = _activeRequest;
            try
            {
                WriteSuccess(request, page);
                _log.LogInfo("Auction search completed id=" + requestId);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                WriteFailure(
                    request,
                    "error",
                    actual.GetType().Name + ": " + actual.Message
                );
                _log.LogWarning(
                    "Auction result serialization failed: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            finally
            {
                ClearActive();
            }
        }

        private static void ClearActive()
        {
            _activeRequestId = 0;
            _activeStartedElapsed = 0;
            _activeRequest = null;
            _activeIl2CppCallback = null;
            _activeManagedCallback = null;
        }

        private static object BuildSearchRequest(AuctionQueryRequest request)
        {
            object search = Activator.CreateInstance(_searchRequestType);
            SetProperty(search, "Query", request.Query);
            SetProperty(search, "PageSize", request.PageSize);
            SetProperty(search, "Cursor", request.Cursor);
            SetNullable(search, "MinimumUnitPrice", request.MinimumUnitPrice);
            SetNullable(search, "MaximumUnitPrice", request.MaximumUnitPrice);
            SetNullable(search, "MinimumLevel", request.MinimumLevel);
            SetNullable(search, "MaximumLevel", request.MaximumLevel);
            SetNullable(search, "MinimumRefine", request.MinimumRefine);
            SetNullable(search, "MaximumRefine", request.MaximumRefine);
            SetNullable(search, "MinimumPotential", request.MinimumPotential);
            SetNullable(search, "MaximumPotential", request.MaximumPotential);
            SetNullable(search, "MinimumQuantity", request.MinimumQuantity);
            SetNullable(search, "HasGem", request.HasGem);
            SetNullable(search, "HasCard", request.HasCard);
            SetProperty(search, "EquipType", request.EquipType);
            SetProperty(search, "Archetype", request.Archetype);
            SetProperty(search, "ItemCategory", request.ItemCategory);
            if (!string.IsNullOrWhiteSpace(request.ItemType))
                SetNullableEnum(search, "ItemType", request.ItemType);
            SetStatFilters(search, request.StatFilters);
            return search;
        }

        private static void SetStatFilters(
            object search, List<AuctionStatFilter> filters
        )
        {
            if (filters == null || filters.Count == 0)
                return;
            PropertyInfo property = RequireProperty(
                search.GetType(), "StatFilters"
            );
            object list = property.GetValue(search, null);
            if (list == null)
                list = Activator.CreateInstance(property.PropertyType);
            Type filterType = property.PropertyType.GetGenericArguments()[0];
            MethodInfo add = list.GetType().GetMethod(
                "Add", new Type[] { filterType }
            );
            if (add == null)
                throw new MissingMethodException(list.GetType().FullName, "Add");
            for (int index = 0; index < filters.Count; index++)
            {
                object filter = Activator.CreateInstance(filterType);
                SetProperty(filter, "Type", filters[index].Type);
                SetProperty(filter, "MinimumValue", filters[index].MinimumValue);
                add.Invoke(list, new object[] { filter });
            }
            property.SetValue(search, list, null);

            PropertyInfo matchMode = RequireProperty(
                search.GetType(), "StatMatchMode"
            );
            matchMode.SetValue(
                search, Enum.Parse(matchMode.PropertyType, "All", true), null
            );
        }

        private static void SetProperty(object instance, string name, object value)
        {
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            property.SetValue(instance, value, null);
        }

        private static void SetNullable(
            object instance, string name, object nullableValue
        )
        {
            if (nullableValue == null)
                return;
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            PropertyInfo hasValue = nullableValue.GetType().GetProperty("HasValue");
            if (hasValue != null && !Convert.ToBoolean(
                hasValue.GetValue(nullableValue, null), CultureInfo.InvariantCulture
            ))
                return;
            PropertyInfo valueProperty = nullableValue.GetType().GetProperty("Value");
            object value = valueProperty == null
                ? nullableValue : valueProperty.GetValue(nullableValue, null);
            object boxed = Activator.CreateInstance(
                property.PropertyType, new object[] { value }
            );
            property.SetValue(instance, boxed, null);
        }

        private static void SetNullableEnum(
            object instance, string name, string enumName
        )
        {
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            Type enumType = property.PropertyType.GetGenericArguments()[0];
            object value = Enum.Parse(enumType, enumName, true);
            object boxed = Activator.CreateInstance(
                property.PropertyType, new object[] { value }
            );
            property.SetValue(instance, boxed, null);
        }

        private static object CreateIl2CppCallback(Action<object> handler)
        {
            MethodInfo helper = typeof(AuctionQueryService).GetMethod(
                "CreateManagedAction",
                BindingFlags.NonPublic | BindingFlags.Static
            ).MakeGenericMethod(_searchPageType);
            _activeManagedCallback = (Delegate)helper.Invoke(
                null, new object[] { handler }
            );
            Type callbackType = _requestVendorItems.GetParameters()[1].ParameterType;
            MethodInfo conversion = callbackType.GetMethod(
                "op_Implicit",
                BindingFlags.Public | BindingFlags.Static
            );
            if (conversion == null)
                throw new MissingMethodException(callbackType.FullName, "op_Implicit");
            return conversion.Invoke(null, new object[] { _activeManagedCallback });
        }

        private static Action<T> CreateManagedAction<T>(Action<object> handler)
        {
            return delegate(T value) { handler(value); };
        }

        private static AuctionQueryRequest ReadRequest()
        {
            try
            {
                if (!File.Exists(Plugin.AuctionRequestPath))
                    return null;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.AuctionRequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                    json = reader.ReadToEnd();

                long requestId;
                long timestamp;
                if (!TryReadLong(json, "request_id", out requestId)
                    || !TryReadLong(json, "timestamp_ms", out timestamp)
                    || requestId <= 0)
                    return null;
                long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                if (Math.Abs(now - timestamp) > RequestMaxAgeMilliseconds)
                    return null;

                AuctionQueryRequest request = new AuctionQueryRequest();
                request.RequestId = requestId;
                request.TimestampMilliseconds = timestamp;
                request.Query = ReadString(json, "query", string.Empty);
                request.Cursor = ReadString(json, "cursor", string.Empty);
                request.PageSize = Math.Max(
                    1, Math.Min(100, ReadInt(json, "page_size", 50))
                );
                request.MinimumUnitPrice = ReadNullableLong(
                    json, "minimum_unit_price"
                );
                request.MaximumUnitPrice = ReadNullableLong(
                    json, "maximum_unit_price"
                );
                request.MinimumLevel = ReadNullableInt(json, "minimum_level");
                request.MaximumLevel = ReadNullableInt(json, "maximum_level");
                request.MinimumRefine = ReadNullableInt(json, "minimum_refine");
                request.MaximumRefine = ReadNullableInt(json, "maximum_refine");
                request.MinimumPotential = ReadNullableInt(
                    json, "minimum_potential"
                );
                request.MaximumPotential = ReadNullableInt(
                    json, "maximum_potential"
                );
                request.MinimumQuantity = ReadNullableInt(
                    json, "minimum_quantity"
                );
                request.HasGem = ReadNullableBool(json, "has_gem");
                request.HasCard = ReadNullableBool(json, "has_card");
                request.ItemType = ReadString(json, "item_type", string.Empty);
                request.EquipType = ReadString(json, "equip_type", string.Empty);
                request.Archetype = ReadString(json, "archetype", string.Empty);
                request.ItemCategory = ReadString(
                    json, "item_category", string.Empty
                );
                request.StatFilters.AddRange(ReadStatFilters(json));
                return request;
            }
            catch
            {
                return null;
            }
        }

        private static void WritePending(AuctionQueryRequest request)
        {
            StringBuilder json = BeginResult(request, "pending");
            json.Append(",\"items\":[]}");
            AtomicWrite(Plugin.AuctionResultPath, json.ToString());
        }

        private static void WriteFailure(
            AuctionQueryRequest request, string status, string message
        )
        {
            if (request == null)
                return;
            StringBuilder json = BeginResult(request, status);
            AppendString(json, "message", message);
            json.Append(",\"items\":[]}");
            AtomicWrite(Plugin.AuctionResultPath, json.ToString());
        }

        private static void WriteSuccess(
            AuctionQueryRequest request, object page
        )
        {
            if (page == null)
                throw new InvalidOperationException("Auction result page was null");
            StringBuilder json = BeginResult(request, "ok");
            AppendBoolean(json, "success", ReadBoolean(_pageSuccess, page));
            AppendString(json, "code", ReadString(_pageCode, page));
            AppendString(json, "message", ReadString(_pageMessage, page));
            AppendString(json, "next_cursor", ReadString(_pageNextCursor, page));
            AppendBoolean(json, "has_more", ReadBoolean(_pageHasMore, page));
            json.Append(",\"items\":[");
            object items = _pageItems.GetValue(page, null);
            int count = CollectionCount(items);
            for (int index = 0; index < count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendItem(json, CollectionItem(items, index));
            }
            json.Append("]}");
            AtomicWrite(Plugin.AuctionResultPath, json.ToString());
        }

        private static StringBuilder BeginResult(
            AuctionQueryRequest request, string status
        )
        {
            StringBuilder json = new StringBuilder(4096);
            json.Append('{');
            AppendNumber(json, "schema_version", 1, false);
            AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AppendNumber(json, "request_id", request.RequestId);
            AppendString(json, "status", status);
            AppendString(json, "query", request.Query);
            AppendNumber(json, "page_size", request.PageSize);
            AppendString(json, "cursor", request.Cursor);
            AppendStatFilters(json, request.StatFilters);
            return json;
        }

        private static void AppendStatFilters(
            StringBuilder json, List<AuctionStatFilter> filters
        )
        {
            json.Append(",\"stat_match_mode\":\"All\",\"stat_filters\":[");
            if (filters != null)
            {
                for (int index = 0; index < filters.Count; index++)
                {
                    if (index > 0)
                        json.Append(',');
                    json.Append('{');
                    AppendString(json, "type", filters[index].Type, false);
                    AppendNumber(
                        json, "minimum_value", filters[index].MinimumValue
                    );
                    json.Append('}');
                }
            }
            json.Append(']');
        }

        private static void AppendItem(StringBuilder json, object itemData)
        {
            json.Append('{');
            if (itemData == null)
            {
                AppendString(json, "item_display_name", string.Empty, false);
                json.Append('}');
                return;
            }
            Type itemDataType = itemData.GetType();
            AppendString(
                json, "seller_id", ReadMemberString(itemDataType, itemData, "SellerId"), false
            );
            AppendString(
                json, "seller_name", ReadMemberString(itemDataType, itemData, "SellerName")
            );
            object listing = ReadMember(itemDataType, itemData, "Listing");
            if (listing != null)
                AppendListing(json, listing);
            json.Append('}');
        }

        private static void AppendListing(StringBuilder json, object listing)
        {
            Type type = listing.GetType();
            AppendString(json, "listing_id", ReadMemberString(type, listing, "ListingId"));
            AppendString(
                json, "item_display_name",
                ReadMemberString(type, listing, "ItemDisplayName")
            );
            AppendNumber(json, "unit_price", ReadMemberLong(type, listing, "UnitPrice"));
            AppendNumber(
                json, "available_quantity",
                ReadMemberLong(type, listing, "AvailableQuantity")
            );
            AppendNumber(
                json, "initial_quantity",
                ReadMemberLong(type, listing, "InitialQuantity")
            );
            AppendNumber(
                json, "sold_quantity", ReadMemberLong(type, listing, "SoldQuantity")
            );
            AppendString(json, "listing_status", ReadMemberString(type, listing, "Status"));
            object snapshot = ReadMember(type, listing, "Item");
            if (snapshot != null)
                AppendItemSnapshot(json, snapshot);
        }

        private static void AppendItemSnapshot(StringBuilder json, object snapshot)
        {
            Type type = snapshot.GetType();
            AppendString(json, "item_id", ReadMemberString(type, snapshot, "ItemId"));
            AppendString(
                json, "instance_id", ReadMemberString(type, snapshot, "InstanceId")
            );
            AppendString(json, "item_type", ReadMemberString(type, snapshot, "Type"));
            AppendNumber(json, "quantity", ReadMemberLong(type, snapshot, "Quantity"));
            AppendString(
                json, "payload_json", ReadMemberString(type, snapshot, "PayloadJson")
            );
            AppendNumber(
                json, "payload_schema_version",
                ReadMemberLong(type, snapshot, "PayloadSchemaVersion")
            );
            AppendString(
                json, "compatibility_fingerprint",
                ReadMemberString(type, snapshot, "CompatibilityFingerprint")
            );
            EquipmentDisplayStatService.AppendForSnapshot(json, snapshot);
        }

        private static object ReadMember(Type type, object instance, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.FlattenHierarchy
            );
            return property == null ? null : property.GetValue(instance, null);
        }

        private static string ReadMemberString(
            Type type, object instance, string name
        )
        {
            object value = ReadMember(type, instance, name);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static long ReadMemberLong(Type type, object instance, string name)
        {
            object value = ReadMember(type, instance, name);
            return value == null ? 0L
                : Convert.ToInt64(value, CultureInfo.InvariantCulture);
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBoolean(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            PropertyInfo count = collection.GetType().GetProperty("Count");
            return count == null ? 0 : Convert.ToInt32(
                count.GetValue(collection, null), CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = collection.GetType().GetProperty("Item");
            if (item == null)
                throw new MissingMemberException(collection.GetType().FullName, "Item");
            return item.GetValue(collection, new object[] { index });
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name
                    && parameters.Length == parameterCount
                    && parameters[0].ParameterType == firstParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException : error;
        }

        private static bool TryReadLong(string json, string name, out long value)
        {
            value = 0;
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name) + "\\\"\\s*:\\s*(-?[0-9]+)"
            );
            return match.Success && long.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            );
        }

        private static int ReadInt(
            string json, string name, int fallback
        )
        {
            long value;
            return TryReadLong(json, name, out value)
                && value >= int.MinValue && value <= int.MaxValue
                ? (int)value : fallback;
        }

        private static int? ReadNullableInt(string json, string name)
        {
            long value;
            return TryReadLong(json, name, out value)
                && value >= int.MinValue && value <= int.MaxValue
                ? (int?)value : null;
        }

        private static long? ReadNullableLong(string json, string name)
        {
            long value;
            return TryReadLong(json, name, out value) ? (long?)value : null;
        }

        private static bool? ReadNullableBool(string json, string name)
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*(true|false)",
                RegexOptions.IgnoreCase
            );
            return match.Success ? (bool?)string.Equals(
                match.Groups[1].Value, "true", StringComparison.OrdinalIgnoreCase
            ) : null;
        }

        private static List<AuctionStatFilter> ReadStatFilters(string json)
        {
            List<AuctionStatFilter> filters = new List<AuctionStatFilter>();
            Match array = Regex.Match(
                json,
                "\\\"stat_filters\\\"\\s*:\\s*\\[(.*?)\\]",
                RegexOptions.Singleline
            );
            if (!array.Success)
                return filters;
            MatchCollection entries = Regex.Matches(
                array.Groups[1].Value,
                "\\{\\s*\\\"type\\\"\\s*:\\s*\\\""
                    + "([A-Za-z][A-Za-z0-9_]*)\\\"\\s*,\\s*"
                    + "\\\"minimum_value\\\"\\s*:\\s*(-?[0-9]+)\\s*\\}"
            );
            for (int index = 0; index < entries.Count && index < 6; index++)
            {
                int minimum;
                if (!int.TryParse(
                    entries[index].Groups[2].Value,
                    NumberStyles.Integer,
                    CultureInfo.InvariantCulture,
                    out minimum
                ))
                    continue;
                AuctionStatFilter filter = new AuctionStatFilter();
                filter.Type = entries[index].Groups[1].Value;
                filter.MinimumValue = minimum;
                filters.Add(filter);
            }
            return filters;
        }

        private static string ReadString(
            string json, string name, string fallback
        )
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\""
            );
            return match.Success ? UnescapeJson(match.Groups[1].Value) : fallback;
        }

        private static string UnescapeJson(string value)
        {
            StringBuilder result = new StringBuilder(value.Length);
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                if (character != '\\' || index + 1 >= value.Length)
                {
                    result.Append(character);
                    continue;
                }
                char escaped = value[++index];
                switch (escaped)
                {
                    case '\\': result.Append('\\'); break;
                    case '"': result.Append('"'); break;
                    case 'n': result.Append('\n'); break;
                    case 'r': result.Append('\r'); break;
                    case 't': result.Append('\t'); break;
                    case 'u':
                        if (index + 4 < value.Length)
                        {
                            int code;
                            if (int.TryParse(
                                value.Substring(index + 1, 4),
                                NumberStyles.HexNumber,
                                CultureInfo.InvariantCulture,
                                out code
                            ))
                            {
                                result.Append((char)code);
                                index += 4;
                                break;
                            }
                        }
                        result.Append('u');
                        break;
                    default: result.Append(escaped); break;
                }
            }
            return result.ToString();
        }

        internal static void AtomicWrite(string path, string contents)
        {
            string temporary = path + ".tmp";
            Exception lastError = null;
            for (int attempt = 0; attempt < FileOperationAttempts; attempt++)
            {
                try
                {
                    File.WriteAllText(temporary, contents, new UTF8Encoding(false));
                    if (File.Exists(path))
                        File.Replace(temporary, path, null);
                    else
                        File.Move(temporary, path);
                    return;
                }
                catch (IOException error) { lastError = error; }
                catch (UnauthorizedAccessException error) { lastError = error; }
                if (attempt + 1 < FileOperationAttempts)
                    Thread.Sleep(2 << attempt);
            }
            throw lastError;
        }

        internal static void AppendNumber(
            StringBuilder json, string name, long value, bool comma = true
        )
        {
            if (comma) json.Append(',');
            AppendName(json, name);
            json.Append(value.ToString(CultureInfo.InvariantCulture));
        }

        internal static void AppendBoolean(
            StringBuilder json, string name, bool value
        )
        {
            json.Append(',');
            AppendName(json, name);
            json.Append(value ? "true" : "false");
        }

        internal static void AppendString(
            StringBuilder json, string name, string value, bool comma = true
        )
        {
            if (comma) json.Append(',');
            AppendName(json, name);
            json.Append('"');
            json.Append(EscapeJson(value ?? string.Empty));
            json.Append('"');
        }

        private static void AppendName(StringBuilder json, string name)
        {
            json.Append('"');
            json.Append(name);
            json.Append("\":");
        }

        private static string EscapeJson(string value)
        {
            StringBuilder escaped = new StringBuilder(value.Length + 8);
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                switch (character)
                {
                    case '\\': escaped.Append("\\\\"); break;
                    case '"': escaped.Append("\\\""); break;
                    case '\n': escaped.Append("\\n"); break;
                    case '\r': escaped.Append("\\r"); break;
                    case '\t': escaped.Append("\\t"); break;
                    default:
                        if (character < 32)
                            escaped.Append(
                                "\\u" + ((int)character).ToString("x4")
                            );
                        else
                            escaped.Append(character);
                        break;
                }
            }
            return escaped.ToString();
        }

    }

    internal sealed class CardPurchaseRequest
    {
        internal long RequestId;
        internal long TimestampMilliseconds;
        internal long ReserveCoins;
        internal long UnitPriceLimitExclusive;
        internal long BalanceBefore;
        internal bool BalanceKnown;
        internal bool Confirmed;
    }

    internal sealed class CardPurchaseCandidate
    {
        internal object Listing;
        internal string ListingId = string.Empty;
        internal string ItemDisplayName = string.Empty;
        internal long UnitPrice;
        internal long ListingVersion;
        internal int AvailableQuantity;
        internal int PurchaseQuantity;
        internal long BalanceBefore;
    }

    internal static class CardPurchaseService
    {
        private const long RequestMaxAgeMilliseconds = 30000;
        private const long SearchTimeoutMilliseconds = 20000;
        private const long PurchaseTimeoutMilliseconds = 45000;

        private static ManualLogSource _log;
        private static Type _searchRequestType;
        private static Type _searchPageType;
        private static MethodInfo _requestVendorItems;
        private static PropertyInfo _pageItems;
        private static PropertyInfo _pageSuccess;
        private static PropertyInfo _pageCode;
        private static PropertyInfo _pageMessage;
        private static PropertyInfo _playerSave;
        private static PropertyInfo _savePlayerData;
        private static PropertyInfo _playerDataCoins;
        private static MethodInfo _saveVendingPurchase;
        private static MethodInfo _saveVendingPurchaseResult;
        private static long _lastSeenRequestId;
        private static long _activeRequestId;
        private static long _activeStartedElapsed;
        private static long _purchaseStartedElapsed;
        private static CardPurchaseRequest _activeRequest;
        private static CardPurchaseCandidate _activeCandidate;
        private static object _activePlayer;
        private static object _activeIl2CppCallback;
        private static Delegate _activeManagedCallback;
        private static bool _reportedResultAvailable;
        private static bool _reportedSuccess;
        private static string _reportedMessage = string.Empty;
        private static string _reportedReason = string.Empty;

        internal static bool IsBusy
        {
            get { return _activeRequestId != 0; }
        }

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            _searchRequestType = PlayerUpdatePatch.FindLoadedType(
                "SpiritVale.Vending.Contracts.SearchRequest"
            );
            _searchPageType = PlayerUpdatePatch.FindLoadedType(
                "VendingManager+VendingSearchPage"
            );
            _requestVendorItems = RequireMethod(
                playerType, "RequestVendorItemList", _searchRequestType, 2
            );
            _pageItems = RequireProperty(_searchPageType, "Items");
            _pageSuccess = RequireProperty(_searchPageType, "Success");
            _pageCode = RequireProperty(_searchPageType, "Code");
            _pageMessage = RequireProperty(_searchPageType, "Message");
            _playerSave = RequireProperty(playerType, "Save");
            _savePlayerData = RequireProperty(
                _playerSave.PropertyType, "PlayerData"
            );
            _playerDataCoins = RequireProperty(
                _savePlayerData.PropertyType, "Coins"
            );
            _saveVendingPurchase = RequireMethod(
                _playerSave.PropertyType, "VendingPurchase", 5
            );
            _saveVendingPurchaseResult = RequireMethod(
                _playerSave.PropertyType, "VendingPurchaseResult_T", 4
            );
            new Harmony(
                "local.spiritvale.positionprobe.cardpurchaseresult"
            ).Patch(
                _saveVendingPurchaseResult,
                new HarmonyMethod(AccessTools.Method(
                    typeof(CardPurchaseService),
                    "VendingPurchaseResultPrefix"
                )),
                null,
                null,
                null,
                null
            );
            log.LogInfo(
                "Card bulk-purchase IPC initialized "
                + "(PlayerSave.VendingPurchase; one listing per request)"
            );
        }

        internal static void Tick(object player, long elapsedMilliseconds)
        {
            if (_requestVendorItems == null || player == null)
                return;

            if (_activeRequestId != 0)
            {
                if (_purchaseStartedElapsed != 0)
                {
                    if (ElapsedMilliseconds(_purchaseStartedElapsed)
                        > PurchaseTimeoutMilliseconds)
                    {
                        CardPurchaseRequest timedOut = _activeRequest;
                        CardPurchaseCandidate candidate = _activeCandidate;
                        ClearActive();
                        WriteTerminal(
                            timedOut,
                            candidate,
                            "unknown",
                            false,
                            "Timeout",
                            string.Empty,
                            "遊戲購買回呼逾時；交易結果不明，BOT 不會自動重試。",
                            true,
                            null
                        );
                    }
                    return;
                }
                if (elapsedMilliseconds - _activeStartedElapsed
                    > SearchTimeoutMilliseconds)
                {
                    CardPurchaseRequest timedOut = _activeRequest;
                    ClearActive();
                    WriteTerminal(
                        timedOut,
                        null,
                        "timeout",
                        false,
                        string.Empty,
                        string.Empty,
                        "Card 拍賣搜尋逾時。",
                        false,
                        null
                    );
                }
                return;
            }

            if (AuctionQueryService.IsBusy)
                return;
            CardPurchaseRequest request = ReadRequest();
            if (request == null || request.RequestId == _lastSeenRequestId)
                return;
            _lastSeenRequestId = request.RequestId;
            if (!request.Confirmed
                || request.ReserveCoins < 0
                || request.UnitPriceLimitExclusive <= 0)
            {
                WriteTerminal(
                    request,
                    null,
                    "error",
                    false,
                    "InvalidRequest",
                    string.Empty,
                    "保留金額不得為負數，且單卡價格上限必須大於 0。",
                    false,
                    null
                );
                return;
            }

            try
            {
                long currentBalance = ReadCurrentCoins(player);
                request.BalanceBefore = currentBalance;
                request.BalanceKnown = true;
                if (currentBalance <= request.ReserveCoins)
                {
                    WriteTerminal(
                        request,
                        null,
                        currentBalance < request.ReserveCoins
                            ? "error" : "budget_exhausted",
                        false,
                        currentBalance < request.ReserveCoins
                            ? "ReserveExceedsBalance" : "ReserveReached",
                        string.Empty,
                        currentBalance < request.ReserveCoins
                            ? "目前餘額低於要求保留的金額，未送出購買。"
                            : "目前餘額已達保留金額，未送出購買。",
                        false,
                        currentBalance
                    );
                    return;
                }
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                WriteTerminal(
                    request,
                    null,
                    "error",
                    false,
                    "BalanceUnavailable",
                    string.Empty,
                    actual.GetType().Name + ": " + actual.Message,
                    false,
                    null
                );
                return;
            }

            _activeRequestId = request.RequestId;
            _activeStartedElapsed = elapsedMilliseconds;
            _activeRequest = request;
            _activePlayer = player;
            try
            {
                object search = BuildSearchRequest(request);
                Action<object> handler = delegate(object page)
                {
                    CompleteSearch(request.RequestId, page);
                };
                _activeIl2CppCallback = CreateIl2CppCallback(handler);
                WriteProgress(request, null, "searching");
                _requestVendorItems.Invoke(
                    player, new object[] { search, _activeIl2CppCallback }
                );
                _log.LogInfo(
                    "Card purchase search requested id=" + request.RequestId
                    + " reserve=" + request.ReserveCoins
                    + " unit_price_limit_exclusive="
                    + request.UnitPriceLimitExclusive
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                ClearActive();
                WriteTerminal(
                    request,
                    null,
                    "error",
                    false,
                    "SearchFailed",
                    string.Empty,
                    actual.GetType().Name + ": " + actual.Message,
                    false,
                    null
                );
            }
        }

        private static object BuildSearchRequest(CardPurchaseRequest request)
        {
            object search = Activator.CreateInstance(_searchRequestType);
            SetProperty(search, "Query", "Card");
            SetProperty(search, "PageSize", 100);
            SetProperty(search, "Cursor", string.Empty);
            SetNullable(
                search,
                "MaximumUnitPrice",
                request.UnitPriceLimitExclusive - 1
            );
            SetNullableEnum(search, "ItemType", "Card");
            SetNullable(search, "MinimumQuantity", 1);
            return search;
        }

        private static void CompleteSearch(long requestId, object page)
        {
            if (_activeRequestId != requestId || _activeRequest == null)
                return;
            CardPurchaseRequest request = _activeRequest;
            try
            {
                if (page == null)
                    throw new InvalidOperationException(
                        "Card auction result page was null"
                    );
                bool success = ReadBoolean(_pageSuccess, page);
                string code = ReadString(_pageCode, page);
                string message = ReadString(_pageMessage, page);
                if (!success)
                {
                    ClearActive();
                    WriteTerminal(
                        request,
                        null,
                        "error",
                        false,
                        code,
                        string.Empty,
                        message.Length > 0 ? message : "Card 拍賣搜尋失敗。",
                        false,
                        null
                    );
                    return;
                }

                long currentBalance = ReadCurrentCoins(_activePlayer);
                request.BalanceBefore = currentBalance;
                request.BalanceKnown = true;
                if (currentBalance <= request.ReserveCoins)
                {
                    ClearActive();
                    WriteTerminal(
                        request,
                        null,
                        currentBalance < request.ReserveCoins
                            ? "error" : "budget_exhausted",
                        false,
                        currentBalance < request.ReserveCoins
                            ? "ReserveExceedsBalance" : "ReserveReached",
                        string.Empty,
                        currentBalance < request.ReserveCoins
                            ? "目前餘額低於要求保留的金額，未送出購買。"
                            : "目前餘額已達保留金額，未送出購買。",
                        false,
                        currentBalance
                    );
                    return;
                }

                CardPurchaseCandidate candidate = SelectCandidate(
                    page, request, currentBalance
                );
                if (candidate == null)
                {
                    ClearActive();
                    WriteTerminal(
                        request,
                        null,
                        "no_match",
                        false,
                        code,
                        string.Empty,
                        "目前沒有單價嚴格小於 "
                            + request.UnitPriceLimitExclusive
                            + " 且可負擔的 Card。",
                        false,
                        null
                    );
                    return;
                }
                _activeCandidate = candidate;
                StartPurchase(request, candidate);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                ClearActive();
                WriteTerminal(
                    request,
                    null,
                    "error",
                    false,
                    "PurchaseStartFailed",
                    string.Empty,
                    actual.GetType().Name + ": " + actual.Message,
                    false,
                    null
                );
            }
        }

        private static CardPurchaseCandidate SelectCandidate(
            object page, CardPurchaseRequest request, long currentBalance
        )
        {
            object items = _pageItems.GetValue(page, null);
            CardPurchaseCandidate selected = null;
            int count = CollectionCount(items);
            for (int index = 0; index < count; index++)
            {
                object itemData = CollectionItem(items, index);
                object listing = ReadMember(itemData, "Listing");
                if (listing == null)
                    continue;
                object snapshot = ReadMember(listing, "Item");
                string itemType = ReadMemberString(snapshot, "Type");
                string status = ReadMemberString(listing, "Status");
                string listingId = ReadMemberString(listing, "ListingId");
                long unitPrice = ReadMemberLong(listing, "UnitPrice");
                int available = ReadMemberInt(listing, "AvailableQuantity");
                if (!string.Equals(itemType, "Card", StringComparison.OrdinalIgnoreCase)
                    || !string.Equals(status, "Active", StringComparison.OrdinalIgnoreCase)
                    || string.IsNullOrWhiteSpace(listingId)
                    || unitPrice <= 0
                    || unitPrice >= request.UnitPriceLimitExclusive
                    || available < 1)
                    continue;
                long affordable = (currentBalance - request.ReserveCoins)
                    / unitPrice;
                if (affordable <= 0)
                    continue;
                if (selected != null
                    && (unitPrice > selected.UnitPrice
                        || (unitPrice == selected.UnitPrice
                            && string.CompareOrdinal(
                                listingId, selected.ListingId
                            ) >= 0)))
                    continue;
                selected = new CardPurchaseCandidate();
                selected.Listing = listing;
                selected.ListingId = listingId;
                selected.ItemDisplayName = ReadMemberString(
                    listing, "ItemDisplayName"
                );
                selected.UnitPrice = unitPrice;
                selected.ListingVersion = ReadMemberLong(listing, "Version");
                selected.AvailableQuantity = available;
                selected.PurchaseQuantity = (int)Math.Min(
                    (long)available, affordable
                );
                selected.BalanceBefore = currentBalance;
            }
            return selected;
        }

        private static void StartPurchase(
            CardPurchaseRequest request, CardPurchaseCandidate candidate
        )
        {
            long currentBalance = ReadCurrentCoins(_activePlayer);
            request.BalanceBefore = currentBalance;
            request.BalanceKnown = true;
            candidate.BalanceBefore = currentBalance;
            if (currentBalance <= request.ReserveCoins)
            {
                ClearActive();
                WriteTerminal(
                    request,
                    candidate,
                    currentBalance < request.ReserveCoins
                        ? "error" : "budget_exhausted",
                    false,
                    currentBalance < request.ReserveCoins
                        ? "ReserveExceedsBalance" : "ReserveReached",
                    string.Empty,
                    currentBalance < request.ReserveCoins
                        ? "目前餘額低於要求保留的金額，未送出購買。"
                        : "目前餘額已達保留金額，未送出購買。",
                    false,
                    currentBalance
                );
                return;
            }
            long affordable = (currentBalance - request.ReserveCoins)
                / candidate.UnitPrice;
            candidate.PurchaseQuantity = (int)Math.Min(
                (long)candidate.AvailableQuantity, affordable
            );
            if (candidate.PurchaseQuantity <= 0)
            {
                ClearActive();
                WriteTerminal(
                    request,
                    candidate,
                    "no_match",
                    false,
                    "CurrentlyUnaffordable",
                    string.Empty,
                    "目前可用餘額買不起這筆 Card；稍後重新搜尋。",
                    false,
                    currentBalance
                );
                return;
            }
            object save = _playerSave.GetValue(_activePlayer, null);
            if (save == null)
                throw new InvalidOperationException("PlayerSave was null");
            Action<object> handler = delegate(object value)
            {
                bool succeeded = value != null && Convert.ToBoolean(
                    value, CultureInfo.InvariantCulture
                );
                CompletePurchaseCallback(request.RequestId, succeeded);
            };
            ParameterInfo[] purchaseParameters =
                _saveVendingPurchase.GetParameters();
            _activeIl2CppCallback = CreateIl2CppCallback(
                handler,
                typeof(bool),
                purchaseParameters[4].ParameterType
            );
            WriteProgress(request, candidate, "purchasing");
            _purchaseStartedElapsed = Stopwatch.GetTimestamp();
            _log.LogInfo(
                "Card purchase submitted id=" + request.RequestId
                + " listing=" + candidate.ListingId
                + " unit_price=" + candidate.UnitPrice
                + " quantity=" + candidate.PurchaseQuantity
                + " path=PlayerSave.VendingPurchase"
            );
            _saveVendingPurchase.Invoke(
                save,
                new object[]
                {
                    candidate.ListingId,
                    candidate.PurchaseQuantity,
                    candidate.UnitPrice,
                    candidate.ListingVersion,
                    _activeIl2CppCallback
                }
            );
        }

        private static void CompletePurchaseCallback(
            long requestId, bool success
        )
        {
            if (_activeRequestId != requestId
                || _activeRequest == null
                || _activeCandidate == null)
                return;
            CardPurchaseRequest request = _activeRequest;
            CardPurchaseCandidate candidate = _activeCandidate;
            try
            {
                long walletCoins = ReadCurrentCoins(_activePlayer);
                bool reported = _reportedResultAvailable;
                bool finalSuccess = reported ? _reportedSuccess : success;
                string reason = reported ? _reportedReason : string.Empty;
                string message = reported ? _reportedMessage : string.Empty;
                bool uncertain = !finalSuccess && string.Equals(
                    reason, "OperationPending", StringComparison.OrdinalIgnoreCase
                );
                ClearActive();
                WriteTerminal(
                    request,
                    candidate,
                    finalSuccess ? "ok" : (uncertain ? "unknown" : "error"),
                    finalSuccess,
                    finalSuccess ? "Success" : "PurchaseRejected",
                    reason,
                    message.Length > 0 ? message : (finalSuccess
                        ? "Card 購買完成。"
                        : "遊戲的拍賣購買流程拒絕這筆交易。"),
                    uncertain,
                    walletCoins
                );
                _log.LogInfo(
                    "Card purchase completed id=" + request.RequestId
                    + " success=" + finalSuccess
                    + " reason=" + reason
                    + " path=PlayerSave.VendingPurchase"
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                ClearActive();
                WriteTerminal(
                    request,
                    candidate,
                    "unknown",
                    false,
                    "CallbackReadFailed",
                    string.Empty,
                    actual.GetType().Name + ": " + actual.Message
                        + "; 購買結果不明，BOT 不會自動重試。",
                    true,
                    null
                );
            }
        }

        private static void VendingPurchaseResultPrefix(object[] __args)
        {
            if (!IsBusy || _purchaseStartedElapsed == 0
                || __args == null || __args.Length < 4)
                return;
            try
            {
                _reportedSuccess = __args[1] != null && Convert.ToBoolean(
                    __args[1], CultureInfo.InvariantCulture
                );
                _reportedMessage = __args[2] == null ? string.Empty
                    : Convert.ToString(
                        __args[2], CultureInfo.InvariantCulture
                    );
                _reportedReason = __args[3] == null ? string.Empty
                    : Convert.ToString(
                        __args[3], CultureInfo.InvariantCulture
                    );
                _reportedResultAvailable = true;
            }
            catch (Exception error)
            {
                _log.LogWarning(
                    "Could not capture vending purchase result details: "
                    + error.GetType().Name + ": " + error.Message
                );
            }
        }

        private static long ReadCurrentCoins(object player)
        {
            if (player == null)
                throw new InvalidOperationException("PlayerController was null");
            object save = _playerSave.GetValue(player, null);
            if (save == null)
                throw new InvalidOperationException("PlayerSave was null");
            object playerData = _savePlayerData.GetValue(save, null);
            if (playerData == null)
                throw new InvalidOperationException("PlayerData was null");
            object value = _playerDataCoins.GetValue(playerData, null);
            if (value == null)
                throw new InvalidOperationException("PlayerData.Coins was null");
            return Convert.ToInt64(value, CultureInfo.InvariantCulture);
        }

        private static void ClearActive()
        {
            _activeRequestId = 0;
            _activeStartedElapsed = 0;
            _purchaseStartedElapsed = 0;
            _activeRequest = null;
            _activeCandidate = null;
            _activePlayer = null;
            _activeIl2CppCallback = null;
            _activeManagedCallback = null;
            _reportedResultAvailable = false;
            _reportedSuccess = false;
            _reportedMessage = string.Empty;
            _reportedReason = string.Empty;
        }

        private static CardPurchaseRequest ReadRequest()
        {
            try
            {
                if (!File.Exists(Plugin.CardPurchaseRequestPath))
                    return null;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.CardPurchaseRequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                    json = reader.ReadToEnd();
                long requestId;
                long timestamp;
                long reserveCoins;
                long unitPriceLimitExclusive;
                if (!TryReadLong(json, "request_id", out requestId)
                    || !TryReadLong(json, "timestamp_ms", out timestamp)
                    || !TryReadLong(
                        json, "reserve_coins", out reserveCoins
                    )
                    || !TryReadLong(
                        json,
                        "unit_price_limit_exclusive",
                        out unitPriceLimitExclusive
                    )
                    || requestId <= 0)
                    return null;
                long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                if (Math.Abs(now - timestamp) > RequestMaxAgeMilliseconds)
                    return null;
                CardPurchaseRequest request = new CardPurchaseRequest();
                request.RequestId = requestId;
                request.TimestampMilliseconds = timestamp;
                request.ReserveCoins = reserveCoins;
                request.UnitPriceLimitExclusive = unitPriceLimitExclusive;
                request.Confirmed = Regex.IsMatch(
                    json,
                    "\\\"confirmation\\\"\\s*:\\s*"
                        + "\\\"BULK_BUY_CARD_WITH_RESERVE\\\""
                );
                return request;
            }
            catch
            {
                return null;
            }
        }

        private static void WriteProgress(
            CardPurchaseRequest request,
            CardPurchaseCandidate candidate,
            string status
        )
        {
            WriteResult(
                request,
                candidate,
                status,
                false,
                string.Empty,
                string.Empty,
                string.Empty,
                false,
                null
            );
        }

        private static void WriteTerminal(
            CardPurchaseRequest request,
            CardPurchaseCandidate candidate,
            string status,
            bool success,
            string code,
            string reason,
            string message,
            bool purchaseMayHaveCompleted,
            long? walletCoins
        )
        {
            if (request == null)
                return;
            WriteResult(
                request,
                candidate,
                status,
                success,
                code,
                reason,
                message,
                purchaseMayHaveCompleted,
                walletCoins
            );
        }

        private static void WriteResult(
            CardPurchaseRequest request,
            CardPurchaseCandidate candidate,
            string status,
            bool success,
            string code,
            string reason,
            string message,
            bool purchaseMayHaveCompleted,
            long? walletCoins
        )
        {
            StringBuilder json = new StringBuilder(1024);
            json.Append('{');
            AuctionQueryService.AppendNumber(
                json, "schema_version", 2, false
            );
            AuctionQueryService.AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AuctionQueryService.AppendNumber(json, "request_id", request.RequestId);
            AuctionQueryService.AppendString(json, "status", status);
            AuctionQueryService.AppendString(json, "query", "Card");
            AuctionQueryService.AppendString(json, "item_type", "Card");
            AuctionQueryService.AppendNumber(
                json, "reserve_coins", request.ReserveCoins
            );
            AuctionQueryService.AppendNumber(
                json,
                "unit_price_limit_exclusive",
                request.UnitPriceLimitExclusive
            );
            AuctionQueryService.AppendNumber(
                json,
                "quantity",
                success && candidate != null ? candidate.PurchaseQuantity : 0
            );
            AuctionQueryService.AppendBoolean(json, "success", success);
            AuctionQueryService.AppendString(json, "code", code);
            AuctionQueryService.AppendString(json, "reason", reason);
            AuctionQueryService.AppendString(json, "message", message);
            AuctionQueryService.AppendBoolean(
                json, "purchase_may_have_completed", purchaseMayHaveCompleted
            );
            if (candidate != null)
            {
                AuctionQueryService.AppendString(
                    json, "listing_id", candidate.ListingId
                );
                AuctionQueryService.AppendString(
                    json, "item_display_name", candidate.ItemDisplayName
                );
                AuctionQueryService.AppendNumber(
                    json, "unit_price", candidate.UnitPrice
                );
                AuctionQueryService.AppendNumber(
                    json, "listing_version", candidate.ListingVersion
                );
                AuctionQueryService.AppendNumber(
                    json, "available_quantity", candidate.AvailableQuantity
                );
                AuctionQueryService.AppendNumber(
                    json, "requested_quantity", candidate.PurchaseQuantity
                );
                AuctionQueryService.AppendNumber(
                    json,
                    "total_spent",
                    success
                        ? candidate.UnitPrice * candidate.PurchaseQuantity
                        : 0
                );
            }
            if (request.BalanceKnown)
                AuctionQueryService.AppendNumber(
                    json, "balance_before", request.BalanceBefore
                );
            if (walletCoins.HasValue)
            {
                AuctionQueryService.AppendNumber(
                    json, "wallet_coins", walletCoins.Value
                );
                AuctionQueryService.AppendNumber(
                    json, "balance_after", walletCoins.Value
                );
            }
            json.Append('}');
            AuctionQueryService.AtomicWrite(
                Plugin.CardPurchaseResultPath, json.ToString()
            );
        }

        private static object CreateIl2CppCallback(Action<object> handler)
        {
            return CreateIl2CppCallback(
                handler,
                _searchPageType,
                _requestVendorItems.GetParameters()[1].ParameterType
            );
        }

        private static object CreateIl2CppCallback(
            Action<object> handler, Type valueType, Type callbackType
        )
        {
            MethodInfo helper = typeof(CardPurchaseService).GetMethod(
                "CreateManagedAction",
                BindingFlags.NonPublic | BindingFlags.Static
            ).MakeGenericMethod(valueType);
            _activeManagedCallback = (Delegate)helper.Invoke(
                null, new object[] { handler }
            );
            MethodInfo conversion = callbackType.GetMethod(
                "op_Implicit",
                BindingFlags.Public | BindingFlags.Static
            );
            if (conversion == null)
                throw new MissingMethodException(callbackType.FullName, "op_Implicit");
            return conversion.Invoke(null, new object[] { _activeManagedCallback });
        }

        private static Action<T> CreateManagedAction<T>(Action<object> handler)
        {
            return delegate(T value) { handler(value); };
        }

        private static object ReadMember(object instance, string name)
        {
            if (instance == null)
                return null;
            PropertyInfo property = instance.GetType().GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.FlattenHierarchy
            );
            return property == null ? null : property.GetValue(instance, null);
        }

        private static string ReadMemberString(object instance, string name)
        {
            object value = ReadMember(instance, name);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static long ReadMemberLong(object instance, string name)
        {
            object value = ReadMember(instance, name);
            return value == null ? 0L
                : Convert.ToInt64(value, CultureInfo.InvariantCulture);
        }

        private static int ReadMemberInt(object instance, string name)
        {
            object value = ReadMember(instance, name);
            return value == null ? 0
                : Convert.ToInt32(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBoolean(object instance, string name)
        {
            object value = ReadMember(instance, name);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBoolean(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            PropertyInfo count = collection.GetType().GetProperty("Count");
            return count == null ? 0 : Convert.ToInt32(
                count.GetValue(collection, null), CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = collection.GetType().GetProperty("Item");
            if (item == null)
                throw new MissingMemberException(
                    collection.GetType().FullName, "Item"
                );
            return item.GetValue(collection, new object[] { index });
        }

        private static void SetProperty(
            object instance, string name, object value
        )
        {
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            property.SetValue(instance, value, null);
        }

        private static void SetNullable(
            object instance, string name, object value
        )
        {
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            Type nullableType = property.PropertyType;
            Type[] arguments = nullableType.GetGenericArguments();
            if (arguments.Length != 1)
                throw new InvalidOperationException(
                    instance.GetType().FullName + "." + name
                    + " is not nullable"
                );
            Type underlying = arguments[0];
            object converted = Convert.ChangeType(
                value, underlying, CultureInfo.InvariantCulture
            );
            object boxed = Activator.CreateInstance(
                nullableType, new object[] { converted }
            );
            property.SetValue(instance, boxed, null);
        }

        private static void SetNullableEnum(
            object instance, string name, string enumName
        )
        {
            PropertyInfo property = RequireProperty(instance.GetType(), name);
            Type nullableType = property.PropertyType;
            Type[] arguments = nullableType.GetGenericArguments();
            if (arguments.Length != 1 || !arguments[0].IsEnum)
                throw new InvalidOperationException(
                    instance.GetType().FullName + "." + name
                    + " is not a nullable enum"
                );
            Type enumType = arguments[0];
            object value = Enum.Parse(enumType, enumName, true);
            object boxed = Activator.CreateInstance(
                nullableType, new object[] { value }
            );
            property.SetValue(instance, boxed, null);
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name
                    && parameters.Length == parameterCount
                    && parameters[0].ParameterType == firstParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException : error;
        }

        private static bool TryReadLong(
            string json, string name, out long value
        )
        {
            value = 0;
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name) + "\\\"\\s*:\\s*(-?[0-9]+)"
            );
            return match.Success && long.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            );
        }

        private static int ReadInt(string json, string name, int fallback)
        {
            long value;
            return TryReadLong(json, name, out value)
                && value >= int.MinValue && value <= int.MaxValue
                ? (int)value : fallback;
        }

        private static long ElapsedMilliseconds(long startedTicks)
        {
            if (startedTicks <= 0)
                return 0;
            return (long)((Stopwatch.GetTimestamp() - startedTicks) * 1000.0
                / Stopwatch.Frequency);
        }
    }

    internal static class InventoryExportService
    {
        private const long RequestMaxAgeMilliseconds = 30000;

        private static ManualLogSource _log;
        private static long _lastRequestId;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _characterInventory;
        private static PropertyInfo _characterEquips;
        private static PropertyInfo _inventoryEquips;
        private static PropertyInfo _equipSlot;
        private static PropertyInfo _equipSlotEquip;
        private static PropertyInfo _equipId;
        private static PropertyInfo _equipUid;
        private static PropertyInfo _equipRefine;
        private static PropertyInfo _equipFavorite;
        private static PropertyInfo _equipPotential;
        private static PropertyInfo _equipStartingPotential;
        private static PropertyInfo _equipSpentPotential;
        private static PropertyInfo _equipChaosType;
        private static PropertyInfo _equipCards;
        private static PropertyInfo _equipSubstats;
        private static PropertyInfo _statType;
        private static PropertyInfo _statValue;
        private static PropertyInfo _statValueString;
        private static PropertyInfo _appServerRuntime;
        private static PropertyInfo _runtimeEquips;
        private static PropertyInfo _configDisplayName;
        private static MethodInfo _toDisplayName;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            Type characterDataType = PlayerUpdatePatch.FindLoadedType(
                "CharacterData"
            );
            Type inventoryType = PlayerUpdatePatch.FindLoadedType("InventoryData");
            Type equipSlotType = PlayerUpdatePatch.FindLoadedType("EquipSlotData");
            Type equipType = PlayerUpdatePatch.FindLoadedType("EquipData");
            Type statType = PlayerUpdatePatch.FindLoadedType("StatData");
            Type appType = PlayerUpdatePatch.FindLoadedType("App");
            Type runtimeType = PlayerUpdatePatch.FindLoadedType(
                "GameServerRuntime"
            );
            Type configType = PlayerUpdatePatch.FindLoadedType("EquipConfig");
            Type extensionsType = PlayerUpdatePatch.FindLoadedType("Extensions");

            _playerCharacterData = RequireProperty(playerType, "CharacterData");
            _characterInventory = RequireProperty(characterDataType, "Inventory");
            _characterEquips = RequireProperty(characterDataType, "Equips");
            _inventoryEquips = RequireProperty(inventoryType, "Equips");
            _equipSlot = RequireProperty(equipSlotType, "Slot");
            _equipSlotEquip = RequireProperty(equipSlotType, "Equip");
            _equipId = RequireProperty(equipType, "Id");
            _equipUid = RequireProperty(equipType, "UID");
            _equipRefine = RequireProperty(equipType, "Refine");
            _equipFavorite = RequireProperty(equipType, "Favorite");
            _equipPotential = RequireProperty(equipType, "Potential");
            _equipStartingPotential = RequireProperty(
                equipType, "StartingPotential"
            );
            _equipSpentPotential = RequireProperty(equipType, "SpentPotential");
            _equipChaosType = RequireProperty(equipType, "ChaosType");
            _equipCards = RequireProperty(equipType, "Cards");
            _equipSubstats = RequireProperty(equipType, "Substats");
            _statType = RequireProperty(statType, "Type");
            _statValue = RequireProperty(statType, "Value");
            _statValueString = RequireProperty(statType, "ValueStr");
            _appServerRuntime = RequireProperty(appType, "ServerRuntime");
            _runtimeEquips = RequireProperty(runtimeType, "Equips");
            _configDisplayName = RequireProperty(configType, "DisplayName");
            _toDisplayName = RequireMethod(
                extensionsType, "ToDisplayName", equipType, 2
            );
            log.LogInfo("Inventory equipment export IPC initialized");
        }

        internal static void Tick(object player)
        {
            long requestId;
            if (!TryReadRequest(out requestId) || requestId == _lastRequestId)
                return;
            _lastRequestId = requestId;
            try
            {
                WriteInventory(requestId, player);
                _log.LogInfo("Inventory equipment export completed id=" + requestId);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                WriteFailure(
                    requestId,
                    actual.GetType().Name + ": " + actual.Message
                );
                _log.LogWarning(
                    "Inventory equipment export failed: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
        }

        private static void WriteInventory(long requestId, object player)
        {
            object character = _playerCharacterData.GetValue(player, null);
            if (character == null)
                throw new InvalidOperationException("CharacterData was null");
            object inventory = _characterInventory.GetValue(character, null);
            if (inventory == null)
                throw new InvalidOperationException("Inventory was null");
            object equips = _inventoryEquips.GetValue(inventory, null);
            if (equips == null)
                throw new InvalidOperationException("Inventory.Equips was null");
            object equippedSlots = _characterEquips.GetValue(character, null);

            List<object> values = DictionaryValues(equips);
            int equippedCount = CollectionCount(equippedSlots);
            StringBuilder json = new StringBuilder(
                Math.Max(4096, (values.Count + equippedCount) * 512)
            );
            json.Append('{');
            AuctionQueryService.AppendNumber(
                json, "schema_version", 2, false
            );
            AuctionQueryService.AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AuctionQueryService.AppendNumber(json, "request_id", requestId);
            AuctionQueryService.AppendString(json, "status", "ok");
            AuctionQueryService.AppendNumber(json, "equipment_count", values.Count);
            json.Append(",\"items\":[");
            for (int index = 0; index < values.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendEquip(json, values[index]);
            }
            json.Append(']');
            AuctionQueryService.AppendNumber(
                json, "equipped_count", equippedCount
            );
            json.Append(",\"equipped_items\":[");
            for (int index = 0; index < equippedCount; index++)
            {
                if (index > 0)
                    json.Append(',');
                object slot = CollectionItem(equippedSlots, index);
                object equip = slot == null
                    ? null : _equipSlotEquip.GetValue(slot, null);
                json.Append('{');
                AuctionQueryService.AppendString(
                    json,
                    "slot",
                    slot == null ? string.Empty : ReadString(_equipSlot, slot),
                    false
                );
                json.Append(",\"item\":");
                if (equip == null)
                    json.Append("null");
                else
                    AppendEquip(json, equip);
                json.Append('}');
            }
            json.Append("]}");
            AuctionQueryService.AtomicWrite(
                Plugin.InventoryResultPath, json.ToString()
            );
        }

        private static void AppendEquip(StringBuilder json, object equip)
        {
            string id = ReadString(_equipId, equip);
            json.Append('{');
            AuctionQueryService.AppendString(json, "item_id", id, false);
            AuctionQueryService.AppendString(
                json, "display_name", ResolveDisplayName(id)
            );
            AuctionQueryService.AppendString(
                json, "full_display_name", ResolveFullDisplayName(equip, id)
            );
            AuctionQueryService.AppendString(
                json, "uid", ReadString(_equipUid, equip)
            );
            AuctionQueryService.AppendNumber(
                json, "refine", ReadInt(_equipRefine, equip)
            );
            AuctionQueryService.AppendBoolean(
                json, "favorite", ReadBool(_equipFavorite, equip)
            );
            AuctionQueryService.AppendNumber(
                json, "potential", ReadInt(_equipPotential, equip)
            );
            AuctionQueryService.AppendNumber(
                json,
                "starting_potential",
                ReadInt(_equipStartingPotential, equip)
            );
            AuctionQueryService.AppendNumber(
                json, "spent_potential", ReadInt(_equipSpentPotential, equip)
            );
            AuctionQueryService.AppendString(
                json, "chaos_type", ReadString(_equipChaosType, equip)
            );
            AppendCards(json, _equipCards.GetValue(equip, null));
            AppendSubstats(json, _equipSubstats.GetValue(equip, null));
            EquipmentDisplayStatService.AppendForEquip(json, equip);
            json.Append('}');
        }

        private static void AppendCards(StringBuilder json, object cards)
        {
            json.Append(",\"cards\":[");
            int count = CollectionCount(cards);
            for (int index = 0; index < count; index++)
            {
                if (index > 0)
                    json.Append(',');
                json.Append('"');
                json.Append(EscapeJson(Convert.ToString(
                    CollectionItem(cards, index), CultureInfo.InvariantCulture
                ) ?? string.Empty));
                json.Append('"');
            }
            json.Append(']');
        }

        private static void AppendSubstats(StringBuilder json, object substats)
        {
            json.Append(",\"substats\":[");
            int count = CollectionCount(substats);
            for (int index = 0; index < count; index++)
            {
                if (index > 0)
                    json.Append(',');
                object stat = CollectionItem(substats, index);
                object type = _statType.GetValue(stat, null);
                json.Append('{');
                AuctionQueryService.AppendString(
                    json,
                    "type",
                    Convert.ToString(type, CultureInfo.InvariantCulture),
                    false
                );
                AuctionQueryService.AppendNumber(
                    json,
                    "type_value",
                    Convert.ToInt64(type, CultureInfo.InvariantCulture)
                );
                AuctionQueryService.AppendNumber(
                    json, "value", ReadInt(_statValue, stat)
                );
                AuctionQueryService.AppendString(
                    json, "value_str", ReadString(_statValueString, stat)
                );
                json.Append('}');
            }
            json.Append(']');
        }

        private static string ResolveDisplayName(string id)
        {
            try
            {
                object config = ResolveConfig(id);
                string name = ReadString(_configDisplayName, config);
                return string.IsNullOrWhiteSpace(name) ? id : name;
            }
            catch
            {
                return id;
            }
        }

        private static string ResolveFullDisplayName(object equip, string id)
        {
            try
            {
                object config = ResolveConfig(id);
                object value = _toDisplayName.Invoke(
                    null, new object[] { equip, config }
                );
                string name = Convert.ToString(
                    value, CultureInfo.InvariantCulture
                );
                return string.IsNullOrWhiteSpace(name)
                    ? ResolveDisplayName(id) : name;
            }
            catch
            {
                return ResolveDisplayName(id);
            }
        }

        private static object ResolveConfig(string id)
        {
            object runtime = _appServerRuntime.GetValue(null, null);
            object configs = _runtimeEquips.GetValue(runtime, null);
            PropertyInfo item = configs.GetType().GetProperty("Item");
            if (item == null)
                throw new MissingMemberException(configs.GetType().FullName, "Item");
            return item.GetValue(configs, new object[] { id });
        }

        private static List<object> DictionaryValues(object dictionary)
        {
            List<object> values = new List<object>();
            MethodInfo getEnumerator = RequireZeroParameterMethod(
                dictionary.GetType(), "GetEnumerator"
            );
            object enumerator = getEnumerator.Invoke(dictionary, null);
            MethodInfo moveNext = RequireZeroParameterMethod(
                enumerator.GetType(), "MoveNext"
            );
            PropertyInfo current = RequireProperty(
                enumerator.GetType(), "Current"
            );
            while (Convert.ToBoolean(
                moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture
            ))
            {
                object pair = current.GetValue(enumerator, null);
                PropertyInfo value = RequireProperty(pair.GetType(), "Value");
                object equip = value.GetValue(pair, null);
                if (equip != null)
                    values.Add(equip);
            }
            return values;
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            PropertyInfo count = RequireProperty(collection.GetType(), "Count");
            return Convert.ToInt32(
                count.GetValue(collection, null), CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = RequireProperty(collection.GetType(), "Item");
            return item.GetValue(collection, new object[] { index });
        }

        private static bool TryReadRequest(out long requestId)
        {
            requestId = 0;
            try
            {
                if (!File.Exists(Plugin.InventoryRequestPath))
                    return false;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.InventoryRequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                    json = reader.ReadToEnd();
                Match id = Regex.Match(
                    json, "\\\"request_id\\\"\\s*:\\s*([0-9]+)"
                );
                Match timestamp = Regex.Match(
                    json, "\\\"timestamp_ms\\\"\\s*:\\s*([0-9]+)"
                );
                long time;
                if (!id.Success || !timestamp.Success
                    || !long.TryParse(
                        id.Groups[1].Value,
                        NumberStyles.Integer,
                        CultureInfo.InvariantCulture,
                        out requestId
                    )
                    || !long.TryParse(
                        timestamp.Groups[1].Value,
                        NumberStyles.Integer,
                        CultureInfo.InvariantCulture,
                        out time
                    )
                    || requestId <= 0)
                    return false;
                return Math.Abs(
                    DateTimeOffset.UtcNow.ToUnixTimeMilliseconds() - time
                ) <= RequestMaxAgeMilliseconds;
            }
            catch
            {
                return false;
            }
        }

        private static void WriteFailure(long requestId, string message)
        {
            StringBuilder json = new StringBuilder(256);
            json.Append('{');
            AuctionQueryService.AppendNumber(
                json, "schema_version", 1, false
            );
            AuctionQueryService.AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AuctionQueryService.AppendNumber(json, "request_id", requestId);
            AuctionQueryService.AppendString(json, "status", "error");
            AuctionQueryService.AppendString(json, "message", message);
            json.Append(",\"items\":[]}");
            AuctionQueryService.AtomicWrite(
                Plugin.InventoryResultPath, json.ToString()
            );
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireZeroParameterMethod(
            Type type, string name
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
                if (methods[index].Name == name
                    && methods[index].GetParameters().Length == 0)
                    return methods[index];
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name
                    && parameters.Length == parameterCount
                    && parameters[0].ParameterType == firstParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static int ReadInt(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? 0
                : Convert.ToInt32(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBool(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException : error;
        }

        private static string EscapeJson(string value)
        {
            StringBuilder escaped = new StringBuilder(value.Length + 8);
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                switch (character)
                {
                    case '\\': escaped.Append("\\\\"); break;
                    case '"': escaped.Append("\\\""); break;
                    case '\n': escaped.Append("\\n"); break;
                    case '\r': escaped.Append("\\r"); break;
                    case '\t': escaped.Append("\\t"); break;
                    default: escaped.Append(character); break;
                }
            }
            return escaped.ToString();
        }
    }

    internal static class InventoryDismantleService
    {
        private const long RequestMaxAgeMilliseconds = 15000;
        private const long VerificationTimeoutMilliseconds = 10000;
        private const string ConfirmationValue = "DISMANTLE_EQUIP";

        private static ManualLogSource _log;
        private static long _lastRequestId;
        private static long _activeRequestId;
        private static long _submittedAtMilliseconds;
        private static string _activeUid = string.Empty;
        private static string _activeItemId = string.Empty;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _playerSave;
        private static PropertyInfo _characterInventory;
        private static PropertyInfo _characterEquips;
        private static PropertyInfo _inventoryEquips;
        private static PropertyInfo _slotEquip;
        private static PropertyInfo _equipId;
        private static PropertyInfo _equipUid;
        private static PropertyInfo _equipFavorite;
        private static MethodInfo _dismantle;
        private static object _equipItemType;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            Type playerSaveType = PlayerUpdatePatch.FindLoadedType("PlayerSave");
            Type characterDataType = PlayerUpdatePatch.FindLoadedType(
                "CharacterData"
            );
            Type inventoryType = PlayerUpdatePatch.FindLoadedType("InventoryData");
            Type equipSlotType = PlayerUpdatePatch.FindLoadedType("EquipSlotData");
            Type equipType = PlayerUpdatePatch.FindLoadedType("EquipData");
            Type itemType = PlayerUpdatePatch.FindLoadedType("ItemType");

            _playerCharacterData = RequireProperty(playerType, "CharacterData");
            _playerSave = RequireProperty(playerType, "Save");
            _characterInventory = RequireProperty(characterDataType, "Inventory");
            _characterEquips = RequireProperty(characterDataType, "Equips");
            _inventoryEquips = RequireProperty(inventoryType, "Equips");
            _slotEquip = RequireProperty(equipSlotType, "Equip");
            _equipId = RequireProperty(equipType, "Id");
            _equipUid = RequireProperty(equipType, "UID");
            _equipFavorite = RequireProperty(equipType, "Favorite");
            _dismantle = RequireMethod(
                playerSaveType, "Dismantle_S", typeof(string), itemType
            );
            _equipItemType = Enum.Parse(itemType, "Equip", true);
            log.LogInfo(
                "Guarded equipment dismantle IPC initialized; exact UID, item ID, "
                    + "fresh confirmation, non-favorite and unequipped checks enabled"
            );
        }

        internal static void Tick(object player, long elapsedMilliseconds)
        {
            if (_activeRequestId > 0)
            {
                object remaining;
                if (!TryFindInventoryEquip(player, _activeUid, out remaining))
                {
                    WriteResult(
                        _activeRequestId,
                        "ok",
                        _activeUid,
                        _activeItemId,
                        "Equipment is no longer present in the backpack",
                        true
                    );
                    _log.LogInfo(
                        "Equipment dismantle verified uid=" + _activeUid
                    );
                    ClearActive();
                }
                else if (elapsedMilliseconds - _submittedAtMilliseconds
                    >= VerificationTimeoutMilliseconds)
                {
                    WriteResult(
                        _activeRequestId,
                        "unverified",
                        _activeUid,
                        _activeItemId,
                        "Dismantle RPC was submitted, but the equipment remained "
                            + "in the backpack after the verification timeout",
                        false
                    );
                    _log.LogWarning(
                        "Equipment dismantle could not be verified uid=" + _activeUid
                    );
                    ClearActive();
                }
            }

            long requestId;
            string uid;
            string itemId;
            string confirmation;
            if (!TryReadRequest(
                out requestId, out uid, out itemId, out confirmation
            ) || requestId == _lastRequestId)
                return;
            _lastRequestId = requestId;

            try
            {
                if (_activeRequestId > 0)
                    throw new InvalidOperationException(
                        "Another dismantle request is awaiting verification"
                    );
                if (confirmation != ConfirmationValue)
                    throw new InvalidOperationException(
                        "Explicit dismantle confirmation was missing"
                    );
                if (string.IsNullOrWhiteSpace(uid)
                    || string.IsNullOrWhiteSpace(itemId))
                    throw new InvalidOperationException(
                        "Both uid and item_id are required"
                    );

                object equip;
                if (!TryFindInventoryEquip(player, uid, out equip))
                    throw new InvalidOperationException(
                        "The exact equipment UID is not in the backpack"
                    );
                string actualItemId = ReadString(_equipId, equip);
                if (!string.Equals(actualItemId, itemId, StringComparison.Ordinal))
                    throw new InvalidOperationException(
                        "The equipment item ID did not match the request"
                    );
                if (ReadBool(_equipFavorite, equip))
                    throw new InvalidOperationException(
                        "Favorite equipment cannot be dismantled through IPC"
                    );
                if (IsEquipped(player, uid))
                    throw new InvalidOperationException(
                        "The equipment is currently worn and cannot be dismantled"
                    );

                object save = _playerSave.GetValue(player, null);
                if (save == null)
                    throw new InvalidOperationException("PlayerSave was null");

                _activeRequestId = requestId;
                _activeUid = uid;
                _activeItemId = itemId;
                _submittedAtMilliseconds = elapsedMilliseconds;
                WriteResult(
                    requestId,
                    "submitted",
                    uid,
                    itemId,
                    "Dismantle RPC submitted; awaiting backpack verification",
                    false
                );
                _dismantle.Invoke(
                    save, new object[] { uid, _equipItemType }
                );
                _log.LogInfo(
                    "Equipment dismantle submitted uid=" + uid
                        + " item_id=" + itemId
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                WriteResult(
                    requestId,
                    "error",
                    uid,
                    itemId,
                    actual.GetType().Name + ": " + actual.Message,
                    false
                );
                _log.LogWarning(
                    "Equipment dismantle rejected uid=" + uid + ": "
                        + actual.GetType().Name + ": " + actual.Message
                );
                if (_activeRequestId == requestId)
                    ClearActive();
            }
        }

        private static bool TryFindInventoryEquip(
            object player, string uid, out object found
        )
        {
            found = null;
            object character = _playerCharacterData.GetValue(player, null);
            if (character == null)
                return false;
            object inventory = _characterInventory.GetValue(character, null);
            if (inventory == null)
                return false;
            object dictionary = _inventoryEquips.GetValue(inventory, null);
            if (dictionary == null)
                return false;

            foreach (object equip in DictionaryValues(dictionary))
            {
                if (string.Equals(
                    ReadString(_equipUid, equip), uid, StringComparison.Ordinal
                ))
                {
                    found = equip;
                    return true;
                }
            }
            return false;
        }

        private static bool IsEquipped(object player, string uid)
        {
            object character = _playerCharacterData.GetValue(player, null);
            object slots = character == null
                ? null : _characterEquips.GetValue(character, null);
            int count = CollectionCount(slots);
            for (int index = 0; index < count; index++)
            {
                object slot = CollectionItem(slots, index);
                object equip = slot == null ? null : _slotEquip.GetValue(slot, null);
                if (equip != null && string.Equals(
                    ReadString(_equipUid, equip), uid, StringComparison.Ordinal
                ))
                    return true;
            }
            return false;
        }

        private static List<object> DictionaryValues(object dictionary)
        {
            List<object> values = new List<object>();
            MethodInfo getEnumerator = RequireZeroParameterMethod(
                dictionary.GetType(), "GetEnumerator"
            );
            object enumerator = getEnumerator.Invoke(dictionary, null);
            MethodInfo moveNext = RequireZeroParameterMethod(
                enumerator.GetType(), "MoveNext"
            );
            PropertyInfo current = RequireProperty(
                enumerator.GetType(), "Current"
            );
            while (Convert.ToBoolean(
                moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture
            ))
            {
                object pair = current.GetValue(enumerator, null);
                PropertyInfo value = RequireProperty(pair.GetType(), "Value");
                object equip = value.GetValue(pair, null);
                if (equip != null)
                    values.Add(equip);
            }
            return values;
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            return Convert.ToInt32(
                RequireProperty(collection.GetType(), "Count").GetValue(
                    collection, null
                ),
                CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            return RequireProperty(collection.GetType(), "Item").GetValue(
                collection, new object[] { index }
            );
        }

        private static bool TryReadRequest(
            out long requestId,
            out string uid,
            out string itemId,
            out string confirmation
        )
        {
            requestId = 0;
            uid = string.Empty;
            itemId = string.Empty;
            confirmation = string.Empty;
            try
            {
                if (!File.Exists(Plugin.DismantleRequestPath))
                    return false;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.DismantleRequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                    json = reader.ReadToEnd();

                long timestamp;
                if (!TryReadLong(json, "request_id", out requestId)
                    || !TryReadLong(json, "timestamp_ms", out timestamp)
                    || requestId <= 0)
                    return false;
                long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                if (Math.Abs(now - timestamp) > RequestMaxAgeMilliseconds)
                    return false;
                uid = ReadJsonString(json, "uid");
                itemId = ReadJsonString(json, "item_id");
                confirmation = ReadJsonString(json, "confirm");
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static bool TryReadLong(
            string json, string name, out long value
        )
        {
            value = 0;
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*([0-9]+)"
            );
            return match.Success && long.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            );
        }

        private static string ReadJsonString(string json, string name)
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\""
            );
            if (!match.Success)
                return string.Empty;
            return Regex.Unescape(match.Groups[1].Value);
        }

        private static bool ReadJsonBool(
            string json, string name, bool fallback
        )
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*(true|false)",
                RegexOptions.IgnoreCase
            );
            if (!match.Success)
                return fallback;
            return string.Equals(
                match.Groups[1].Value, "true", StringComparison.OrdinalIgnoreCase
            );
        }

        private static void WriteResult(
            long requestId,
            string status,
            string uid,
            string itemId,
            string message,
            bool verifiedAbsent
        )
        {
            StringBuilder json = new StringBuilder(384);
            json.Append('{');
            AuctionQueryService.AppendNumber(
                json, "schema_version", 1, false
            );
            AuctionQueryService.AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AuctionQueryService.AppendNumber(json, "request_id", requestId);
            AuctionQueryService.AppendString(json, "status", status);
            AuctionQueryService.AppendString(json, "uid", uid);
            AuctionQueryService.AppendString(json, "item_id", itemId);
            AuctionQueryService.AppendString(json, "message", message);
            AuctionQueryService.AppendBoolean(
                json, "verified_absent", verifiedAbsent
            );
            json.Append('}');
            AuctionQueryService.AtomicWrite(
                Plugin.DismantleResultPath, json.ToString()
            );
        }

        private static void ClearActive()
        {
            _activeRequestId = 0;
            _submittedAtMilliseconds = 0;
            _activeUid = string.Empty;
            _activeItemId = string.Empty;
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireZeroParameterMethod(
            Type type, string name
        )
        {
            return RequireMethod(type, name, null, null);
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, Type secondParameter
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name != name)
                    continue;
                if (firstParameter == null && secondParameter == null
                    && parameters.Length == 0)
                    return methods[index];
                if (firstParameter != null && secondParameter != null
                    && parameters.Length == 2
                    && parameters[0].ParameterType == firstParameter
                    && parameters[1].ParameterType == secondParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBool(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException : error;
        }
    }

    internal static class EquipmentFavoriteService
    {
        private const long RequestMaxAgeMilliseconds = 15000;
        private const long VerificationTimeoutMilliseconds = 10000;
        private const string ConfirmationValue = "SET_FAVORITE";

        private static ManualLogSource _log;
        private static long _lastRequestId;
        private static long _activeRequestId;
        private static long _submittedAtMilliseconds;
        private static string _activeUid = string.Empty;
        private static string _activeItemId = string.Empty;
        private static string _activeLocation = string.Empty;
        private static bool _activeDesired;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _playerSave;
        private static PropertyInfo _characterInventory;
        private static PropertyInfo _characterEquips;
        private static PropertyInfo _inventoryEquips;
        private static PropertyInfo _slotEquip;
        private static PropertyInfo _equipId;
        private static PropertyInfo _equipUid;
        private static PropertyInfo _equipFavorite;
        private static MethodInfo _toggleFavorite;
        private static object _equipItemType;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            Type playerSaveType = PlayerUpdatePatch.FindLoadedType("PlayerSave");
            Type characterDataType = PlayerUpdatePatch.FindLoadedType(
                "CharacterData"
            );
            Type inventoryType = PlayerUpdatePatch.FindLoadedType("InventoryData");
            Type equipSlotType = PlayerUpdatePatch.FindLoadedType("EquipSlotData");
            Type equipType = PlayerUpdatePatch.FindLoadedType("EquipData");
            Type itemType = PlayerUpdatePatch.FindLoadedType("ItemType");

            _playerCharacterData = RequireProperty(playerType, "CharacterData");
            _playerSave = RequireProperty(playerType, "Save");
            _characterInventory = RequireProperty(characterDataType, "Inventory");
            _characterEquips = RequireProperty(characterDataType, "Equips");
            _inventoryEquips = RequireProperty(inventoryType, "Equips");
            _slotEquip = RequireProperty(equipSlotType, "Equip");
            _equipId = RequireProperty(equipType, "Id");
            _equipUid = RequireProperty(equipType, "UID");
            _equipFavorite = RequireProperty(equipType, "Favorite");
            _toggleFavorite = RequireMethod(
                playerSaveType, "ToggleFavorite_S", typeof(string), itemType
            );
            _equipItemType = Enum.Parse(itemType, "Equip", true);
            log.LogInfo(
                "Guarded equipment favorite IPC initialized; exact UID, item ID, "
                    + "location, desired state and fresh confirmation checks enabled"
            );
        }

        internal static void Tick(object player, long elapsedMilliseconds)
        {
            if (_activeRequestId > 0)
            {
                object current;
                if (!TryFindEquipment(
                    player,
                    _activeLocation,
                    _activeUid,
                    _activeItemId,
                    out current
                ))
                {
                    WriteResult(
                        _activeRequestId,
                        "unverified",
                        _activeUid,
                        _activeItemId,
                        _activeLocation,
                        "Target left the requested location during verification",
                        !_activeDesired
                    );
                    ClearActive();
                }
                else if (ReadBool(_equipFavorite, current) == _activeDesired)
                {
                    WriteResult(
                        _activeRequestId,
                        "ok",
                        _activeUid,
                        _activeItemId,
                        _activeLocation,
                        "Equipment favorite state verified",
                        _activeDesired
                    );
                    _log.LogInfo(
                        "Equipment favorite verified uid=" + _activeUid
                            + " favorite=" + _activeDesired
                    );
                    ClearActive();
                }
                else if (elapsedMilliseconds - _submittedAtMilliseconds
                    >= VerificationTimeoutMilliseconds)
                {
                    WriteResult(
                        _activeRequestId,
                        "unverified",
                        _activeUid,
                        _activeItemId,
                        _activeLocation,
                        "Favorite RPC was submitted, but the requested state "
                            + "was not observed before the verification timeout",
                        !_activeDesired
                    );
                    _log.LogWarning(
                        "Equipment favorite could not be verified uid=" + _activeUid
                    );
                    ClearActive();
                }
            }

            long requestId;
            string uid;
            string itemId;
            string location;
            string confirmation;
            bool desired;
            if (!TryReadRequest(
                out requestId,
                out uid,
                out itemId,
                out location,
                out desired,
                out confirmation
            ) || requestId == _lastRequestId)
                return;
            _lastRequestId = requestId;

            try
            {
                if (_activeRequestId > 0)
                    throw new InvalidOperationException(
                        "Another favorite request is awaiting verification"
                    );
                if (confirmation != ConfirmationValue)
                    throw new InvalidOperationException(
                        "Explicit favorite confirmation was missing"
                    );
                if (string.IsNullOrWhiteSpace(uid)
                    || string.IsNullOrWhiteSpace(itemId))
                    throw new InvalidOperationException(
                        "Both uid and item_id are required"
                    );
                if (location != "backpack" && location != "equipped")
                    throw new InvalidOperationException(
                        "location must be backpack or equipped"
                    );

                object equip;
                if (!TryFindEquipment(
                    player, location, uid, itemId, out equip
                ))
                    throw new InvalidOperationException(
                        "The exact UID and item ID are not in the requested location"
                    );
                if (ReadBool(_equipFavorite, equip) == desired)
                {
                    WriteResult(
                        requestId,
                        "ok",
                        uid,
                        itemId,
                        location,
                        "Equipment already had the requested favorite state; "
                            + "no toggle was sent",
                        desired
                    );
                    return;
                }

                object save = _playerSave.GetValue(player, null);
                if (save == null)
                    throw new InvalidOperationException("PlayerSave was null");

                _activeRequestId = requestId;
                _activeUid = uid;
                _activeItemId = itemId;
                _activeLocation = location;
                _activeDesired = desired;
                _submittedAtMilliseconds = elapsedMilliseconds;
                WriteResult(
                    requestId,
                    "submitted",
                    uid,
                    itemId,
                    location,
                    "Favorite RPC submitted; awaiting state verification",
                    !desired
                );
                _toggleFavorite.Invoke(
                    save, new object[] { uid, _equipItemType }
                );
                _log.LogInfo(
                    "Equipment favorite submitted uid=" + uid
                        + " item_id=" + itemId + " location=" + location
                        + " desired=" + desired
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                WriteResult(
                    requestId,
                    "error",
                    uid,
                    itemId,
                    location,
                    actual.GetType().Name + ": " + actual.Message,
                    !desired
                );
                _log.LogWarning(
                    "Equipment favorite rejected uid=" + uid + ": "
                        + actual.GetType().Name + ": " + actual.Message
                );
                if (_activeRequestId == requestId)
                    ClearActive();
            }
        }

        private static bool TryFindEquipment(
            object player,
            string location,
            string uid,
            string itemId,
            out object found
        )
        {
            found = null;
            object character = _playerCharacterData.GetValue(player, null);
            if (character == null)
                return false;
            if (location == "backpack")
            {
                object inventory = _characterInventory.GetValue(character, null);
                object dictionary = inventory == null
                    ? null : _inventoryEquips.GetValue(inventory, null);
                int backpackMatches = 0;
                foreach (object equip in DictionaryValues(dictionary))
                {
                    if (!EquipmentMatches(equip, uid, itemId))
                        continue;
                    found = equip;
                    backpackMatches++;
                }
                return backpackMatches == 1;
            }
            object slots = character == null
                ? null : _characterEquips.GetValue(character, null);
            int count = CollectionCount(slots);
            int equippedMatches = 0;
            for (int index = 0; index < count; index++)
            {
                object slot = CollectionItem(slots, index);
                object equip = slot == null ? null : _slotEquip.GetValue(slot, null);
                if (!EquipmentMatches(equip, uid, itemId))
                    continue;
                found = equip;
                equippedMatches++;
            }
            return equippedMatches == 1;
        }

        private static bool EquipmentMatches(
            object equip, string uid, string itemId
        )
        {
            return equip != null
                && string.Equals(
                    ReadString(_equipUid, equip), uid, StringComparison.Ordinal
                )
                && string.Equals(
                    ReadString(_equipId, equip), itemId, StringComparison.Ordinal
                );
        }

        private static List<object> DictionaryValues(object dictionary)
        {
            List<object> values = new List<object>();
            if (dictionary == null)
                return values;
            MethodInfo getEnumerator = dictionary.GetType().GetMethod(
                "GetEnumerator", Type.EmptyTypes
            );
            if (getEnumerator == null)
                throw new MissingMethodException(
                    dictionary.GetType().FullName, "GetEnumerator"
                );
            object enumerator = getEnumerator.Invoke(dictionary, null);
            MethodInfo moveNext = enumerator.GetType().GetMethod(
                "MoveNext", Type.EmptyTypes
            );
            if (moveNext == null)
                throw new MissingMethodException(
                    enumerator.GetType().FullName, "MoveNext"
                );
            PropertyInfo current = RequireProperty(
                enumerator.GetType(), "Current"
            );
            while (Convert.ToBoolean(
                moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture
            ))
            {
                object pair = current.GetValue(enumerator, null);
                object equip = RequireProperty(
                    pair.GetType(), "Value"
                ).GetValue(pair, null);
                if (equip != null)
                    values.Add(equip);
            }
            return values;
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            return Convert.ToInt32(
                RequireProperty(collection.GetType(), "Count").GetValue(
                    collection, null
                ),
                CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            return RequireProperty(collection.GetType(), "Item").GetValue(
                collection, new object[] { index }
            );
        }

        private static bool TryReadRequest(
            out long requestId,
            out string uid,
            out string itemId,
            out string location,
            out bool desired,
            out string confirmation
        )
        {
            requestId = 0;
            uid = string.Empty;
            itemId = string.Empty;
            location = string.Empty;
            desired = false;
            confirmation = string.Empty;
            try
            {
                if (!File.Exists(Plugin.FavoriteRequestPath))
                    return false;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.FavoriteRequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                    json = reader.ReadToEnd();

                long timestamp;
                if (!TryReadLong(json, "request_id", out requestId)
                    || !TryReadLong(json, "timestamp_ms", out timestamp)
                    || requestId <= 0)
                    return false;
                long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                if (Math.Abs(now - timestamp) > RequestMaxAgeMilliseconds)
                    return false;
                uid = ReadJsonString(json, "uid");
                itemId = ReadJsonString(json, "item_id");
                location = ReadJsonString(json, "location").ToLowerInvariant();
                desired = ReadJsonBool(json, "desired", true);
                confirmation = ReadJsonString(json, "confirm");
                return true;
            }
            catch
            {
                return false;
            }
        }

        private static bool TryReadLong(
            string json, string name, out long value
        )
        {
            value = 0;
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*([0-9]+)"
            );
            return match.Success && long.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            );
        }

        private static string ReadJsonString(string json, string name)
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\""
            );
            if (!match.Success)
                return string.Empty;
            return Regex.Unescape(match.Groups[1].Value);
        }

        private static bool ReadJsonBool(
            string json, string name, bool fallback
        )
        {
            Match match = Regex.Match(
                json,
                "\\\"" + Regex.Escape(name)
                    + "\\\"\\s*:\\s*(true|false)",
                RegexOptions.IgnoreCase
            );
            if (!match.Success)
                return fallback;
            return string.Equals(
                match.Groups[1].Value, "true", StringComparison.OrdinalIgnoreCase
            );
        }

        private static void WriteResult(
            long requestId,
            string status,
            string uid,
            string itemId,
            string location,
            string message,
            bool favorite
        )
        {
            StringBuilder json = new StringBuilder(384);
            json.Append('{');
            AuctionQueryService.AppendNumber(
                json, "schema_version", 1, false
            );
            AuctionQueryService.AppendNumber(
                json,
                "timestamp_ms",
                DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            );
            AuctionQueryService.AppendNumber(json, "request_id", requestId);
            AuctionQueryService.AppendString(json, "status", status);
            AuctionQueryService.AppendString(json, "uid", uid);
            AuctionQueryService.AppendString(json, "item_id", itemId);
            AuctionQueryService.AppendString(json, "location", location);
            AuctionQueryService.AppendString(json, "message", message);
            AuctionQueryService.AppendBoolean(json, "favorite", favorite);
            json.Append('}');
            AuctionQueryService.AtomicWrite(
                Plugin.FavoriteResultPath, json.ToString()
            );
        }

        private static void ClearActive()
        {
            _activeRequestId = 0;
            _submittedAtMilliseconds = 0;
            _activeUid = string.Empty;
            _activeItemId = string.Empty;
            _activeLocation = string.Empty;
            _activeDesired = false;
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireMethod(
            Type type, string name, Type firstParameter, Type secondParameter
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name
                    && parameters.Length == 2
                    && parameters[0].ParameterType == firstParameter
                    && parameters[1].ParameterType == secondParameter)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static string ReadString(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value == null ? string.Empty
                : Convert.ToString(value, CultureInfo.InvariantCulture);
        }

        private static bool ReadBool(PropertyInfo property, object instance)
        {
            object value = property.GetValue(instance, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException : error;
        }
    }

    internal static class ReconnectPatch
    {
        private const long UpdateIntervalMilliseconds = 100;

        private static readonly Stopwatch Timer = Stopwatch.StartNew();
        private static ManualLogSource _log;
        private static PropertyInfo _appPlayer;
        private static PropertyInfo _appUi;
        private static PropertyInfo _appTugboat;
        private static PropertyInfo _hasPendingReconnect;
        private static PropertyInfo _uiIsInGame;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _characterUid;
        private static MethodInfo _showLogin;
        private static MethodInfo _getLoginScreen;
        private static MethodInfo _getCharacterSelectScreen;
        private static MethodInfo _loginConnect;
        private static PropertyInfo _characterSelectCharacters;
        private static MethodInfo _playCharacter;
        private static PropertyInfo _componentGameObject;
        private static PropertyInfo _gameObjectActiveInHierarchy;
        private static MethodInfo _getConnectionState;

        private static long _lastUpdateMilliseconds;
        private static long _missingSinceMilliseconds = -1;
        private static long _attemptStartedMilliseconds = -1;
        private static long _nextAttemptMilliseconds = -1;
        private static int _attempts;
        private static bool _wasAuthorized;
        private static bool _characterPlayInvoked;
        private static string _lastCharacterUid = string.Empty;
        private static string _lastLoggedState = string.Empty;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            Type appType = PlayerUpdatePatch.FindLoadedType("App");
            Type playerType = PlayerUpdatePatch.FindLoadedType("PlayerController");
            Type characterDataType = PlayerUpdatePatch.FindLoadedType("CharacterData");
            Type uiManagerType = PlayerUpdatePatch.FindLoadedType("UIManager");
            Type uiLoginType = PlayerUpdatePatch.FindLoadedType("UILogin");
            Type uiCharacterSelectType = PlayerUpdatePatch.FindLoadedType(
                "UICharacterSelect"
            );
            Type componentType = PlayerUpdatePatch.FindLoadedType(
                "UnityEngine.Component"
            );
            Type gameObjectType = PlayerUpdatePatch.FindLoadedType(
                "UnityEngine.GameObject"
            );

            _appPlayer = RequireProperty(appType, "Player");
            _appUi = RequireProperty(appType, "UI");
            _appTugboat = RequireProperty(appType, "Tugboat");
            _hasPendingReconnect = RequireProperty(appType, "HasPendingReconnect");
            _uiIsInGame = RequireProperty(uiManagerType, "IsInGame");
            _playerCharacterData = RequireProperty(playerType, "CharacterData");
            _characterUid = RequireProperty(characterDataType, "UID");
            _showLogin = RequireMethod(uiManagerType, "ShowLogin", 0);
            MethodInfo getScreen = RequireGenericMethod(uiManagerType, "GetScreen", 0);
            _getLoginScreen = getScreen.MakeGenericMethod(uiLoginType);
            _getCharacterSelectScreen = getScreen.MakeGenericMethod(
                uiCharacterSelectType
            );
            _loginConnect = RequireMethod(uiLoginType, "Connect", 0);
            _characterSelectCharacters = RequireProperty(
                uiCharacterSelectType, "Characters"
            );
            _playCharacter = RequireMethod(uiCharacterSelectType, "PlayCharacter", 1);
            _componentGameObject = RequireProperty(componentType, "gameObject");
            _gameObjectActiveInHierarchy = RequireProperty(
                gameObjectType, "activeInHierarchy"
            );
            _getConnectionState = RequireMethodWithParameter(
                _appTugboat.PropertyType, "GetConnectionState", typeof(bool)
            );
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo value = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (value == null)
                throw new MissingMemberException(type.FullName, name);
            return value;
        }

        private static MethodInfo RequireMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && !methods[index].IsGenericMethodDefinition
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireGenericMethod(
            Type type, string name, int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].IsGenericMethodDefinition
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireMethodWithParameter(
            Type type, string name, Type parameterType
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                ParameterInfo[] parameters = methods[index].GetParameters();
                if (methods[index].Name == name && parameters.Length == 1
                    && parameters[0].ParameterType == parameterType)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static void Postfix()
        {
            long now = Timer.ElapsedMilliseconds;
            if (now - _lastUpdateMilliseconds < UpdateIntervalMilliseconds)
                return;
            _lastUpdateMilliseconds = now;

            try
            {
                Tick(now);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                LogState(
                    "error",
                    "Auto relogin failed safely: " + actual.GetType().Name
                        + ": " + actual.Message
                );
                NavigationRequest request = PlayerUpdatePatch.ReadRequest(
                    DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                );
                int maximum = request == null ? 5 : request.AutoReloginMaxAttempts;
                PlayerUpdatePatch.WriteReloginState(
                    "relogin_error", "ERROR", _attempts, maximum,
                    actual.GetType().Name + ": " + actual.Message,
                    _lastCharacterUid
                );
            }
        }

        private static void Tick(long now)
        {
            long utcNow = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            NavigationRequest request = PlayerUpdatePatch.ReadRequest(utcNow);
            object player = _appPlayer.GetValue(null, null);
            object ui = _appUi.GetValue(null, null);
            bool clientConnected = IsClientConnected();
            bool isInGame = ui != null && Convert.ToBoolean(
                _uiIsInGame.GetValue(ui, null), CultureInfo.InvariantCulture
            );
            if (player != null && isInGame)
                RememberCharacter(player);
            if (player != null && clientConnected && isInGame)
            {
                ResetCycle();
                _wasAuthorized = IsAuthorized(request);
                return;
            }

            bool authorized = IsAuthorized(request) && _lastCharacterUid.Length > 0;
            if (!authorized)
            {
                if (_wasAuthorized)
                    ResetCycle();
                _wasAuthorized = false;
                PlayerUpdatePatch.WriteReloginState(
                    "no_player", "DISABLED", 0,
                    request == null ? 5 : request.AutoReloginMaxAttempts,
                    _lastCharacterUid.Length == 0
                        ? "No previously connected character is available"
                        : "Bot heartbeat, --run, or F8 navigation is inactive",
                    _lastCharacterUid
                );
                return;
            }

            if (!_wasAuthorized)
            {
                ResetCycle();
                _wasAuthorized = true;
            }
            if (_missingSinceMilliseconds < 0)
                _missingSinceMilliseconds = now;

            long missingFor = now - _missingSinceMilliseconds;
            long grace = SecondsToMilliseconds(
                request.AutoReloginDisconnectGraceSeconds
            );
            if (missingFor < grace)
            {
                WriteStatus(
                    request, "relogin_waiting", "WAITING",
                    "Waiting for disconnect confirmation"
                );
                return;
            }

            bool builtinPending = Convert.ToBoolean(
                _hasPendingReconnect.GetValue(null, null),
                CultureInfo.InvariantCulture
            );
            long builtinDeadline = grace + SecondsToMilliseconds(
                request.AutoReloginBuiltinWaitMaxSeconds
            );
            if (builtinPending && missingFor < builtinDeadline)
            {
                WriteStatus(
                    request, "relogin_waiting", "WAITING",
                    "Waiting for the game's built-in reconnect"
                );
                return;
            }

            if (_attempts >= request.AutoReloginMaxAttempts
                && _attemptStartedMilliseconds < 0)
            {
                WriteStatus(
                    request, "relogin_paused", PausedState(request),
                    "Paused after maximum login attempts; toggle F8 or log in manually"
                );
                return;
            }

            if (_attemptStartedMilliseconds < 0)
            {
                if (_nextAttemptMilliseconds >= 0 && now < _nextAttemptMilliseconds)
                {
                    WriteStatus(
                        request, "relogin_waiting", "WAITING",
                        "Waiting before the next login attempt"
                    );
                    return;
                }
                StartAttempt(request, now);
            }

            TrySelectCharacter(request, now);
            if (_attemptStartedMilliseconds >= 0
                && now - _attemptStartedMilliseconds >= SecondsToMilliseconds(
                    request.AutoReloginAttemptTimeoutSeconds
                ))
            {
                FinishFailedAttempt(request, now, "Login attempt timed out");
            }
        }

        private static bool IsAuthorized(NavigationRequest request)
        {
            return request != null && request.BotActive
                && request.AutoReloginEnabled;
        }

        internal static bool IsClientConnected()
        {
            object tugboat = _appTugboat.GetValue(null, null);
            if (tugboat == null)
                return false;
            object state = _getConnectionState.Invoke(
                tugboat, new object[] { false }
            );
            return Convert.ToInt32(state, CultureInfo.InvariantCulture) == 8;
        }

        private static void RememberCharacter(object player)
        {
            object data = _playerCharacterData.GetValue(player, null);
            if (data == null)
                return;
            string uid = Convert.ToString(
                _characterUid.GetValue(data, null), CultureInfo.InvariantCulture
            );
            if (!string.IsNullOrEmpty(uid))
                _lastCharacterUid = uid;
        }

        private static void StartAttempt(NavigationRequest request, long now)
        {
            _attempts++;
            _attemptStartedMilliseconds = now;
            _nextAttemptMilliseconds = -1;
            _characterPlayInvoked = false;
            object ui = _appUi.GetValue(null, null);
            if (ui == null)
            {
                FinishFailedAttempt(request, now, "UI manager is unavailable");
                return;
            }

            _showLogin.Invoke(ui, null);
            object login = _getLoginScreen.Invoke(ui, null);
            if (login != null)
                _loginConnect.Invoke(login, null);
            WriteStatus(
                request, "relogin_connecting", "CONNECTING",
                "Connecting to the previous server"
            );
        }

        private static void TrySelectCharacter(NavigationRequest request, long now)
        {
            if (_attemptStartedMilliseconds < 0 || _characterPlayInvoked)
                return;
            object ui = _appUi.GetValue(null, null);
            if (ui == null)
                return;
            object screen = _getCharacterSelectScreen.Invoke(ui, null);
            if (screen == null || !IsActiveComponent(screen))
            {
                if (IsClientConnected())
                {
                    WriteStatus(
                        request,
                        "relogin_selecting_character",
                        "SELECTING CHARACTER",
                        "Waiting for the character selection screen"
                    );
                }
                return;
            }

            object characters = _characterSelectCharacters.GetValue(screen, null);
            int count = CollectionCount(characters);
            if (count <= 0)
            {
                WriteStatus(
                    request, "relogin_selecting_character", "SELECTING CHARACTER",
                    "Waiting for the character list"
                );
                return;
            }

            for (int index = 0; index < count; index++)
            {
                object character = CollectionItem(characters, index);
                string uid = character == null ? string.Empty : Convert.ToString(
                    _characterUid.GetValue(character, null), CultureInfo.InvariantCulture
                );
                if (uid == _lastCharacterUid)
                {
                    _playCharacter.Invoke(screen, new object[] { character });
                    _characterPlayInvoked = true;
                    WriteStatus(
                        request, "relogin_selecting_character",
                        "SELECTING CHARACTER", "Entering the previous character"
                    );
                    return;
                }
            }

            FinishFailedAttempt(
                request, now, "The previously connected character was not found"
            );
        }

        private static bool IsActiveComponent(object component)
        {
            object gameObject = _componentGameObject.GetValue(component, null);
            return gameObject != null && Convert.ToBoolean(
                _gameObjectActiveInHierarchy.GetValue(gameObject, null),
                CultureInfo.InvariantCulture
            );
        }

        private static int CollectionCount(object collection)
        {
            if (collection == null)
                return 0;
            PropertyInfo count = collection.GetType().GetProperty("Count");
            if (count == null)
                count = collection.GetType().GetProperty("Length");
            return count == null ? 0 : Convert.ToInt32(
                count.GetValue(collection, null), CultureInfo.InvariantCulture
            );
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = collection.GetType().GetProperty("Item");
            if (item == null)
                return null;
            return item.GetValue(collection, new object[] { index });
        }

        private static void FinishFailedAttempt(
            NavigationRequest request, long now, string message
        )
        {
            _attemptStartedMilliseconds = -1;
            _characterPlayInvoked = false;
            if (_attempts >= request.AutoReloginMaxAttempts)
            {
                _nextAttemptMilliseconds = -1;
                WriteStatus(request, "relogin_paused", PausedState(request), message);
                return;
            }
            _nextAttemptMilliseconds = now + SecondsToMilliseconds(
                request.AutoReloginRetryDelaySeconds
            );
            WriteStatus(request, "relogin_waiting", "WAITING", message);
        }

        private static void WriteStatus(
            NavigationRequest request,
            string status,
            string state,
            string message
        )
        {
            PlayerUpdatePatch.WriteReloginState(
                status, state, _attempts, request.AutoReloginMaxAttempts,
                message, _lastCharacterUid
            );
            LogState(state, message + " (" + _attempts.ToString(
                CultureInfo.InvariantCulture
            ) + "/" + request.AutoReloginMaxAttempts.ToString(
                CultureInfo.InvariantCulture
            ) + ")");
        }

        private static string PausedState(NavigationRequest request)
        {
            return "PAUSED AFTER " + request.AutoReloginMaxAttempts.ToString(
                CultureInfo.InvariantCulture
            ) + " ATTEMPTS";
        }

        private static void LogState(string state, string message)
        {
            string key = state + ":" + message;
            if (key == _lastLoggedState)
                return;
            _lastLoggedState = key;
            _log.LogInfo("Auto relogin " + state + ": " + message);
        }

        private static long SecondsToMilliseconds(float value)
        {
            return (long)(Math.Max(0f, value) * 1000f);
        }

        private static void ResetCycle()
        {
            _missingSinceMilliseconds = -1;
            _attemptStartedMilliseconds = -1;
            _nextAttemptMilliseconds = -1;
            _attempts = 0;
            _characterPlayInvoked = false;
            _lastLoggedState = string.Empty;
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException
                : error;
        }
    }

    internal sealed class VectorData
    {
        internal float X;
        internal float Y;
        internal float Z;

        internal VectorData(float x, float y, float z)
        {
            X = x;
            Y = y;
            Z = z;
        }
    }

    internal sealed class MonsterSnapshot
    {
        internal int ObjectId;
        internal string ConfigId;
        internal string DisplayName;
        internal string Rank;
        internal object PositionValue;
        internal VectorData Position;
        internal VectorData ViewportPosition;
        internal bool ViewportVisible;
        internal float HealthRatio;
        internal float ColliderRadius;
    }

    internal sealed class ObservedPlayerSnapshot
    {
        internal int ObjectId;
        internal string PlayerId;
        internal string DisplayName;
        internal object PositionValue;
        internal VectorData Position;
        internal float ColliderRadius;
        internal bool Alive;
        internal bool Visible;
        internal bool PartyMember;
        internal bool Selected;
    }

    internal sealed class PartyMemberSnapshot
    {
        internal string DisplayName;
        internal string PlayerId;
        internal int ObjectId;
        internal int MapId;
        internal string InstanceId;
        internal int ChannelIndex;
        internal bool IsLocal;
        internal object SourceValue;
    }

    internal sealed class ChannelSwitchSnapshot
    {
        internal long RequestId;
        internal string TargetPlayerId = string.Empty;
        internal int TargetMapId;
        internal string TargetInstanceId = string.Empty;
        internal int TargetChannelIndex = -1;
        internal string Status = "idle";
        internal string Error = string.Empty;
    }

    internal sealed class StatusEffectSnapshot
    {
        internal string Id = string.Empty;
        internal string DisplayName = string.Empty;
        internal string Category = string.Empty;
        internal float Duration;
        internal float DurationMax;
        internal int Level;
        internal int Stacks;
        internal int MaxStacks;
        internal bool InfiniteDuration;
        internal bool IsSkill;
        internal bool IsToggle;
    }

    internal sealed class StatusComponentSnapshot
    {
        internal bool Available;
        internal string Error = string.Empty;
        internal bool ActiveStatusesAvailable;
        internal string ActiveStatusesError = string.Empty;
        internal readonly List<string> ActiveStatusIds = new List<string>();
        internal readonly List<string> Buffs = new List<string>();
        internal readonly List<string> Debuffs = new List<string>();
        internal readonly List<StatusEffectSnapshot> Effects =
            new List<StatusEffectSnapshot>();
    }

    internal sealed class SummonDisplaySnapshot
    {
        internal string SkillId = string.Empty;
        internal string Id = string.Empty;
        internal int Level;
    }

    internal sealed class SummonDisplaysSnapshot
    {
        internal bool Available;
        internal string Error = string.Empty;
        internal readonly List<SummonDisplaySnapshot> Items =
            new List<SummonDisplaySnapshot>();
    }

    internal sealed class WalletCoinsSnapshot
    {
        internal bool Available;
        internal long Coins;
        internal string Error = string.Empty;
    }

    internal sealed class PlayerScanDiagnostics
    {
        internal string Source = "map";
        internal int MapCount;
        internal int SceneCount;
        internal int SourceCount;
        internal int Castable;
        internal int RejectedLocal;
        internal int RejectedInactive;
        internal int RejectedOtherMap;
        internal int RejectedInvalidObjectId;
        internal int RejectedDuplicate;
        internal int RejectedError;
        internal int Accepted;
        internal int SelectedObjectId;
        internal string SelectionSource = "none";
        internal string LastError = string.Empty;
    }

    internal sealed class LootSnapshot
    {
        internal int ObjectId;
        internal string ItemId;
        internal string DisplayName;
        internal string SpriteId;
        internal string Rarity;
        internal int RarityValue;
        internal string LootType;
        internal object PositionValue;
        internal VectorData Position;
        internal VectorData ViewportPosition;
        internal bool ViewportVisible;
        internal bool Locked;
        internal string OwnerPlayerId;
        internal int OwnerPartyId;
        internal bool OwnedByLocalPlayer;
        internal float InteractionRange;
    }

    internal sealed class CachedLootEntry
    {
        internal object SourceValue;
        internal LootSnapshot Snapshot;
        internal int SeenPass;
    }

    internal sealed class MapExitSnapshot
    {
        internal VectorData Position;
        internal float InteractionRange;
    }

    internal sealed class LootScanDiagnostics
    {
        internal string Source = "map";
        internal bool Active;
        internal bool Incremental = true;
        internal int MapCount;
        internal int SceneCount;
        internal int SourceCount;
        internal int BatchLimit;
        internal int Processed;
        internal int Cached;
        internal int Exported;
        internal bool PassCompleted;
        internal bool SceneFallbackDeferred;
        internal int RejectedInactive;
        internal int RejectedOtherMap;
        internal int RejectedNoData;
        internal int RejectedInvalidObjectId;
        internal int RejectedError;
        internal int Accepted;
        internal int AcceptedLocal;
        internal int AcceptedForeign;
        internal string LastError = string.Empty;
    }

    internal sealed class MonsterScanDiagnostics
    {
        internal string Source = "monsters";
        internal int MonstersCount;
        internal int UnitsCount;
        internal int SceneCount;
        internal string SceneStatus = "not_used";
        internal int SourceCount;
        internal int Castable;
        internal int RejectedNoNetworkObject;
        internal int RejectedOtherMap;
        internal int UnknownMapCandidates;
        internal int AcceptedByNavMesh;
        internal int RejectedNoNavMesh;
        internal string NavMeshFilterError = string.Empty;
        internal int RejectedTrainingDummy;
        internal int RejectedInactive;
        internal int RejectedNotDisplayed;
        internal int RejectedDead;
        internal int RejectedNoData;
        internal int RejectedNotEnemy;
        internal int Accepted;
        internal readonly List<int> TeamValues = new List<int>();
        internal readonly Dictionary<string, int> NetworkMapCounts =
            new Dictionary<string, int>();
    }

    internal static class PlayerUpdatePatch
    {
        private const long NavigationUpdateIntervalMilliseconds = 250;
        private const long GeneralUpdateIntervalMilliseconds = 400;
        private const long PlayerSafetyUpdateIntervalMilliseconds = 25;
        private const int LootScanBatchSize = 24;
        private const int LootScanMinimumBatchSize = 4;
        private const long LootScanBudgetMilliseconds = 2;
        private const int LootCacheLimit = 384;
        private const int LootExportLimit = 96;
        private const long LootSceneFallbackIntervalMilliseconds = 10000;
        private const float NearbyLootExportRadiusSquared = 36f;
        private const long RequestMaxAgeMilliseconds = 2000;
        private const long ErrorLogIntervalMilliseconds = 5000;
        private const int EnemyCombatTeamValue = 1;
        private const int FileOperationAttempts = 5;

        private static readonly Stopwatch Timer = Stopwatch.StartNew();
        private static readonly Regex RequestIdPattern = new Regex(
            "\\\"request_id\\\"\\s*:\\s*(-?[0-9]+)", RegexOptions.Compiled
        );
        private static readonly Regex TargetIdPattern = new Regex(
            "\\\"target_object_id\\\"\\s*:\\s*(-?[0-9]+)", RegexOptions.Compiled
        );
        private static readonly Regex TargetKindPattern = new Regex(
            "\\\"target_kind\\\"\\s*:\\s*\\\"(none|monster|loot|player)\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex FollowChannelRequestIdPattern = new Regex(
            "\\\"follow_channel_request_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex ChannelSwitchRequestIdPattern = new Regex(
            "\\\"channel_switch_request_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex ChannelSwitchIndexPattern = new Regex(
            "\\\"channel_switch_index\\\"\\s*:\\s*(-?[0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex ConsumableUseRequestIdPattern = new Regex(
            "\\\"consumable_use_request_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex ConsumableNamePattern = new Regex(
            "\\\"consumable_name\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\"",
            RegexOptions.Compiled
        );
        private static readonly Regex FollowPlayerIdPattern = new Regex(
            "\\\"follow_player_id\\\"\\s*:\\s*\\\"((?:\\\\.|[^\\\"\\\\])*)\\\"",
            RegexOptions.Compiled
        );
        private static readonly Regex TimestampPattern = new Regex(
            "\\\"timestamp_ms\\\"\\s*:\\s*(-?[0-9]+)", RegexOptions.Compiled
        );
        private static readonly Regex BotActivePattern = new Regex(
            "\\\"bot_active\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex MovementKeysPattern = new Regex(
            "\\\"movement_keys\\\"\\s*:\\s*\\\"([wasd]*)\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex ShiftKeysPattern = new Regex(
            "\\\"shift_keys\\\"\\s*:\\s*\\\""
                + "(lshift|rshift|lshift,rshift|rshift,lshift)?\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex SummonActionPattern = new Regex(
            "\\\"summon_action\\\"\\s*:\\s*\\\""
                + "(reanimation|mount)?\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex SkillKeyRequestIdPattern = new Regex(
            "\\\"skill_key_request_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex SkillKeyPattern = new Regex(
            "\\\"skill_key\\\"\\s*:\\s*\\\"(numpad[0-9])?\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex SkillKeyTargetSummonPattern = new Regex(
            "\\\"skill_key_target_summon\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex LootInteractPattern = new Regex(
            "\\\"loot_interact\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex LootInteractObjectIdPattern = new Regex(
            "\\\"loot_interact_object_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex FocusTargetIdPattern = new Regex(
            "\\\"focus_target_object_id\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );
        private static readonly Regex FocusTargetWorldPattern = new Regex(
            "\\\"focus_target_world\\\"\\s*:\\s*\\[\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\\s*,\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\\s*,\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?(?:[eE][+-]?[0-9]+)?)\\s*\\]",
            RegexOptions.Compiled
        );
        private static readonly Regex MovementVectorPattern = new Regex(
            "\\\"movement_world\\\"\\s*:\\s*\\[\\s*(-?[0-9]+)\\s*,"
                + "\\s*(-?[0-9]+)\\s*,\\s*(-?[0-9]+)\\s*\\]",
            RegexOptions.Compiled
        );
        private static readonly Regex BackgroundInputModePattern = new Regex(
            "\\\"background_input_mode\\\"\\s*:\\s*"
                + "\\\"(inputs|both|apply|send|send_apply|send_process)\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex BackgroundSkillModePattern = new Regex(
            "\\\"background_skill_mode\\\"\\s*:\\s*"
                + "\\\"(capture|process|click|process_click)\\\"",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex ProbeActivePattern = new Regex(
            "\\\"probe_active\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex LootScanActivePattern = new Regex(
            "\\\"loot_scan_active\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex PartyFollowActivePattern = new Regex(
            "\\\"party_follow_active\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex AutoReloginEnabledPattern = new Regex(
            "\\\"auto_relogin_enabled\\\"\\s*:\\s*(true|false)",
            RegexOptions.Compiled | RegexOptions.IgnoreCase
        );
        private static readonly Regex ReloginDisconnectGracePattern = new Regex(
            "\\\"auto_relogin_disconnect_grace_sec\\\"\\s*:\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?)",
            RegexOptions.Compiled
        );
        private static readonly Regex ReloginBuiltinWaitPattern = new Regex(
            "\\\"auto_relogin_builtin_wait_max_sec\\\"\\s*:\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?)",
            RegexOptions.Compiled
        );
        private static readonly Regex ReloginAttemptTimeoutPattern = new Regex(
            "\\\"auto_relogin_attempt_timeout_sec\\\"\\s*:\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?)",
            RegexOptions.Compiled
        );
        private static readonly Regex ReloginRetryDelayPattern = new Regex(
            "\\\"auto_relogin_retry_delay_sec\\\"\\s*:\\s*"
                + "(-?[0-9]+(?:\\.[0-9]+)?)",
            RegexOptions.Compiled
        );
        private static readonly Regex ReloginMaxAttemptsPattern = new Regex(
            "\\\"auto_relogin_max_attempts\\\"\\s*:\\s*([0-9]+)",
            RegexOptions.Compiled
        );

        private static ManualLogSource _log;
        private static long _lastNavigationUpdateMilliseconds;
        private static long _lastGeneralUpdateMilliseconds;
        private static long _lastPlayerSafetyUpdateMilliseconds;
        private static long _lastErrorLogMilliseconds;
        private static bool _probeActive;
        private static NavigationRequest _cachedRequest;
        private static bool _localPlayerAliveKnown;
        private static bool _localPlayerAlive;
        private static bool _generalSnapshotReady;
        private static long _generalSnapshotMapId = long.MinValue;
        private static long _generalSnapshotInstanceId = long.MinValue;
        private static bool _generalSnapshotPartyFollowActive;
        private static string _generalSnapshotFollowPlayerId = string.Empty;
        private static List<ObservedPlayerSnapshot> _cachedPlayers =
            new List<ObservedPlayerSnapshot>();
        private static List<PartyMemberSnapshot> _cachedPartyMembers =
            new List<PartyMemberSnapshot>();
        private static PlayerScanDiagnostics _cachedPlayerScan =
            new PlayerScanDiagnostics();
        private static List<LootSnapshot> _cachedLoots = new List<LootSnapshot>();
        private static LootScanDiagnostics _cachedLootScan =
            new LootScanDiagnostics();
        private static readonly Dictionary<int, CachedLootEntry> _lootCache =
            new Dictionary<int, CachedLootEntry>();
        private static readonly List<object> _trackedLoots = new List<object>();
        private static bool _lootLifecycleTrackingAvailable;
        private static int _lootScanCursor;
        private static int _lootScanPass = 1;
        private static string _lootScanSource = string.Empty;
        private static long _lootCacheMapId = long.MinValue;
        private static long _lootCacheInstanceId = long.MinValue;
        private static long _lootSceneSeedMapId = long.MinValue;
        private static long _lootSceneSeedInstanceId = long.MinValue;
        private static long _lastLootSceneFallbackMilliseconds =
            -LootSceneFallbackIntervalMilliseconds;
        private static List<MapExitSnapshot> _cachedMapExits =
            new List<MapExitSnapshot>();
        private static bool _mapExitCacheReady;
        private static long _mapExitCacheMapId = long.MinValue;
        private static long _mapExitCacheInstanceId = long.MinValue;
        private static readonly object StateWriterLock = new object();
        private static string _pendingStateContents;
        private static bool _stateWriterScheduled;
        private static long _lastFollowChannelRequestId;
        private static ChannelSwitchSnapshot _channelSwitch =
            new ChannelSwitchSnapshot();

        private static Type _appType;
        private static Type _playerType;
        private static Type _monsterType;
        private static Type _lootType;
        private static Type _mapExitType;
        private static Type _navMeshType;
        private static Type _navMeshPathType;
        private static PropertyInfo _appPlayer;
        private static PropertyInfo _appGame;
        private static PropertyInfo _appCamera;
        private static PropertyInfo _appUi;
        private static PropertyInfo _gameMap;
        private static PropertyInfo _uiGame;
        private static PropertyInfo _uiGameTarget;
        private static PropertyInfo _networkObject;
        private static PropertyInfo _networkMapId;
        private static PropertyInfo _networkInstanceId;
        private static MethodInfo _mapGet;
        private static PropertyInfo _mapId;
        private static PropertyInfo _instanceId;
        private static PropertyInfo _players;
        private static PropertyInfo _monsters;
        private static PropertyInfo _units;
        private static PropertyInfo _loots;
        private static PropertyInfo _position;
        private static PropertyInfo _isActive;
        private static PropertyInfo _isAliveAndDisplayed;
        private static PropertyInfo _health;
        private static PropertyInfo _collider;
        private static PropertyInfo _defaultColliderRadius;
        private static PropertyInfo _displayName;
        private static PropertyInfo _objectId;
        private static PropertyInfo _playerId;
        private static PropertyInfo _playerCharacterData;
        private static PropertyInfo _characterName;
        private static PropertyInfo _playerSave;
        private static PropertyInfo _savePlayerData;
        private static PropertyInfo _playerDataCoins;
        private static PropertyInfo _playerCurrentParty;
        private static PropertyInfo _partyMembers;
        private static PropertyInfo _partyMemberDisplayName;
        private static PropertyInfo _partyMemberPlayerId;
        private static PropertyInfo _partyMemberObjectId;
        private static PropertyInfo _partyMemberMapId;
        private static PropertyInfo _partyMemberInstanceId;
        private static PropertyInfo _partyMemberChannelIndex;
        private static PropertyInfo _partyMemberCachedPlayer;
        private static MethodInfo _partyMemberGetPlayer;
        private static PropertyInfo _playerSummoning;
        private static PropertyInfo _unitSummoning;
        private static PropertyInfo _summonOwner;
        private static PropertyInfo _mountController;
        private static PropertyInfo _summonIsMountable;
        private static PropertyInfo _summonActiveSummons;
        private static PropertyInfo _summonPrimary;
        private static PropertyInfo _summonId;
        private static PropertyInfo _summonMountId;
        private static PropertyInfo _summonMountedSummonId;
        private static PropertyInfo _summonIsMounting;
        private static PropertyInfo _summonDisplays;
        private static PropertyInfo _summonDisplaySkillId;
        private static PropertyInfo _summonDisplayId;
        private static PropertyInfo _summonDisplayLevel;
        private static PropertyInfo _playerStatus;
        private static PropertyInfo _statusBuffs;
        private static PropertyInfo _statusDebuffs;
        private static PropertyInfo _statusEffects;
        private static PropertyInfo _statusDisplays;
        private static PropertyInfo _statusEffectId;
        private static PropertyInfo _statusEffectConfig;
        private static PropertyInfo _statusEffectDuration;
        private static PropertyInfo _statusEffectDurationMax;
        private static PropertyInfo _statusEffectLevel;
        private static PropertyInfo _statusEffectStacks;
        private static PropertyInfo _statusEffectMaxStacks;
        private static PropertyInfo _statusEffectInfiniteDuration;
        private static PropertyInfo _statusEffectIsSkill;
        private static PropertyInfo _statusEffectIsToggle;
        private static PropertyInfo _statusConfigDisplayName;
        private static PropertyInfo _statusConfigCategory;
        private static PropertyInfo _isTrainingDummy;
        private static PropertyInfo _monsterData;
        private static PropertyInfo _configId;
        private static PropertyInfo _monsterRank;
        private static PropertyInfo _syncVarValue;
        private static PropertyInfo _monsterTeam;
        private static PropertyInfo _monsterId;
        private static PropertyInfo _healthIsAlive;
        private static PropertyInfo _healthRatio;
        private static PropertyInfo _camera;
        private static PropertyInfo _componentTransform;
        private static PropertyInfo _componentGameObject;
        private static PropertyInfo _gameObjectActiveInHierarchy;
        private static PropertyInfo _transformPosition;
        private static PropertyInfo _transformForward;
        private static PropertyInfo _transformRight;
        private static PropertyInfo _transformLossyScale;
        private static PropertyInfo _capsuleRadius;
        private static PropertyInfo _colliderBounds;
        private static PropertyInfo _boundsCenter;
        private static PropertyInfo _lootDto;
        private static PropertyInfo _lootDtoValue;
        private static PropertyInfo _lootDisplayName;
        private static PropertyInfo _lootInteractionRange;
        private static PropertyInfo _mapExitInteractionRange;
        private static PropertyInfo _lootLock;
        private static PropertyInfo _lootLockValue;
        private static PropertyInfo _lockPlayerId;
        private static PropertyInfo _lockPartyId;
        private static PropertyInfo _lootDtoDisplayName;
        private static PropertyInfo _lootDtoSpriteId;
        private static PropertyInfo _lootDtoRarity;
        private static PropertyInfo _lootDtoType;
        private static MethodInfo _lootIsLocked;
        private static MethodInfo _worldToViewportPoint;
        private static MethodInfo _playerIsInMyParty;
        private static MethodInfo _playerRequestChannelSwitch;
        private static MethodInfo _playerTrySwitchToInstance;
        private static MethodInfo _playerSendChannelList;
        private static long _lastChannelSwitchRequestId;
        private static long _lastChannelListRequestTicks;
        private static MethodInfo _tryCastPlayer;
        private static MethodInfo _tryCastMonster;
        private static MethodInfo _findScenePlayers;
        private static MethodInfo _findSceneMonsters;
        private static MethodInfo _findSceneLoots;
        private static MethodInfo _findSceneMapExits;
        private static object _findObjectsSortNone;
        private static string _sceneScanInitializationError;
        private static MethodInfo _calculatePath;
        private static PropertyInfo _pathStatus;
        private static PropertyInfo _pathCorners;
        private static MethodInfo _clearCorners;
        private static object _navPath;
        private static object _filterNavPath;
        private static int _allAreas;
        internal static Type FindLoadedType(string fullName)
        {
            Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
            for (int index = 0; index < assemblies.Length; index++)
            {
                Type type = assemblies[index].GetType(fullName, false);
                if (type != null)
                    return type;
            }
            if (fullName.StartsWith("UnityEngine.AI.", StringComparison.Ordinal))
            {
                try
                {
                    Assembly aiModule = Assembly.Load("UnityEngine.AIModule");
                    Type aiType = aiModule.GetType(fullName, false);
                    if (aiType != null)
                        return aiType;
                }
                catch
                {
                    // The final TypeLoadException below includes the exact type.
                }
            }
            throw new TypeLoadException("Loaded type not found: " + fullName);
        }

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            _appType = FindLoadedType("App");
            Type gameType = FindLoadedType("Game");
            Type mapManagerType = FindLoadedType("MapManager");
            Type mapInstanceType = FindLoadedType("MapInstance");
            Type baseUnitType = FindLoadedType("BaseUnitController");
            Type partyType = FindLoadedType("Party");
            Type partyMemberType = FindLoadedType("PartyMember");
            _playerType = FindLoadedType("PlayerController");
            _monsterType = FindLoadedType("MonsterController");
            _lootType = FindLoadedType("LootDrop");
            _mapExitType = FindLoadedType("MapExit");
            Type monsterDtoType = FindLoadedType("MonsterDto");
            Type lootDtoType = FindLoadedType("LootDropDto");
            Type lockDtoType = FindLoadedType("LockDto");
            Type healthType = FindLoadedType("HealthComponent");
            Type summoningType = FindLoadedType("SummoningComponent");
            Type summonSkillDataType = FindLoadedType(
                "SummoningComponent+SummonSkillData"
            );
            Type statusComponentType = FindLoadedType("StatusComponent");
            Type statusEffectStateType = FindLoadedType("StatusEffectState");
            Type statusConfigType = FindLoadedType("StatusConfig");
            Type cameraControllerType = FindLoadedType("CameraController");
            Type uiManagerType = FindLoadedType("UIManager");
            Type uiGameType = FindLoadedType("UIGame");
            Type componentType = FindLoadedType("UnityEngine.Component");
            Type gameObjectType = FindLoadedType("UnityEngine.GameObject");
            Type transformType = FindLoadedType("UnityEngine.Transform");
            Type capsuleType = FindLoadedType("UnityEngine.CapsuleCollider");
            Type objectBaseType = FindLoadedType(
                "Il2CppInterop.Runtime.InteropTypes.Il2CppObjectBase"
            );
            _navMeshType = FindLoadedType("UnityEngine.AI.NavMesh");
            _navMeshPathType = FindLoadedType("UnityEngine.AI.NavMeshPath");

            _appPlayer = RequireProperty(_appType, "Player");
            _appGame = RequireProperty(_appType, "Game");
            _appCamera = RequireProperty(_appType, "Camera");
            _appUi = RequireProperty(_appType, "UI");
            _gameMap = RequireProperty(gameType, "Map");
            _uiGame = RequireProperty(uiManagerType, "Game");
            _uiGameTarget = RequireProperty(uiGameType, "Target");
            _networkObject = RequireProperty(_playerType, "NetworkObject");
            _networkMapId = RequireProperty(_networkObject.PropertyType, "MapId");
            _networkInstanceId = RequireProperty(
                _networkObject.PropertyType, "InstanceId"
            );
            _mapGet = RequireMethod(mapManagerType, "Get", 1);
            _mapId = RequireProperty(mapInstanceType, "MapId");
            _instanceId = RequireProperty(mapInstanceType, "InstanceId");
            _players = RequireProperty(mapInstanceType, "Players");
            _monsters = RequireProperty(mapInstanceType, "Monsters");
            _units = RequireProperty(mapInstanceType, "Units");
            _loots = RequireProperty(mapInstanceType, "Loots");
            _position = RequireProperty(baseUnitType, "Position");
            _isActive = RequireProperty(baseUnitType, "IsActive");
            _isAliveAndDisplayed = RequireProperty(baseUnitType, "IsAliveAndDisplayed");
            _health = RequireProperty(baseUnitType, "Health");
            _collider = RequireProperty(baseUnitType, "Collider");
            _defaultColliderRadius = RequireProperty(baseUnitType, "DefaultColliderRadius");
            _displayName = RequireProperty(baseUnitType, "DisplayName");
            _objectId = RequireProperty(_playerType, "ObjectId");
            _playerId = RequireProperty(_playerType, "PlayerId");
            _playerCharacterData = RequireProperty(_playerType, "CharacterData");
            _characterName = RequireProperty(
                _playerCharacterData.PropertyType, "Name"
            );
            try
            {
                _playerSave = RequireProperty(_playerType, "Save");
                _savePlayerData = RequireProperty(
                    _playerSave.PropertyType, "PlayerData"
                );
                _playerDataCoins = RequireProperty(
                    _savePlayerData.PropertyType, "Coins"
                );
            }
            catch (Exception error)
            {
                _playerSave = null;
                _savePlayerData = null;
                _playerDataCoins = null;
                _log.LogWarning(
                    "PlayerData.Coins unavailable; navigation earnings disabled: "
                    + error.GetType().Name + ": " + error.Message
                );
            }
            _playerCurrentParty = RequireProperty(_playerType, "CurrentParty");
            _partyMembers = RequireProperty(partyType, "Members");
            _partyMemberDisplayName = RequireProperty(
                partyMemberType, "DisplayName"
            );
            _partyMemberPlayerId = RequireProperty(partyMemberType, "PlayerId");
            _partyMemberObjectId = RequireProperty(partyMemberType, "ObjectId");
            _partyMemberMapId = RequireProperty(partyMemberType, "MapId");
            _partyMemberInstanceId = RequireProperty(
                partyMemberType, "InstanceId"
            );
            _partyMemberChannelIndex = RequireProperty(
                partyMemberType, "ChannelIndex"
            );
            _partyMemberCachedPlayer = RequireProperty(
                partyMemberType, "CachedPlayer"
            );
            _partyMemberGetPlayer = RequireMethod(partyMemberType, "GetPlayer", 0);
            _playerSummoning = RequireProperty(_playerType, "Summoning");
            _unitSummoning = RequireProperty(baseUnitType, "Summoning");
            _summonOwner = RequireProperty(summoningType, "Summoner");
            _mountController = RequireProperty(
                summoningType, "MountController_C"
            );
            _summonIsMountable = RequireProperty(
                summoningType, "IsMountableSummon"
            );
            _summonActiveSummons = RequireProperty(
                summoningType, "ActiveSummons"
            );
            _summonPrimary = RequireProperty(summoningType, "Primary");
            _summonId = RequireProperty(summoningType, "SummonId");
            _summonMountId = RequireProperty(summoningType, "MountId");
            _summonMountedSummonId = RequireProperty(
                summoningType, "MountedSummonId"
            );
            _summonIsMounting = RequireProperty(summoningType, "IsMounting");
            _summonDisplays = RequireProperty(summoningType, "SummonDisplays_C");
            _summonDisplaySkillId = RequireProperty(
                summonSkillDataType, "SkillId"
            );
            _summonDisplayId = RequireProperty(summonSkillDataType, "Id");
            _summonDisplayLevel = RequireProperty(summonSkillDataType, "Level");
            _playerStatus = RequireProperty(_playerType, "Status");
            _statusBuffs = RequireProperty(statusComponentType, "Buffs");
            _statusDebuffs = RequireProperty(statusComponentType, "Debuffs");
            _statusEffects = RequireProperty(statusComponentType, "Effects");
            try
            {
                _statusDisplays = RequireProperty(
                    statusComponentType, "StatusDisplays_C"
                );
            }
            catch (Exception error)
            {
                _statusDisplays = null;
                _log.LogWarning(
                    "StatusDisplays_C unavailable; active status checks disabled: "
                    + error.GetType().Name + ": " + error.Message
                );
            }
            _statusEffectId = RequireProperty(statusEffectStateType, "Id");
            _statusEffectConfig = RequireProperty(statusEffectStateType, "Config");
            _statusEffectDuration = RequireProperty(
                statusEffectStateType, "Duration"
            );
            _statusEffectDurationMax = RequireProperty(
                statusEffectStateType, "DurationMax"
            );
            _statusEffectLevel = RequireProperty(statusEffectStateType, "Level");
            _statusEffectStacks = RequireProperty(statusEffectStateType, "Stacks");
            _statusEffectMaxStacks = RequireProperty(
                statusEffectStateType, "MaxStacks"
            );
            _statusEffectInfiniteDuration = RequireProperty(
                statusEffectStateType, "InfiniteDuration"
            );
            _statusEffectIsSkill = RequireProperty(
                statusEffectStateType, "IsSkill"
            );
            _statusEffectIsToggle = RequireProperty(
                statusEffectStateType, "IsToggle"
            );
            _statusConfigDisplayName = RequireProperty(
                statusConfigType, "DisplayName"
            );
            _statusConfigCategory = RequireProperty(statusConfigType, "Category");
            _playerIsInMyParty = RequireMethod(_playerType, "IsInMyParty", 1);
            _playerRequestChannelSwitch = RequireMethod(
                _playerType, "RequestChannelSwitch", 1
            );
            _playerTrySwitchToInstance = RequireMethod(
                _playerType, "TrySwitchToInstance", 1
            );
            try
            {
                _playerSendChannelList = RequireMethod(
                    _playerType, "SendChannelList", 0
                );
            }
            catch (Exception error)
            {
                _playerSendChannelList = null;
                _log.LogWarning(
                    "SendChannelList unavailable; channel data will only "
                    + "populate after a manual channel switch: "
                    + error.GetType().Name + ": " + error.Message
                );
            }
            _isTrainingDummy = RequireProperty(_monsterType, "IsTrainingDummy");
            _monsterData = RequireProperty(_monsterType, "Data");
            _configId = RequireProperty(_monsterType, "ConfigId");
            _monsterRank = RequireProperty(_monsterType, "MonsterRank");
            _syncVarValue = RequireProperty(_monsterData.PropertyType, "Value");
            _monsterTeam = RequireProperty(monsterDtoType, "Team");
            _monsterId = RequireProperty(monsterDtoType, "Id");
            _healthIsAlive = RequireProperty(healthType, "IsAlive");
            _healthRatio = RequireProperty(healthType, "HealthNormalised");
            _camera = RequireProperty(cameraControllerType, "cam");
            _componentTransform = RequireProperty(componentType, "transform");
            _componentGameObject = RequireProperty(componentType, "gameObject");
            _gameObjectActiveInHierarchy = RequireProperty(
                gameObjectType, "activeInHierarchy"
            );
            _transformPosition = RequireProperty(transformType, "position");
            _transformForward = RequireProperty(transformType, "forward");
            _transformRight = RequireProperty(transformType, "right");
            _transformLossyScale = RequireProperty(transformType, "lossyScale");
            _capsuleRadius = RequireProperty(capsuleType, "radius");
            try
            {
                _colliderBounds = RequireProperty(capsuleType, "bounds");
                _boundsCenter = RequireProperty(
                    _colliderBounds.PropertyType, "center"
                );
            }
            catch (Exception error)
            {
                _colliderBounds = null;
                _boundsCenter = null;
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Monster cursor projection will use unit positions: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            _lootDto = RequireProperty(_lootType, "Dto");
            _lootDtoValue = RequireProperty(_lootDto.PropertyType, "Value");
            _lootDisplayName = RequireProperty(_lootType, "DisplayName");
            _lootInteractionRange = RequireProperty(_lootType, "InteractionRange");
            _mapExitInteractionRange = RequireProperty(
                _mapExitType, "InteractionRange"
            );
            _lootLock = RequireProperty(_lootType, "Lock");
            _lootLockValue = RequireProperty(_lootLock.PropertyType, "Value");
            _lockPlayerId = RequireProperty(lockDtoType, "PlayerId");
            _lockPartyId = RequireProperty(lockDtoType, "PartyId");
            _lootDtoDisplayName = RequireProperty(lootDtoType, "DisplayName");
            _lootDtoSpriteId = RequireProperty(lootDtoType, "SpriteId");
            _lootDtoRarity = RequireProperty(lootDtoType, "Rarity");
            _lootDtoType = RequireProperty(lootDtoType, "LootType");
            _lootIsLocked = RequireMethod(lockDtoType, "IsLocked", 1);
            // Loot pickup is driven by injecting the game's Pickup action hotkey
            // through the input path (see BackgroundMovementPatch), so no
            // LootDrop/PlayerController pickup methods are resolved here.
            _worldToViewportPoint = RequireMethod(_camera.PropertyType,
                "WorldToViewportPoint", 1);

            MethodInfo tryCast = RequireGenericMethod(objectBaseType, "TryCast", 0);
            _tryCastPlayer = tryCast.MakeGenericMethod(_playerType);
            _tryCastMonster = tryCast.MakeGenericMethod(_monsterType);
            try
            {
                Type unityObjectType = FindLoadedType("UnityEngine.Object");
                Type findObjectsSortModeType = FindLoadedType(
                    "UnityEngine.FindObjectsSortMode"
                );
                MethodInfo findObjectsByType = RequireGenericMethod(
                    unityObjectType, "FindObjectsByType", 1
                );
                _findSceneMonsters = findObjectsByType.MakeGenericMethod(
                    _monsterType
                );
                _findScenePlayers = findObjectsByType.MakeGenericMethod(_playerType);
                _findSceneLoots = findObjectsByType.MakeGenericMethod(_lootType);
                _findSceneMapExits = findObjectsByType.MakeGenericMethod(
                    _mapExitType
                );
                _findObjectsSortNone = Enum.ToObject(findObjectsSortModeType, 0);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                _sceneScanInitializationError = actual.GetType().Name
                    + ": " + actual.Message;
                log.LogWarning(
                    "Unity scene monster scanner disabled: "
                    + _sceneScanInitializationError
                );
            }

            _calculatePath = RequireMethod(_navMeshType, "CalculatePath", 4);
            _allAreas = Convert.ToInt32(
                _navMeshType.GetField("AllAreas", BindingFlags.Public | BindingFlags.Static)
                    .GetValue(null),
                CultureInfo.InvariantCulture
            );
            _pathStatus = RequireProperty(_navMeshPathType, "status");
            _pathCorners = RequireProperty(_navMeshPathType, "corners");
            _clearCorners = RequireMethod(_navMeshPathType, "ClearCorners", 0);
            _navPath = Activator.CreateInstance(_navMeshPathType);
            _filterNavPath = Activator.CreateInstance(_navMeshPathType);

            try
            {
                ConsumableUseService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                ConsumableUseService.SetUnavailable(actual);
                log.LogWarning(
                    "Consumable-use navigation IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                EquipmentDisplayStatService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Equipment display stat conversion disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                AuctionQueryService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Auction query IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                CardPurchaseService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Card purchase IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                InventoryExportService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Inventory equipment export IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                InventoryDismantleService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Inventory dismantle IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
            try
            {
                EquipmentFavoriteService.Initialize(log);
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                log.LogWarning(
                    "Equipped favorite IPC disabled: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
        }

        internal static void SetLootLifecycleTrackingAvailable(bool available)
        {
            _lootLifecycleTrackingAvailable = available;
        }

        internal static void TrackLoot(object loot)
        {
            if (loot == null || _lootType == null || !_lootType.IsInstanceOfType(loot))
                return;
            for (int index = 0; index < _trackedLoots.Count; index++)
            {
                if (object.ReferenceEquals(_trackedLoots[index], loot))
                    return;
            }
            _trackedLoots.Add(loot);
        }

        internal static void ForgetLoot(object loot)
        {
            if (loot == null)
                return;
            for (int index = _trackedLoots.Count - 1; index >= 0; index--)
            {
                if (object.ReferenceEquals(_trackedLoots[index], loot))
                    _trackedLoots.RemoveAt(index);
            }
            try
            {
                int objectId = Convert.ToInt32(
                    _objectId.GetValue(loot, null), CultureInfo.InvariantCulture
                );
                if (objectId > 0)
                    RemoveLootFromCaches(objectId);
            }
            catch
            {
                // A despawning IL2CPP object may already have lost its native body.
            }
        }

        private static PropertyInfo RequireProperty(Type type, string name)
        {
            PropertyInfo property = type.GetProperty(
                name,
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            if (property == null)
                throw new MissingMemberException(type.FullName, name);
            return property;
        }

        private static MethodInfo RequireMethod(Type type, string name, int parameterCount)
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static MethodInfo RequireGenericMethod(
            Type type,
            string name,
            int parameterCount
        )
        {
            MethodInfo[] methods = type.GetMethods(
                BindingFlags.Public | BindingFlags.NonPublic
                    | BindingFlags.Instance | BindingFlags.Static
                    | BindingFlags.FlattenHierarchy
            );
            for (int index = 0; index < methods.Length; index++)
            {
                if (methods[index].Name == name
                    && methods[index].IsGenericMethodDefinition
                    && methods[index].GetParameters().Length == parameterCount)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name);
        }

        private static void Postfix()
        {
            long elapsed = Timer.ElapsedMilliseconds;
            bool navigationDue = elapsed - _lastNavigationUpdateMilliseconds
                >= NavigationUpdateIntervalMilliseconds;
            bool generalDue = elapsed - _lastGeneralUpdateMilliseconds
                >= GeneralUpdateIntervalMilliseconds;
            bool playerSafetyDue = _probeActive
                && elapsed - _lastPlayerSafetyUpdateMilliseconds
                    >= PlayerSafetyUpdateIntervalMilliseconds;
            if (!navigationDue && !generalDue && !playerSafetyDue)
                return;
            if (navigationDue)
                _lastNavigationUpdateMilliseconds = elapsed;
            if (generalDue)
                _lastGeneralUpdateMilliseconds = elapsed;
            if (playerSafetyDue)
                _lastPlayerSafetyUpdateMilliseconds = elapsed;

            try
            {
                if (navigationDue)
                {
                    _cachedRequest = ReadRequest(
                        DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                    );
                    _probeActive = _cachedRequest != null
                        && (_cachedRequest.ProbeActive
                            || _cachedRequest.PartyFollowActive);
                    if (!_probeActive)
                        _localPlayerAliveKnown = false;
                }
                if (!ReconnectPatch.IsClientConnected())
                {
                    _localPlayerAliveKnown = false;
                    return;
                }
                object player = _appPlayer.GetValue(null, null);
                if (player == null)
                {
                    _localPlayerAliveKnown = false;
                    return;
                }
                bool playerAlive = ReadPlayerAlive(player);
                bool deathTransition = !playerAlive
                    && (!_localPlayerAliveKnown || _localPlayerAlive);
                _localPlayerAliveKnown = true;
                _localPlayerAlive = playerAlive;
                if (navigationDue)
                    ConsumableUseService.Tick(
                        player, _cachedRequest, playerAlive
                    );
                if (!navigationDue && !generalDue && !deathTransition)
                    return;
                if (generalDue)
                {
                    AuctionQueryService.Tick(player, elapsed);
                    CardPurchaseService.Tick(player, elapsed);
                    InventoryExportService.Tick(player);
                    InventoryDismantleService.Tick(player, elapsed);
                    EquipmentFavoriteService.Tick(player, elapsed);
                }
                if (!_probeActive)
                    return;
                if (navigationDue || deathTransition)
                {
                    WriteSnapshot(player, generalDue, _cachedRequest);
                }
                else if (generalDue)
                {
                    RefreshGeneralSnapshot(player, _cachedRequest);
                }
            }
            catch (Exception error)
            {
                TryWriteError(Unwrap(error));
                if (elapsed - _lastErrorLogMilliseconds >= ErrorLogIntervalMilliseconds)
                {
                    _lastErrorLogMilliseconds = elapsed;
                    Exception actual = Unwrap(error);
                    _log.LogWarning(
                        "Memory navigation snapshot failed: "
                        + actual.GetType().Name + ": " + actual.Message
                    );
                }
            }
        }

        private static Exception Unwrap(Exception error)
        {
            TargetInvocationException invocation = error as TargetInvocationException;
            return invocation != null && invocation.InnerException != null
                ? invocation.InnerException
                : error;
        }

        private static object CurrentMapInstance(object player)
        {
            object networkObject = _networkObject.GetValue(player, null);
            object game = _appGame.GetValue(null, null);
            object mapManager = game == null ? null : _gameMap.GetValue(game, null);
            return mapManager == null || networkObject == null
                ? null
                : _mapGet.Invoke(mapManager, new object[] { networkObject });
        }

        internal static object FindEnemyUnitByObjectId(int objectId)
        {
            if (objectId <= 0)
                return null;
            object player = _appPlayer.GetValue(null, null);
            object mapInstance = player == null
                ? null : CurrentMapInstance(player);
            if (mapInstance != null)
            {
                object match = FindEnemyUnitInCollection(
                    _monsters.GetValue(mapInstance, null), objectId
                );
                if (match != null)
                    return match;
                match = FindEnemyUnitInCollection(
                    _units.GetValue(mapInstance, null), objectId
                );
                if (match != null)
                    return match;
            }
            if (_findSceneMonsters == null)
                return null;
            object sceneMonsters = _findSceneMonsters.Invoke(
                null, new object[] { _findObjectsSortNone }
            );
            return FindEnemyUnitInCollection(sceneMonsters, objectId);
        }

        internal static object GetUnitPositionValue(object unit)
        {
            return unit == null ? null : _position.GetValue(unit, null);
        }

        internal static object GetUnitAimPositionValue(object unit)
        {
            if (unit == null)
                return null;
            object position = GetUnitPositionValue(unit);
            return MonsterAimPosition(unit, position);
        }

        internal static VectorData GetUnitAimPosition(object unit)
        {
            return ReadVector(GetUnitAimPositionValue(unit));
        }

        internal static int GetUnitObjectId(object unit)
        {
            if (unit == null)
                return 0;
            try
            {
                return Convert.ToInt32(
                    _objectId.GetValue(unit, null),
                    CultureInfo.InvariantCulture
                );
            }
            catch
            {
                return 0;
            }
        }

        // Client summons are scene units; Primary/ActiveSummons may be empty.
        // Never infer ownership from combat team alone.
        internal static bool IsOwnedLivingSummon(object unit, object player)
        {
            if (unit == null || player == null || GetUnitObjectId(unit) <= 0
                || GetUnitObjectId(unit) == GetUnitObjectId(player))
                return false;
            try
            {
                object summoning = _unitSummoning.GetValue(unit, null);
                object owner = summoning == null ? null : _summonOwner.GetValue(summoning, null);
                if (GetUnitObjectId(owner) != GetUnitObjectId(player)
                    || !Convert.ToBoolean(_isActive.GetValue(unit, null))
                    || !Convert.ToBoolean(_isAliveAndDisplayed.GetValue(unit, null)))
                    return false;
                object health = _health.GetValue(unit, null);
                if (health == null || !Convert.ToBoolean(_healthIsAlive.GetValue(health, null)))
                    return false;
                object network = _networkObject.GetValue(unit, null);
                if (network == null)
                    return false;
                long map = Convert.ToInt64(_networkMapId.GetValue(network, null));
                long instance = Convert.ToInt64(_networkInstanceId.GetValue(network, null));
                // Client network map fields can be unset. Scene membership and
                // a live local owner identify those units; reject known other maps.
                if ((map != 0 || instance != 0)
                    && !SameMapIdentity(CurrentMapInstance(player), map, instance))
                    return false;
                return true;
            }
            catch { return false; }
        }

        internal static object ResolveSummonUnit(object playerController)
        {
            if (playerController == null || _findSceneMonsters == null)
                return null;
            object best = null;
            double bestDistance = double.PositiveInfinity;
            VectorData origin = ReadVector(GetUnitPositionValue(playerController));
            object list = _findSceneMonsters.Invoke(null, new object[] { _findObjectsSortNone });
            int count = list == null ? 0 : CollectionCount(list);
            for (int index = 0; index < count; index++)
            {
                try
                {
                    object unit = CollectionItem(list, index);
                    if (!IsOwnedLivingSummon(unit, playerController))
                        continue;
                    VectorData position = ReadVector(GetUnitPositionValue(unit));
                    double dx = position.X - origin.X;
                    double dy = position.Y - origin.Y;
                    double dz = position.Z - origin.Z;
                    double distance = dx * dx + dy * dy + dz * dz;
                    if (distance < bestDistance)
                    {
                        bestDistance = distance;
                        best = unit;
                    }
                }
                catch { /* A despawned candidate must not hide other summons. */ }
            }
            return best;
        }

        internal static object ResolveAnySummonUnit()
        {
            return ResolveSummonUnit(_appPlayer.GetValue(null, null));
        }

        private static void AppendGuardianBond(StringBuilder json, object player)
        {
            bool available = false;
            bool linked = false;
            int candidateId = 0;
            int linkedId = 0;
            string error = string.Empty;
            try
            {
                candidateId = GetUnitObjectId(ResolveSummonUnit(player));
                object skills = RequireProperty(player.GetType(), "Skills").GetValue(player, null);
                object sync = RequireProperty(skills.GetType(), "BondSync").GetValue(skills, null);
                object dto = RequireProperty(sync.GetType(), "Value").GetValue(sync, null);
                object entries = RequireProperty(dto.GetType(), "Entries").GetValue(dto, null);
                int count = entries == null ? 0 : CollectionCount(entries);
                for (int i = 0; i < count; i++)
                {
                    object entry = CollectionItem(entries, i);
                    string id = (string)RequireProperty(entry.GetType(), "SkillId").GetValue(entry, null);
                    bool caster = Convert.ToBoolean(RequireProperty(entry.GetType(), "Caster").GetValue(entry, null));
                    if (id != "GuardianBond" || !caster)
                        continue;
                    object other = RequireProperty(entry.GetType(), "Other").GetValue(entry, null);
                    int otherId = other == null ? 0 : Convert.ToInt32(
                        RequireProperty(other.GetType(), "ObjectId").GetValue(other, null));
                    object target = null;
                    if (otherId > 0)
                    {
                        object list = _findSceneMonsters.Invoke(null, new object[] { _findObjectsSortNone });
                        int units = list == null ? 0 : CollectionCount(list);
                        for (int j = 0; j < units; j++)
                        {
                            object unit = CollectionItem(list, j);
                            if (GetUnitObjectId(unit) == otherId && IsOwnedLivingSummon(unit, player))
                            { target = unit; break; }
                        }
                    }
                    if (IsOwnedLivingSummon(target, player))
                    { linked = true; linkedId = otherId; break; }
                }
                available = true;
            }
            catch (Exception ex)
            { error = ex.GetType().Name + ": " + ex.Message; }
            json.Append(",\"guardian_bond\":{");
            json.Append("\"available\":").Append(available ? "true" : "false");
            json.Append(",\"has_owned_bond\":").Append(linked ? "true" : "false");
            AppendNumber(json, "candidate_unit_id", candidateId);
            AppendNumber(json, "linked_unit_id", linkedId);
            AppendString(json, "error", error);
            AppendString(json, "cast_error", BackgroundMovementPatch.GuardianBondCastError);
            json.Append('}');
        }

        // Object-id convenience wrappers (used by the memory_state diagnostics).
        internal static int GetPrimarySummonObjectId(object playerController)
        {
            return GetUnitObjectId(ResolveSummonUnit(playerController));
        }

        internal static int ResolveAnySummonObjectId()
        {
            return GetUnitObjectId(ResolveAnySummonUnit());
        }

        private static object FindEnemyUnitInCollection(
            object collection,
            int objectId
        )
        {
            if (collection == null)
                return null;
            int count = CollectionCount(collection);
            for (int index = 0; index < count; index++)
            {
                try
                {
                    object unit = CollectionItem(collection, index);
                    if (unit == null)
                        continue;
                    object monster = _monsterType.IsInstanceOfType(unit)
                        ? unit
                        : _tryCastMonster.Invoke(unit, null);
                    if (monster == null)
                        continue;
                    int candidateId = Convert.ToInt32(
                        _objectId.GetValue(monster, null),
                        CultureInfo.InvariantCulture
                    );
                    if (candidateId == objectId)
                        return monster;
                }
                catch
                {
                    // Scene collections may change while a monster despawns.
                }
            }
            return null;
        }

        private static object CurrentCamera()
        {
            object cameraController = _appCamera.GetValue(null, null);
            return cameraController == null
                ? null
                : _camera.GetValue(cameraController, null);
        }

        private static bool ReadPlayerAlive(object player)
        {
            object health = _health.GetValue(player, null);
            return health != null
                && Convert.ToBoolean(
                    _healthIsAlive.GetValue(health, null),
                    CultureInfo.InvariantCulture
                );
        }

        private static void RefreshGeneralSnapshot(
            object player,
            NavigationRequest request
        )
        {
            object mapInstance = CurrentMapInstance(player);
            if (mapInstance == null)
                return;
            object playerPositionValue = _position.GetValue(player, null);
            object camera = CurrentCamera();
            long mapId = Convert.ToInt64(
                _mapId.GetValue(mapInstance, null), CultureInfo.InvariantCulture
            );
            long instanceId = Convert.ToInt64(
                _instanceId.GetValue(mapInstance, null),
                CultureInfo.InvariantCulture
            );
            RefreshGeneralSnapshot(
                mapInstance,
                player,
                playerPositionValue,
                camera,
                mapId,
                instanceId,
                request
            );
        }

        private static void RefreshGeneralSnapshot(
            object mapInstance,
            object player,
            object playerPositionValue,
            object camera,
            long mapId,
            long instanceId,
            NavigationRequest request
        )
        {
            PlayerScanDiagnostics playerScan = new PlayerScanDiagnostics();
            List<PartyMemberSnapshot> partyMembers = CollectPartyMembers(player);
            bool partyFollowActive = request != null
                && request.PartyFollowActive;
            bool lootScanActive = request != null
                && request.LootScanActive
                && !partyFollowActive;
            List<ObservedPlayerSnapshot> players;
            LootScanDiagnostics lootScan = new LootScanDiagnostics();
            List<LootSnapshot> loots;
            List<MapExitSnapshot> mapExits;
            if (partyFollowActive)
            {
                players = CollectFollowedPartyPlayer(
                    partyMembers,
                    request.FollowPlayerId,
                    checked((int)mapId),
                    playerScan
                );
                lootScan.Source = "disabled_party_follow";
                loots = new List<LootSnapshot>();
                mapExits = new List<MapExitSnapshot>();
            }
            else
            {
                players = CollectObservedPlayers(
                    mapInstance, player, playerPositionValue, playerScan
                );
                if (lootScanActive)
                {
                    int priorityLootObjectId = request.TargetKind == "loot"
                        ? request.TargetObjectId : 0;
                    loots = CollectLootsIncremental(
                        mapInstance,
                        player,
                        playerPositionValue,
                        mapId,
                        instanceId,
                        priorityLootObjectId,
                        lootScan
                    );
                }
                else
                {
                    ResetLootScanState(false);
                    lootScan.Source = "disabled_f7";
                    lootScan.BatchLimit = LootScanBatchSize;
                    loots = new List<LootSnapshot>();
                }
                if (!_mapExitCacheReady
                    || _mapExitCacheMapId != mapId
                    || _mapExitCacheInstanceId != instanceId)
                {
                    _cachedMapExits = CollectMapExits();
                    _mapExitCacheMapId = mapId;
                    _mapExitCacheInstanceId = instanceId;
                    _mapExitCacheReady = true;
                }
                mapExits = _cachedMapExits;
            }
            _cachedPlayers = players;
            _cachedPartyMembers = partyMembers;
            _cachedPlayerScan = playerScan;
            _cachedLoots = loots;
            _cachedLootScan = lootScan;
            if (!partyFollowActive)
                _cachedMapExits = mapExits;
            _generalSnapshotMapId = mapId;
            _generalSnapshotInstanceId = instanceId;
            _generalSnapshotPartyFollowActive = partyFollowActive;
            _generalSnapshotFollowPlayerId = partyFollowActive
                ? request.FollowPlayerId ?? string.Empty
                : string.Empty;
            _generalSnapshotReady = true;
        }

        private static void WriteSnapshot(
            object player,
            bool refreshGeneralSnapshot,
            NavigationRequest request
        )
        {
            long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
            object mapInstance = CurrentMapInstance(player);
            if (mapInstance == null)
            {
                AtomicWrite(BuildUnavailableState("no_map", timestamp, player));
                return;
            }

            object playerPositionValue = _position.GetValue(player, null);
            VectorData playerPosition = ReadVector(playerPositionValue);
            float playerRadius = WorldColliderRadius(player);
            bool playerAlive = ReadPlayerAlive(player);
            VectorData cameraForward = new VectorData(0f, 0f, 1f);
            VectorData cameraRight = new VectorData(1f, 0f, 0f);
            object camera = CurrentCamera();
            if (camera != null)
            {
                object transform = _componentTransform.GetValue(camera, null);
                cameraForward = NormalizeHorizontal(
                    ReadVector(_transformForward.GetValue(transform, null)),
                    cameraForward
                );
                cameraRight = NormalizeHorizontal(
                    ReadVector(_transformRight.GetValue(transform, null)),
                    cameraRight
                );
            }

            long mapId = Convert.ToInt64(
                _mapId.GetValue(mapInstance, null), CultureInfo.InvariantCulture
            );
            long instanceId = Convert.ToInt64(
                _instanceId.GetValue(mapInstance, null),
                CultureInfo.InvariantCulture
            );
            bool partyFollowActive = request != null
                && request.PartyFollowActive;
            string followPlayerId = partyFollowActive
                ? request.FollowPlayerId ?? string.Empty
                : string.Empty;
            if (
                refreshGeneralSnapshot
                || !_generalSnapshotReady
                || _generalSnapshotMapId != mapId
                || _generalSnapshotInstanceId != instanceId
                || _generalSnapshotPartyFollowActive != partyFollowActive
                || !string.Equals(
                    _generalSnapshotFollowPlayerId,
                    followPlayerId,
                    StringComparison.Ordinal
                )
            )
            {
                RefreshGeneralSnapshot(
                    mapInstance,
                    player,
                    playerPositionValue,
                    camera,
                    mapId,
                    instanceId,
                    request
                );
            }
            List<ObservedPlayerSnapshot> players = _cachedPlayers;
            List<PartyMemberSnapshot> partyMembers = _cachedPartyMembers;
            PlayerScanDiagnostics playerScan = _cachedPlayerScan;
            MonsterScanDiagnostics monsterScan = new MonsterScanDiagnostics();
            List<MonsterSnapshot> monsters;
            if (partyFollowActive)
            {
                monsterScan.Source = "disabled_party_follow";
                monsters = new List<MonsterSnapshot>();
            }
            else
            {
                monsters = CollectEnemyMonsters(
                    mapInstance, playerPositionValue, camera, monsterScan
                );
            }
            List<LootSnapshot> loots = _cachedLoots;
            LootScanDiagnostics lootScan = _cachedLootScan;
            List<MapExitSnapshot> mapExits = _cachedMapExits;
            HandleFollowChannelSwitch(
                player, request, partyMembers, checked((int)mapId)
            );
            MaybeRefreshChannelList(player);
            HandleBossChannelSwitch(player, request);
            object summoning = _playerSummoning.GetValue(player, null);
            bool isMountedSummon = ReadIsMountedSummon(summoning);
            bool isMountableSummon = ReadIsMountableSummon(summoning);
            int activeSummonCount = ReadActiveSummonCount(summoning);
            bool hasPrimarySummon = ReadObjectPresent(_summonPrimary, summoning);
            string summonId = ReadStringProperty(_summonId, summoning);
            string mountId = ReadStringProperty(_summonMountId, summoning);
            string mountedSummonId = ReadStringProperty(
                _summonMountedSummonId, summoning
            );
            bool isMounting = ReadBoolProperty(_summonIsMounting, summoning);
            SummonDisplaysSnapshot summonDisplays = ReadSummonDisplays(summoning);
            StatusComponentSnapshot statusComponent = ReadStatusComponent(player);
            WalletCoinsSnapshot walletCoins = ReadWalletCoins(player);
            long responseRequestId = request == null ? 0 : request.RequestId;
            string responseTargetKind = request == null ? "none" : request.TargetKind;
            int responseTargetId = request == null ? 0 : request.TargetObjectId;
            string pathStatus = "missing";
            List<VectorData> corners = new List<VectorData>();

            if (request != null)
            {
                object targetPositionValue = null;
                if (request.TargetKind == "loot")
                {
                    for (int index = 0; index < loots.Count; index++)
                    {
                        if (loots[index].ObjectId == request.TargetObjectId)
                        {
                            targetPositionValue = loots[index].PositionValue;
                            break;
                        }
                    }
                }
                else if (request.TargetKind == "player")
                {
                    for (int index = 0; index < players.Count; index++)
                    {
                        if (players[index].ObjectId == request.TargetObjectId)
                        {
                            targetPositionValue = players[index].PositionValue;
                            break;
                        }
                    }
                }
                else
                {
                    for (int index = 0; index < monsters.Count; index++)
                    {
                        if (monsters[index].ObjectId == request.TargetObjectId)
                        {
                            targetPositionValue = monsters[index].PositionValue;
                            break;
                        }
                    }
                }

                if (targetPositionValue != null)
                {
                    _clearCorners.Invoke(_navPath, null);
                    bool calculated = Convert.ToBoolean(
                        _calculatePath.Invoke(
                            null,
                            new object[] {
                                playerPositionValue,
                                targetPositionValue,
                                _allAreas,
                                _navPath
                            }
                        ),
                        CultureInfo.InvariantCulture
                    );
                    if (calculated)
                    {
                        pathStatus = PathStatusName(
                            _pathStatus.GetValue(_navPath, null)
                        );
                        corners = ReadVectorCollection(
                            _pathCorners.GetValue(_navPath, null)
                        );
                    }
                    else
                    {
                        pathStatus = "invalid";
                    }
                }
            }

            StringBuilder json = new StringBuilder(4096);
            json.Append('{');
            AppendNumber(json, "schema_version", Plugin.SchemaVersion, false);
            AppendNumber(json, "timestamp_ms", timestamp);
            AppendString(json, "status", "ok");
            AppendNumber(json, "map_id", mapId);
            AppendNumber(json, "instance_id", instanceId);
            AppendNumber(
                json,
                "channel_index",
                ChannelListPatch.Available ? ChannelListPatch.CurrentIndex : -1
            );
            AppendNumber(
                json,
                "channel_count",
                ChannelListPatch.Available ? ChannelListPatch.Count : 0
            );
            json.Append(",\"player\":{");
            AppendVector(json, "position", playerPosition, false);
            AppendVector2(json, "camera_forward_xz", cameraForward.X, cameraForward.Z);
            AppendVector2(json, "camera_right_xz", cameraRight.X, cameraRight.Z);
            AppendFloat(json, "collider_radius", playerRadius);
            json.Append(",\"alive\":");
            json.Append(playerAlive ? "true" : "false");
            json.Append(",\"wallet_coins_available\":");
            json.Append(walletCoins.Available ? "true" : "false");
            AppendNumber(json, "wallet_coins", walletCoins.Coins);
            AppendString(json, "wallet_coins_error", walletCoins.Error);
            json.Append(",\"is_mounted_summon\":");
            json.Append(isMountedSummon ? "true" : "false");
            json.Append(",\"is_mountable_summon\":");
            json.Append(isMountableSummon ? "true" : "false");
            json.Append(",\"active_summon_count\":");
            json.Append(activeSummonCount.ToString(CultureInfo.InvariantCulture));
            json.Append(",\"has_primary_summon\":");
            json.Append(hasPrimarySummon ? "true" : "false");
            json.Append(",\"is_mounting\":");
            json.Append(isMounting ? "true" : "false");
            AppendString(json, "summon_id", summonId);
            AppendString(json, "mount_id", mountId);
            AppendString(json, "mounted_summon_id", mountedSummonId);
            AppendString(
                json, "summon_mount_state_source", "mount_controller"
            );
            AppendSummonDisplays(json, summonDisplays);
            AppendSummonUnitDiagnostics(json, summoning);
            AppendStatusComponent(json, statusComponent);
            AppendGuardianBond(json, player);
            json.Append('}');
            json.Append(",\"players\":[");
            for (int index = 0; index < players.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendObservedPlayer(json, players[index]);
            }
            json.Append(']');
            AppendPlayerScan(json, playerScan);
            json.Append(",\"party_members\":[");
            for (int index = 0; index < partyMembers.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendPartyMember(json, partyMembers[index]);
            }
            json.Append(']');
            AppendChannelSwitch(json, _channelSwitch);
            ConsumableUseService.AppendJson(json);
            json.Append(",\"monsters\":[");
            for (int index = 0; index < monsters.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendMonster(json, monsters[index]);
            }
            json.Append(']');
            AppendMonsterScan(json, monsterScan);
            json.Append(",\"loots\":[");
            for (int index = 0; index < loots.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendLoot(json, loots[index]);
            }
            json.Append(']');
            AppendLootScan(json, lootScan);
            json.Append(",\"map_exits\":[");
            for (int index = 0; index < mapExits.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendMapExit(json, mapExits[index]);
            }
            json.Append(']');
            json.Append(",\"path\":{");
            AppendNumber(json, "request_id", responseRequestId, false);
            AppendString(json, "target_kind", responseTargetKind);
            AppendNumber(json, "target_object_id", responseTargetId);
            AppendString(json, "status", pathStatus);
            json.Append(",\"corners\":[");
            for (int index = 0; index < corners.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                AppendRawVector(json, corners[index]);
            }
            json.Append("]}}");
            AtomicWrite(json.ToString());
        }

        private static bool ReadIsMountedSummon(object summoning)
        {
            return summoning != null
                && _mountController.GetValue(summoning, null) != null;
        }

        private static bool ReadIsMountableSummon(object summoning)
        {
            if (summoning == null)
                return false;
            object value = _summonIsMountable.GetValue(summoning, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static int ReadActiveSummonCount(object summoning)
        {
            if (summoning == null)
                return 0;
            object list = _summonActiveSummons.GetValue(summoning, null);
            if (list == null)
                return 0;
            PropertyInfo countProperty = list.GetType().GetProperty("Count");
            if (countProperty == null)
                return 0;
            object count = countProperty.GetValue(list, null);
            return count == null ? 0 : Convert.ToInt32(
                count, CultureInfo.InvariantCulture
            );
        }

        private static bool ReadObjectPresent(
            PropertyInfo property, object summoning
        )
        {
            return summoning != null
                && property.GetValue(summoning, null) != null;
        }

        // Build-1 diagnostic: surface the object ids + runtime types of the
        // player's own summons so we can confirm which source (Primary vs
        // ActiveSummons) yields the same id space as PlayerInputDto.UnitId
        // (the value captured when manually casting Guardian Bond on a summon).
        // Purely additive to the JSON; never throws into the snapshot path.
        private static void AppendSummonUnitDiagnostics(
            StringBuilder json, object summoning
        )
        {
            int primaryId = 0;
            string primaryType = string.Empty;
            List<int> activeIds = new List<int>();
            string activeType = string.Empty;
            try
            {
                if (summoning != null)
                {
                    object primary = _summonPrimary.GetValue(summoning, null);
                    if (primary != null)
                    {
                        primaryType = primary.GetType().Name;
                        primaryId = GetUnitObjectId(primary);
                    }
                    object list = _summonActiveSummons.GetValue(
                        summoning, null
                    );
                    if (list != null)
                    {
                        int count = CollectionCount(list);
                        for (int index = 0; index < count; index++)
                        {
                            object summon = CollectionItem(list, index);
                            if (summon == null)
                                continue;
                            if (activeType.Length == 0)
                                activeType = summon.GetType().Name;
                            activeIds.Add(GetUnitObjectId(summon));
                        }
                    }
                }
            }
            catch
            {
                // diagnostics only; never break the snapshot
            }
            int sceneSummonId = 0;
            try
            {
                sceneSummonId = ResolveAnySummonObjectId();
            }
            catch
            {
                sceneSummonId = 0;
            }
            AppendNumber(json, "primary_summon_unit_id", primaryId);
            AppendNumber(json, "scene_summon_unit_id", sceneSummonId);
            AppendString(json, "primary_summon_type", primaryType);
            AppendString(json, "active_summon_type", activeType);
            json.Append(",\"active_summon_unit_ids\":[");
            for (int index = 0; index < activeIds.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                json.Append(
                    activeIds[index].ToString(CultureInfo.InvariantCulture)
                );
            }
            json.Append(']');
        }

        private static string ReadStringProperty(
            PropertyInfo property, object summoning
        )
        {
            if (summoning == null)
                return string.Empty;
            object value = property.GetValue(summoning, null);
            return value == null ? string.Empty : value.ToString();
        }

        private static bool ReadBoolProperty(
            PropertyInfo property, object summoning
        )
        {
            if (summoning == null)
                return false;
            object value = property.GetValue(summoning, null);
            return value != null && Convert.ToBoolean(
                value, CultureInfo.InvariantCulture
            );
        }

        private static SummonDisplaysSnapshot ReadSummonDisplays(object summoning)
        {
            SummonDisplaysSnapshot snapshot = new SummonDisplaysSnapshot();
            try
            {
                if (summoning == null)
                    throw new InvalidOperationException("Player.Summoning is null");
                object displays = _summonDisplays.GetValue(summoning, null);
                int count = displays == null ? 0 : CollectionCount(displays);
                for (int index = 0; index < count; index++)
                {
                    object display = CollectionItem(displays, index);
                    if (display == null)
                        continue;
                    SummonDisplaySnapshot item = new SummonDisplaySnapshot();
                    item.SkillId = ReadStringProperty(
                        _summonDisplaySkillId, display
                    );
                    item.Id = ReadStringProperty(_summonDisplayId, display);
                    item.Level = ReadIntProperty(_summonDisplayLevel, display);
                    snapshot.Items.Add(item);
                }
                snapshot.Available = true;
            }
            catch (Exception error)
            {
                snapshot.Available = false;
                snapshot.Error = error.GetType().Name + ": " + error.Message;
            }
            return snapshot;
        }

        private static StatusComponentSnapshot ReadStatusComponent(object player)
        {
            StatusComponentSnapshot snapshot = new StatusComponentSnapshot();
            try
            {
                object status = player == null
                    ? null : _playerStatus.GetValue(player, null);
                if (status == null)
                    throw new InvalidOperationException("Player.Status is null");

                try
                {
                    if (_statusDisplays == null)
                        throw new MissingMemberException(
                            "StatusComponent", "StatusDisplays_C"
                        );
                    snapshot.ActiveStatusIds.AddRange(
                        ReadStatusDisplayIds(
                            _statusDisplays.GetValue(status, null)
                        )
                    );
                    snapshot.ActiveStatusIds.Sort(StringComparer.Ordinal);
                    snapshot.ActiveStatusesAvailable = true;
                }
                catch (Exception activeError)
                {
                    snapshot.ActiveStatusesAvailable = false;
                    snapshot.ActiveStatusesError = activeError.GetType().Name
                        + ": " + activeError.Message;
                }

                snapshot.Buffs.AddRange(ReadStringCollection(
                    _statusBuffs.GetValue(status, null)
                ));
                snapshot.Debuffs.AddRange(ReadStringCollection(
                    _statusDebuffs.GetValue(status, null)
                ));
                snapshot.Buffs.Sort(StringComparer.Ordinal);
                snapshot.Debuffs.Sort(StringComparer.Ordinal);

                object effects = _statusEffects.GetValue(status, null);
                int count = effects == null ? 0 : CollectionCount(effects);
                for (int index = 0; index < count; index++)
                {
                    object effect = CollectionItem(effects, index);
                    if (effect == null)
                        continue;
                    object config = _statusEffectConfig.GetValue(effect, null);
                    StatusEffectSnapshot item = new StatusEffectSnapshot();
                    item.Id = ReadStringProperty(_statusEffectId, effect);
                    item.DisplayName = config == null
                        ? string.Empty
                        : ReadStringProperty(_statusConfigDisplayName, config);
                    item.Category = config == null
                        ? string.Empty
                        : ReadStringProperty(_statusConfigCategory, config);
                    item.Duration = ReadFloatProperty(_statusEffectDuration, effect);
                    item.DurationMax = ReadFloatProperty(
                        _statusEffectDurationMax, effect
                    );
                    item.Level = ReadIntProperty(_statusEffectLevel, effect);
                    item.Stacks = ReadIntProperty(_statusEffectStacks, effect);
                    item.MaxStacks = ReadIntProperty(_statusEffectMaxStacks, effect);
                    item.InfiniteDuration = ReadBoolProperty(
                        _statusEffectInfiniteDuration, effect
                    );
                    item.IsSkill = ReadBoolProperty(_statusEffectIsSkill, effect);
                    item.IsToggle = ReadBoolProperty(_statusEffectIsToggle, effect);
                    snapshot.Effects.Add(item);
                }
                snapshot.Available = true;
            }
            catch (Exception error)
            {
                snapshot.Available = false;
                snapshot.Error = error.GetType().Name + ": " + error.Message;
            }
            return snapshot;
        }

        private static WalletCoinsSnapshot ReadWalletCoins(object player)
        {
            WalletCoinsSnapshot snapshot = new WalletCoinsSnapshot();
            try
            {
                if (_playerSave == null || _savePlayerData == null
                    || _playerDataCoins == null)
                {
                    throw new MissingMemberException(
                        "PlayerSave.PlayerData", "Coins"
                    );
                }
                if (player == null)
                    throw new InvalidOperationException("PlayerController is null");
                object save = _playerSave.GetValue(player, null);
                if (save == null)
                    throw new InvalidOperationException("PlayerSave is null");
                object playerData = _savePlayerData.GetValue(save, null);
                if (playerData == null)
                    throw new InvalidOperationException("PlayerData is null");
                object value = _playerDataCoins.GetValue(playerData, null);
                if (value == null)
                    throw new InvalidOperationException("PlayerData.Coins is null");
                snapshot.Coins = Convert.ToInt64(
                    value, CultureInfo.InvariantCulture
                );
                snapshot.Available = true;
            }
            catch (Exception error)
            {
                snapshot.Available = false;
                snapshot.Error = error.GetType().Name + ": " + error.Message;
            }
            return snapshot;
        }

        private static List<string> ReadStatusDisplayIds(object collection)
        {
            List<string> result = new List<string>();
            if (collection == null)
                return result;
            object source = collection;
            PropertyInfo keys = collection.GetType().GetProperty(
                "Keys", BindingFlags.Public | BindingFlags.Instance
            );
            if (keys != null)
                source = keys.GetValue(collection, null);
            if (source == null)
                return result;

            MethodInfo getEnumerator = RequireMethod(
                source.GetType(), "GetEnumerator", 0
            );
            object enumerator = getEnumerator.Invoke(source, null);
            MethodInfo moveNext = RequireMethod(
                enumerator.GetType(), "MoveNext", 0
            );
            PropertyInfo current = RequireProperty(
                enumerator.GetType(), "Current"
            );
            HashSet<string> unique = new HashSet<string>(
                StringComparer.OrdinalIgnoreCase
            );
            while (Convert.ToBoolean(
                moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture
            ))
            {
                object item = current.GetValue(enumerator, null);
                if (item == null)
                    continue;
                object id = item;
                if (!(item is string))
                {
                    PropertyInfo key = item.GetType().GetProperty("Key");
                    if (key != null)
                        id = key.GetValue(item, null);
                    else
                    {
                        PropertyInfo idProperty = item.GetType().GetProperty("Id");
                        if (idProperty != null)
                            id = idProperty.GetValue(item, null);
                    }
                }
                string text = Convert.ToString(
                    id, CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (!string.IsNullOrWhiteSpace(text) && unique.Add(text))
                    result.Add(text);
            }
            return result;
        }

        private static List<string> ReadStringCollection(object collection)
        {
            List<string> result = new List<string>();
            if (collection == null)
                return result;
            MethodInfo getEnumerator = RequireMethod(
                collection.GetType(), "GetEnumerator", 0
            );
            object enumerator = getEnumerator.Invoke(collection, null);
            MethodInfo moveNext = RequireMethod(
                enumerator.GetType(), "MoveNext", 0
            );
            PropertyInfo current = RequireProperty(
                enumerator.GetType(), "Current"
            );
            while (Convert.ToBoolean(
                moveNext.Invoke(enumerator, null), CultureInfo.InvariantCulture
            ))
            {
                string value = Convert.ToString(
                    current.GetValue(enumerator, null),
                    CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (!string.IsNullOrEmpty(value))
                    result.Add(value);
            }
            return result;
        }

        private static float ReadFloatProperty(PropertyInfo property, object value)
        {
            object raw = value == null ? null : property.GetValue(value, null);
            return raw == null ? 0f : Convert.ToSingle(
                raw, CultureInfo.InvariantCulture
            );
        }

        private static int ReadIntProperty(PropertyInfo property, object value)
        {
            object raw = value == null ? null : property.GetValue(value, null);
            return raw == null ? 0 : Convert.ToInt32(
                raw, CultureInfo.InvariantCulture
            );
        }

        private static List<PartyMemberSnapshot> CollectPartyMembers(
            object localPlayer
        )
        {
            List<PartyMemberSnapshot> result = new List<PartyMemberSnapshot>();
            object party = _playerCurrentParty.GetValue(localPlayer, null);
            object members = party == null
                ? null
                : _partyMembers.GetValue(party, null);
            if (members == null)
                return result;

            string localPlayerId = Convert.ToString(
                _playerId.GetValue(localPlayer, null),
                CultureInfo.InvariantCulture
            ) ?? string.Empty;
            int count = CollectionCount(members);
            for (int index = 0; index < count; index++)
            {
                try
                {
                    object member = CollectionItem(members, index);
                    if (member == null)
                        continue;
                    PartyMemberSnapshot snapshot = new PartyMemberSnapshot();
                    snapshot.DisplayName = Convert.ToString(
                        _partyMemberDisplayName.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    snapshot.PlayerId = Convert.ToString(
                        _partyMemberPlayerId.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    if (string.IsNullOrWhiteSpace(snapshot.PlayerId))
                        continue;
                    snapshot.ObjectId = Convert.ToInt32(
                        _partyMemberObjectId.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    );
                    snapshot.MapId = Convert.ToInt32(
                        _partyMemberMapId.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    );
                    snapshot.InstanceId = Convert.ToString(
                        _partyMemberInstanceId.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    snapshot.ChannelIndex = Convert.ToInt32(
                        _partyMemberChannelIndex.GetValue(member, null),
                        CultureInfo.InvariantCulture
                    );
                    snapshot.IsLocal = !string.IsNullOrEmpty(localPlayerId)
                        && string.Equals(
                            snapshot.PlayerId,
                            localPlayerId,
                            StringComparison.Ordinal
                        );
                    snapshot.SourceValue = member;
                    result.Add(snapshot);
                }
                catch (Exception error)
                {
                    Exception actual = Unwrap(error);
                    _log.LogDebug(
                        "Skipped unreadable party member: "
                        + actual.GetType().Name + ": " + actual.Message
                    );
                }
            }
            return result;
        }

        private static List<ObservedPlayerSnapshot> CollectFollowedPartyPlayer(
            List<PartyMemberSnapshot> partyMembers,
            string followPlayerId,
            int currentMapId,
            PlayerScanDiagnostics diagnostics
        )
        {
            List<ObservedPlayerSnapshot> result =
                new List<ObservedPlayerSnapshot>();
            diagnostics.Source = "party_target";
            diagnostics.SourceCount = partyMembers.Count;
            if (string.IsNullOrWhiteSpace(followPlayerId))
                return result;

            PartyMemberSnapshot target = null;
            PartyMemberSnapshot local = null;
            for (int index = 0; index < partyMembers.Count; index++)
            {
                PartyMemberSnapshot member = partyMembers[index];
                if (member.IsLocal)
                    local = member;
                if (!member.IsLocal
                    && string.Equals(
                        member.PlayerId,
                        followPlayerId,
                        StringComparison.Ordinal
                    ))
                    target = member;
            }
            if (target == null)
                return result;
            if (target.MapId > 0 && target.MapId != currentMapId)
            {
                diagnostics.RejectedOtherMap++;
                return result;
            }
            if (local != null
                && !string.IsNullOrWhiteSpace(target.InstanceId)
                && !string.IsNullOrWhiteSpace(local.InstanceId)
                && !string.Equals(
                    target.InstanceId,
                    local.InstanceId,
                    StringComparison.Ordinal
                ))
            {
                diagnostics.RejectedOtherMap++;
                return result;
            }
            if (local != null
                && target.ChannelIndex >= 0
                && local.ChannelIndex >= 0
                && target.ChannelIndex != local.ChannelIndex)
            {
                diagnostics.RejectedOtherMap++;
                return result;
            }

            try
            {
                object observed = _partyMemberCachedPlayer.GetValue(
                    target.SourceValue, null
                );
                if (observed == null)
                {
                    observed = _partyMemberGetPlayer.Invoke(
                        target.SourceValue, null
                    );
                }
                if (observed == null || !_playerType.IsInstanceOfType(observed))
                    return result;
                diagnostics.Castable = 1;

                int objectId = Convert.ToInt32(
                    _objectId.GetValue(observed, null),
                    CultureInfo.InvariantCulture
                );
                string playerId = Convert.ToString(
                    _playerId.GetValue(observed, null),
                    CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (objectId <= 0)
                {
                    diagnostics.RejectedInvalidObjectId++;
                    return result;
                }
                if (!string.Equals(
                    playerId, followPlayerId, StringComparison.Ordinal
                ))
                {
                    diagnostics.RejectedError++;
                    diagnostics.LastError = "party target PlayerId mismatch";
                    return result;
                }
                if (!Convert.ToBoolean(_isActive.GetValue(observed, null)))
                {
                    diagnostics.RejectedInactive++;
                    return result;
                }

                object health = _health.GetValue(observed, null);
                object positionValue = _position.GetValue(observed, null);
                string displayName = Convert.ToString(
                    _displayName.GetValue(observed, null),
                    CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (string.IsNullOrWhiteSpace(displayName))
                    displayName = target.DisplayName ?? string.Empty;

                ObservedPlayerSnapshot snapshot =
                    new ObservedPlayerSnapshot();
                snapshot.ObjectId = objectId;
                snapshot.PlayerId = playerId;
                snapshot.DisplayName = displayName;
                snapshot.PositionValue = positionValue;
                snapshot.Position = ReadVector(positionValue);
                snapshot.ColliderRadius = WorldColliderRadius(observed);
                snapshot.Alive = health != null
                    && Convert.ToBoolean(_healthIsAlive.GetValue(health, null));
                snapshot.Visible = Convert.ToBoolean(
                    _isAliveAndDisplayed.GetValue(observed, null)
                );
                snapshot.PartyMember = true;
                snapshot.Selected = false;
                result.Add(snapshot);
                diagnostics.Accepted = 1;
            }
            catch (Exception error)
            {
                diagnostics.RejectedError++;
                Exception actual = Unwrap(error);
                diagnostics.LastError = actual.GetType().Name
                    + ": " + actual.Message;
            }
            return result;
        }

        private static void HandleFollowChannelSwitch(
            object player,
            NavigationRequest request,
            List<PartyMemberSnapshot> partyMembers,
            int currentMapId
        )
        {
            if (request == null
                || request.FollowChannelRequestId <= 0
                || request.FollowChannelRequestId == _lastFollowChannelRequestId)
                return;

            _lastFollowChannelRequestId = request.FollowChannelRequestId;
            ChannelSwitchSnapshot result = new ChannelSwitchSnapshot();
            result.RequestId = request.FollowChannelRequestId;
            result.TargetPlayerId = request.FollowPlayerId ?? string.Empty;
            _channelSwitch = result;

            if (!request.BotActive)
            {
                result.Status = "bot_inactive";
                return;
            }
            if (string.IsNullOrWhiteSpace(result.TargetPlayerId))
            {
                result.Status = "missing_player_id";
                return;
            }

            PartyMemberSnapshot target = null;
            PartyMemberSnapshot local = null;
            for (int index = 0; index < partyMembers.Count; index++)
            {
                PartyMemberSnapshot member = partyMembers[index];
                if (member.IsLocal)
                    local = member;
                if (string.Equals(
                    member.PlayerId,
                    result.TargetPlayerId,
                    StringComparison.Ordinal
                ))
                    target = member;
            }
            if (target == null || target.IsLocal)
            {
                result.Status = "target_not_remote_party_member";
                return;
            }

            result.TargetMapId = target.MapId;
            result.TargetInstanceId = target.InstanceId ?? string.Empty;
            result.TargetChannelIndex = target.ChannelIndex;
            if (target.MapId > 0 && target.MapId != currentMapId)
            {
                result.Status = "different_map";
                return;
            }
            if (local == null)
            {
                result.Status = "local_party_member_missing";
                return;
            }
            if (target.ChannelIndex < 0)
            {
                result.Status = "channel_unavailable";
                return;
            }

            try
            {
                if (!string.IsNullOrWhiteSpace(target.InstanceId)
                    && !string.Equals(
                        target.InstanceId,
                        local.InstanceId,
                        StringComparison.Ordinal
                    ))
                {
                    _playerTrySwitchToInstance.Invoke(
                        player, new object[] { target.InstanceId }
                    );
                    result.Status = "instance_requested";
                }
                else if (target.ChannelIndex != local.ChannelIndex)
                {
                    _playerRequestChannelSwitch.Invoke(
                        player, new object[] { target.ChannelIndex }
                    );
                    result.Status = "channel_requested";
                }
                else
                {
                    result.Status = "already_same_channel";
                }
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                result.Status = "error";
                result.Error = actual.GetType().Name + ": " + actual.Message;
                _log.LogWarning(
                    "F2 party channel switch failed: " + result.Error
                );
            }
        }

        // Boss avoidance: Python asks the probe to hop to a specific 0-based
        // channel index (independent of any party member) by bumping
        // channel_switch_request_id with channel_switch_index. Mirrors the
        // dedup/guard style of HandleFollowChannelSwitch.
        private static void HandleBossChannelSwitch(
            object player, NavigationRequest request
        )
        {
            if (request == null
                || request.ChannelSwitchRequestId <= 0
                || request.ChannelSwitchRequestId == _lastChannelSwitchRequestId)
                return;
            _lastChannelSwitchRequestId = request.ChannelSwitchRequestId;
            if (!request.BotActive)
                return;
            int index = request.ChannelSwitchIndex;
            int count = ChannelListPatch.Available ? ChannelListPatch.Count : 0;
            if (index < 0 || (count > 0 && index >= count))
            {
                _log.LogWarning(
                    "Boss channel switch ignored: index " + index
                    + " out of range (count " + count + ")"
                );
                return;
            }
            try
            {
                _playerRequestChannelSwitch.Invoke(
                    player, new object[] { index }
                );
                _log.LogInfo(
                    "Boss channel switch requested: index " + index
                );
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                _log.LogWarning(
                    "Boss channel switch failed: "
                    + actual.GetType().Name + ": " + actual.Message
                );
            }
        }

        // The server only pushes the channel list on login / map change /
        // channel switch, so a bot that loads on demand mid-session starts
        // blind. While channel data is still unknown, ask the server to resend
        // it (throttled) so channel_index/channel_count populate on their own.
        private static void MaybeRefreshChannelList(object player)
        {
            if (_playerSendChannelList == null || ChannelListPatch.Available)
                return;
            long now = DateTime.UtcNow.Ticks;
            if (now - _lastChannelListRequestTicks
                < TimeSpan.TicksPerSecond * 3)
                return;
            _lastChannelListRequestTicks = now;
            try
            {
                _playerSendChannelList.Invoke(player, null);
            }
            catch (Exception error)
            {
                _log.LogDebug(
                    "SendChannelList failed: " + Unwrap(error).Message
                );
            }
        }

        private static List<ObservedPlayerSnapshot> CollectObservedPlayers(
            object mapInstance,
            object localPlayer,
            object localPositionValue,
            PlayerScanDiagnostics diagnostics
        )
        {
            List<ObservedPlayerSnapshot> result =
                new List<ObservedPlayerSnapshot>();
            object list = _players.GetValue(mapInstance, null);
            diagnostics.MapCount = list == null ? 0 : CollectionCount(list);
            diagnostics.SourceCount = diagnostics.MapCount;
            if (diagnostics.SourceCount == 0)
            {
                diagnostics.Source = "scene";
                if (_findScenePlayers == null)
                {
                    diagnostics.LastError = _sceneScanInitializationError
                        ?? "scene player scanner unavailable";
                    list = null;
                }
                else
                {
                    try
                    {
                        list = _findScenePlayers.Invoke(
                            null, new object[] { _findObjectsSortNone }
                        );
                        diagnostics.SceneCount = list == null
                            ? 0 : CollectionCount(list);
                        diagnostics.SourceCount = diagnostics.SceneCount;
                    }
                    catch (Exception error)
                    {
                        Exception actual = Unwrap(error);
                        diagnostics.LastError = actual.GetType().Name
                            + ": " + actual.Message;
                        list = null;
                    }
                }
            }
            if (list == null)
                return result;

            int localObjectId = Convert.ToInt32(
                _objectId.GetValue(localPlayer, null), CultureInfo.InvariantCulture
            );
            string localPlayerId = Convert.ToString(
                _playerId.GetValue(localPlayer, null), CultureInfo.InvariantCulture
            ) ?? string.Empty;
            int selectedObjectId = 0;
            try
            {
                object uiManager = _appUi.GetValue(null, null);
                object uiGame = uiManager == null
                    ? null
                    : _uiGame.GetValue(uiManager, null);
                object uiTarget = uiGame == null
                    ? null
                    : _uiGameTarget.GetValue(uiGame, null);
                object selectedPlayer = uiTarget == null
                    ? null
                    : (_playerType.IsInstanceOfType(uiTarget)
                        ? uiTarget
                        : _tryCastPlayer.Invoke(uiTarget, null));
                if (selectedPlayer != null)
                {
                    selectedObjectId = Convert.ToInt32(
                        _objectId.GetValue(selectedPlayer, null),
                        CultureInfo.InvariantCulture
                    );
                    diagnostics.SelectionSource = "ui_game_target";
                    diagnostics.SelectedObjectId = selectedObjectId;
                }
            }
            catch (Exception error)
            {
                selectedObjectId = 0;
                Exception actual = Unwrap(error);
                diagnostics.SelectionSource = "error";
                diagnostics.LastError = actual.GetType().Name
                    + ": " + actual.Message;
            }

            HashSet<int> seenObjectIds = new HashSet<int>();
            for (int index = 0; index < diagnostics.SourceCount; index++)
            {
                try
                {
                    object unit = CollectionItem(list, index);
                    if (unit == null)
                        continue;
                    object observed = _playerType.IsInstanceOfType(unit)
                        ? unit
                        : _tryCastPlayer.Invoke(unit, null);
                    if (observed == null)
                        continue;
                    diagnostics.Castable++;

                    int objectId = Convert.ToInt32(
                        _objectId.GetValue(observed, null),
                        CultureInfo.InvariantCulture
                    );
                    string playerId = Convert.ToString(
                        _playerId.GetValue(observed, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    if (objectId == localObjectId
                        || (!string.IsNullOrEmpty(localPlayerId)
                            && playerId == localPlayerId))
                    {
                        diagnostics.RejectedLocal++;
                        continue;
                    }
                    if (objectId <= 0)
                    {
                        diagnostics.RejectedInvalidObjectId++;
                        continue;
                    }
                    if (!seenObjectIds.Add(objectId))
                    {
                        diagnostics.RejectedDuplicate++;
                        continue;
                    }
                    if (!Convert.ToBoolean(_isActive.GetValue(observed, null)))
                    {
                        diagnostics.RejectedInactive++;
                        continue;
                    }

                    object positionValue = _position.GetValue(observed, null);
                    if (diagnostics.Source == "scene"
                        && !ScenePlayerMatchesMap(
                            observed,
                            mapInstance,
                            localPositionValue,
                            positionValue
                        ))
                    {
                        diagnostics.RejectedOtherMap++;
                        continue;
                    }

                    object health = _health.GetValue(observed, null);
                    string displayName = Convert.ToString(
                        _displayName.GetValue(observed, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                    if (string.IsNullOrWhiteSpace(displayName))
                    {
                        object characterData = _playerCharacterData.GetValue(
                            observed, null
                        );
                        if (characterData != null)
                        {
                            displayName = Convert.ToString(
                                _characterName.GetValue(characterData, null),
                                CultureInfo.InvariantCulture
                            ) ?? string.Empty;
                        }
                    }

                    bool partyMember = false;
                    try
                    {
                        partyMember = Convert.ToBoolean(
                            _playerIsInMyParty.Invoke(
                                localPlayer, new object[] { observed }
                            ),
                            CultureInfo.InvariantCulture
                        );
                    }
                    catch
                    {
                        partyMember = false;
                    }

                    ObservedPlayerSnapshot snapshot =
                        new ObservedPlayerSnapshot();
                    snapshot.ObjectId = objectId;
                    snapshot.PlayerId = playerId;
                    snapshot.DisplayName = displayName;
                    snapshot.PositionValue = positionValue;
                    snapshot.Position = ReadVector(positionValue);
                    snapshot.ColliderRadius = WorldColliderRadius(observed);
                    snapshot.Alive = health != null
                        && Convert.ToBoolean(_healthIsAlive.GetValue(health, null));
                    snapshot.Visible = Convert.ToBoolean(
                        _isAliveAndDisplayed.GetValue(observed, null)
                    );
                    snapshot.PartyMember = partyMember;
                    snapshot.Selected = objectId == selectedObjectId;
                    result.Add(snapshot);
                    diagnostics.Accepted++;
                }
                catch (Exception error)
                {
                    diagnostics.RejectedError++;
                    Exception actual = Unwrap(error);
                    diagnostics.LastError = actual.GetType().Name
                        + ": " + actual.Message;
                }
            }
            return result;
        }

        private static bool ScenePlayerMatchesMap(
            object observed,
            object mapInstance,
            object localPositionValue,
            object observedPositionValue
        )
        {
            object networkObject = _networkObject.GetValue(observed, null);
            if (networkObject == null)
                return false;
            long mapId = Convert.ToInt64(
                _networkMapId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            long instanceId = Convert.ToInt64(
                _networkInstanceId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            if (SameMapIdentity(mapInstance, mapId, instanceId))
                return true;
            if (mapId != 0 || instanceId != 0)
                return false;
            return HasUsableNavMeshPath(
                localPositionValue, observedPositionValue, null
            );
        }

        private static List<LootSnapshot> CollectLootsIncremental(
            object mapInstance,
            object player,
            object playerPositionValue,
            long mapId,
            long instanceId,
            int priorityLootObjectId,
            LootScanDiagnostics diagnostics
        )
        {
            diagnostics.Active = true;
            diagnostics.BatchLimit = LootScanBatchSize;
            if (_lootCacheMapId != mapId || _lootCacheInstanceId != instanceId)
            {
                bool knownPreviousMap = _lootCacheMapId != long.MinValue;
                ResetLootScanState(knownPreviousMap);
                _lootCacheMapId = mapId;
                _lootCacheInstanceId = instanceId;
            }

            object list = _loots.GetValue(mapInstance, null);
            diagnostics.MapCount = list == null ? 0 : CollectionCount(list);
            bool requiresMapFilter = false;
            if (diagnostics.MapCount > 0)
            {
                diagnostics.Source = "map_incremental";
                diagnostics.SourceCount = diagnostics.MapCount;
            }
            else
            {
                bool seeded = EnsureTrackedLootSeed(mapId, instanceId, diagnostics);
                if (_trackedLoots.Count > 0)
                {
                    list = _trackedLoots;
                    diagnostics.Source = "lifecycle_incremental";
                    diagnostics.SourceCount = _trackedLoots.Count;
                    requiresMapFilter = true;
                }
                else
                {
                    diagnostics.Source = _lootLifecycleTrackingAvailable
                        ? "lifecycle_empty" : "scene_fallback_deferred";
                    diagnostics.SceneFallbackDeferred =
                        !_lootLifecycleTrackingAvailable && !seeded;
                    _lootCache.Clear();
                    diagnostics.Cached = 0;
                    diagnostics.Exported = 0;
                    return new List<LootSnapshot>();
                }
            }

            if (!string.Equals(
                _lootScanSource, diagnostics.Source, StringComparison.Ordinal
            ))
            {
                _lootScanSource = diagnostics.Source;
                _lootScanCursor = 0;
                AdvanceLootScanPass();
            }

            string localPlayerId = Convert.ToString(
                _playerId.GetValue(player, null), CultureInfo.InvariantCulture
            ) ?? string.Empty;
            long startedTicks = Timer.ElapsedTicks;
            CachedLootEntry priorityEntry;
            if (priorityLootObjectId > 0
                && _lootCache.TryGetValue(priorityLootObjectId, out priorityEntry))
            {
                ProcessLootForCache(
                    priorityEntry.SourceValue,
                    mapInstance,
                    player,
                    playerPositionValue,
                    localPlayerId,
                    requiresMapFilter,
                    diagnostics
                );
            }

            int count = diagnostics.SourceCount;
            if (_lootScanCursor >= count)
            {
                CompleteLootScanPass(diagnostics);
                _lootScanCursor = 0;
            }
            int batchProcessed = 0;
            while (_lootScanCursor < count && batchProcessed < LootScanBatchSize)
            {
                if (batchProcessed >= LootScanMinimumBatchSize
                    && ElapsedMilliseconds(startedTicks)
                        >= LootScanBudgetMilliseconds)
                    break;
                object loot = CollectionItem(list, _lootScanCursor);
                _lootScanCursor++;
                batchProcessed++;
                diagnostics.Processed++;
                ProcessLootForCache(
                    loot,
                    mapInstance,
                    player,
                    playerPositionValue,
                    localPlayerId,
                    requiresMapFilter,
                    diagnostics
                );
            }
            if (_lootScanCursor >= count)
            {
                CompleteLootScanPass(diagnostics);
                _lootScanCursor = 0;
            }
            return BuildLootExport(
                ReadVector(playerPositionValue), priorityLootObjectId, diagnostics
            );
        }

        private static bool EnsureTrackedLootSeed(
            long mapId,
            long instanceId,
            LootScanDiagnostics diagnostics
        )
        {
            long elapsed = Timer.ElapsedMilliseconds;
            bool mapNotSeeded = _lootSceneSeedMapId != mapId
                || _lootSceneSeedInstanceId != instanceId;
            bool fallbackDue = !_lootLifecycleTrackingAvailable
                && elapsed - _lastLootSceneFallbackMilliseconds
                    >= LootSceneFallbackIntervalMilliseconds;
            if (!mapNotSeeded && !fallbackDue)
                return false;
            if (mapNotSeeded
                && _lootLifecycleTrackingAvailable
                && _trackedLoots.Count > 0)
            {
                _lootSceneSeedMapId = mapId;
                _lootSceneSeedInstanceId = instanceId;
                return false;
            }
            if (_findSceneLoots == null)
            {
                diagnostics.LastError = "scene loot seed unavailable: "
                    + (_sceneScanInitializationError ?? "unknown");
                return false;
            }

            _lootSceneSeedMapId = mapId;
            _lootSceneSeedInstanceId = instanceId;
            _lastLootSceneFallbackMilliseconds = elapsed;
            try
            {
                object sceneLoots = _findSceneLoots.Invoke(
                    null, new object[] { _findObjectsSortNone }
                );
                diagnostics.SceneCount = sceneLoots == null
                    ? 0 : CollectionCount(sceneLoots);
                if (!_lootLifecycleTrackingAvailable)
                    _trackedLoots.Clear();
                for (int index = 0; index < diagnostics.SceneCount; index++)
                {
                    object loot = CollectionItem(sceneLoots, index);
                    if (loot == null || !_lootType.IsInstanceOfType(loot))
                        continue;
                    _trackedLoots.Add(loot);
                }
                return true;
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                diagnostics.LastError = actual.GetType().Name
                    + ": " + actual.Message;
                return false;
            }
        }

        internal static bool CanInteractWithCachedLoot(object player, int objectId, out string reason)
        {
            reason = "missing cached loot";
            CachedLootEntry entry;
            if (player == null || objectId <= 0)
                return false;
            if (!_lootCache.TryGetValue(objectId, out entry))
            {
                // The incremental exported snapshot can outlive the live
                // interaction cache. Purge that ghost immediately so Python
                // does not circle and retry it until the next full scan pass.
                RemovePublishedLoot(objectId);
                return false;
            }
            try
            {
                object loot = entry.SourceValue;
                if (loot == null || !_lootType.IsInstanceOfType(loot)
                    || GetUnitObjectId(loot) != objectId)
                {
                    RemoveLootFromCaches(objectId);
                    return false;
                }
                object gameObject = _componentGameObject.GetValue(loot, null);
                reason = "inactive loot";
                if (gameObject == null || !Convert.ToBoolean(
                    _gameObjectActiveInHierarchy.GetValue(gameObject, null)))
                {
                    RemoveLootFromCaches(objectId);
                    return false;
                }
                object transform = _componentTransform.GetValue(loot, null);
                object position = transform == null ? null : _transformPosition.GetValue(transform, null);
                reason = "wrong map or missing position";
                if (position == null || !SceneLootMatchesMap(loot, CurrentMapInstance(player),
                    GetUnitPositionValue(player), position))
                {
                    RemoveLootFromCaches(objectId);
                    return false;
                }
                object dtoSync = _lootDto.GetValue(loot, null);
                object dto = dtoSync == null ? null : _lootDtoValue.GetValue(dtoSync, null);
                reason = "missing data or excluded equipment";
                if (dto == null)
                {
                    RemoveLootFromCaches(objectId);
                    return false;
                }
                string kind = Convert.ToString(_lootDtoType.GetValue(dto, null));
                if (string.Equals(kind, "Equip", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(kind, "Equipment", StringComparison.OrdinalIgnoreCase))
                {
                    RemoveLootFromCaches(objectId);
                    return false;
                }
                object lockSync = _lootLock.GetValue(loot, null);
                object lockValue = lockSync == null ? null : _lootLockValue.GetValue(lockSync, null);
                reason = "locked loot";
                if (lockValue == null || Convert.ToBoolean(
                    _lootIsLocked.Invoke(lockValue, new object[] { player })))
                    return false;
                reason = string.Empty;
                return true;
            }
            catch (Exception error)
            {
                reason = Unwrap(error).GetType().Name + ": " + Unwrap(error).Message;
                RemoveLootFromCaches(objectId);
                return false;
            }
        }

        private static void RemovePublishedLoot(int objectId)
        {
            if (objectId <= 0)
                return;
            for (int index = _cachedLoots.Count - 1; index >= 0; index--)
            {
                LootSnapshot snapshot = _cachedLoots[index];
                if (snapshot != null && snapshot.ObjectId == objectId)
                    _cachedLoots.RemoveAt(index);
            }
            _cachedLootScan.Cached = _lootCache.Count;
            _cachedLootScan.Exported = _cachedLoots.Count;
        }

        private static void RemoveLootFromCaches(int objectId)
        {
            if (objectId <= 0)
                return;
            _lootCache.Remove(objectId);
            RemovePublishedLoot(objectId);
        }

        private static void ProcessLootForCache(
            object loot,
            object mapInstance,
            object player,
            object playerPositionValue,
            string localPlayerId,
            bool requiresMapFilter,
            LootScanDiagnostics diagnostics
        )
        {
            int objectId = 0;
            try
            {
                if (loot == null || !_lootType.IsInstanceOfType(loot))
                    return;
                objectId = Convert.ToInt32(
                    _objectId.GetValue(loot, null), CultureInfo.InvariantCulture
                );
                if (objectId <= 0)
                {
                    diagnostics.RejectedInvalidObjectId++;
                    return;
                }
                object gameObject = _componentGameObject.GetValue(loot, null);
                if (gameObject == null || !Convert.ToBoolean(
                    _gameObjectActiveInHierarchy.GetValue(gameObject, null)
                ))
                {
                    diagnostics.RejectedInactive++;
                    RemoveLootFromCaches(objectId);
                    return;
                }

                object transform = _componentTransform.GetValue(loot, null);
                object positionValue = transform == null ? null
                    : _transformPosition.GetValue(transform, null);
                if (requiresMapFilter && !SceneLootMatchesMap(
                    loot, mapInstance, playerPositionValue, positionValue
                ))
                {
                    diagnostics.RejectedOtherMap++;
                    RemoveLootFromCaches(objectId);
                    return;
                }

                object dtoSync = _lootDto.GetValue(loot, null);
                object dto = dtoSync == null ? null
                    : _lootDtoValue.GetValue(dtoSync, null);
                if (dto == null)
                {
                    diagnostics.RejectedNoData++;
                    return;
                }
                object rarityValue = _lootDtoRarity.GetValue(dto, null);
                string lootType = Convert.ToString(
                    _lootDtoType.GetValue(dto, null), CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (string.Equals(lootType, "Equip", StringComparison.OrdinalIgnoreCase)
                    || string.Equals(
                        lootType, "Equipment", StringComparison.OrdinalIgnoreCase
                    ))
                {
                    RemoveLootFromCaches(objectId);
                    return;
                }

                object lockSync = _lootLock.GetValue(loot, null);
                object lockValue = lockSync == null ? null
                    : _lootLockValue.GetValue(lockSync, null);
                string ownerPlayerId = lockValue == null ? string.Empty
                    : Convert.ToString(
                        _lockPlayerId.GetValue(lockValue, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                int ownerPartyId = lockValue == null ? 0
                    : Convert.ToInt32(
                        _lockPartyId.GetValue(lockValue, null),
                        CultureInfo.InvariantCulture
                    );
                bool ownedByLocalPlayer = !string.IsNullOrEmpty(localPlayerId)
                    && string.Equals(
                        ownerPlayerId, localPlayerId, StringComparison.Ordinal
                    );

                LootSnapshot snapshot = new LootSnapshot();
                snapshot.ObjectId = objectId;
                snapshot.ItemId = string.Empty;
                snapshot.DisplayName = Convert.ToString(
                    _lootDisplayName.GetValue(loot, null),
                    CultureInfo.InvariantCulture
                ) ?? string.Empty;
                if (string.IsNullOrEmpty(snapshot.DisplayName))
                {
                    snapshot.DisplayName = Convert.ToString(
                        _lootDtoDisplayName.GetValue(dto, null),
                        CultureInfo.InvariantCulture
                    ) ?? string.Empty;
                }
                snapshot.SpriteId = Convert.ToString(
                    _lootDtoSpriteId.GetValue(dto, null),
                    CultureInfo.InvariantCulture
                ) ?? string.Empty;
                snapshot.Rarity = Convert.ToString(
                    rarityValue, CultureInfo.InvariantCulture
                ) ?? string.Empty;
                snapshot.RarityValue = Convert.ToInt32(
                    rarityValue, CultureInfo.InvariantCulture
                );
                snapshot.LootType = lootType;
                snapshot.PositionValue = positionValue;
                snapshot.Position = ReadVector(positionValue);
                snapshot.ViewportPosition = new VectorData(0f, 0f, -1f);
                snapshot.ViewportVisible = false;
                snapshot.Locked = lockValue != null && Convert.ToBoolean(
                    _lootIsLocked.Invoke(lockValue, new object[] { player })
                );
                snapshot.OwnerPlayerId = ownerPlayerId;
                snapshot.OwnerPartyId = ownerPartyId;
                snapshot.OwnedByLocalPlayer = ownedByLocalPlayer;
                snapshot.InteractionRange = Convert.ToSingle(
                    _lootInteractionRange.GetValue(loot, null),
                    CultureInfo.InvariantCulture
                );

                CachedLootEntry entry;
                if (!_lootCache.TryGetValue(objectId, out entry))
                {
                    entry = new CachedLootEntry();
                    _lootCache[objectId] = entry;
                }
                entry.SourceValue = loot;
                entry.Snapshot = snapshot;
                entry.SeenPass = _lootScanPass;
                diagnostics.Accepted++;
                if (ownedByLocalPlayer)
                    diagnostics.AcceptedLocal++;
                else
                    diagnostics.AcceptedForeign++;
            }
            catch (Exception error)
            {
                diagnostics.RejectedError++;
                Exception actual = Unwrap(error);
                diagnostics.LastError = actual.GetType().Name
                    + ": " + actual.Message;
            }
        }

        private static List<LootSnapshot> BuildLootExport(
            VectorData playerPosition,
            int priorityLootObjectId,
            LootScanDiagnostics diagnostics
        )
        {
            List<LootSnapshot> result = new List<LootSnapshot>(_lootCache.Count);
            foreach (CachedLootEntry entry in _lootCache.Values)
            {
                if (entry != null && entry.Snapshot != null)
                    result.Add(entry.Snapshot);
            }
            result.Sort(delegate(LootSnapshot left, LootSnapshot right)
            {
                bool leftPriority = left.ObjectId == priorityLootObjectId;
                bool rightPriority = right.ObjectId == priorityLootObjectId;
                if (leftPriority != rightPriority)
                    return leftPriority ? -1 : 1;
                float leftDistance = HorizontalDistanceSquared(
                    playerPosition, left.Position
                );
                float rightDistance = HorizontalDistanceSquared(
                    playerPosition, right.Position
                );
                bool leftNearby = leftDistance <= NearbyLootExportRadiusSquared;
                bool rightNearby = rightDistance <= NearbyLootExportRadiusSquared;
                if (leftNearby != rightNearby)
                    return leftNearby ? -1 : 1;
                if (left.OwnedByLocalPlayer != right.OwnedByLocalPlayer)
                    return left.OwnedByLocalPlayer ? -1 : 1;
                if (!leftNearby && left.OwnedByLocalPlayer)
                {
                    int ownedRarityOrder = right.RarityValue.CompareTo(
                        left.RarityValue
                    );
                    if (ownedRarityOrder != 0)
                        return ownedRarityOrder;
                }
                int distanceOrder = leftDistance.CompareTo(rightDistance);
                if (distanceOrder != 0)
                    return distanceOrder;
                int rarityOrder = right.RarityValue.CompareTo(left.RarityValue);
                return rarityOrder != 0
                    ? rarityOrder : left.ObjectId.CompareTo(right.ObjectId);
            });
            if (result.Count > LootCacheLimit)
            {
                HashSet<int> retainedObjectIds = new HashSet<int>();
                for (int index = 0; index < LootCacheLimit; index++)
                    retainedObjectIds.Add(result[index].ObjectId);
                List<int> discardedObjectIds = new List<int>();
                foreach (int objectId in _lootCache.Keys)
                {
                    if (!retainedObjectIds.Contains(objectId))
                        discardedObjectIds.Add(objectId);
                }
                for (int index = 0; index < discardedObjectIds.Count; index++)
                    _lootCache.Remove(discardedObjectIds[index]);
                result.RemoveRange(
                    LootCacheLimit, result.Count - LootCacheLimit
                );
            }
            if (result.Count > LootExportLimit)
                result.RemoveRange(LootExportLimit, result.Count - LootExportLimit);
            diagnostics.Cached = _lootCache.Count;
            diagnostics.Exported = result.Count;
            return result;
        }

        private static void CompleteLootScanPass(LootScanDiagnostics diagnostics)
        {
            List<int> stale = new List<int>();
            foreach (KeyValuePair<int, CachedLootEntry> pair in _lootCache)
            {
                if (pair.Value == null || pair.Value.SeenPass != _lootScanPass)
                    stale.Add(pair.Key);
            }
            for (int index = 0; index < stale.Count; index++)
                _lootCache.Remove(stale[index]);
            diagnostics.PassCompleted = true;
            AdvanceLootScanPass();
        }

        private static void AdvanceLootScanPass()
        {
            if (_lootScanPass == int.MaxValue)
            {
                _lootScanPass = 1;
                _lootCache.Clear();
            }
            else
            {
                _lootScanPass++;
            }
        }

        private static void ResetLootScanState(bool clearTrackedLoots)
        {
            _lootCache.Clear();
            _lootScanCursor = 0;
            _lootScanSource = string.Empty;
            AdvanceLootScanPass();
            if (clearTrackedLoots)
            {
                _trackedLoots.Clear();
                _lootSceneSeedMapId = long.MinValue;
                _lootSceneSeedInstanceId = long.MinValue;
            }
        }

        private static long ElapsedMilliseconds(long startedTicks)
        {
            return (Timer.ElapsedTicks - startedTicks) * 1000L
                / Stopwatch.Frequency;
        }

        private static float HorizontalDistanceSquared(
            VectorData left, VectorData right
        )
        {
            float x = left.X - right.X;
            float z = left.Z - right.Z;
            return x * x + z * z;
        }

        private static List<MapExitSnapshot> CollectMapExits()
        {
            List<MapExitSnapshot> result = new List<MapExitSnapshot>();
            if (_findSceneMapExits == null)
                return result;
            object list;
            try
            {
                list = _findSceneMapExits.Invoke(
                    null, new object[] { _findObjectsSortNone }
                );
            }
            catch
            {
                return result;
            }
            int count = list == null ? 0 : CollectionCount(list);
            for (int index = 0; index < count; index++)
            {
                try
                {
                    object mapExit = CollectionItem(list, index);
                    if (mapExit == null || !_mapExitType.IsInstanceOfType(mapExit))
                        continue;
                    object gameObject = _componentGameObject.GetValue(mapExit, null);
                    if (gameObject == null || !Convert.ToBoolean(
                        _gameObjectActiveInHierarchy.GetValue(gameObject, null)
                    ))
                        continue;
                    object transform = _componentTransform.GetValue(mapExit, null);
                    if (transform == null)
                        continue;
                    MapExitSnapshot snapshot = new MapExitSnapshot();
                    snapshot.Position = ReadVector(
                        _transformPosition.GetValue(transform, null)
                    );
                    snapshot.InteractionRange = Math.Max(
                        0f,
                        Convert.ToSingle(
                            _mapExitInteractionRange.GetValue(mapExit, null),
                            CultureInfo.InvariantCulture
                        )
                    );
                    result.Add(snapshot);
                }
                catch
                {
                    // One malformed or unloading exit must not invalidate the
                    // navigation snapshot; it will be retried on the next scan.
                }
            }
            return result;
        }

        private static bool SceneLootMatchesMap(
            object loot,
            object mapInstance,
            object playerPositionValue,
            object lootPositionValue
        )
        {
            object networkObject = _networkObject.GetValue(loot, null);
            if (networkObject == null)
                return false;
            long mapId = Convert.ToInt64(
                _networkMapId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            long instanceId = Convert.ToInt64(
                _networkInstanceId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            if (SameMapIdentity(mapInstance, mapId, instanceId))
                return true;
            if (mapId != 0 || instanceId != 0)
                return false;
            return HasUsableNavMeshPath(
                playerPositionValue, lootPositionValue, null
            );
        }

        private static List<MonsterSnapshot> CollectEnemyMonsters(
            object mapInstance,
            object playerPositionValue,
            object camera,
            MonsterScanDiagnostics diagnostics
        )
        {
            List<MonsterSnapshot> result = new List<MonsterSnapshot>();
            object monsters = _monsters.GetValue(mapInstance, null);
            object units = _units.GetValue(mapInstance, null);
            diagnostics.MonstersCount = monsters == null
                ? 0 : CollectionCount(monsters);
            diagnostics.UnitsCount = units == null
                ? 0 : CollectionCount(units);

            object list = monsters;
            diagnostics.Source = "monsters";
            diagnostics.SourceCount = diagnostics.MonstersCount;
            if (diagnostics.SourceCount == 0 && diagnostics.UnitsCount > 0)
            {
                list = units;
                diagnostics.Source = "units";
                diagnostics.SourceCount = diagnostics.UnitsCount;
            }
            if (diagnostics.SourceCount == 0)
            {
                diagnostics.Source = "scene";
                if (_findSceneMonsters == null)
                {
                    diagnostics.SceneStatus = "unavailable: "
                        + (_sceneScanInitializationError ?? "unknown");
                    list = null;
                }
                else
                {
                    try
                    {
                        list = _findSceneMonsters.Invoke(
                            null, new object[] { _findObjectsSortNone }
                        );
                        diagnostics.SceneCount = list == null
                            ? 0 : CollectionCount(list);
                        diagnostics.SourceCount = diagnostics.SceneCount;
                        diagnostics.SceneStatus = "ok";
                    }
                    catch (Exception error)
                    {
                        Exception actual = Unwrap(error);
                        diagnostics.SceneStatus = "error: "
                            + actual.GetType().Name + ": " + actual.Message;
                        list = null;
                    }
                }
            }
            if (list == null)
                return result;

            int count = diagnostics.SourceCount;
            for (int index = 0; index < count; index++)
            {
                object unit = CollectionItem(list, index);
                if (unit == null)
                    continue;
                object monster = _monsterType.IsInstanceOfType(unit)
                    ? unit
                    : _tryCastMonster.Invoke(unit, null);
                if (monster == null)
                    continue;
                diagnostics.Castable++;
                if (Convert.ToBoolean(_isTrainingDummy.GetValue(monster, null)))
                {
                    diagnostics.RejectedTrainingDummy++;
                    continue;
                }
                if (!Convert.ToBoolean(_isActive.GetValue(monster, null)))
                {
                    diagnostics.RejectedInactive++;
                    continue;
                }
                if (!Convert.ToBoolean(_isAliveAndDisplayed.GetValue(monster, null)))
                {
                    diagnostics.RejectedNotDisplayed++;
                    continue;
                }

                object health = _health.GetValue(monster, null);
                if (health == null
                    || !Convert.ToBoolean(_healthIsAlive.GetValue(health, null)))
                {
                    diagnostics.RejectedDead++;
                    continue;
                }

                object syncData = _monsterData.GetValue(monster, null);
                object data = syncData == null
                    ? null
                    : _syncVarValue.GetValue(syncData, null);
                if (data == null)
                {
                    diagnostics.RejectedNoData++;
                    continue;
                }
                int team = Convert.ToInt32(
                    _monsterTeam.GetValue(data, null), CultureInfo.InvariantCulture
                );
                if (!diagnostics.TeamValues.Contains(team))
                    diagnostics.TeamValues.Add(team);
                if (team != EnemyCombatTeamValue)
                {
                    diagnostics.RejectedNotEnemy++;
                    continue;
                }

                object positionValue = _position.GetValue(monster, null);
                if (diagnostics.Source == "scene"
                    && !SceneMonsterMatchesMap(
                        monster,
                        mapInstance,
                        playerPositionValue,
                        positionValue,
                        diagnostics
                    ))
                    continue;

                string configId = Convert.ToString(
                    _configId.GetValue(monster, null), CultureInfo.InvariantCulture
                );
                if (string.IsNullOrEmpty(configId))
                {
                    configId = Convert.ToString(
                        _monsterId.GetValue(data, null), CultureInfo.InvariantCulture
                    );
                }

                MonsterSnapshot snapshot = new MonsterSnapshot();
                snapshot.ObjectId = Convert.ToInt32(
                    _objectId.GetValue(monster, null), CultureInfo.InvariantCulture
                );
                snapshot.ConfigId = configId ?? string.Empty;
                snapshot.DisplayName = Convert.ToString(
                    _displayName.GetValue(monster, null), CultureInfo.InvariantCulture
                ) ?? string.Empty;
                snapshot.Rank = Convert.ToString(
                    _monsterRank.GetValue(monster, null), CultureInfo.InvariantCulture
                ) ?? string.Empty;
                snapshot.PositionValue = positionValue;
                snapshot.Position = ReadVector(positionValue);
                object aimPositionValue = MonsterAimPosition(monster, positionValue);
                snapshot.ViewportPosition = camera == null
                    ? new VectorData(0f, 0f, -1f)
                    : ReadVector(_worldToViewportPoint.Invoke(
                        camera, new object[] { aimPositionValue }
                    ));
                snapshot.ViewportVisible = snapshot.ViewportPosition.Z > 0f
                    && snapshot.ViewportPosition.X >= 0f
                    && snapshot.ViewportPosition.X <= 1f
                    && snapshot.ViewportPosition.Y >= 0f
                    && snapshot.ViewportPosition.Y <= 1f;
                snapshot.HealthRatio = Convert.ToSingle(
                    _healthRatio.GetValue(health, null), CultureInfo.InvariantCulture
                );
                snapshot.ColliderRadius = WorldColliderRadius(monster);
                result.Add(snapshot);
                diagnostics.Accepted++;
            }
            return result;
        }

        private static object MonsterAimPosition(object monster, object fallback)
        {
            if (_colliderBounds == null || _boundsCenter == null)
                return fallback;
            try
            {
                object collider = _collider.GetValue(monster, null);
                object bounds = collider == null
                    ? null : _colliderBounds.GetValue(collider, null);
                object center = bounds == null
                    ? null : _boundsCenter.GetValue(bounds, null);
                return center ?? fallback;
            }
            catch
            {
                return fallback;
            }
        }

        private static bool SceneMonsterMatchesMap(
            object monster,
            object mapInstance,
            object playerPositionValue,
            object monsterPositionValue,
            MonsterScanDiagnostics diagnostics
        )
        {
            object networkObject = _networkObject.GetValue(monster, null);
            if (networkObject == null)
            {
                diagnostics.RejectedNoNetworkObject++;
                return false;
            }

            long mapId = Convert.ToInt64(
                _networkMapId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            long instanceId = Convert.ToInt64(
                _networkInstanceId.GetValue(networkObject, null),
                CultureInfo.InvariantCulture
            );
            RecordNetworkMap(diagnostics, mapId, instanceId);
            if (SameMapIdentity(mapInstance, mapId, instanceId))
                return true;

            if (mapId != 0 || instanceId != 0)
            {
                diagnostics.RejectedOtherMap++;
                return false;
            }

            diagnostics.UnknownMapCandidates++;
            if (HasUsableNavMeshPath(
                playerPositionValue, monsterPositionValue, diagnostics
            ))
            {
                diagnostics.AcceptedByNavMesh++;
                return true;
            }
            diagnostics.RejectedNoNavMesh++;
            return false;
        }

        private static bool HasUsableNavMeshPath(
            object source,
            object target,
            MonsterScanDiagnostics diagnostics
        )
        {
            try
            {
                _clearCorners.Invoke(_filterNavPath, null);
                bool calculated = Convert.ToBoolean(
                    _calculatePath.Invoke(
                        null,
                        new object[] { source, target, _allAreas, _filterNavPath }
                    ),
                    CultureInfo.InvariantCulture
                );
                if (!calculated)
                    return false;
                string status = PathStatusName(
                    _pathStatus.GetValue(_filterNavPath, null)
                );
                return status == "complete" || status == "partial";
            }
            catch (Exception error)
            {
                Exception actual = Unwrap(error);
                if (diagnostics != null)
                {
                    diagnostics.NavMeshFilterError = actual.GetType().Name
                        + ": " + actual.Message;
                }
                return false;
            }
        }

        private static void RecordNetworkMap(
            MonsterScanDiagnostics diagnostics,
            long mapId,
            long instanceId
        )
        {
            string key = mapId.ToString(CultureInfo.InvariantCulture)
                + "/" + instanceId.ToString(CultureInfo.InvariantCulture);
            int count;
            diagnostics.NetworkMapCounts.TryGetValue(key, out count);
            diagnostics.NetworkMapCounts[key] = count + 1;
        }

        private static bool SameMapIdentity(
            object expected,
            long candidateMap,
            long candidateInstance
        )
        {
            if (expected == null)
                return false;
            long expectedMap = Convert.ToInt64(
                _mapId.GetValue(expected, null), CultureInfo.InvariantCulture
            );
            long expectedInstance = Convert.ToInt64(
                _instanceId.GetValue(expected, null), CultureInfo.InvariantCulture
            );
            return expectedMap == candidateMap
                && expectedInstance == candidateInstance;
        }

        private static void AppendMonsterScan(
            StringBuilder json,
            MonsterScanDiagnostics diagnostics
        )
        {
            json.Append(",\"monster_scan\":{");
            AppendString(json, "source", diagnostics.Source, false);
            AppendNumber(json, "monsters_count", diagnostics.MonstersCount);
            AppendNumber(json, "units_count", diagnostics.UnitsCount);
            AppendNumber(json, "scene_count", diagnostics.SceneCount);
            AppendString(json, "scene_status", diagnostics.SceneStatus);
            AppendNumber(json, "source_count", diagnostics.SourceCount);
            AppendNumber(json, "castable", diagnostics.Castable);
            AppendNumber(
                json,
                "rejected_no_network_object",
                diagnostics.RejectedNoNetworkObject
            );
            AppendNumber(
                json, "rejected_other_map", diagnostics.RejectedOtherMap
            );
            AppendNumber(
                json, "unknown_map_candidates", diagnostics.UnknownMapCandidates
            );
            AppendNumber(
                json, "accepted_by_navmesh", diagnostics.AcceptedByNavMesh
            );
            AppendNumber(
                json, "rejected_no_navmesh", diagnostics.RejectedNoNavMesh
            );
            AppendString(
                json, "navmesh_filter_error", diagnostics.NavMeshFilterError
            );
            AppendNumber(
                json, "rejected_training_dummy", diagnostics.RejectedTrainingDummy
            );
            AppendNumber(json, "rejected_inactive", diagnostics.RejectedInactive);
            AppendNumber(
                json, "rejected_not_displayed", diagnostics.RejectedNotDisplayed
            );
            AppendNumber(json, "rejected_dead", diagnostics.RejectedDead);
            AppendNumber(json, "rejected_no_data", diagnostics.RejectedNoData);
            AppendNumber(json, "rejected_not_enemy", diagnostics.RejectedNotEnemy);
            AppendNumber(json, "accepted", diagnostics.Accepted);
            json.Append(",\"team_values\":[");
            for (int index = 0; index < diagnostics.TeamValues.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                json.Append(diagnostics.TeamValues[index].ToString(
                    CultureInfo.InvariantCulture
                ));
            }
            json.Append(']');
            json.Append(",\"network_maps\":{");
            bool firstMap = true;
            foreach (KeyValuePair<string, int> pair in diagnostics.NetworkMapCounts)
            {
                if (!firstMap)
                    json.Append(',');
                firstMap = false;
                AppendName(json, pair.Key);
                json.Append(pair.Value.ToString(CultureInfo.InvariantCulture));
            }
            json.Append("}}");
        }

        private static void AppendPlayerScan(
            StringBuilder json,
            PlayerScanDiagnostics diagnostics
        )
        {
            json.Append(",\"player_scan\":{");
            AppendString(json, "source", diagnostics.Source, false);
            AppendNumber(json, "map_count", diagnostics.MapCount);
            AppendNumber(json, "scene_count", diagnostics.SceneCount);
            AppendNumber(json, "source_count", diagnostics.SourceCount);
            AppendNumber(json, "castable", diagnostics.Castable);
            AppendNumber(json, "rejected_local", diagnostics.RejectedLocal);
            AppendNumber(json, "rejected_inactive", diagnostics.RejectedInactive);
            AppendNumber(json, "rejected_other_map", diagnostics.RejectedOtherMap);
            AppendNumber(
                json,
                "rejected_invalid_object_id",
                diagnostics.RejectedInvalidObjectId
            );
            AppendNumber(json, "rejected_duplicate", diagnostics.RejectedDuplicate);
            AppendNumber(json, "rejected_error", diagnostics.RejectedError);
            AppendNumber(json, "accepted", diagnostics.Accepted);
            AppendNumber(
                json, "selected_object_id", diagnostics.SelectedObjectId
            );
            AppendString(
                json, "selection_source", diagnostics.SelectionSource
            );
            AppendString(json, "last_error", diagnostics.LastError);
            json.Append('}');
        }

        private static void AppendLootScan(
            StringBuilder json,
            LootScanDiagnostics diagnostics
        )
        {
            json.Append(",\"loot_scan\":{");
            AppendString(json, "source", diagnostics.Source, false);
            json.Append(",\"active\":");
            json.Append(diagnostics.Active ? "true" : "false");
            json.Append(",\"incremental\":");
            json.Append(diagnostics.Incremental ? "true" : "false");
            AppendNumber(json, "map_count", diagnostics.MapCount);
            AppendNumber(json, "scene_count", diagnostics.SceneCount);
            AppendNumber(json, "source_count", diagnostics.SourceCount);
            AppendNumber(json, "batch_limit", diagnostics.BatchLimit);
            AppendNumber(json, "processed", diagnostics.Processed);
            AppendNumber(json, "cached", diagnostics.Cached);
            AppendNumber(json, "exported", diagnostics.Exported);
            json.Append(",\"pass_completed\":");
            json.Append(diagnostics.PassCompleted ? "true" : "false");
            json.Append(",\"scene_fallback_deferred\":");
            json.Append(diagnostics.SceneFallbackDeferred ? "true" : "false");
            AppendString(json, "viewport_projection", "disabled_not_required");
            AppendNumber(json, "rejected_inactive", diagnostics.RejectedInactive);
            AppendNumber(json, "rejected_other_map", diagnostics.RejectedOtherMap);
            AppendNumber(json, "rejected_no_data", diagnostics.RejectedNoData);
            AppendNumber(
                json,
                "rejected_invalid_object_id",
                diagnostics.RejectedInvalidObjectId
            );
            AppendString(json, "ownership_filter", "all");
            AppendNumber(json, "rejected_not_owned", 0);
            AppendNumber(json, "rejected_error", diagnostics.RejectedError);
            AppendNumber(json, "accepted", diagnostics.Accepted);
            AppendNumber(json, "accepted_local", diagnostics.AcceptedLocal);
            AppendNumber(json, "accepted_foreign", diagnostics.AcceptedForeign);
            AppendString(json, "last_error", diagnostics.LastError);
            json.Append('}');
        }

        private static int CollectionCount(object collection)
        {
            PropertyInfo count = collection.GetType().GetProperty("Count");
            if (count == null)
                count = collection.GetType().GetProperty("Length");
            if (count == null)
                throw new MissingMemberException(collection.GetType().FullName, "Count");
            return Convert.ToInt32(count.GetValue(collection, null));
        }

        private static object CollectionItem(object collection, int index)
        {
            PropertyInfo item = collection.GetType().GetProperty("Item");
            if (item == null)
                throw new MissingMemberException(collection.GetType().FullName, "Item");
            return item.GetValue(collection, new object[] { index });
        }

        private static List<VectorData> ReadVectorCollection(object collection)
        {
            List<VectorData> result = new List<VectorData>();
            if (collection == null)
                return result;

            IEnumerable enumerable = collection as IEnumerable;
            if (enumerable != null)
            {
                foreach (object value in enumerable)
                    result.Add(ReadVector(value));
                return result;
            }

            int count = CollectionCount(collection);
            for (int index = 0; index < count; index++)
                result.Add(ReadVector(CollectionItem(collection, index)));
            return result;
        }

        private static string PathStatusName(object value)
        {
            string name = Convert.ToString(value, CultureInfo.InvariantCulture);
            if (name == "PathComplete")
                return "complete";
            if (name == "PathPartial")
                return "partial";
            return "invalid";
        }

        private static VectorData ReadVector(object value)
        {
            if (value == null)
                return new VectorData(0f, 0f, 0f);
            Type type = value.GetType();
            return new VectorData(
                ReadFloatMember(type, value, "x"),
                ReadFloatMember(type, value, "y"),
                ReadFloatMember(type, value, "z")
            );
        }

        private static float ReadFloatMember(Type type, object value, string name)
        {
            FieldInfo field = type.GetField(
                name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance
            );
            if (field != null)
                return Convert.ToSingle(field.GetValue(value), CultureInfo.InvariantCulture);
            PropertyInfo property = type.GetProperty(
                name, BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance
            );
            if (property != null)
                return Convert.ToSingle(property.GetValue(value, null), CultureInfo.InvariantCulture);
            throw new MissingMemberException(type.FullName, name);
        }

        private static float WorldColliderRadius(object unit)
        {
            float fallback = Math.Max(
                0.1f,
                Convert.ToSingle(
                    _defaultColliderRadius.GetValue(unit, null),
                    CultureInfo.InvariantCulture
                )
            );
            try
            {
                object collider = _collider.GetValue(unit, null);
                if (collider == null)
                    return fallback;
                object transform = _componentTransform.GetValue(collider, null);
                VectorData scale = ReadVector(
                    _transformLossyScale.GetValue(transform, null)
                );
                float radius = Convert.ToSingle(
                    _capsuleRadius.GetValue(collider, null), CultureInfo.InvariantCulture
                );
                float horizontalScale = Math.Max(Math.Abs(scale.X), Math.Abs(scale.Z));
                return Math.Max(0.1f, radius * horizontalScale);
            }
            catch
            {
                return fallback;
            }
        }

        private static VectorData NormalizeHorizontal(
            VectorData value,
            VectorData fallback
        )
        {
            float length = (float)Math.Sqrt(value.X * value.X + value.Z * value.Z);
            if (length < 0.0001f)
                return fallback;
            return new VectorData(value.X / length, 0f, value.Z / length);
        }

        internal static NavigationRequest ReadRequest(long nowMilliseconds)
        {
            try
            {
                if (!File.Exists(Plugin.RequestPath))
                    return null;
                string json;
                using (FileStream stream = new FileStream(
                    Plugin.RequestPath,
                    FileMode.Open,
                    FileAccess.Read,
                    FileShare.ReadWrite | FileShare.Delete
                ))
                using (StreamReader reader = new StreamReader(
                    stream, Encoding.UTF8, true
                ))
                {
                    json = reader.ReadToEnd();
                }
                Match requestId = RequestIdPattern.Match(json);
                Match targetId = TargetIdPattern.Match(json);
                Match targetKind = TargetKindPattern.Match(json);
                Match timestamp = TimestampPattern.Match(json);
                if (!requestId.Success || !targetId.Success || !timestamp.Success)
                    return null;

                NavigationRequest request = new NavigationRequest();
                request.RequestId = long.Parse(
                    requestId.Groups[1].Value, CultureInfo.InvariantCulture
                );
                request.TargetObjectId = int.Parse(
                    targetId.Groups[1].Value, CultureInfo.InvariantCulture
                );
                request.TargetKind = targetKind.Success
                    ? targetKind.Groups[1].Value.ToLowerInvariant()
                    : "monster";
                request.FollowChannelRequestId = Math.Max(
                    0L,
                    ReadLong(json, FollowChannelRequestIdPattern, 0L)
                );
                Match followPlayerId = FollowPlayerIdPattern.Match(json);
                request.FollowPlayerId = followPlayerId.Success
                    ? UnescapeJson(followPlayerId.Groups[1].Value)
                    : string.Empty;
                request.ChannelSwitchRequestId = Math.Max(
                    0L,
                    ReadLong(json, ChannelSwitchRequestIdPattern, 0L)
                );
                request.ChannelSwitchIndex = (int)ReadLong(
                    json, ChannelSwitchIndexPattern, -1L
                );
                request.ConsumableUseRequestId = Math.Max(
                    0L,
                    ReadLong(json, ConsumableUseRequestIdPattern, 0L)
                );
                Match consumableName = ConsumableNamePattern.Match(json);
                request.ConsumableName = consumableName.Success
                    ? UnescapeJson(consumableName.Groups[1].Value)
                    : string.Empty;
                request.TimestampMilliseconds = long.Parse(
                    timestamp.Groups[1].Value, CultureInfo.InvariantCulture
                );
                request.BotActive = ReadBoolean(json, BotActivePattern, false);
                Match movementKeys = MovementKeysPattern.Match(json);
                request.MovementKeys = movementKeys.Success
                    ? movementKeys.Groups[1].Value.ToLowerInvariant()
                    : string.Empty;
                Match shiftKeys = ShiftKeysPattern.Match(json);
                request.ShiftKeys = shiftKeys.Success
                    ? shiftKeys.Groups[1].Value.ToLowerInvariant()
                    : string.Empty;
                Match summonAction = SummonActionPattern.Match(json);
                request.SummonAction = summonAction.Success
                    ? summonAction.Groups[1].Value.ToLowerInvariant()
                    : string.Empty;
                request.SkillKeyRequestId = Math.Max(
                    0L, ReadLong(json, SkillKeyRequestIdPattern, 0L)
                );
                Match skillKey = SkillKeyPattern.Match(json);
                request.SkillKey = skillKey.Success
                    ? skillKey.Groups[1].Value.ToLowerInvariant()
                    : string.Empty;
                request.SkillKeyTargetSummon = ReadBoolean(
                    json, SkillKeyTargetSummonPattern, false
                );
                request.LootInteract = Math.Max(
                    0, ReadInteger(json, LootInteractPattern, 0)
                );
                request.LootInteractObjectId = Math.Max(
                    0, ReadInteger(json, LootInteractObjectIdPattern, 0)
                );
                request.FocusTargetObjectId = Math.Max(
                    0, ReadInteger(json, FocusTargetIdPattern, 0)
                );
                Match focusTargetWorld = FocusTargetWorldPattern.Match(json);
                if (focusTargetWorld.Success)
                {
                    request.FocusTargetWorldX = float.Parse(
                        focusTargetWorld.Groups[1].Value,
                        CultureInfo.InvariantCulture
                    );
                    request.FocusTargetWorldY = float.Parse(
                        focusTargetWorld.Groups[2].Value,
                        CultureInfo.InvariantCulture
                    );
                    request.FocusTargetWorldZ = float.Parse(
                        focusTargetWorld.Groups[3].Value,
                        CultureInfo.InvariantCulture
                    );
                }
                Match movementVector = MovementVectorPattern.Match(json);
                if (movementVector.Success)
                {
                    request.MovementWorldX = Math.Max(
                        -1, Math.Min(1, int.Parse(
                            movementVector.Groups[1].Value,
                            CultureInfo.InvariantCulture
                        ))
                    );
                    request.MovementWorldY = Math.Max(
                        -1, Math.Min(1, int.Parse(
                            movementVector.Groups[2].Value,
                            CultureInfo.InvariantCulture
                        ))
                    );
                    request.MovementWorldZ = Math.Max(
                        -1, Math.Min(1, int.Parse(
                            movementVector.Groups[3].Value,
                            CultureInfo.InvariantCulture
                        ))
                    );
                }
                Match backgroundInputMode = BackgroundInputModePattern.Match(json);
                request.BackgroundInputMode = backgroundInputMode.Success
                    ? backgroundInputMode.Groups[1].Value.ToLowerInvariant()
                    : "inputs";
                Match backgroundSkillMode = BackgroundSkillModePattern.Match(json);
                request.BackgroundSkillMode = backgroundSkillMode.Success
                    ? backgroundSkillMode.Groups[1].Value.ToLowerInvariant()
                    : "capture";
                request.ProbeActive = ReadBoolean(
                    json, ProbeActivePattern, request.BotActive
                );
                request.LootScanActive = ReadBoolean(
                    json, LootScanActivePattern, request.ProbeActive
                );
                request.PartyFollowActive = ReadBoolean(
                    json, PartyFollowActivePattern, false
                );
                request.AutoReloginEnabled = ReadBoolean(
                    json, AutoReloginEnabledPattern, false
                );
                request.AutoReloginDisconnectGraceSeconds = Math.Max(
                    0.5f,
                    ReadSingle(json, ReloginDisconnectGracePattern, 3f)
                );
                request.AutoReloginBuiltinWaitMaxSeconds = Math.Max(
                    0f,
                    ReadSingle(json, ReloginBuiltinWaitPattern, 30f)
                );
                request.AutoReloginAttemptTimeoutSeconds = Math.Max(
                    1f,
                    ReadSingle(json, ReloginAttemptTimeoutPattern, 30f)
                );
                request.AutoReloginRetryDelaySeconds = Math.Max(
                    0f,
                    ReadSingle(json, ReloginRetryDelayPattern, 10f)
                );
                request.AutoReloginMaxAttempts = Math.Min(
                    20,
                    Math.Max(1, ReadInteger(json, ReloginMaxAttemptsPattern, 5))
                );
                bool navigationRequest = request.RequestId > 0
                    && request.TargetObjectId > 0
                    && (request.TargetKind == "monster"
                        || request.TargetKind == "loot"
                        || request.TargetKind == "player");
                bool heartbeatRequest = request.RequestId >= 0
                    && request.TargetObjectId <= 0
                    && request.TargetKind == "none";
                if (!navigationRequest && !heartbeatRequest)
                    return null;
                if (Math.Abs(nowMilliseconds - request.TimestampMilliseconds)
                    > RequestMaxAgeMilliseconds)
                    return null;
                return request;
            }
            catch
            {
                return null;
            }
        }

        private static bool ReadBoolean(
            string json, Regex pattern, bool fallback
        )
        {
            Match match = pattern.Match(json);
            return match.Success
                ? string.Equals(
                    match.Groups[1].Value, "true",
                    StringComparison.OrdinalIgnoreCase
                )
                : fallback;
        }

        private static float ReadSingle(
            string json, Regex pattern, float fallback
        )
        {
            Match match = pattern.Match(json);
            float value;
            return match.Success && float.TryParse(
                match.Groups[1].Value,
                NumberStyles.Float,
                CultureInfo.InvariantCulture,
                out value
            ) ? value : fallback;
        }

        private static int ReadInteger(
            string json, Regex pattern, int fallback
        )
        {
            Match match = pattern.Match(json);
            int value;
            return match.Success && int.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            ) ? value : fallback;
        }

        private static long ReadLong(
            string json, Regex pattern, long fallback
        )
        {
            Match match = pattern.Match(json);
            long value;
            return match.Success && long.TryParse(
                match.Groups[1].Value,
                NumberStyles.Integer,
                CultureInfo.InvariantCulture,
                out value
            ) ? value : fallback;
        }

        internal static void WriteReloginState(
            string status,
            string state,
            int attempt,
            int maximumAttempts,
            string message,
            string characterUid
        )
        {
            try
            {
                long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                StringBuilder json = new StringBuilder(512);
                json.Append(BuildUnavailableStatePrefix(status, timestamp, null));
                json.Append(",\"relogin\":{");
                AppendString(json, "state", state, false);
                AppendNumber(json, "attempt", attempt);
                AppendNumber(json, "max_attempts", maximumAttempts);
                AppendString(json, "message", message);
                AppendString(json, "last_character_id", characterUid);
                json.Append('}');
                AppendUnavailableStateSuffix(json);
                AtomicWrite(json.ToString());
            }
            catch
            {
                // Reconnect diagnostics must never escape into UIManager.LateUpdate.
            }
        }

        private static string BuildUnavailableState(
            string status,
            long timestamp,
            object player
        )
        {
            StringBuilder json = new StringBuilder(256);
            json.Append(BuildUnavailableStatePrefix(status, timestamp, player));
            AppendUnavailableStateSuffix(json);
            return json.ToString();
        }

        private static string BuildUnavailableStatePrefix(
            string status, long timestamp, object player
        )
        {
            StringBuilder json = new StringBuilder(256);
            json.Append('{');
            AppendNumber(json, "schema_version", Plugin.SchemaVersion, false);
            AppendNumber(json, "timestamp_ms", timestamp);
            AppendString(json, "status", status);
            json.Append(",\"map_id\":0,\"instance_id\":0");
            if (player == null)
                json.Append(",\"player\":null");
            else
            {
                json.Append(",\"player\":{");
                AppendVector(
                    json,
                    "position",
                    ReadVector(_position.GetValue(player, null)),
                    false
                );
                json.Append('}');
            }
            return json.ToString();
        }

        private static void AppendUnavailableStateSuffix(StringBuilder json)
        {
            json.Append(",\"players\":[]");
            json.Append(",\"player_scan\":null");
            json.Append(",\"party_members\":[]");
            AppendChannelSwitch(json, _channelSwitch);
            ConsumableUseService.AppendJson(json);
            json.Append(",\"monsters\":[]");
            json.Append(",\"monster_scan\":null");
            json.Append(",\"loots\":[],\"loot_scan\":null");
            json.Append(",\"map_exits\":[]");
            json.Append(",\"path\":{\"request_id\":0,\"target_kind\":\"none\",");
            json.Append("\"target_object_id\":0,");
            json.Append("\"status\":\"missing\",\"corners\":[]}}");
        }

        private static void TryWriteError(Exception error)
        {
            try
            {
                long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                StringBuilder json = new StringBuilder(256);
                json.Append('{');
                AppendNumber(json, "schema_version", Plugin.SchemaVersion, false);
                AppendNumber(json, "timestamp_ms", timestamp);
                AppendString(json, "status", "error");
                AppendString(json, "error", error.GetType().Name + ": " + error.Message);
                json.Append(",\"map_id\":0,\"instance_id\":0,\"player\":null,");
                json.Append("\"players\":[],\"player_scan\":null,");
                json.Append("\"party_members\":[]");
                AppendChannelSwitch(json, _channelSwitch);
                ConsumableUseService.AppendJson(json);
                json.Append(",\"monsters\":[],\"monster_scan\":null,");
                json.Append("\"loots\":[],\"loot_scan\":null,");
                json.Append("\"map_exits\":[],");
                json.Append("\"path\":{\"request_id\":0,");
                json.Append("\"target_kind\":\"none\",\"target_object_id\":0,");
                json.Append("\"status\":\"missing\",\"corners\":[]}}");
                AtomicWrite(json.ToString());
            }
            catch
            {
                // Diagnostics must never escape into Game.Update.
            }
        }

        private static void AtomicWrite(string contents)
        {
            bool scheduleWriter = false;
            lock (StateWriterLock)
            {
                _pendingStateContents = contents;
                if (!_stateWriterScheduled)
                {
                    _stateWriterScheduled = true;
                    scheduleWriter = true;
                }
            }
            if (!scheduleWriter)
                return;
            if (!ThreadPool.QueueUserWorkItem(StateWriterLoop))
            {
                lock (StateWriterLock)
                {
                    _stateWriterScheduled = false;
                    _pendingStateContents = null;
                }
                WriteStateFileNow(contents);
            }
        }

        private static void StateWriterLoop(object ignored)
        {
            while (true)
            {
                string contents;
                lock (StateWriterLock)
                {
                    contents = _pendingStateContents;
                    _pendingStateContents = null;
                    if (contents == null)
                    {
                        _stateWriterScheduled = false;
                        return;
                    }
                }
                try
                {
                    WriteStateFileNow(contents);
                }
                catch (Exception error)
                {
                    if (_log != null)
                    {
                        _log.LogWarning(
                            "Async navigation state write failed: "
                            + error.GetType().Name + ": " + error.Message
                        );
                    }
                }
            }
        }

        private static void WriteStateFileNow(string contents)
        {
            string temporary = Plugin.StatePath + ".tmp";
            Exception lastError = null;
            for (int attempt = 0; attempt < FileOperationAttempts; attempt++)
            {
                try
                {
                    File.WriteAllText(temporary, contents, new UTF8Encoding(false));
                    if (File.Exists(Plugin.StatePath))
                        File.Replace(temporary, Plugin.StatePath, null);
                    else
                        File.Move(temporary, Plugin.StatePath);
                    return;
                }
                catch (IOException error)
                {
                    lastError = error;
                }
                catch (UnauthorizedAccessException error)
                {
                    lastError = error;
                }

                if (attempt + 1 < FileOperationAttempts)
                    Thread.Sleep(2 << attempt);
            }
            throw lastError;
        }

        private static void AppendMonster(StringBuilder json, MonsterSnapshot monster)
        {
            json.Append('{');
            AppendNumber(json, "object_id", monster.ObjectId, false);
            AppendString(json, "config_id", monster.ConfigId);
            AppendString(json, "display_name", monster.DisplayName);
            AppendString(json, "rank", monster.Rank);
            AppendVector(json, "position", monster.Position);
            AppendVector(json, "viewport_position", monster.ViewportPosition);
            json.Append(",\"viewport_visible\":");
            json.Append(monster.ViewportVisible ? "true" : "false");
            AppendFloat(json, "health_ratio", monster.HealthRatio);
            AppendFloat(json, "collider_radius", monster.ColliderRadius);
            AppendString(json, "team", "enemy");
            json.Append(",\"alive\":true,\"visible\":true,\"training_dummy\":false");
            json.Append('}');
        }

        private static void AppendObservedPlayer(
            StringBuilder json,
            ObservedPlayerSnapshot player
        )
        {
            json.Append('{');
            AppendNumber(json, "object_id", player.ObjectId, false);
            AppendString(json, "player_id", player.PlayerId);
            AppendString(json, "display_name", player.DisplayName);
            AppendVector(json, "position", player.Position);
            AppendFloat(json, "collider_radius", player.ColliderRadius);
            json.Append(",\"alive\":");
            json.Append(player.Alive ? "true" : "false");
            json.Append(",\"visible\":");
            json.Append(player.Visible ? "true" : "false");
            json.Append(",\"party_member\":");
            json.Append(player.PartyMember ? "true" : "false");
            json.Append(",\"selected\":");
            json.Append(player.Selected ? "true" : "false");
            json.Append('}');
        }

        private static void AppendPartyMember(
            StringBuilder json,
            PartyMemberSnapshot member
        )
        {
            json.Append('{');
            AppendString(json, "display_name", member.DisplayName, false);
            AppendString(json, "player_id", member.PlayerId);
            AppendNumber(json, "object_id", member.ObjectId);
            AppendNumber(json, "map_id", member.MapId);
            AppendString(json, "instance_id", member.InstanceId);
            AppendNumber(json, "channel_index", member.ChannelIndex);
            json.Append(",\"is_local\":");
            json.Append(member.IsLocal ? "true" : "false");
            json.Append('}');
        }

        private static void AppendChannelSwitch(
            StringBuilder json,
            ChannelSwitchSnapshot channelSwitch
        )
        {
            json.Append(",\"channel_switch\":{");
            AppendNumber(json, "request_id", channelSwitch.RequestId, false);
            AppendString(json, "target_player_id", channelSwitch.TargetPlayerId);
            AppendNumber(json, "target_map_id", channelSwitch.TargetMapId);
            AppendString(
                json, "target_instance_id", channelSwitch.TargetInstanceId
            );
            AppendNumber(
                json,
                "target_channel_index",
                channelSwitch.TargetChannelIndex
            );
            AppendString(json, "status", channelSwitch.Status);
            AppendString(json, "error", channelSwitch.Error);
            json.Append('}');
        }

        private static void AppendLoot(StringBuilder json, LootSnapshot loot)
        {
            json.Append('{');
            AppendNumber(json, "object_id", loot.ObjectId, false);
            AppendString(json, "item_id", loot.ItemId);
            AppendString(json, "display_name", loot.DisplayName);
            AppendString(json, "sprite_id", loot.SpriteId);
            AppendString(json, "rarity", loot.Rarity);
            AppendNumber(json, "rarity_value", loot.RarityValue);
            AppendString(json, "loot_type", loot.LootType);
            AppendVector(json, "position", loot.Position);
            AppendVector(json, "viewport_position", loot.ViewportPosition);
            json.Append(",\"viewport_visible\":");
            json.Append(loot.ViewportVisible ? "true" : "false");
            json.Append(",\"locked\":");
            json.Append(loot.Locked ? "true" : "false");
            AppendString(json, "owner_player_id", loot.OwnerPlayerId);
            AppendNumber(json, "owner_party_id", loot.OwnerPartyId);
            json.Append(",\"owned_by_local_player\":");
            json.Append(loot.OwnedByLocalPlayer ? "true" : "false");
            AppendFloat(json, "interaction_range", loot.InteractionRange);
            json.Append('}');
        }

        private static void AppendMapExit(
            StringBuilder json, MapExitSnapshot mapExit
        )
        {
            json.Append('{');
            AppendVector(json, "position", mapExit.Position, false);
            AppendFloat(json, "interaction_range", mapExit.InteractionRange);
            json.Append('}');
        }

        private static void AppendNumber(
            StringBuilder json,
            string name,
            long value,
            bool comma = true
        )
        {
            if (comma)
                json.Append(',');
            AppendName(json, name);
            json.Append(value.ToString(CultureInfo.InvariantCulture));
        }

        private static void AppendFloat(StringBuilder json, string name, float value)
        {
            json.Append(',');
            AppendName(json, name);
            AppendRawFloat(json, value);
        }

        private static void AppendString(
            StringBuilder json,
            string name,
            string value,
            bool comma = true
        )
        {
            if (comma)
                json.Append(',');
            AppendName(json, name);
            json.Append('"');
            json.Append(EscapeJson(value ?? string.Empty));
            json.Append('"');
        }

        private static void AppendStatusComponent(
            StringBuilder json, StatusComponentSnapshot status
        )
        {
            json.Append(",\"status_component\":{");
            json.Append("\"available\":");
            json.Append(status.Available ? "true" : "false");
            AppendString(json, "error", status.Error);
            json.Append(",\"active_statuses_available\":");
            json.Append(status.ActiveStatusesAvailable ? "true" : "false");
            AppendString(
                json, "active_statuses_error", status.ActiveStatusesError
            );
            json.Append(",\"active_status_ids\":[");
            AppendStringValues(json, status.ActiveStatusIds);
            json.Append(']');
            json.Append(",\"buffs\":[");
            AppendStringValues(json, status.Buffs);
            json.Append("],\"debuffs\":[");
            AppendStringValues(json, status.Debuffs);
            json.Append("],\"effects\":[");
            for (int index = 0; index < status.Effects.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                StatusEffectSnapshot effect = status.Effects[index];
                json.Append('{');
                AppendString(json, "id", effect.Id, false);
                AppendString(json, "display_name", effect.DisplayName);
                AppendString(json, "category", effect.Category);
                AppendFloat(json, "duration", effect.Duration);
                AppendFloat(json, "duration_max", effect.DurationMax);
                AppendNumber(json, "level", effect.Level);
                AppendNumber(json, "stacks", effect.Stacks);
                AppendNumber(json, "max_stacks", effect.MaxStacks);
                json.Append(",\"infinite_duration\":");
                json.Append(effect.InfiniteDuration ? "true" : "false");
                json.Append(",\"is_skill\":");
                json.Append(effect.IsSkill ? "true" : "false");
                json.Append(",\"is_toggle\":");
                json.Append(effect.IsToggle ? "true" : "false");
                json.Append('}');
            }
            json.Append("]}");
        }

        private static void AppendSummonDisplays(
            StringBuilder json, SummonDisplaysSnapshot displays
        )
        {
            json.Append(",\"summon_displays\":{");
            json.Append("\"available\":");
            json.Append(displays.Available ? "true" : "false");
            AppendString(json, "error", displays.Error);
            json.Append(",\"items\":[");
            for (int index = 0; index < displays.Items.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                SummonDisplaySnapshot item = displays.Items[index];
                json.Append('{');
                AppendString(json, "skill_id", item.SkillId, false);
                AppendString(json, "id", item.Id);
                AppendNumber(json, "level", item.Level);
                json.Append('}');
            }
            json.Append("]}");
        }

        private static void AppendStringValues(
            StringBuilder json, List<string> values
        )
        {
            for (int index = 0; index < values.Count; index++)
            {
                if (index > 0)
                    json.Append(',');
                json.Append('"');
                json.Append(EscapeJson(values[index] ?? string.Empty));
                json.Append('"');
            }
        }

        private static string UnescapeJson(string value)
        {
            if (string.IsNullOrEmpty(value) || value.IndexOf('\\') < 0)
                return value ?? string.Empty;
            StringBuilder decoded = new StringBuilder(value.Length);
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                if (character != '\\' || index + 1 >= value.Length)
                {
                    decoded.Append(character);
                    continue;
                }
                char escape = value[++index];
                switch (escape)
                {
                    case '\\': decoded.Append('\\'); break;
                    case '"': decoded.Append('"'); break;
                    case '/': decoded.Append('/'); break;
                    case 'b': decoded.Append('\b'); break;
                    case 'f': decoded.Append('\f'); break;
                    case 'n': decoded.Append('\n'); break;
                    case 'r': decoded.Append('\r'); break;
                    case 't': decoded.Append('\t'); break;
                    case 'u':
                        if (index + 4 < value.Length)
                        {
                            int code;
                            if (int.TryParse(
                                value.Substring(index + 1, 4),
                                NumberStyles.HexNumber,
                                CultureInfo.InvariantCulture,
                                out code
                            ))
                            {
                                decoded.Append((char)code);
                                index += 4;
                                break;
                            }
                        }
                        decoded.Append('u');
                        break;
                    default: decoded.Append(escape); break;
                }
            }
            return decoded.ToString();
        }

        private static void AppendVector(
            StringBuilder json,
            string name,
            VectorData value,
            bool comma = true
        )
        {
            if (comma)
                json.Append(',');
            AppendName(json, name);
            AppendRawVector(json, value);
        }

        private static void AppendVector2(
            StringBuilder json,
            string name,
            float x,
            float z
        )
        {
            json.Append(',');
            AppendName(json, name);
            json.Append('[');
            AppendRawFloat(json, x);
            json.Append(',');
            AppendRawFloat(json, z);
            json.Append(']');
        }

        private static void AppendRawVector(StringBuilder json, VectorData value)
        {
            json.Append('[');
            AppendRawFloat(json, value.X);
            json.Append(',');
            AppendRawFloat(json, value.Y);
            json.Append(',');
            AppendRawFloat(json, value.Z);
            json.Append(']');
        }

        private static void AppendRawFloat(StringBuilder json, float value)
        {
            if (float.IsNaN(value) || float.IsInfinity(value))
                json.Append('0');
            else
                json.Append(value.ToString("R", CultureInfo.InvariantCulture));
        }

        private static void AppendName(StringBuilder json, string name)
        {
            json.Append('"');
            json.Append(name);
            json.Append("\":");
        }

        private static string EscapeJson(string value)
        {
            StringBuilder escaped = new StringBuilder(value.Length + 8);
            for (int index = 0; index < value.Length; index++)
            {
                char character = value[index];
                switch (character)
                {
                    case '\\': escaped.Append("\\\\"); break;
                    case '"': escaped.Append("\\\""); break;
                    case '\n': escaped.Append("\\n"); break;
                    case '\r': escaped.Append("\\r"); break;
                    case '\t': escaped.Append("\\t"); break;
                    default:
                        if (character < 32)
                            escaped.Append("\\u" + ((int)character).ToString("x4"));
                        else
                            escaped.Append(character);
                        break;
                }
            }
            return escaped.ToString();
        }
    }
}
