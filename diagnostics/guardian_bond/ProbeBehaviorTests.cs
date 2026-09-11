using System;
using System.Collections.Generic;
using System.Reflection;
using System.IO;
using System.Text;

public struct Vec { public float x, y, z; }
public struct Dto {
    public ulong Hotkeys { get; set; } public ulong HotkeysHeld { get; set; }
    public int UnitId { get; set; } public bool FastCast { get; set; }
    public bool Click { get; set; } public bool AltClick { get; set; }
    public bool SkillHold { get; set; } public int ClickSkillIndex { get; set; }
    public Vec ClickPosition { get; set; } public Vec FastCastPosition { get; set; }
}
public class Network { public int ObjectId { get; set; } public long MapId { get; set; } public long InstanceId { get; set; } }
public class Health { public Health() { IsAlive = true; } public bool IsAlive { get; set; } }
public class Summoning { public Unit Summoner { get; set; } }
public class Skill { public Skill() { Id = "GuardianBond"; } public string Id { get; set; } public bool IsOnCooldown { get; set; } }
public class Entry { public Entry() { SkillId = "GuardianBond"; } public Network Other { get; set; } public string SkillId { get; set; } public bool Caster { get; set; } }
public class Bonds { public Bonds() { Entries = new List<Entry>(); } public List<Entry> Entries { get; set; } }
public class Sync { public Sync() { Value = new Bonds(); } public Bonds Value { get; set; } }
public class Skills { public Skills() { BondSync = new Sync(); }
    public bool IsCasting { get; set; }
    public bool Allowed = true;
    public bool CanHit(Skill skill, Unit target) { return Allowed; }
    public Sync BondSync { get; set; }
}
public class Unit { public Unit() { IsActive = true; IsAliveAndDisplayed = true; Health = new Health(); Summoning = new Summoning(); NetworkObject = new Network(); Skills = new Skills(); }
    public int ObjectId { get; set; }
    public bool IsActive { get; set; }
    public bool IsAliveAndDisplayed { get; set; }
    public Health Health { get; set; }
    public Summoning Summoning { get; set; }
    public Network NetworkObject { get; set; }
    public Vec Position { get; set; }
    public Skills Skills { get; set; }
    public Dto Inputs { get; set; } public Dto currentInputs { get; set; }
    public Unit enemy { get; set; } public Unit player { get; set; }
    public object interactable { get; set; } public Vec position { get; set; }
    public Unit CastTarget { get; set; }
    public Skill Bound = new Skill(); public int Processed, Clicked;
    public Skill GetAssignedSkill(int slot) { return Bound; }
    public void ClickSkill(int slot) { Clicked++; }
    public void ProcessSkills() {
        if (!Inputs.FastCast || Inputs.UnitId != player.ObjectId || Inputs.Hotkeys != (1UL << 28)
            || currentInputs.UnitId != Inputs.UnitId || enemy != null)
            throw new Exception("Skill processed against stale/incorrect local DTO");
        Processed++;
        CastTarget = player;
        // Simulate native FastCast updating its own value-type Inputs.
        Dto dto = Inputs; dto.ClickSkillIndex = 28; Inputs = dto;
    }
}
public static class Scene { public static List<Unit> Units = new List<Unit>(); public static List<Unit> Find(object mode) { return Units; } }
public enum Hotkey { Skill3_9 = 28 }
public struct HotkeyBinding { public int Main; }
public static class HotkeyManager {
    public static HotkeyBinding Get(Hotkey key) {
        return new HotkeyBinding { Main = (int)UnityEngine.KeyCode.Keypad9 };
    }
}
namespace UnityEngine {
    public enum KeyCode { LeftShift=1, RightShift, Alpha9, Alpha0,
        Keypad0=10, Keypad1, Keypad2, Keypad3, Keypad4, Keypad5,
        Keypad6, Keypad7, Keypad8, Keypad9 }
}
public static class ProbeBehaviorTests {
    static Type background, playerPatch;
    static BindingFlags Flags = BindingFlags.Static | BindingFlags.Public | BindingFlags.NonPublic;
    static void Set(Type type, string name, object value) { type.GetField(name, Flags).SetValue(null, value); }
    static object Call(Type type, string name, params object[] args) { return type.GetMethod(name, Flags).Invoke(null, args); }
    static void Property(Type target, string name, Type fake, string prop) { Set(target, name, fake.GetProperty(prop)); }
    static void Check(bool condition, string message) { if (!condition) throw new Exception(message); Console.WriteLine("PASS " + message); }
    static object[] Fire(Unit player, long id) {
        object[] args = { player, (object)new Dto(), id, "numpad9", true };
        Call(background, "FireSkillKeyHotkeys", args); return args;
    }
    public static int Main(string[] args) {
        try {
            string core = args[1];
            AppDomain.CurrentDomain.AssemblyResolve += (sender, evt) => {
                string path = Path.Combine(core, new AssemblyName(evt.Name).Name + ".dll");
                return File.Exists(path) ? Assembly.LoadFrom(path) : null;
            };
            Assembly probe = Assembly.LoadFrom(args[0]);
            background = probe.GetType("SpiritValePositionProbe.BackgroundMovementPatch", true);
            playerPatch = probe.GetType("SpiritValePositionProbe.PlayerUpdatePatch", true);
            foreach (string name in new [] { "Hotkeys", "HotkeysHeld", "UnitId", "FastCast", "Click", "AltClick", "SkillHold", "ClickSkillIndex", "ClickPosition", "FastCastPosition" })
                Property(background, "_" + char.ToLowerInvariant(name[0]) + name.Substring(1), typeof(Dto), name);
            foreach (string name in new [] { "Inputs", "currentInputs", "enemy", "interactable", "CastTarget" })
                Property(background, "_" + char.ToLowerInvariant(name[0]) + name.Substring(1), typeof(Unit), name);
            Property(background, "_targetPlayer", typeof(Unit), "player");
            Property(background, "_samplePosition", typeof(Unit), "position");
            Set(background, "_processSkills", typeof(Unit).GetMethod("ProcessSkills"));
            Set(background, "_getAssignedSkill", typeof(Unit).GetMethod("GetAssignedSkill"));
            Set(background, "_clickSkill", typeof(Unit).GetMethod("ClickSkill"));
            Set(background, "_moveType", typeof(Vec));
            foreach (string axis in new [] { "X", "Y", "Z" }) Set(background, "_move" + axis + "Field", typeof(Vec).GetField(axis.ToLowerInvariant()));
            Type logger = Assembly.LoadFrom(Path.Combine(core, "BepInEx.Core.dll")).GetType("BepInEx.Logging.ManualLogSource");
            Set(background, "_log", Activator.CreateInstance(logger, new object[] { "GuardianBondTests" }));
            var keys = (Dictionary<string, List<int>>)background.GetField("NumpadHotkeys", Flags).GetValue(null);
            keys["numpad9"] = new List<int> { 28 };
            Property(playerPatch, "_objectId", typeof(Unit), "ObjectId");
            Property(playerPatch, "_unitSummoning", typeof(Unit), "Summoning");
            Property(playerPatch, "_summonOwner", typeof(Summoning), "Summoner");
            Property(playerPatch, "_isActive", typeof(Unit), "IsActive");
            Property(playerPatch, "_isAliveAndDisplayed", typeof(Unit), "IsAliveAndDisplayed");
            Property(playerPatch, "_health", typeof(Unit), "Health");
            Property(playerPatch, "_healthIsAlive", typeof(Health), "IsAlive");
            Property(playerPatch, "_networkObject", typeof(Unit), "NetworkObject");
            Property(playerPatch, "_networkMapId", typeof(Network), "MapId");
            Property(playerPatch, "_networkInstanceId", typeof(Network), "InstanceId");
            Property(playerPatch, "_position", typeof(Unit), "Position");
            Set(playerPatch, "_findSceneMonsters", typeof(Scene).GetMethod("Find"));
            Unit player = new Unit { ObjectId = 1 };
            Unit foreign = new Unit { ObjectId = 2, Summoning = new Summoning { Summoner = new Unit { ObjectId = 9 } } };
            Unit own = new Unit { ObjectId = 3, Summoning = new Summoning { Summoner = player }, Position = new Vec { x = 4 } };
            Unit dead = new Unit { ObjectId = 4, Summoning = new Summoning { Summoner = player }, Health = new Health { IsAlive = false } };
            Scene.Units.AddRange(new [] { foreign, dead, own });
            Check((Unit)Call(playerPatch, "ResolveSummonUnit", player) == own, "choose living own summon despite closer foreign/dead units");
            keys["numpad9"].Clear();
            object[] fired = Fire(player, 1);
            Check(keys["numpad9"].Count == 1, "late-loaded key bindings are refreshed on request");
            Check(player.Processed == 1 && player.Clicked == 0, "same-frame skill processing without deferred ClickSkill");
            Check(((Dto)fired[1]).UnitId == 3 && ((Dto)fired[1]).ClickSkillIndex == 28, "read back native-modified value DTO for RPC");
            Fire(player, 1);
            Check(player.Processed == 1, "duplicate request ID does not cast twice");
            Scene.Units.Remove(own); Fire(player, 2);
            Check(player.Processed == 1 && player.Clicked == 0, "no owned summon never falls back to untargeted key");
            Scene.Units.Add(own); player.Bound.Id = "Heal"; Fire(player, 3);
            Check(player.Processed == 1, "wrong key binding is rejected");
            player.Bound.Id = "GuardianBond"; player.Skills.IsCasting = true; Fire(player, 4);
            Check(player.Processed == 1, "active cast is not interrupted");
            player.Skills.IsCasting = false; player.Bound.IsOnCooldown = true; Fire(player, 5);
            Check(player.Processed == 1, "cooldown prevents cast");
            player.Bound.IsOnCooldown = false; player.Skills.Allowed = false; Fire(player, 6);
            Check(player.Processed == 1, "game target validation is respected");
            player.Skills.Allowed = true;
            Entry link = new Entry { Other = new Network { ObjectId = 3 }, Caster = false };
            player.Skills.BondSync.Value.Entries.Add(link);
            StringBuilder json = new StringBuilder(); Call(playerPatch, "AppendGuardianBond", json, player);
            Check(json.ToString().Contains("\"has_owned_bond\":false"), "incoming bond is not outgoing success");
            link.Caster = true; json.Clear(); Call(playerPatch, "AppendGuardianBond", json, player);
            Check(json.ToString().Contains("\"has_owned_bond\":true"), "outgoing owned bond confirms success");
            link.Other.ObjectId = 2; json.Clear(); Call(playerPatch, "AppendGuardianBond", json, player);
            Check(json.ToString().Contains("\"has_owned_bond\":false"), "outgoing foreign bond is not success");
            Console.WriteLine("13 behavior checks passed"); return 0;
        } catch (Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}
