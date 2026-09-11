"""Read GuardianBond's config from the installed game without modifying it."""
import json
from pathlib import Path
import UnityPy
from UnityPy.helpers.TypeTreeGenerator import TypeTreeGenerator
from UnityPy.helpers.TypeTreeNode import TypeTreeNode

root = Path(__file__).resolve().parent
game = Path(r'C:\Program Files (x86)\Steam\steamapps\common\SpiritVale')
generator = TypeTreeGenerator('6000.0.64f1')
generator.load_local_game(str(game))
nodes = json.loads(generator.get_nodes_as_json('Assembly-CSharp', 'SkillConfig'))
# Native MonoBehaviour header aligns its enabled byte before the script PPtr.
next(n for n in nodes if n['m_Name'] == 'm_Enabled')['m_MetaFlag'] |= 0x4000
node = TypeTreeNode.from_list(nodes)
env = UnityPy.load(str(game / 'SpiritVale_Data/sharedassets0.assets'))
obj = next(o for o in env.objects if o.path_id == 88154)
tree = obj.read_typetree(node)
assert tree['Id'] == 'GuardianBond'
(root / 'GuardianBond.skill.json').write_text(
    json.dumps(tree, ensure_ascii=False, indent=2), encoding='utf-8'
)
print({key: tree[key] for key in ('Id', 'TargetType', 'CastType', 'Bond', 'CanCastGround', 'Range')})
