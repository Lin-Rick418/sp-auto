"""Rule editor and guarded periodic backpack equipment automation."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
import json
import math
import os
from pathlib import Path
import queue
import threading
import time
from typing import Any, Callable, ContextManager, Iterable

import spiritvale_inventory_pricer as inventory_pricer
from spiritvale_paths import IPC_DIR


BASE_DIR = Path(__file__).resolve().parent
FILTER_CONFIG_PATH = BASE_DIR / "spiritvale_equipment_filter.json"
FAVORITE_REQUEST_PATH = IPC_DIR / "spiritvale_favorite_request.json"
FAVORITE_RESULT_PATH = IPC_DIR / "spiritvale_favorite_result.json"
DISMANTLE_REQUEST_PATH = IPC_DIR / "spiritvale_dismantle_request.json"
DISMANTLE_RESULT_PATH = IPC_DIR / "spiritvale_dismantle_result.json"
FILTER_INTERVAL_SEC = 100.0
FAVORITE_CONFIRMATION = "SET_FAVORITE"
DISMANTLE_CONFIRMATION = "DISMANTLE_EQUIP"


STAT_TYPES = tuple(
    """
Str Vit Agi Dex Int Luk AllStats Hp Mp Atk Matk Def Mdef Hit Flee Crit
DefFlat MdefFlat ElementWeapon ElementArmor HealthOnHit ManaOnHit LeechKill
LeechKillMp Splash Range StatusImmune ReverseHealing NoAction NoMove NoAttack
NoCast NoKnockback NoFlee NoCastCancel NoFlinch NoReflect NoRegenHp NoRegenMp
AutocastHit AutocastAttack AutocastChance GrantSkill SkillLevel DamageToElement
DamageToBoss DamageElement DamageMelee DamageMagic SkillDamage CostSkill
CooldownSkill CritDamage ElementResist AtkWeapon MatkWeapon DamageFromElement
DamageFromMagic DamageFromMelee HpRegen HpRegenMax MpRegen MpRegenMax AtkSpd
CastSpd MoveSpd AfterCastDelay Healing HealingReceived AtkMult MatkMult HpMult
MpMult DefMult MdefMult HpRegenMult MpRegenMult FleeMult HitMult CritMult
DoubleAttack EnergyShield FreeCastMove FreeCastAtk SpellEcho Block ReflectDamage
DualWield ExpRate DropRate MpCost LifeBond SummonStatShare SummonDamageShare
ReflectSpell BlockShield RangeWand LeechChance Leech LeechMpChance LeechMp
WeightLimit DamageRanged DamageFromRanged SkillCooldown SkillDuration SkillArea
SkillHits SkillCost SkillRemoveKnockback SkillRemoveStatus Invisible Detector
HpRegenRate MpRegenRate SummonHealingReceived SummonReflectDamage
SummonHealthRegen HealthBarrier BuffDuration CritDef PerfectDodge PerfectCloak
SkillPiercing SkillChains NoBlock SpellAuto SpellDodge TotalAtk TotalMatk Chain
SummonAtkSpd SummonAtkMult SummonMatkMult SummonHpMult SummonAllStats
SummonHealing SummonCrit FinalDamage FinalDamageReduction FinalDamageTaken
AllResist DamageStatus DamageFromGround DamageFromStatus SkillCastTime
AutoattackDamage NoStatusApply SkillSplash Sacrifice SacrificeDamage MatkPerStr
AtkPerStr StrMult VitMult AgiMult DexMult IntMult LukMult AtkSpdMult CastSpdMult
MoveSpdMult SkillCharges AutoFire DamageCloseRange DamageFarRange DamageToSummons
DamageFromSummons SummonSpellEcho SummonDamage SummonDamageReduction SummonLeech
SummonCostShare SummonHit SummonAutoattackDamage SummonResist SiphonHp SiphonMp
HealShare DeathShare AutocastDeath AutocastKill CooldownRecovery StatusMaxStacks
TwohandedStanceBonus AtkSpdLimit AutoattackMatk CastTimeReduction
CastTimeReductionLimit CastRange DodgeRecovery AtkSpdFlat ThreatMult DefPierce
MdefPierce PerfectHit HealingToBarrier SkillPull SkillDamageLowHp SkillRange
SkillInstances SkillCrit SkillLeap SkillThreat SkillCastTimeMult SkillHitsMult
SkillDurationMult SkillDamageReceived SkillDamageVsStatus SkillReplace
StatusReplace StatusDuration SkillMaxInstances SkillAutocast SkillApplyStatus
SkillConsumeStatus SkillRecoverHp SkillRecoverMp DamageVsStatus SetAtkSpd
MpCostAsHp StatusPerMissingHpMult MoveSpdCap ApplyStatusAttack ApplyStatusHit
RatingHp RatingAtk RatingMatk RatingExp DamageDeferred SplashDamageReduction
BondTargets
""".split()
)
STAT_TYPE_SET = frozenset(STAT_TYPES)

STAT_TYPE_ZH = dict(
    line.split("=", 1)
    for line in """
