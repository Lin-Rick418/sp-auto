using System;
using System.Diagnostics;
using System.Globalization;
using System.IO;
using System.Reflection;
using System.Text;
using System.Text.RegularExpressions;
using BepInEx;
using BepInEx.Logging;
using BepInEx.Unity.IL2CPP;
using HarmonyLib;

namespace SpiritValeProbeLoader
{
    [BepInPlugin("local.spiritvale.probeloader", "SpiritVale Probe Loader", "2.11.0")]
    public sealed class Plugin : BasePlugin
    {
        public override void Load()
        {
            ProbeLoader.Initialize(Log);
            Type game = ProbeLoader.FindLoadedType("Game");
            MethodInfo update = ProbeLoader.RequireZeroParameterMethod(
                game, "Update"
            );
            MethodInfo postfix = AccessTools.Method(typeof(ProbeLoader), "Postfix");
            new Harmony("local.spiritvale.probeloader.hook").Patch(
                update,
                null,
                new HarmonyMethod(postfix),
                null,
                null,
                null
            );
            Log.LogInfo(
                "On-demand probe loader v2.11.0 ready; the navigation probe "
                    + "will load only after a fresh Python request"
            );
        }
    }

    internal static class ProbeLoader
    {
        private const long PollIntervalMilliseconds = 250;
        private const long RequestMaxAgeMilliseconds = 15000;
        private const int FileOperationAttempts = 5;
        private const string ProbePluginId = "local.spiritvale.positionprobe";

        private static readonly Stopwatch Timer = Stopwatch.StartNew();
        private static readonly Regex RequestIdPattern = new Regex(
            "\\\"request_id\\\"\\s*:\\s*([0-9]+)", RegexOptions.Compiled
        );
        private static readonly Regex TimestampPattern = new Regex(
            "\\\"timestamp_ms\\\"\\s*:\\s*([0-9]+)", RegexOptions.Compiled
        );

        private static ManualLogSource _log;
        private static string _requestPath;
        private static string _statePath;
        private static string _probeDirectory;
        private static long _lastPollMilliseconds;
        private static long _lastRequestWriteTicks;
        private static long _lastRequestId;

        internal static void Initialize(ManualLogSource log)
        {
            _log = log;
            string ipcDirectory = Path.Combine(
                Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
                "SpiritValeBot"
            );
            Directory.CreateDirectory(ipcDirectory);
            _requestPath = Path.Combine(
                ipcDirectory, "spiritvale_probe_load_request.json"
            );
            _statePath = Path.Combine(
                ipcDirectory, "spiritvale_probe_loader_state.json"
            );
            _probeDirectory = Path.Combine(
                Paths.BepInExRootPath, "ondemand", "SpiritValePositionProbe"
            );
        }

        internal static Type FindLoadedType(string fullName)
        {
            Assembly[] assemblies = AppDomain.CurrentDomain.GetAssemblies();
            for (int index = 0; index < assemblies.Length; index++)
            {
                Type type = assemblies[index].GetType(fullName, false);
                if (type != null)
                    return type;
            }
            throw new TypeLoadException("Loaded type not found: " + fullName);
        }

