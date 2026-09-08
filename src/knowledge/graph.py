"""
Graph Relationship and Causal Network Storage using NetworkX.
Represents entities, claims, contradictions, problem hypotheses, causal edges, and provenance lineage.
"""

from typing import List, Dict, Any, Optional
import networkx as nx

from src.knowledge.interfaces import GraphStoreInterface


class NetworkXGraphStore(GraphStoreInterface):
    """NetworkX-backed directed knowledge graph store."""

    def __init__(self):
        self.graph = nx.DiGraph()

    def add_node(self, node_id: str, node_type: str, properties: Dict[str, Any] = None) -> None:
        """Add a graph entity node with type and attributes."""
        props = properties or {}
        props["node_type"] = node_type
        self.graph.add_node(node_id, **props)

    def add_edge(
        self,
        source_id: str,
        target_id: str,
        relation_type: str,
        properties: Dict[str, Any] = None
    ) -> None:
        """Add a directed relational edge."""
        props = properties or {}
        props["relation_type"] = relation_type
        self.graph.add_edge(source_id, target_id, **props)

    def get_neighbors(self, node_id: str, relation_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve neighboring nodes, optionally filtered by edge relation type."""
        if node_id not in self.graph:
            return []

        neighbors = []
        for nbr in self.graph.successors(node_id):
            edge_data = self.graph.get_edge_data(node_id, nbr)
            if relation_type is None or edge_data.get("relation_type") == relation_type:
                node_data = self.graph.nodes[nbr]
                neighbors.append({
                    "node_id": nbr,
                    "relation_type": edge_data.get("relation_type"),
                    "node_type": node_data.get("node_type"),
                    "properties": node_data,
                })

        return neighbors

    def get_causal_path(self, start_id: str, end_id: str) -> List[str]:
        """Find the shortest causal path between two entities if one exists."""
        if start_id not in self.graph or end_id not in self.graph:
            return []
        try:
            return nx.shortest_path(self.graph, source=start_id, target=end_id)
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return []

    def get_subgraph_nodes(self, node_ids: List[str]) -> Dict[str, Any]:
        """Extract a subgraph representation for export/visualization."""
        subgraph = self.graph.subgraph(node_ids)
        nodes = [{"id": n, **self.graph.nodes[n]} for n in subgraph.nodes]
        edges = [
            {"source": u, "target": v, **self.graph.get_edge_data(u, v)}
            for u, v in subgraph.edges
        ]
        return {"nodes": nodes, "edges": edges}

    def get_full_graph_data(self, limit_nodes: int = 150) -> Dict[str, Any]:
        """Return formatted graph nodes and edges optimized for interactive canvas rendering."""
        selected_nodes = list(self.graph.nodes)[:limit_nodes]
        subgraph = self.graph.subgraph(selected_nodes)

        nodes = []
        for n in subgraph.nodes:
            props = dict(self.graph.nodes[n])
            node_type = props.get("node_type", "ENTITY")
            label = props.get("title") or props.get("topic") or str(n)
            if len(label) > 40:
                label = label[:37] + "..."

            nodes.append({
                "id": str(n),
                "label": label,
                "type": node_type,
                "properties": props,
            })

        edges = []
        for u, v in subgraph.edges:
            data = self.graph.get_edge_data(u, v) or {}
            edges.append({
                "source": str(u),
                "target": str(v),
                "relation": data.get("relation_type", "RELATED_TO"),
            })

        return {"nodes": nodes, "edges": edges, "total_nodes": self.graph.number_of_nodes(), "total_edges": self.graph.number_of_edges()}

    def clear(self):
        """Reset the graph."""
        self.graph.clear()

