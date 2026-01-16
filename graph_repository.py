import logging
from typing import Any

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from pyvis.network import Network
from dotenv import load_dotenv
from os import getenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class GraphApp:
    def __init__(self, uri: str, user: str, password: str):
        self.uri = uri
        self.user = user
        self.password = password
        self._connect()

    def _connect(self) -> None:
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            self.driver.verify_connectivity()
            logger.info("Successfully connected to Neo4j database")
        except Neo4jError as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise

    def close(self) -> None:
        if self.driver:
            self.driver.close()
            logger.info("Database connection closed")

    def _execute_query(
        self, query: str, parameters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Neo4jError as e:
            logger.error(f"Query execution failed: {e}")
            raise

    def add_user(self, name):
        
        query = "MERGE (u:User {name: $name})"
        self._execute_query(query, {"name": name})

    def add_product(self, name):
        query = "MERGE (p:Product {name: $name})"
        self._execute_query(query, {"name": name})

    def follow_user(self, user1, user2):
        query = """
        MATCH (a:User {name: $u1}), (b:User {name: $u2})
        MERGE (a)-[:FOLLOWS]->(b)
        """
        self._execute_query(query, {"u1": user1, "u2": user2})

    def rate_product(self, user, product, rating, label):
        query = """
        MATCH (u:User {name: $user}), (p:Product {name: $product})
        MERGE (u)-[r:RATES]->(p)
        SET r.rating = $rating, r.type = $label
        """
        self._execute_query(
            query, {"user": user, "product": product, "rating": rating, "label": label}
        )

    def get_users(self):
        return [
            x["name"] for x in self._execute_query("MATCH (u:User) RETURN u.name as name")
        ]

    def get_products(self):
        return [
            x["name"] for x in self._execute_query("MATCH (p:Product) RETURN p.name as name")
        ]

    def rec_by_friends(self, user_name, min_friends=1):
        query = """
        MATCH (u:User {name: $name})-[:FOLLOWS]->(friend)-[r:RATES]->(p:Product)
        WHERE r.rating >= 4  // Zakładamy, że polecenie to ocena >= 4
        WITH p, count(friend) as friend_count
        WHERE friend_count >= $min_friends
        RETURN p.name as Produkt, friend_count as Liczba_Polecen
        ORDER BY friend_count DESC
        """
        return self._execute_query(query, {"name": user_name, "min_friends": min_friends})

    def rec_collaborative(self, user_name):
        query = """
        MATCH (u:User {name: $name})-[r1:RATES]->(p:Product)<-[r2:RATES]-(other:User)
        WHERE abs(r1.rating - r2.rating) <= 1  // Znajdź użytkowników o podobnym guście (podobne oceny tych samych produktów)
        WITH other, u
        MATCH (other)-[r3:RATES]->(rec_p:Product)
        WHERE NOT (u)-[:RATES]->(rec_p) AND r3.rating >= 4 // Znajdź co oni lubią, a czego ja nie ocenilem
        RETURN rec_p.name as Produkt, count(*) as Waga_Rekomendacji
        ORDER BY Waga_Rekomendacji DESC
        """
        return self._execute_query(query, {"name": user_name})

    def visualize_user_graph(self, user_name):
        query = """
        MATCH path = (u:User {name: $name})-[*1..2]-(node)
        RETURN path
        """
        results = self.driver.session().run(query, name=user_name)

        net = Network(
            height="500px", width="100%", bgcolor="#222222", font_color="white"
        )

        for record in results:
            for node in record["path"].nodes:
                color = "#00ff41" if "User" in node.labels else "#ff0055"
                label = node["name"]
                net.add_node(node.element_id, label=label, title=label, color=color)

            for rel in record["path"].relationships:
                net.add_edge(
                    rel.start_node.element_id, rel.end_node.element_id, title=rel.type
                )

        return net
