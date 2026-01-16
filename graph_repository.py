import logging
from typing import Any, Literal

from neo4j import GraphDatabase
from neo4j.exceptions import Neo4jError
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
load_dotenv()


class GraphRepository:
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

    def create_constraints(self) -> None:
        """Create database constraints for data integrity."""
        constraints = [
            "CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE",
            "CREATE CONSTRAINT product_name IF NOT EXISTS FOR (p:Product) REQUIRE p.name IS UNIQUE",
        ]

        for constraint in constraints:
            try:
                self._execute_query(constraint)
                logger.info(f"Constraint created: {constraint}")
            except Neo4jError as e:
                logger.warning(f"Constraint already exists or failed: {e}")

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

    def add_user(self, name: str) -> bool:
        if not name or not name.strip():
            raise ValueError("User name cannot be empty")

        query = "MERGE (u:User {name: $name}) RETURN u"
        try:
            self._execute_query(query, {"name": name.strip()})
            logger.info(f"User '{name}' added/verified")
            return True
        except Neo4jError as e:
            logger.error(f"Failed to add user '{name}': {e}")
            return False

    def delete_user(self, user_name: str) -> bool:
        query = """
        MATCH (u:User {name: $name})
        DETACH DELETE u
        """
        try:
            self._execute_query(query, {"name": user_name})
            logger.info(f"User '{user_name}' deleted")
            return True
        except Neo4jError as e:
            logger.error(f"Failed to delete user '{user_name}': {e}")
            return False

    def add_product(self, name: str, category: str | None = None) -> bool:
        if not name or not name.strip():
            raise ValueError("Product name cannot be empty")

        query = """
                MERGE (p:Product {name: $name})
                SET p.category = $category
                RETURN p
                """
        try:
            self._execute_query(query, {"name": name.strip(), "category": category})
            logger.info(f"Product '{name}' added/verified")
            return True
        except Neo4jError as e:
            logger.error(f"Failed to add product '{name}': {e}")
            return False

    def delete_product(self, product_name: str) -> bool:
        query = """
        MATCH (p:Product {name: $name})
        DETACH DELETE p
        """
        try:
            self._execute_query(query, {"name": product_name})
            logger.info(f"Product '{product_name}' deleted")
            return True
        except Neo4jError as e:
            logger.error(f"Failed to delete product '{product_name}': {e}")
            return False

    def create_follow_relationship(self, follower: str, followee: str) -> bool:
        if follower == followee:
            raise ValueError("A user cannot follow themselves")

        query = """
                MATCH (a:User {name: $follower}), (b:User {name: $followee})
                MERGE (a)-[r:FOLLOWS]->(b)
                RETURN r
                """

        try:
            result = self._execute_query(
                query, {"follower": follower, "followee": followee}
            )
            if result:
                logger.info(f"'{follower}' now follows '{followee}'")
                return True
            else:
                logger.warning(f"Users not found: '{follower}' or '{followee}'")
                return False
        except Neo4jError as e:
            logger.error(f"Failed to create follow relationship: {e}")
            return False

    def rate_product(
        self,
        user: str,
        product: str,
        rating: int,
        rating_type: Literal["recommends", "discourages", "rates"] = "rates",
    ) -> bool:
        query = """
        MATCH (u:User {name: $user}), (p:Product {name: $product})
        MERGE (u)-[r:RATES]->(p)
        SET r.rating = $rating, r.type = $type
        """
        try:
            result = self._execute_query(
                query,
                {
                    "user": user,
                    "product": product,
                    "rating": rating,
                    "type": rating_type,
                },
            )
            if result:
                logger.info(f"'{user}' rated '{product}': {rating} ({rating_type})")
                return True
            else:
                logger.warning(f"User or product not found: '{user}', '{product}'")
                return False
        except Neo4jError as e:
            logger.error(f"Failed to save rating: {e}")
            return False

    def get_all_users(self) -> list[str]:
        query = "MATCH (u:User) RETURN u.name as name ORDER BY name"
        try:
            results = self._execute_query(query)
            return [r["name"] for r in results]
        except Neo4jError as e:
            logger.error(f"Failed to retrieve users: {e}")
            return []

    def get_all_products(self) -> list[str]:
        query = "MATCH (p:Product) RETURN p.name as name ORDER BY name"
        try:
            results = self._execute_query(query)
            return [r["name"] for r in results]
        except Neo4jError as e:
            logger.error(f"Failed to retrieve products: {e}")
            return []

    def recommend_by_friends(
        self, user_name: str, min_friends: int = 1, min_rating: int = 4
    ) -> list[dict[str, Any]]:
        query = """
           MATCH (u:User {name: $name})-[:FOLLOWS]->(friend)-[r:RATES]->(p:Product)
           WHERE r.rating >= $min_rating AND NOT (u)-[:RATES]->(p)
           WITH p, collect(DISTINCT friend.name) as recommenders, count(DISTINCT friend) as friend_count
           WHERE friend_count >= $min_friends
           RETURN 
               p.name as product,
               friend_count as recommendation_count,
               recommenders as recommended_by
           ORDER BY friend_count DESC, p.name
           """
        try:
            return self._execute_query(
                query,
                {
                    "name": user_name,
                    "min_friends": min_friends,
                    "min_rating": min_rating,
                },
            )
        except Neo4jError as e:
            logger.error(f"Failed to get friend recommendations: {e}")
            return []

    def recommend_collaborative(
        self, user_name: str, similarity_threshold: int = 1, min_rating: int = 4
    ) -> list[dict[str, Any]]:
        """
        Get collaborative filtering recommendations.

        Args:
            user_name: Name of the user
            similarity_threshold: Maximum rating difference for similarity
            min_rating: Minimum rating for recommendations

        Returns:
            List of recommended products with recommendation weight
        """
        query = """
        MATCH (u:User {name: $name})-[r1:RATES]->(p:Product)<-[r2:RATES]-(similar:User)
        WHERE abs(r1.rating - r2.rating) <= $threshold
        WITH similar, u, count(*) as shared_products
        WHERE shared_products >= 2
        MATCH (similar)-[r3:RATES]->(rec:Product)
        WHERE NOT (u)-[:RATES]->(rec) AND r3.rating >= $min_rating
        WITH rec, collect(DISTINCT similar.name) as similar_users, 
             count(DISTINCT similar) as recommendation_weight,
             avg(r3.rating) as avg_rating
        RETURN 
            rec.name as product,
            recommendation_weight,
            round(avg_rating * 100) / 100 as average_rating,
            similar_users as recommended_by_similar
        ORDER BY recommendation_weight DESC, avg_rating DESC
        """
        try:
            return self._execute_query(
                query,
                {
                    "name": user_name,
                    "threshold": similarity_threshold,
                    "min_rating": min_rating,
                },
            )
        except Neo4jError as e:
            logger.error(f"Failed to get collaborative recommendations: {e}")
            return []

    def get_user_network(self, user_name: str, depth: int = 2) -> Any:
        if not 1 <= depth <= 3:
            raise ValueError("Depth must be between 1 and 3")

        query = f"""
        MATCH path = (u:User {{name: $name}})-[*1..{depth}]-(node)
        RETURN path
        LIMIT 200
        """
        try:
            with self.driver.session() as session:
                return session.run(query, name=user_name)
        except Neo4jError as e:
            logger.error(f"Failed to get user network: {e}")
            return None

    def get_user_stats(self, user_name: str) -> dict[str, int]:
        query = """
        MATCH (u:User {name: $name})
        OPTIONAL MATCH (u)-[:FOLLOWS]->(following)
        OPTIONAL MATCH (u)<-[:FOLLOWS]-(follower)
        OPTIONAL MATCH (u)-[:RATES]->(rated)
        RETURN 
            count(DISTINCT following) as following_count,
            count(DISTINCT follower) as follower_count,
            count(DISTINCT rated) as rated_count
        """
        try:
            result = self._execute_query(query, {"name": user_name})
            if result:
                return result[0]
            return {"following_count": 0, "follower_count": 0, "rated_count": 0}
        except Neo4jError as e:
            logger.error(f"Failed to get user stats: {e}")
            return {"following_count": 0, "follower_count": 0, "rated_count": 0}
