from .parse_pdb import parse_pdb, label_pocket_residues
# graph_construction imports torch_geometric — import it directly where needed
# to avoid ImportError when PyG is not installed
