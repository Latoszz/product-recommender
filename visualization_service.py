import logging

from pyvis.network import Network

logger = logging.getLogger(__name__)


class VisualizationService:
    NODE_COLORS = {"User": "#00ff41", "Product": "#ff0055"}

    RELATIONSHIP_COLORS = {"FOLLOWS": "#4285f4", "RATES": "#fbbc04"}

    def __init__(self, height: str = "600px", width: str = "100%"):
        self.height = height
        self.width = width

    def create_user_network(self, query_result, selected_user: str, show_ratings: bool = True) -> Network | None:
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
                central_gravity=0.5,
                spring_length=100,
                spring_strength=0.01,
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
                        if label == selected_user:
                            size *= 1.2
                            color = "#ffffff"

                        net.add_node(
                            node_id,
                            label=label,
                            title=title,
                            color=color,
                            size=size,
                            shape="dot",
                        )
                        added_nodes.add(node_id)

                for relation in path.relationships:
                    edge_id = (
                        relation.start_node.element_id,
                        relation.end_node.element_id,
                        relation.type,
                    )

                    if edge_id not in added_edges:
                        relation_type = relation.type
                        color = self.RELATIONSHIP_COLORS.get(relation_type, "#888888")

                        title = relation_type
                        if show_ratings and relation_type == "RATES":
                            rating = relation.get("rating")
                            rating_type = relation.get("type", "rates")
                            if rating:
                                title = f"{relation_type}: {rating}/5 ({rating_type})"

                        width = 2 if relation_type == "FOLLOWS" else 3

                        net.add_edge(
                            relation.start_node.element_id,
                            relation.end_node.element_id,
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
