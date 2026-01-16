from pyvis.network import Network
import logging

logger = logging.getLogger(__name__)


class VisualizationService:
    NODE_COLORS = {"User": "#00ff41", "Product": "#ff0055"}

    RELATIONSHIP_COLORS = {"FOLLOWS": "#4285f4", "RATES": "#fbbc04"}

    def __init__(self, height: str = "600px", width: str = "100%"):
        self.height = height
        self.width = width

    def create_user_network(
        self, query_result, show_ratings: bool = True
    ) -> Network | None:
        try:
            net = Network(
                height=self.height,
                width=self.width,
                bgcolor="#1e1e1e",
                font_color="white",
                directed=True,
            )

            net.barnes_hut(
                gravity=-8000,
                central_gravity=0.3,
                spring_length=200,
                spring_strength=0.001,
                damping=0.09,
            )

            added_nodes = set()
            added_edges = set()

            for record in query_result:
                path = record["path"]

                for node in path.nodes:
                    node_id = node.element_id

                    if node_id not in added_nodes:
                        label = node["name"]
                        node_type = list(node.labels)[0]
                        color = self.NODE_COLORS.get(node_type, "#cccccc")

                        size = 25 if node_type == "User" else 20

                        title = f"{node_type}: {label}"

                        net.add_node(
                            node_id,
                            label=label,
                            title=title,
                            color=color,
                            size=size,
                            shape="dot",
                        )
                        added_nodes.add(node_id)

                for rel in path.relationships:
                    edge_id = (
                        rel.start_node.element_id,
                        rel.end_node.element_id,
                        rel.type,
                    )

                    if edge_id not in added_edges:
                        rel_type = rel.type
                        color = self.RELATIONSHIP_COLORS.get(rel_type, "#888888")

                        title = rel_type
                        if show_ratings and rel_type == "RATES":
                            rating = rel.get("rating")
                            rating_type = rel.get("type", "rates")
                            if rating:
                                title = f"{rel_type}: {rating}/5 ({rating_type})"

                        width = 2 if rel_type == "FOLLOWS" else 3

                        net.add_edge(
                            rel.start_node.element_id,
                            rel.end_node.element_id,
                            title=title,
                            color=color,
                            width=width,
                            arrows="to",
                        )
                        added_edges.add(edge_id)

            if len(added_nodes) == 0:
                return None

            return net

        except Exception as e:
            logger.error(f"Failed to create visualization: {e}")
            return None

    def save_html(self, net: Network, filename: str) -> bool:
        try:
            net.save_graph(filename)
            logger.info(f"Visualization saved to {filename}")
            return True
        except Exception as e:
            logger.error(f"Failed to save visualization: {e}")
            return False