        internal static MethodInfo RequireZeroParameterMethod(
            Type type, string name
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
                    && methods[index].GetParameters().Length == 0)
                    return methods[index];
            }
            throw new MissingMethodException(type.FullName, name + "()");
        }

        private static void Postfix()
        {
            long elapsed = Timer.ElapsedMilliseconds;
            if (elapsed - _lastPollMilliseconds < PollIntervalMilliseconds)
                return;
            _lastPollMilliseconds = elapsed;

            long requestId;
            long timestamp;
            if (!TryReadFreshRequest(out requestId, out timestamp))
                return;
            if (requestId == _lastRequestId)
                return;

            try
            {
                if (!IsProbeLoaded())
                {
                    string probePath = Path.Combine(
                        _probeDirectory, "SpiritValePositionProbe.dll"
                    );
                    if (!File.Exists(probePath))
                        throw new FileNotFoundException(
                            "On-demand probe DLL was not found", probePath
                        );

                    _log.LogInfo(
                        "Fresh Python request received; loading probe from "
                            + probePath
                    );
                    IL2CPPChainloader.Instance.LoadPlugins(
                        new string[] { _probeDirectory }
                    );
                    if (!IsProbeLoaded())
                        throw new InvalidOperationException(
                            "BepInEx returned without loading " + ProbePluginId
                        );
                }

                if (WriteState(requestId, "loaded", string.Empty))
                    _lastRequestId = requestId;
            }
            catch (Exception error)
            {
                Exception actual = error;
                while (actual.InnerException != null)
                    actual = actual.InnerException;
                string message = actual.GetType().Name + ": " + actual.Message;
                _log.LogError("On-demand probe load failed: " + message);
                if (WriteState(requestId, "error", message))
                    _lastRequestId = requestId;
            }
        }

        private static bool IsProbeLoaded()
        {
            return IL2CPPChainloader.Instance != null
                && IL2CPPChainloader.Instance.Plugins.ContainsKey(ProbePluginId);
        }

        private static bool TryReadFreshRequest(
            out long requestId, out long timestamp
        )
        {
            requestId = 0;
            timestamp = 0;
            try
            {
                if (!File.Exists(_requestPath))
                    return false;
                long writeTicks = File.GetLastWriteTimeUtc(_requestPath).Ticks;
                if (writeTicks == _lastRequestWriteTicks)
                    return false;
                _lastRequestWriteTicks = writeTicks;
                string json;
                using (FileStream stream = new FileStream(
                    _requestPath,
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

                Match requestIdMatch = RequestIdPattern.Match(json);
                Match timestampMatch = TimestampPattern.Match(json);
                if (!requestIdMatch.Success || !timestampMatch.Success)
                    return false;
                requestId = long.Parse(
                    requestIdMatch.Groups[1].Value, CultureInfo.InvariantCulture
                );
                timestamp = long.Parse(
                    timestampMatch.Groups[1].Value, CultureInfo.InvariantCulture
                );
                long now = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                return requestId > 0
                    && Math.Abs(now - timestamp) <= RequestMaxAgeMilliseconds;
            }
            catch
            {
                requestId = 0;
                timestamp = 0;
                return false;
            }
        }

        private static bool WriteState(
            long requestId, string status, string error
        )
        {
            try
            {
                StringBuilder json = new StringBuilder(256);
                json.Append('{');
                json.Append("\"schema_version\":1");
                json.Append(",\"loader_version\":\"2.11.0\"");
                json.Append(",\"request_id\":");
                json.Append(requestId.ToString(CultureInfo.InvariantCulture));
                json.Append(",\"timestamp_ms\":");
                json.Append(
                    DateTimeOffset.UtcNow.ToUnixTimeMilliseconds().ToString(
                        CultureInfo.InvariantCulture
                    )
                );
                json.Append(",\"status\":\"");
                AppendEscaped(json, status);
                json.Append("\",\"error\":\"");
                AppendEscaped(json, error);
                json.Append("\"}");

                string temporary = _statePath + ".tmp";
                Exception lastError = null;
                for (int attempt = 0; attempt < FileOperationAttempts; attempt++)
                {
                    try
                    {
                        File.WriteAllText(
                            temporary, json.ToString(), new UTF8Encoding(false)
                        );
                        if (File.Exists(_statePath))
                            File.Replace(temporary, _statePath, null);
                        else
                            File.Move(temporary, _statePath);
                        return true;
                    }
                    catch (IOException writeError)
                    {
                        lastError = writeError;
                    }
                    catch (UnauthorizedAccessException writeError)
                    {
                        lastError = writeError;
                    }
                    if (attempt + 1 < FileOperationAttempts)
                        System.Threading.Thread.Sleep(2 << attempt);
                }
                throw lastError;
            }
            catch (Exception errorValue)
            {
                _log.LogWarning(
                    "Could not write probe loader state: "
                        + errorValue.GetType().Name + ": " + errorValue.Message
                );
                return false;
            }
        }

        private static void AppendEscaped(StringBuilder text, string value)
        {
            string actual = value ?? string.Empty;
            for (int index = 0; index < actual.Length; index++)
            {
                char character = actual[index];
                if (character == '\\' || character == '\"')
                {
                    text.Append('\\');
                    text.Append(character);
                }
                else if (character == '\n')
                    text.Append("\\n");
                else if (character == '\r')
                    text.Append("\\r");
                else if (character == '\t')
                    text.Append("\\t");
                else if (character >= ' ')
                    text.Append(character);
            }
        }
    }
}
