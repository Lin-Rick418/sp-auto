using System;
using System.Collections;
using System.Reflection;
using System.IO;

namespace PickupTests {
public struct Vec { public float x, y, z; }
public struct Dto {
    public Vec Move { get; set; } public Vec ClickPosition { get; set; } public Vec FastCastPosition { get; set; }
    public ulong Hotkeys { get; set; } public ulong HotkeysHeld { get; set; }
    public int UnitId { get; set; } public int LootId { get; set; } public int InteractableId { get; set; }
    public bool Click { get; set; } public bool AltClick { get; set; } public bool FastCast { get; set; }
    public bool SkillHold { get; set; } public int ClickSkillIndex { get; set; }
}
public class Network { public long MapId { get; set; } public long InstanceId { get; set; } }
public class Skills { public bool IsCasting { get; set; } }
public class Unit {
    public int ObjectId { get; set; } public Network NetworkObject { get; set; }
    public Vec Position { get; set; } public Skills Skills { get; set; }
    public object SkillReady { get; set; }
    public object enemy { get; set; }
    public Dto Inputs { get; set; } public Dto currentInputs { get; set; }
    public Dto Sent; public int Applied, Targeted, SentCount;
    public int ClickedSkill = -1, SkillClicks;
    public void ProcessMovement(Dto dto) { }
    public void ClickSkill(int index) { ClickedSkill=index; SkillClicks++; }
    public void ApplyInputs(Dto dto) {
        if (!dto.Click || dto.InteractableId != 99 || dto.UnitId != 0 || dto.Hotkeys != 0)
            throw new Exception("Wrong local click DTO");
        if (Inputs.InteractableId != 99 || currentInputs.InteractableId != 99)
            throw new Exception("Value DTO written too early");
        Applied++; Inputs = dto;
    }
    public void ProcessTargeting() { Targeted++; }
    public void SendInputsToServer(Dto dto) { Sent = dto; SentCount++; }
}
public class GameObject { public bool activeInHierarchy { get; set; } }
public class Transform { public Vec position { get; set; } }
public class Data { public string Type { get; set; } }
public class Lock { public bool Locked; public bool IsLocked(Unit player) { return Locked; } }
public class Sync<T> { public T Value { get; set; } }
public class Loot : Unit {
    public GameObject gameObject { get; set; } public Transform transform { get; set; }
    public Sync<Data> Dto { get; set; } public Sync<Lock> Lock { get; set; }
}
public class Map { public long MapId { get; set; } public long InstanceId { get; set; } }
public class MapManager { public Map Current; public Map Get(Network network) { return Current; } }
public class Game { public MapManager Map { get; set; } }
public static class App { public static Unit Player { get; set; } public static Game Game { get; set; } }

public static class Tests {
    static BindingFlags All = BindingFlags.Static | BindingFlags.Instance | BindingFlags.Public | BindingFlags.NonPublic;
    static Type bg, patch; static object request; static int checks;
    static void Set(Type type, string name, object value) { type.GetField(name, All).SetValue(null, value); }
    static void Req(string name, object value) { request.GetType().GetField(name, All).SetValue(request, value); }
    static object Call(Type type, string name, params object[] args) { return type.GetMethod(name, All).Invoke(null, args); }
    static void Prop(Type target, string field, Type type, string name) { Set(target, field, type.GetProperty(name)); }
    static void Check(bool ok, string name) { if (!ok) throw new Exception(name); checks++; Console.WriteLine("PASS " + name); }
    static bool Eligible(Unit player, int id) { return (bool)Call(patch, "CanInteractWithCachedLoot", player, id, ""); }
    static bool Prepare(Unit player, int seq, int id, out Dto dto) {
        Req("LootInteract", seq); Req("LootInteractObjectId", id);
        object boxed = new Dto { UnitId=777, LootId=888, Hotkeys=ulong.MaxValue, HotkeysHeld=ulong.MaxValue,
            FastCast=true, AltClick=true, SkillHold=true, Move=new Vec { x=1 } };
        bool ok = (bool)Call(bg, "ApplyPendingLootPickup", player, boxed); dto=(Dto)boxed; return ok;
    }
    public static int Main(string[] args) {
        try {
            AppDomain.CurrentDomain.AssemblyResolve += (sender, evt) => {
                string path=Path.Combine(args[1], new AssemblyName(evt.Name).Name+".dll");
                return File.Exists(path) ? Assembly.LoadFrom(path) : null;
            };
            Assembly assembly=Assembly.LoadFrom(args[0]);
            bg=assembly.GetType("SpiritValePositionProbe.BackgroundMovementPatch", true);
            patch=assembly.GetType("SpiritValePositionProbe.PlayerUpdatePatch", true);
            foreach (string name in new [] { "Move", "ClickPosition", "FastCastPosition", "Hotkeys", "HotkeysHeld",
                "UnitId", "LootId", "InteractableId", "Click", "AltClick", "FastCast", "SkillHold", "ClickSkillIndex" })
                Prop(bg, "_"+char.ToLowerInvariant(name[0])+name.Substring(1), typeof(Dto), name);
            foreach (string name in new [] { "Inputs", "currentInputs", "SkillReady", "ObjectId", "enemy" })
                Prop(bg, "_"+char.ToLowerInvariant(name[0])+name.Substring(1), typeof(Unit), name);
            Prop(bg, "_appPlayer", typeof(App), "Player");
            Set(bg, "_inputDtoType", typeof(Dto)); Set(bg, "_moveType", typeof(Vec));
            foreach (string axis in new [] { "X", "Y", "Z" }) Set(bg, "_move"+axis+"Field", typeof(Vec).GetField(axis.ToLowerInvariant()));
            foreach (string name in new [] { "ApplyInputs", "ProcessTargeting", "SendInputsToServer", "ProcessMovement", "ClickSkill" })
                Set(bg, "_"+char.ToLowerInvariant(name[0])+name.Substring(1), typeof(Unit).GetMethod(name));
            Type log=Assembly.LoadFrom(Path.Combine(args[1], "BepInEx.Core.dll")).GetType("BepInEx.Logging.ManualLogSource");
            Set(bg, "_log", Activator.CreateInstance(log, new object[] { "PickupTests" }));
            Set(patch, "_lootType", typeof(Loot));
            Prop(patch, "_objectId", typeof(Unit), "ObjectId"); Prop(patch, "_position", typeof(Unit), "Position");
            Prop(patch, "_networkObject", typeof(Unit), "NetworkObject");
            Prop(patch, "_networkMapId", typeof(Network), "MapId"); Prop(patch, "_networkInstanceId", typeof(Network), "InstanceId");
            Prop(patch, "_appGame", typeof(App), "Game"); Prop(patch, "_gameMap", typeof(Game), "Map");
            Set(patch, "_mapGet", typeof(MapManager).GetMethod("Get"));
            Prop(patch, "_mapId", typeof(Map), "MapId"); Prop(patch, "_instanceId", typeof(Map), "InstanceId");
            Prop(patch, "_componentGameObject", typeof(Loot), "gameObject");
            Prop(patch, "_gameObjectActiveInHierarchy", typeof(GameObject), "activeInHierarchy");
            Prop(patch, "_componentTransform", typeof(Loot), "transform"); Prop(patch, "_transformPosition", typeof(Transform), "position");
            Prop(patch, "_lootDto", typeof(Loot), "Dto"); Prop(patch, "_lootDtoValue", typeof(Sync<Data>), "Value");
            Prop(patch, "_lootDtoType", typeof(Data), "Type");
            Prop(patch, "_lootLock", typeof(Loot), "Lock"); Prop(patch, "_lootLockValue", typeof(Sync<Lock>), "Value");
            Set(patch, "_lootIsLocked", typeof(Lock).GetMethod("IsLocked"));
            App.Game=new Game { Map=new MapManager { Current=new Map { MapId=1, InstanceId=2 } } };
            Unit player=new Unit { ObjectId=1, NetworkObject=new Network { MapId=1, InstanceId=2 }, Skills=new Skills() };
            App.Player=player;
            Loot loot=new Loot { ObjectId=99, NetworkObject=new Network { MapId=1, InstanceId=2 },
                gameObject=new GameObject { activeInHierarchy=true }, transform=new Transform(),
                Dto=new Sync<Data> { Value=new Data { Type="Card" } }, Lock=new Sync<Lock> { Value=new Lock() } };
            Type entryType=assembly.GetType("SpiritValePositionProbe.CachedLootEntry", true);
            object entry=Activator.CreateInstance(entryType, true); entryType.GetField("SourceValue", All).SetValue(entry, loot);
            IDictionary lootCache=(IDictionary)patch.GetField("_lootCache", All).GetValue(null);
            Action cacheLoot=()=>lootCache[99]=entry;
            cacheLoot();
            Check(Eligible(player,99), "live unlocked exact ID accepted");
            Check(!Eligible(player,98), "missing ID cannot fall back to nearby loot");
            loot.ObjectId=98; Check(!Eligible(player,99), "recycled object rejected"); loot.ObjectId=99; cacheLoot();
            loot.gameObject.activeInHierarchy=false; Check(!Eligible(player,99), "despawned loot rejected"); loot.gameObject.activeInHierarchy=true; cacheLoot();
            loot.NetworkObject.InstanceId=3; Check(!Eligible(player,99), "other instance rejected"); loot.NetworkObject.InstanceId=2; cacheLoot();
            loot.Lock.Value.Locked=true; Check(!Eligible(player,99), "server ownership lock respected"); loot.Lock.Value.Locked=false;
            loot.Dto.Value.Type="Equipment"; Check(!Eligible(player,99), "excluded equipment rejected"); loot.Dto.Value.Type="Card"; cacheLoot();
            Type snapshotType=assembly.GetType("SpiritValePositionProbe.LootSnapshot", true);
            IList published=(IList)patch.GetField("_cachedLoots", All).GetValue(null);
            Func<object> publishLoot=()=> {
                object value=Activator.CreateInstance(snapshotType, true);
                snapshotType.GetField("ObjectId", All).SetValue(value, 99);
                published.Add(value); return value;
            };
            published.Clear(); publishLoot(); lootCache.Remove(99);
            Check(!Eligible(player,99) && published.Count==0,
                "missing interaction cache purges published ghost loot");
            cacheLoot(); publishLoot(); Call(patch,"ForgetLoot",loot);
            Check(!lootCache.Contains(99) && published.Count==0,
                "loot lifecycle removal clears interaction and published caches");
            cacheLoot();
            request=Activator.CreateInstance(assembly.GetType("SpiritValePositionProbe.NavigationRequest", true), true);
            Set(bg, "_request", request); Req("BotActive",true); Req("LootScanActive",true);
            Dto dto; Check(Prepare(player,1,99,out dto), "new request emits one click");
            Check(dto.Click && dto.InteractableId==99 && dto.UnitId==0 && dto.LootId==0, "interactable ID isolated from skill and legacy loot IDs");
            Check(dto.Hotkeys==0 && dto.HotkeysHeld==0 && !dto.FastCast && !dto.AltClick && !dto.SkillHold && dto.Move.x==0,
                "pickup clears movement and competing skill or area-pickup keys");
            Check(!Prepare(player,1,99,out dto), "same sequence does not repeat click across frames");
            player.Skills.IsCasting=true; Check(!Prepare(player,2,99,out dto), "active cast deferred"); player.Skills.IsCasting=false;
            player.SkillReady=new object(); Check(!Prepare(player,3,99,out dto), "pending targeted skill cannot consume loot click"); player.SkillReady=null;
            Check(!Prepare(player,4,0,out dto), "invalid ID produces no click");
            Req("BackgroundInputMode", "send"); Req("LootInteract",5); Req("LootInteractObjectId",99);
            Set(bg, "_lastRequestReadMilliseconds", DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()+60000);
            Call(bg,"UpdatePostfix",player);
            Check(player.Applied==1 && player.Targeted==1 && player.SentCount==1, "same-frame local apply, targeting and RPC dispatch");
            Check(player.Sent.InteractableId==99 && player.Sent.Click && player.Sent.Hotkeys==0, "RPC carries exact loot click without V");
            Call(bg,"UpdatePostfix",player);
            Check(player.Applied==1 && !player.Sent.Click && player.Sent.InteractableId==0, "next frame releases click and target ID");
            Req("BotActive",false); Req("LootInteract",6); Call(bg,"UpdatePostfix",player);
            Req("BotActive",true); Call(bg,"UpdatePostfix",player);
            Check(player.Applied==1, "disabled request not replayed on resume");
            Req("LootScanActive",false); Req("LootInteract",7); Call(bg,"UpdatePostfix",player);
            Req("LootScanActive",true); Call(bg,"UpdatePostfix",player);
            Check(player.Applied==1, "F7-off pickup not replayed on enable");
            // Buff maintenance starts with BotActive=true and no Shift intent.
            // Native ProcessSkills treats ClickSkillIndex=0 as Skill1_1 even
            // when both hotkey masks are empty. Neutral input must use -1.
            Req("LootScanActive",false); Req("BackgroundInputMode","send_process");
            Req("BackgroundSkillMode","capture"); Req("ShiftKeys","");
            Set(bg,"_wasSending",false);
            int before=player.SentCount;
            Call(bg,"UpdatePostfix",player);
            Check(player.SentCount==before+1 && player.Sent.ClickSkillIndex==-1
                && player.Sent.Hotkeys==0 && player.Sent.HotkeysHeld==0,
                "startup upkeep heartbeat cannot select Left Shift skill zero");
            IDictionary numpad=(IDictionary)bg.GetField("NumpadHotkeys",All).GetValue(null);
            numpad["numpad5"]=new System.Collections.Generic.List<int> { 24 };
            Req("SkillKeyRequestId",1L); Req("SkillKey","numpad5");
            Call(bg,"UpdatePostfix",player);
            Check(player.ClickedSkill==24 && player.SkillClicks==1
                && player.Sent.ClickSkillIndex==-1 && player.Sent.Hotkeys==0,
                "summon request queues NumPad skill without an implicit attack RPC");
            Call(bg,"UpdatePostfix",player);
            Check(player.SkillClicks==1 && player.Sent.ClickSkillIndex==-1,
                "waiting for buff confirmation neither repeats skill nor attacks");
            Req("BotActive",false); Call(bg,"UpdatePostfix",player);
            Check(player.Sent.ClickSkillIndex==-1 && player.Sent.Hotkeys==0,
                "stop RPC also uses the no-skill sentinel");
            Req("BotActive",true); Req("BackgroundSkillMode","process");
            Req("BackgroundInputMode","send"); Req("ShiftKeys","lshift,rshift");
            ((IList)bg.GetField("LeftShiftHotkeys",All).GetValue(null)).Add(0);
            ((IList)bg.GetField("RightShiftHotkeys",All).GetValue(null)).Add(1);
            Call(bg,"UpdatePostfix",player);
            Check(player.Sent.Hotkeys==3UL && player.Sent.HotkeysHeld==3UL
                && player.Sent.ClickSkillIndex==-1,
                "explicit attacks still use only the requested Shift hotkeys");
            Req("ShiftKeys",""); Call(bg,"UpdatePostfix",player);
            Check(player.Sent.Hotkeys==0 && player.Sent.HotkeysHeld==0
                && player.Sent.ClickSkillIndex==-1,
                "releasing attacks cannot reselect skill zero");
            Req("BackgroundInputMode","capture");
            player.Inputs=new Dto { ClickSkillIndex=0 };
            Call(bg,"Postfix",player,false);
            Check(player.Inputs.ClickSkillIndex==-1 && player.Inputs.Hotkeys==0,
                "capture fallback without game input also uses no-skill sentinel");
            player.Inputs=new Dto { ClickSkillIndex=24 };
            Call(bg,"Postfix",player,true);
            Check(player.Inputs.ClickSkillIndex==24,
                "real captured NumPad buff click survives input overlay");
            Console.WriteLine(checks+" pickup behavior checks passed"); return 0;
        } catch(Exception error) { Console.Error.WriteLine(error); return 1; }
    }
}}