Str=力量
Vit=體力
Agi=敏捷
Dex=靈巧
Int=智力
Luk=幸運
AllStats=全能力
Hp=生命值
Mp=魔力值
Atk=物理攻擊力
Matk=魔法攻擊力
Def=物理防禦力
Mdef=魔法防禦力
Hit=命中
Flee=迴避
Crit=暴擊
DefFlat=固定物理防禦
MdefFlat=固定魔法防禦
ElementWeapon=武器屬性
ElementArmor=防具屬性
HealthOnHit=命中時恢復生命
ManaOnHit=命中時恢復魔力
LeechKill=擊殺時吸取生命
LeechKillMp=擊殺時吸取魔力
Splash=範圍濺射
Range=攻擊距離
StatusImmune=狀態免疫
ReverseHealing=治療反轉
NoAction=無法行動
NoMove=無法移動
NoAttack=無法攻擊
NoCast=無法施法
NoKnockback=免疫擊退
NoFlee=無法迴避
NoCastCancel=施法不會中斷
NoFlinch=不會硬直
NoReflect=無法反射
NoRegenHp=無法恢復生命
NoRegenMp=無法恢復魔力
AutocastHit=命中時自動施法
AutocastAttack=攻擊時自動施法
AutocastChance=自動施法機率
GrantSkill=獲得技能
SkillLevel=技能等級
DamageToElement=對指定屬性傷害
DamageToBoss=對首領傷害
DamageElement=屬性傷害
DamageMelee=近戰傷害
DamageMagic=魔法傷害
SkillDamage=技能傷害
CostSkill=指定技能消耗
CooldownSkill=指定技能冷卻
CritDamage=暴擊傷害
ElementResist=屬性抗性
AtkWeapon=武器物理攻擊力
MatkWeapon=武器魔法攻擊力
DamageFromElement=承受屬性傷害
DamageFromMagic=承受魔法傷害
DamageFromMelee=承受近戰傷害
HpRegen=生命恢復
HpRegenMax=最大生命恢復
MpRegen=魔力恢復
MpRegenMax=最大魔力恢復
AtkSpd=攻擊速度
CastSpd=施法速度
MoveSpd=移動速度
AfterCastDelay=施法後延遲
Healing=治療量
HealingReceived=受到治療量
AtkMult=物理攻擊力百分比
MatkMult=魔法攻擊力百分比
HpMult=生命值百分比
MpMult=魔力值百分比
DefMult=物理防禦力百分比
MdefMult=魔法防禦力百分比
HpRegenMult=生命恢復百分比
MpRegenMult=魔力恢復百分比
FleeMult=迴避百分比
HitMult=命中百分比
CritMult=暴擊百分比
DoubleAttack=二連擊
EnergyShield=能量護盾
FreeCastMove=施法時可移動
FreeCastAtk=施法時可攻擊
SpellEcho=法術回響
Block=格擋
ReflectDamage=傷害反射
DualWield=雙持
ExpRate=經驗倍率
DropRate=掉落倍率
MpCost=魔力消耗
LifeBond=生命連結
SummonStatShare=召喚物能力共享
SummonDamageShare=召喚物傷害分攤
ReflectSpell=法術反射
BlockShield=盾牌格擋
RangeWand=法杖射程
LeechChance=生命吸取機率
Leech=生命吸取
LeechMpChance=魔力吸取機率
LeechMp=魔力吸取
WeightLimit=負重上限
DamageRanged=遠程傷害
DamageFromRanged=承受遠程傷害
SkillCooldown=技能冷卻時間
SkillDuration=技能持續時間
SkillArea=技能範圍
SkillHits=技能命中次數
SkillCost=技能消耗
SkillRemoveKnockback=技能移除擊退
SkillRemoveStatus=技能移除狀態
Invisible=隱形
Detector=偵測隱形
HpRegenRate=生命恢復速率
MpRegenRate=魔力恢復速率
SummonHealingReceived=召喚物受到治療量
SummonReflectDamage=召喚物傷害反射
SummonHealthRegen=召喚物生命恢復
HealthBarrier=生命屏障
BuffDuration=增益持續時間
CritDef=暴擊防禦
PerfectDodge=完全閃避
PerfectCloak=完全隱匿
SkillPiercing=技能穿透
SkillChains=技能連鎖次數
NoBlock=無法格擋
SpellAuto=自動法術
SpellDodge=法術閃避
TotalAtk=總物理攻擊力
TotalMatk=總魔法攻擊力
Chain=連鎖
SummonAtkSpd=召喚物攻擊速度
SummonAtkMult=召喚物物理攻擊百分比
SummonMatkMult=召喚物魔法攻擊百分比
SummonHpMult=召喚物生命值百分比
SummonAllStats=召喚物全能力
SummonHealing=召喚物治療量
SummonCrit=召喚物暴擊
FinalDamage=最終傷害
FinalDamageReduction=最終傷害減免
FinalDamageTaken=最終承受傷害
AllResist=全抗性
DamageStatus=狀態傷害
DamageFromGround=承受地面傷害
DamageFromStatus=承受狀態傷害
SkillCastTime=技能施法時間
AutoattackDamage=普通攻擊傷害
NoStatusApply=無法附加狀態
SkillSplash=技能濺射
Sacrifice=犧牲
SacrificeDamage=犧牲傷害
MatkPerStr=每點力量提供魔法攻擊
AtkPerStr=每點力量提供物理攻擊
StrMult=力量百分比
VitMult=體力百分比
AgiMult=敏捷百分比
DexMult=靈巧百分比
IntMult=智力百分比
LukMult=幸運百分比
AtkSpdMult=攻擊速度百分比
CastSpdMult=施法速度百分比
MoveSpdMult=移動速度百分比
SkillCharges=技能充能次數
AutoFire=自動連射
DamageCloseRange=近距離傷害
DamageFarRange=遠距離傷害
DamageToSummons=對召喚物傷害
DamageFromSummons=承受召喚物傷害
SummonSpellEcho=召喚物法術回響
SummonDamage=召喚物傷害
SummonDamageReduction=召喚物傷害減免
SummonLeech=召喚物生命吸取
SummonCostShare=召喚物消耗分攤
SummonHit=召喚物命中
SummonAutoattackDamage=召喚物普通攻擊傷害
SummonResist=召喚物抗性
SiphonHp=汲取生命
SiphonMp=汲取魔力
HealShare=治療共享
DeathShare=死亡連結
AutocastDeath=死亡時自動施法
AutocastKill=擊殺時自動施法
CooldownRecovery=冷卻恢復速度
StatusMaxStacks=狀態最大層數
TwohandedStanceBonus=雙手武器姿態加成
AtkSpdLimit=攻擊速度上限
AutoattackMatk=普通攻擊魔法攻擊力
CastTimeReduction=施法時間縮短
CastTimeReductionLimit=施法時間縮短上限
CastRange=施法距離
DodgeRecovery=閃避恢復
AtkSpdFlat=固定攻擊速度
ThreatMult=仇恨倍率
DefPierce=物理防禦穿透
MdefPierce=魔法防禦穿透
PerfectHit=必中
HealingToBarrier=治療轉為屏障
SkillPull=技能拉取
SkillDamageLowHp=低生命時技能傷害
SkillRange=技能距離
SkillInstances=技能實例數
SkillCrit=技能暴擊
SkillLeap=技能跳躍
SkillThreat=技能仇恨
SkillCastTimeMult=技能施法時間倍率
SkillHitsMult=技能命中次數倍率
SkillDurationMult=技能持續時間倍率
SkillDamageReceived=承受技能傷害
SkillDamageVsStatus=對狀態目標的技能傷害
SkillReplace=技能替換
StatusReplace=狀態替換
StatusDuration=狀態持續時間
SkillMaxInstances=技能最大實例數
SkillAutocast=技能自動施放
SkillApplyStatus=技能附加狀態
SkillConsumeStatus=技能消耗狀態
SkillRecoverHp=技能恢復生命
SkillRecoverMp=技能恢復魔力
DamageVsStatus=對狀態目標傷害
SetAtkSpd=設定攻擊速度
MpCostAsHp=以生命支付魔力消耗
StatusPerMissingHpMult=依損失生命增加狀態效果
MoveSpdCap=移動速度上限
ApplyStatusAttack=攻擊時附加狀態
ApplyStatusHit=命中時附加狀態
RatingHp=生命評分
RatingAtk=物理攻擊評分
RatingMatk=魔法攻擊評分
RatingExp=經驗評分
DamageDeferred=延遲承受傷害
SplashDamageReduction=濺射傷害減免
BondTargets=連結目標數
""".strip().splitlines()
)

if frozenset(STAT_TYPE_ZH) != STAT_TYPE_SET:
    missing = sorted(STAT_TYPE_SET - frozenset(STAT_TYPE_ZH))
    extra = sorted(frozenset(STAT_TYPE_ZH) - STAT_TYPE_SET)
    raise RuntimeError(f"Chinese stat labels mismatch: missing={missing}, extra={extra}")


@dataclass(frozen=True)
class EquipmentFilterRule:
    stat_type: str
    minimum: float


@dataclass(frozen=True)
class EquipmentFilterProfile:
    item_id: str
    display_name: str
    minimum_matches: int = 1
    rules: tuple[EquipmentFilterRule, ...] = ()
    always_dismantle: bool = False


@dataclass(frozen=True)
class EquipmentFilterConfig:
    enabled: bool = False
    profiles: tuple[EquipmentFilterProfile, ...] = ()


@dataclass(frozen=True)
class EquipmentFilterDecision:
    uid: str
    item_id: str
    display_name: str
    favorite: bool
    matched_count: int
    required_count: int
    matched_types: tuple[str, ...]
    keep: bool
    forced_dismantle: bool


@dataclass(frozen=True)
class EquipmentFilterState:
    phase: str = "idle"
    message: str = "Equipment filter is idle"
    running: bool = False
    timestamp_ms: int = 0
    next_run_at: float = 0.0
    scanned: int = 0
    kept: int = 0
    protected: int = 0
    skipped: int = 0
    favorited: int = 0
    dismantled: int = 0
    forced_dismantled: int = 0
    errors: int = 0


InventoryReader = Callable[[float], dict[str, Any]]
FavoriteMutator = Callable[..., dict[str, Any]]
Dismantler = Callable[..., dict[str, Any]]
ProgressCallback = Callable[[EquipmentFilterState], None]
CancelCheck = Callable[[], bool]
LockFactory = Callable[[CancelCheck], ContextManager[None]]


def stat_display_label(stat_type: str) -> str:
    acronyms = {
        "Hp": "HP",
        "Mp": "MP",
        "Atk": "ATK",
        "Matk": "MATK",
        "Def": "DEF",
        "Mdef": "MDEF",
    }
    if stat_type in acronyms:
        base_label = f"{acronyms[stat_type]}  ({stat_type})"
    elif stat_type.endswith("Mult"):
        base = stat_type[:-4]
        rendered = acronyms.get(base, base)
        base_label = f"{rendered}%  ({stat_type})"
    else:
        base_label = stat_type
    chinese = STAT_TYPE_ZH.get(stat_type, "未知詞條")
    return f"{base_label} — {chinese}"


def _atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def validate_filter_profile(profile: EquipmentFilterProfile) -> None:
    if not profile.item_id.strip():
        raise ValueError("equipment filter profile item_id is required")
    if not profile.display_name.strip():
        raise ValueError(f"display_name is required for {profile.item_id}")
    if type(profile.minimum_matches) is not int or profile.minimum_matches < 1:
        raise ValueError("minimum_matches must be a positive integer")
    if type(profile.always_dismantle) is not bool:
        raise ValueError("always_dismantle must be true or false")
    seen: set[str] = set()
    for rule in profile.rules:
        if rule.stat_type not in STAT_TYPE_SET:
            raise ValueError(f"unknown equipment stat type: {rule.stat_type}")
        if rule.stat_type in seen:
            raise ValueError(f"duplicate equipment stat rule: {rule.stat_type}")
        seen.add(rule.stat_type)
        if not math.isfinite(float(rule.minimum)):
            raise ValueError(f"minimum for {rule.stat_type} must be finite")
    if (
        profile.rules
        and not profile.always_dismantle
        and profile.minimum_matches > len(profile.rules)
    ):
        raise ValueError(
            f"minimum_matches for {profile.display_name} cannot exceed "
            "the number of filled rules"
        )


def validate_filter_config(config: EquipmentFilterConfig) -> None:
    if type(config.enabled) is not bool:
        raise ValueError("equipment filter enabled must be true or false")
    seen: set[str] = set()
    for profile in config.profiles:
        validate_filter_profile(profile)
        if profile.item_id in seen:
            raise ValueError(f"duplicate equipment profile: {profile.item_id}")
        seen.add(profile.item_id)


def active_profiles(
    config: EquipmentFilterConfig,
) -> tuple[EquipmentFilterProfile, ...]:
    return tuple(
        profile
        for profile in config.profiles
        if profile.rules or profile.always_dismantle
    )


def save_filter_config(
    path: Path, config: EquipmentFilterConfig
) -> None:
    validate_filter_config(config)
    _atomic_write_json(
        path,
        {
            "schema_version": 3,
            "enabled": config.enabled,
            "interval_sec": int(FILTER_INTERVAL_SEC),
            "profiles": [
                {
                    "item_id": profile.item_id,
                    "display_name": profile.display_name,
                    "minimum_matches": profile.minimum_matches,
                    "always_dismantle": profile.always_dismantle,
                    "rules": [asdict(rule) for rule in profile.rules],
                }
                for profile in config.profiles
            ],
        },
    )


def load_filter_config(path: Path = FILTER_CONFIG_PATH) -> EquipmentFilterConfig:
    if not path.exists():
        config = EquipmentFilterConfig()
        save_filter_config(path, config)
        return config
    raw = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(raw, dict):
        raise ValueError("equipment filter config must be an object")
    schema_version = raw.get("schema_version", 1)
    if schema_version not in {2, 3}:
        # A global v1 rule cannot be assigned to a name without guessing.
        # Disable it safely and let the editor create explicit named profiles.
        return EquipmentFilterConfig()
    profiles_raw = raw.get("profiles", [])
    if not isinstance(profiles_raw, list):
        raise ValueError("equipment filter profiles must be an array")
    profiles: list[EquipmentFilterProfile] = []
    for profile_raw in profiles_raw:
        if not isinstance(profile_raw, dict):
            raise ValueError("each equipment filter profile must be an object")
        item_id = str(profile_raw.get("item_id") or "")
        display_name = str(profile_raw.get("display_name") or item_id)
        rules_raw = profile_raw.get("rules", [])
        if not isinstance(rules_raw, list):
            raise ValueError(f"rules for {display_name or '?'} must be an array")
        rules: list[EquipmentFilterRule] = []
        for entry in rules_raw:
            if not isinstance(entry, dict):
                raise ValueError("each equipment filter rule must be an object")
            stat_type = str(entry.get("stat_type") or "")
            try:
                minimum = float(entry.get("minimum"))
            except (TypeError, ValueError) as error:
                raise ValueError(f"invalid minimum for {stat_type or '?'}") from error
            rules.append(EquipmentFilterRule(stat_type, minimum))
        profiles.append(
            EquipmentFilterProfile(
                item_id=item_id,
                display_name=display_name,
                minimum_matches=profile_raw.get("minimum_matches", 1),
                rules=tuple(rules),
                always_dismantle=(
                    profile_raw.get("always_dismantle", False)
                    if schema_version >= 3
                    else False
                ),
            )
        )
    config = EquipmentFilterConfig(
        enabled=raw.get("enabled", False),
        profiles=tuple(profiles),
    )
    validate_filter_config(config)
    return config


def _decimal(value: object) -> Decimal | None:
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    return result if result.is_finite() else None


def displayed_stat_values(item: dict[str, Any]) -> dict[str, Decimal]:
    values: dict[str, Decimal] = {}
    stats = item.get("display_substats")
    if not isinstance(stats, list):
        return values
    for stat in stats:
        if not isinstance(stat, dict):
            continue
        stat_type = str(stat.get("type") or "")
        if stat_type not in STAT_TYPE_SET:
            continue
        number = _decimal(stat.get("value"))
        if number is None:
            continue
        previous = values.get(stat_type)
        if previous is None or number > previous:
            values[stat_type] = number
    return values


def equipment_catalog(inventory: dict[str, Any]) -> dict[str, str]:
    """Return stable item_id -> display name pairs from backpack and equipment."""
    catalog: dict[str, str] = {}
    candidates: list[object] = list(inventory.get("items", []))
    for equipped in inventory.get("equipped_items", []):
        if isinstance(equipped, dict):
            candidates.append(equipped.get("item"))
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        item_id = str(candidate.get("item_id") or "").strip()
        if not item_id:
            continue
        display_name = str(candidate.get("display_name") or item_id).strip()
        catalog[item_id] = display_name or item_id
    return catalog


def evaluate_equipment(
    item: dict[str, Any], profile: EquipmentFilterProfile
) -> EquipmentFilterDecision:
    validate_filter_profile(profile)
    if not profile.rules and not profile.always_dismantle:
        raise ValueError(
            "a profile requires filled rules or always_dismantle"
        )
    item_id = str(item.get("item_id") or "")
    if item_id != profile.item_id:
        raise ValueError(
            f"equipment item_id {item_id or '?'} does not match profile "
            f"{profile.item_id}"
        )
    uid = str(item.get("uid") or "")
    if not uid or not item_id:
        raise ValueError("equipment item was missing uid or item_id")
    if profile.always_dismantle:
        matched: tuple[str, ...] = ()
        required_count = 0
        keep = False
    else:
        values = displayed_stat_values(item)
        matched = tuple(
            rule.stat_type
            for rule in profile.rules
            if rule.stat_type in values
            and values[rule.stat_type] >= Decimal(str(rule.minimum))
        )
        required_count = profile.minimum_matches
        keep = len(matched) >= profile.minimum_matches
    return EquipmentFilterDecision(
        uid=uid,
        item_id=item_id,
        display_name=str(item.get("display_name") or item_id),
        favorite=item.get("favorite") is True,
        matched_count=len(matched),
        required_count=required_count,
        matched_types=matched,
        keep=keep,
        forced_dismantle=profile.always_dismantle,
    )


def _wait_for_result(
    path: Path,
    request_id: int,
    *,
    timeout: float,
    cancel_check: CancelCheck,
) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    latest: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if cancel_check():
            raise RuntimeError("equipment filter cancelled")
        try:
            candidate = json.loads(path.read_text(encoding="utf-8-sig"))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            time.sleep(0.05)
            continue
        if not isinstance(candidate, dict) or candidate.get("request_id") != request_id:
            time.sleep(0.05)
            continue
        latest = candidate
        if candidate.get("status") in {"ok", "error", "unverified"}:
            return candidate
        time.sleep(0.05)
    status = str(latest.get("status")) if latest else "no response"
    raise TimeoutError(f"equipment mutation timed out after {status}")


def request_favorite_state(
    uid: str,
    item_id: str,
    *,
    desired: bool,
    location: str = "backpack",
    timeout: float = 12.0,
    cancel_check: CancelCheck = lambda: False,
) -> dict[str, Any]:
    request_id = time.time_ns() // 1_000
    _atomic_write_json(
        FAVORITE_REQUEST_PATH,
        {
            "schema_version": 1,
            "request_id": request_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "uid": uid,
            "item_id": item_id,
            "location": location,
            "desired": desired,
            "confirm": FAVORITE_CONFIRMATION,
        },
    )
    result = _wait_for_result(
        FAVORITE_RESULT_PATH,
        request_id,
        timeout=timeout,
        cancel_check=cancel_check,
    )
    if result.get("status") != "ok" or result.get("favorite") is not desired:
        raise RuntimeError(str(result.get("message") or "favorite mutation failed"))
    return result


def request_dismantle(
    uid: str,
    item_id: str,
    *,
    timeout: float = 12.0,
    cancel_check: CancelCheck = lambda: False,
) -> dict[str, Any]:
    request_id = time.time_ns() // 1_000
    _atomic_write_json(
        DISMANTLE_REQUEST_PATH,
        {
            "schema_version": 1,
            "request_id": request_id,
            "timestamp_ms": time.time_ns() // 1_000_000,
            "uid": uid,
            "item_id": item_id,
            "confirm": DISMANTLE_CONFIRMATION,
        },
    )
    result = _wait_for_result(
        DISMANTLE_RESULT_PATH,
        request_id,
        timeout=timeout,
        cancel_check=cancel_check,
    )
    if result.get("status") != "ok" or result.get("verified_absent") is not True:
        raise RuntimeError(str(result.get("message") or "dismantle failed"))
    return result


def _default_lock_factory(cancel_check: CancelCheck) -> ContextManager[None]:
    return inventory_pricer.pricing_session_lock(cancel_check=cancel_check)


class EquipmentFilterRunner:
    """Run one serialized read/evaluate/mutate cycle."""

    def __init__(
        self,
        *,
        inventory_reader: InventoryReader = inventory_pricer.read_inventory,
        favorite_mutator: FavoriteMutator = request_favorite_state,
        dismantler: Dismantler = request_dismantle,
        lock_factory: LockFactory = _default_lock_factory,
    ) -> None:
        self.inventory_reader = inventory_reader
        self.favorite_mutator = favorite_mutator
        self.dismantler = dismantler
        self.lock_factory = lock_factory

    def run(
        self,
        config: EquipmentFilterConfig,
        *,
        cancel_check: CancelCheck = lambda: False,
        progress: ProgressCallback | None = None,
    ) -> EquipmentFilterState:
        validate_filter_config(config)
        if not config.enabled:
            raise ValueError("equipment filter is disabled")
        profiles = {
            profile.item_id: profile for profile in active_profiles(config)
        }
        if not profiles:
            raise ValueError(
                "equipment filter has no named profiles with rules or "
                "always-dismantle mode"
            )

        def emit(state: EquipmentFilterState) -> None:
            if progress is not None:
                progress(state)

        with self.lock_factory(cancel_check):
            emit(
                EquipmentFilterState(
                    phase="reading",
                    message="Reading fresh backpack equipment",
                    running=True,
                    timestamp_ms=time.time_ns() // 1_000_000,
                )
            )
            inventory = self.inventory_reader(8.0)
            items = [
                item
                for item in inventory.get("items", [])
                if isinstance(item, dict)
            ]
            decisions: list[EquipmentFilterDecision] = []
            errors = 0
            protected = 0
            skipped = 0
            for item in items:
                if item.get("favorite") is True:
                    protected += 1
                    continue
                item_id = str(item.get("item_id") or "")
                profile = profiles.get(item_id)
                if profile is None:
                    skipped += 1
                    continue
                try:
                    decisions.append(evaluate_equipment(item, profile))
                except ValueError:
                    errors += 1

            kept = sum(decision.keep for decision in decisions)
            favorited = 0
            dismantled = 0
            forced_dismantled = 0
            total = len(items)
            for decision in decisions:
                if cancel_check():
                    raise RuntimeError("equipment filter cancelled")
                if decision.forced_dismantle:
                    action = "force_dismantle"
                    action_detail = "unconditional"
                else:
                    action = "favorite" if decision.keep else "dismantle"
                    action_detail = (
                        f"{decision.matched_count}/{decision.required_count}"
                    )
                emit(
                    EquipmentFilterState(
                        phase=action,
                        message=(
                            f"{action}: {decision.display_name} "
                            f"({action_detail})"
                        ),
                        running=True,
                        timestamp_ms=time.time_ns() // 1_000_000,
                        scanned=total,
                        kept=kept,
                        protected=protected,
                        skipped=skipped,
                        favorited=favorited,
                        dismantled=dismantled,
                        forced_dismantled=forced_dismantled,
                        errors=errors,
                    )
                )
                try:
                    if decision.keep:
                        self.favorite_mutator(
                            decision.uid,
                            decision.item_id,
                            desired=True,
                            location="backpack",
                            cancel_check=cancel_check,
                        )
                        favorited += 1
                    else:
                        self.dismantler(
                            decision.uid,
                            decision.item_id,
                            cancel_check=cancel_check,
                        )
                        dismantled += 1
                        if decision.forced_dismantle:
                            forced_dismantled += 1
                except Exception:
                    errors += 1

            return EquipmentFilterState(
                phase="complete",
                message=(
                    f"Complete: scanned {total}, kept {kept}, "
                    f"protected {protected}, skipped {skipped}, "
                    f"favorited {favorited}, "
                    f"dismantled {dismantled} (forced {forced_dismantled}), "
                    f"errors {errors}"
                ),
                running=False,
                timestamp_ms=time.time_ns() // 1_000_000,
                scanned=total,
                kept=kept,
                protected=protected,
                skipped=skipped,
                favorited=favorited,
                dismantled=dismantled,
                forced_dismantled=forced_dismantled,
                errors=errors,
            )


class EquipmentFilterController:
    """Schedule one guarded cycle every 100 seconds."""

    def __init__(
        self,
        *,
        config_path: Path = FILTER_CONFIG_PATH,
        runner: EquipmentFilterRunner | None = None,
        interval_sec: float = FILTER_INTERVAL_SEC,
    ) -> None:
        self.config_path = config_path
        self.runner = runner or EquipmentFilterRunner()
        self.interval_sec = float(interval_sec)
        self._updates: queue.SimpleQueue[EquipmentFilterState] = queue.SimpleQueue()
        self._stop_event = threading.Event()
        self._run_now_event = threading.Event()
        self._thread: threading.Thread | None = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop_event = threading.Event()
        self._run_now_event = threading.Event()
        self._thread = threading.Thread(
            target=self._loop,
            name="SpiritValeEquipmentFilter",
            daemon=True,
        )
        self._thread.start()

    def request_immediate(self) -> None:
        self._run_now_event.set()

    def poll_latest(self) -> EquipmentFilterState | None:
        latest = None
        while True:
            try:
                latest = self._updates.get_nowait()
            except queue.Empty:
                return latest

    def stop(self, join_timeout: float = 2.0) -> None:
        self._stop_event.set()
        self._run_now_event.set()
        if self._thread is not None:
            self._thread.join(max(0.0, join_timeout))

    def _loop(self) -> None:
        next_run = time.monotonic() + self.interval_sec
        previously_enabled = False
        while not self._stop_event.is_set():
            try:
                config = load_filter_config(self.config_path)
            except Exception as error:
                self._updates.put(
                    EquipmentFilterState(
                        phase="error",
                        message=f"Filter config error: {error}",
                        timestamp_ms=time.time_ns() // 1_000_000,
                    )
                )
                self._stop_event.wait(1.0)
                continue

            enabled = config.enabled and bool(active_profiles(config))
            now = time.monotonic()
            if enabled and not previously_enabled:
                next_run = now + self.interval_sec
            previously_enabled = enabled
            run_now = self._run_now_event.is_set()
            if run_now:
                self._run_now_event.clear()
            if enabled and (run_now or now >= next_run):
                try:
                    result = self.runner.run(
                        config,
                        cancel_check=self._stop_event.is_set,
                        progress=self._updates.put,
                    )
                except Exception as error:
                    result = EquipmentFilterState(
                        phase="error",
                        message=str(error),
                        timestamp_ms=time.time_ns() // 1_000_000,
                    )
                self._updates.put(result)
                next_run = time.monotonic() + self.interval_sec
            elif enabled:
                self._updates.put(
                    EquipmentFilterState(
                        phase="scheduled",
                        message=f"Next backpack filter in {max(0, int(next_run-now))}s",
                        next_run_at=next_run,
                    )
                )
            wait_seconds = 1.0
            if enabled:
                wait_seconds = min(
                    1.0,
                    max(0.05, next_run - time.monotonic()),
                )
            self._stop_event.wait(wait_seconds)


class EquipmentFilterEditor:
    """Persistent per-item Tk editor toggled by the Delete hotkey."""

    def __init__(
        self,
        *,
        config_path: Path = FILTER_CONFIG_PATH,
        run_now: Callable[[], None] | None = None,
        inventory_reader: InventoryReader = inventory_pricer.read_inventory,
    ) -> None:
        self.config_path = config_path
        self.run_now = run_now
        self.inventory_reader = inventory_reader
        self._commands: queue.SimpleQueue[tuple[str, object]] = queue.SimpleQueue()
        self._thread: threading.Thread | None = None
        self._last_status = "先選裝備名稱，再設定該名稱自己的詞條與 N。"
        self._status_lock = threading.Lock()

    def toggle(self) -> None:
        if self._thread is None or not self._thread.is_alive():
            self._thread = threading.Thread(
                target=self._ui_main,
                name="SpiritValeEquipmentFilterEditor",
                daemon=True,
            )
            self._thread.start()
        self._commands.put(("toggle", ""))

    def set_status(self, message: str) -> None:
        with self._status_lock:
            self._last_status = message
        if self._thread is not None and self._thread.is_alive():
            self._commands.put(("status", message))

    def stop(self) -> None:
        self._commands.put(("stop", ""))
        if self._thread is not None:
            self._thread.join(2.0)

    def _ui_main(self) -> None:
        import tkinter as tk
        from tkinter import messagebox, ttk

        root = tk.Tk()
        root.title("SpiritVale 依裝備名稱設定詞條篩選")
        root.geometry("780x860")
        root.attributes("-topmost", True)
        root.withdraw()

        enabled_var = tk.BooleanVar(value=False)
        selected_label_var = tk.StringVar(value="")
        minimum_matches_var = tk.StringVar(value="1")
        always_dismantle_var = tk.BooleanVar(value=False)
        always_button_text_var = tk.StringVar(value="此名稱一律分解")
        search_var = tk.StringVar(value="")
        with self._status_lock:
            initial_status = self._last_status
        status_var = tk.StringVar(value=initial_status)
        value_vars = {stat_type: tk.StringVar(value="") for stat_type in STAT_TYPES}
        profiles: dict[str, EquipmentFilterProfile] = {}
        catalog: dict[str, str] = {}
        label_to_item_id: dict[str, str] = {}
        current_item_id: str | None = None
        catalog_loading = False

        header = tk.Frame(root, padx=12, pady=10)
        header.pack(fill="x")
        tk.Checkbutton(
            header,
            text="啟用每 100 秒自動篩選（收藏品永不分解）",
            variable=enabled_var,
        ).grid(row=0, column=0, columnspan=5, sticky="w")
        tk.Label(header, text="裝備名稱：").grid(row=1, column=0, sticky="w")
        item_selector = ttk.Combobox(
            header,
            textvariable=selected_label_var,
            state="readonly",
            width=47,
        )
        item_selector.grid(row=1, column=1, columnspan=3, sticky="ew", padx=(0, 8))
        refresh_button = tk.Button(header, text="重新讀取裝備", width=13)
        refresh_button.grid(row=1, column=4, sticky="e")
        tk.Label(header, text="此名稱至少符合 N 項：").grid(
            row=2, column=0, sticky="w", pady=(7, 0)
        )
        minimum_spinbox = tk.Spinbox(
            header,
            from_=1,
            to=len(STAT_TYPES),
            width=7,
            textvariable=minimum_matches_var,
        )
        minimum_spinbox.grid(row=2, column=1, sticky="w", pady=(7, 0))
        tk.Label(header, text="搜尋詞條：").grid(
            row=2, column=2, sticky="e", pady=(7, 0)
        )
        tk.Entry(header, textvariable=search_var, width=22).grid(
            row=2, column=3, columnspan=2, sticky="ew", pady=(7, 0)
        )
        header.columnconfigure(3, weight=1)
        tk.Label(
            header,
            text=(
                "每個裝備名稱各自保存規則；未設定名稱安全略過。"
                "裝備畫面值 ≥ 輸入值，空白表示不使用。"
            ),
            fg="#7a3100",
            anchor="w",
        ).grid(row=3, column=0, columnspan=5, sticky="ew", pady=(8, 0))

        table_host = tk.Frame(root, padx=12)
        table_host.pack(fill="both", expand=True)
        canvas = tk.Canvas(table_host, highlightthickness=0)
        scrollbar = tk.Scrollbar(table_host, orient="vertical", command=canvas.yview)
        rows_frame = tk.Frame(canvas)
        window_id = canvas.create_window((0, 0), window=rows_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        row_widgets: dict[str, tuple[tk.Label, tk.Entry]] = {}
        tk.Label(rows_frame, text="詞條", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=0, sticky="w", padx=6, pady=4
        )
        tk.Label(rows_frame, text="最低值", font=("Segoe UI", 10, "bold")).grid(
            row=0, column=1, sticky="w", padx=6, pady=4
        )
        for index, stat_type in enumerate(STAT_TYPES, 1):
            label = tk.Label(rows_frame, text=stat_display_label(stat_type), anchor="w")
            entry = tk.Entry(rows_frame, textvariable=value_vars[stat_type], width=14)
            label.grid(row=index, column=0, sticky="ew", padx=6, pady=2)
            entry.grid(row=index, column=1, sticky="w", padx=6, pady=2)
            row_widgets[stat_type] = (label, entry)
        rows_frame.columnconfigure(0, weight=1)

        def refresh_scroll(_event: object | None = None) -> None:
            canvas.configure(scrollregion=canvas.bbox("all"))
            canvas.itemconfigure(window_id, width=canvas.winfo_width())

        rows_frame.bind("<Configure>", refresh_scroll)
        canvas.bind("<Configure>", refresh_scroll)
        canvas.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-event.delta / 120), "units"),
        )

        def filter_rows(*_args: object) -> None:
            query = search_var.get().strip().casefold()
            visible_row = 1
            for stat_type, (label, entry) in row_widgets.items():
                text = stat_display_label(stat_type).casefold()
                if query and query not in text:
                    label.grid_remove()
                    entry.grid_remove()
                    continue
                label.grid(row=visible_row, column=0, sticky="ew", padx=6, pady=2)
                entry.grid(row=visible_row, column=1, sticky="w", padx=6, pady=2)
                visible_row += 1
            refresh_scroll()

        search_var.trace_add("write", filter_rows)

        def selector_label(item_id: str) -> str:
            name = catalog.get(item_id) or profiles[item_id].display_name
            rule_count = len(profiles[item_id].rules) if item_id in profiles else 0
            if item_id in profiles and profiles[item_id].always_dismantle:
                marker = "[一律分解] "
            else:
                marker = "✓ " if rule_count else ""
            return f"{marker}{name}  [{item_id}]"

        def update_mode_controls() -> None:
            forced = always_dismantle_var.get()
            state = "disabled" if forced else "normal"
            minimum_spinbox.configure(state=state)
            for _label, entry in row_widgets.values():
                entry.configure(state=state)
            always_button_text_var.set(
                "取消一律分解" if forced else "此名稱一律分解"
            )

        def clear_profile_form() -> None:
            minimum_matches_var.set("1")
            always_dismantle_var.set(False)
            for variable in value_vars.values():
                variable.set("")
            update_mode_controls()

        def load_profile_form(item_id: str) -> None:
            nonlocal current_item_id
            current_item_id = item_id
            clear_profile_form()
            profile = profiles.get(item_id)
            if profile is not None:
                minimum_matches_var.set(str(profile.minimum_matches))
                always_dismantle_var.set(profile.always_dismantle)
                for rule in profile.rules:
                    value_vars[rule.stat_type].set(format(rule.minimum, "g"))
            update_mode_controls()
            name = catalog.get(item_id) or (profile.display_name if profile else item_id)
            if profile is not None and profile.always_dismantle:
                status_var.set(
                    f"目前編輯：{name}；模式為一律分解（收藏品仍保護）。"
                )
            else:
                status_var.set(
                    f"目前編輯：{name}；此名稱有 "
                    f"{len(profile.rules) if profile else 0} 項條件。"
                )

        def profile_from_form(item_id: str) -> EquipmentFilterProfile:
            rules: list[EquipmentFilterRule] = []
            for stat_type, variable in value_vars.items():
                text = variable.get().strip()
                if not text:
                    continue
                value = float(text)
                if not math.isfinite(value):
                    raise ValueError(f"{stat_type} 必須是有限數字")
                rules.append(EquipmentFilterRule(stat_type, value))
            minimum_matches = int(minimum_matches_var.get().strip())
            old = profiles.get(item_id)
            display_name = catalog.get(item_id) or (
                old.display_name if old is not None else item_id
            )
            profile = EquipmentFilterProfile(
                item_id=item_id,
                display_name=display_name,
                minimum_matches=minimum_matches,
                rules=tuple(rules),
                always_dismantle=always_dismantle_var.get(),
            )
            validate_filter_profile(profile)
            return profile

        def store_current_profile(*, show_error: bool = True) -> bool:
            if current_item_id is None:
                return True
            try:
                profiles[current_item_id] = profile_from_form(current_item_id)
            except (TypeError, ValueError) as error:
                if show_error:
                    messagebox.showerror("目前裝備設定錯誤", str(error), parent=root)
                return False
            return True

        def rebuild_selector(preferred: str | None = None) -> None:
            nonlocal label_to_item_id
            item_ids = sorted(
                set(catalog) | set(profiles),
                key=lambda value: (
                    (catalog.get(value) or profiles[value].display_name).casefold(),
                    value.casefold(),
                ),
            )
            labels = [selector_label(item_id) for item_id in item_ids]
            label_to_item_id = dict(zip(labels, item_ids))
            item_selector.configure(values=labels)
            chosen = current_item_id if current_item_id in item_ids else preferred
            if chosen not in item_ids:
                chosen = item_ids[0] if item_ids else None
            if chosen is None:
                selected_label_var.set("")
                clear_profile_form()
                status_var.set("目前沒有可選裝備；請按「重新讀取裝備」。")
                return
            selected_label_var.set(selector_label(chosen))
            if current_item_id != chosen:
                load_profile_form(chosen)

        def on_item_selected(_event: object | None = None) -> None:
            selected = label_to_item_id.get(selected_label_var.get())
            if selected is None or selected == current_item_id:
                return
            previous = current_item_id
            if not store_current_profile():
                if previous is not None:
                    selected_label_var.set(selector_label(previous))
                return
            load_profile_form(selected)
            rebuild_selector(selected)

        item_selector.bind("<<ComboboxSelected>>", on_item_selected)

        def request_catalog_refresh() -> None:
            nonlocal catalog_loading
            if catalog_loading:
                return
            catalog_loading = True
            refresh_button.configure(state="disabled")
            status_var.set("正在從遊戲內存讀取背包與穿戴裝備名稱……")

            def worker() -> None:
                try:
                    inventory = self.inventory_reader(8.0)
                    self._commands.put(("catalog", equipment_catalog(inventory)))
                except Exception as error:
                    self._commands.put(("catalog_error", str(error)))

            threading.Thread(
                target=worker,
                name="SpiritValeEquipmentCatalog",
                daemon=True,
            ).start()

        refresh_button.configure(command=request_catalog_refresh)

        def load_into_form() -> None:
            nonlocal profiles, catalog, current_item_id
            try:
                config = load_filter_config(self.config_path)
            except Exception as error:
                messagebox.showerror("設定錯誤", str(error), parent=root)
                return
            enabled_var.set(config.enabled)
            profiles = {profile.item_id: profile for profile in config.profiles}
            catalog = {
                profile.item_id: profile.display_name for profile in config.profiles
            }
            current_item_id = None
            rebuild_selector()
            request_catalog_refresh()

        def save_from_form() -> EquipmentFilterConfig | None:
            if not store_current_profile():
                return None
            config = EquipmentFilterConfig(
                enabled=enabled_var.get(),
                profiles=tuple(
                    profiles[item_id] for item_id in sorted(profiles)
                ),
            )
            if config.enabled and not active_profiles(config):
                messagebox.showerror(
                    "無法儲存",
                    "啟用前至少要替一個裝備名稱填寫詞條或設為一律分解；"
                    "未設定名稱不會分解。",
                    parent=root,
                )
                return None
            try:
                save_filter_config(self.config_path, config)
            except (ValueError, OSError) as error:
                messagebox.showerror("無法儲存", str(error), parent=root)
                return None
            active = active_profiles(config)
            forced_count = sum(profile.always_dismantle for profile in active)
            status_var.set(
                f"已儲存：{len(active)} 個裝備名稱、"
                f"共 {sum(len(profile.rules) for profile in active)} 項條件、"
                f"{forced_count} 個一律分解。"
            )
            rebuild_selector(current_item_id)
            return config

        def remove_current_profile() -> None:
            if current_item_id is None:
                return
            profiles.pop(current_item_id, None)
            clear_profile_form()
            rebuild_selector(current_item_id)
            status_var.set("已清除此名稱的規則；按「儲存」後生效。")

        def toggle_always_dismantle() -> None:
            if current_item_id is None:
                return
            name = catalog.get(current_item_id) or current_item_id
            if not always_dismantle_var.get():
                confirmed = messagebox.askyesno(
                    "確認一律分解",
                    f"要將「{name}」設為不看素質、一律分解嗎？\n\n"
                    "只有未收藏的同名背包裝備會被分解；收藏品仍無條件保護。\n"
                    "按「儲存全部名稱」或「儲存並立即執行」後生效。",
                    parent=root,
                )
                if not confirmed:
                    return
                always_dismantle_var.set(True)
                status_var.set(
                    f"{name} 已暫設為一律分解；收藏品仍保護。請按儲存。"
                )
            else:
                always_dismantle_var.set(False)
                status_var.set(
                    f"已取消 {name} 的一律分解；原詞條規則恢復使用。請按儲存。"
                )
            update_mode_controls()

        buttons = tk.Frame(root, padx=12, pady=10)
        buttons.pack(fill="x")
        tk.Button(buttons, text="儲存全部名稱", width=15, command=save_from_form).pack(
            side="left"
        )
        tk.Button(
            buttons,
            text="清除此名稱規則",
            width=15,
            command=remove_current_profile,
        ).pack(side="left", padx=8)
        tk.Button(
            buttons,
            textvariable=always_button_text_var,
            width=15,
            fg="#9a0000",
            command=toggle_always_dismantle,
        ).pack(side="left", padx=(0, 8))

        def save_and_run() -> None:
            config = save_from_form()
            if config is not None and config.enabled and self.run_now is not None:
                self.run_now()
                status_var.set("已要求立即執行一次；之後仍每 100 秒執行。")

        tk.Button(buttons, text="儲存並立即執行", width=17, command=save_and_run).pack(
            side="left"
        )
        tk.Button(buttons, text="隱藏", width=7, command=root.withdraw).pack(
            side="right"
        )
        tk.Label(root, textvariable=status_var, anchor="w", padx=12, pady=6).pack(
            fill="x"
        )
        root.protocol("WM_DELETE_WINDOW", root.withdraw)
        load_into_form()
        filter_rows()

        def poll_commands() -> None:
            nonlocal catalog_loading
            while True:
                try:
                    command, value = self._commands.get_nowait()
                except queue.Empty:
                    break
                if command == "toggle":
                    if root.state() == "withdrawn":
                        load_into_form()
                        root.deiconify()
                        root.lift()
                    else:
                        root.withdraw()
                elif command == "status":
                    status_var.set(str(value))
                elif command == "catalog":
                    catalog_loading = False
                    refresh_button.configure(state="normal")
                    if isinstance(value, dict):
                        catalog.update(
                            {
                                str(item_id): str(display_name)
                                for item_id, display_name in value.items()
                            }
                        )
                    rebuild_selector(current_item_id)
                    status_var.set(
                        f"已讀取 {len(catalog)} 個裝備名稱；請選名稱後設定。"
                    )
                elif command == "catalog_error":
                    catalog_loading = False
                    refresh_button.configure(state="normal")
                    status_var.set(f"讀取裝備名稱失敗：{value}")
                elif command == "stop":
                    root.destroy()
                    return
            root.after(100, poll_commands)

        root.after(50, poll_commands)
        root.mainloop()


def no_lock_factory(_cancel_check: CancelCheck) -> ContextManager[None]:
    """Test helper for runners that use injected in-memory dependencies."""
    return nullcontext()
