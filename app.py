import os

import streamlit as st
from dotenv import load_dotenv

from graph_repository import GraphRepository, Rating
from visualization_service import VisualizationService

load_dotenv()


@st.cache_resource
def get_repository() -> GraphRepository:
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")

    if not all([uri, user, password]):
        st.error("Database credentials not configured. Check your .env file.")
        st.stop()

    try:
        repo = GraphRepository(uri, user, password)
        repo.create_constraints()
        return repo
    except Exception as e:
        st.error(f"Failed to connect to database: {e}")
        st.stop()


def render_sidebar():
    with st.sidebar:
        st.header("About")
        st.markdown("""
        This application provides product recommendations based on:
        - Friend recommendations (social filtering)
        - Collaborative filtering (similar users)

        **How to use:**
        1. Add users and products
        2. Create follow relationships
        3. Add product ratings
        4. View recommendations
        """)

        st.divider()

        st.header("Database Info")
        repo = get_repository()
        user_count = len(repo.get_all_users())
        product_count = len(repo.get_all_products())

        col1, col2 = st.columns(2)
        col1.metric("Users", user_count)
        col2.metric("Products", product_count)


def render_data_management(repo: GraphRepository):
    st.header("Data Management")

    tab1, tab2, tab3 = st.tabs(["Add Data", "Create Relationships", "Delete Data"])

    with tab1:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("Add User")
            new_user = st.text_input("User name", key="new_user")
            if st.button("Add User", type="primary"):
                try:
                    repo.add_user(new_user.strip())
                    st.success(f"User '{new_user}' added successfully")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Failed to add user: {e}")

        with col2:
            st.subheader("Add Product")
            new_product = st.text_input("Product name", key="new_product")
            product_category = st.text_input("Category (optional)", key="product_cat")
            if st.button("Add Product", type="primary"):
                try:
                    repo.add_product(
                        new_product.strip(),
                        product_category.strip() if product_category else None,
                    )
                    st.success(f"Product '{new_product}' added successfully")
                    st.rerun()
                except ValueError as e:
                    st.error(str(e))
                except Exception as e:
                    st.error(f"Failed to add product: {e}")

    with tab2:
        users = repo.get_all_users()
        products = repo.get_all_products()

        if not users:
            st.info("No users available. Add some users first.")
            return

        subtab1, subtab2 = st.tabs(["Follow Relationships", "Product Ratings"])

        with subtab1:
            render_follow_tab(users, repo)

        with subtab2:
            render_rate_tab(users, products, repo)

    with tab3:
        st.subheader("Delete Data")
        st.warning("Deletion is permanent and will remove all associated relationships")

        col1, col2 = st.columns(2)

        with col1:
            users = repo.get_all_users()
            if users:
                user_to_delete = st.selectbox(
                    "Select user to delete",
                    users,
                    key="del_user",
                )
                if st.button("Delete User", type="secondary"):
                    if repo.delete_user(user_to_delete):
                        st.success(f"User '{user_to_delete}' deleted")
                        st.rerun()
                    else:
                        st.error("Failed to delete user")

        with col2:
            products = repo.get_all_products()
            if not products:
                return

            product_to_delete = st.selectbox(
                "Select product to delete",
                products,
                key="del_prod",
            )
            if st.button("Delete Product", type="secondary"):
                if repo.delete_product(product_to_delete):
                    st.success(f"Product '{product_to_delete}' deleted")
                    st.rerun()
                else:
                    st.error("Failed to delete product")


def render_follow_tab(users, repo):
    st.subheader("Create Follow Relationship")

    if len(users) < 2:
        st.info("At least 2 users are needed to create follow relationships")
        return

    col1, col2 = st.columns(2)
    with col1:
        follower = st.selectbox("Follower", users, key="follower")
    with col2:
        followee_options = [u for u in users if u != follower]
        followee = st.selectbox("Follows", followee_options, key="followee")

    if st.button("Create Follow Relationship", type="primary"):
        try:
            repo.create_follow_relationship(follower, followee)
            st.success(f"'{follower}' now follows '{followee}'")
        except Exception as e:
            st.error(f"Error: {e}")


def render_rate_tab(users, products, repo):
    st.subheader("Rate Product")

    if not products:
        st.info("No products available. Add some products first.")
        return

    col1, col2 = st.columns(2)
    with col1:
        rating_user = st.selectbox("User", users, key="rating_user")
    with col2:
        rating_product = st.selectbox("Product", products, key="rating_product")

    col3, col4 = st.columns(2)
    with col3:
        rating = st.slider("Rating", 1, 5, 5, key="rating")
    with col4:
        rating_type = st.selectbox(
            label="Type",
            options=Rating,
            key="rating_type",
        )

    if st.button("Save Rating", type="primary"):
        try:
            repo.rate_product(rating_user, rating_product, rating, rating_type)
            st.success(f"Rating saved: {rating_user} > {rating_product} ({rating}/5)")
        except Exception as e:
            st.error(f"Error: {e}")


def render_analysis(repo: GraphRepository, viz_service: VisualizationService):
    st.header("Analysis & Recommendations")

    users = repo.get_all_users()

    if not users:
        st.info("No users available. Add some users to get started.")
        return

    selected_user = st.selectbox("Select user for analysis", users, key="analysis_user")

    stats = repo.get_user_stats(selected_user)

    st.subheader(f"User Statistics: {selected_user}")
    col1, col2, col3 = st.columns(3)
    col1.metric("Following", stats["following_count"])
    col2.metric("Followers", stats["follower_count"])
    col3.metric("Products Rated", stats["rated_count"])

    st.divider()

    st.subheader("Network Visualization")

    depth = st.slider("Network depth", 1, 3, 2, key="viz_depth")

    try:
        records = repo.get_user_network(selected_user, depth)

        if records:
            net = viz_service.create_user_network(records, selected_user=selected_user)

            if net:
                html_data = net.generate_html()

                st.components.v1.html(html_data, height=650)
            else:
                st.info("No network data to visualize. Add relationships to see the network.")
        else:
            st.info("No network data available.")
    except Exception as e:
        st.error(f"Visualization error: {e}")

    st.divider()

    st.subheader("Recommendations")

    rec_col1, rec_col2 = st.columns(2)

    with rec_col1:
        st.markdown("##### Friend-Based Recommendations")
        st.caption("Products recommended by people you follow")

        min_friends = st.slider(
            "Minimum recommenders",
            min_value=1,
            max_value=10,
            value=1,
            key="min_friends",
        )

        min_rating = st.slider(
            "Minimum rating",
            min_value=1,
            max_value=5,
            value=4,
            key="friend_min_rating",
        )

        friend_recs = repo.recommend_by_friends(selected_user, min_friends, min_rating)

        if friend_recs:
            for rec in friend_recs:
                with st.expander(
                    f"**{rec['product']}** ({rec['recommendation_count']} recommendations)",
                ):
                    st.write("Recommended by:")
                    for friend in rec["recommended_by"]:
                        st.write(f"- {friend}")
        else:
            st.info("No recommendations available. Your friends need to rate products first.")

    with rec_col2:
        st.markdown("##### Collaborative Filtering")
        st.caption("Based on users with similar taste")

        similarity = st.slider(
            "Similarity threshold",
            min_value=0,
            max_value=2,
            value=1,
            key="similarity",
            help="Maximum rating difference for considering users similar",
        )

        collab_min_rating = st.slider(
            "Minimum rating",
            min_value=1,
            max_value=5,
            value=4,
            key="collab_min_rating",
        )

        collab_recs = repo.recommend_collaborative(
            selected_user,
            similarity,
            collab_min_rating,
        )

        if collab_recs:
            for rec in collab_recs:
                with st.expander(
                    f"**{rec['product']}** (Weight: {rec['recommendation_weight']}, Avg: {rec['average_rating']}/5)",
                ):
                    st.write("Similar users who recommend this:")
                    for user in rec["recommended_by_similar"]:
                        st.write(f"- {user}")
        else:
            st.info(
                "Not enough data for collaborative filtering. Rate more products and follow more users.",
            )


def main():
    st.set_page_config(
        page_title="Neo4j Product Recommender",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.title("Neo4j Product Recommender")
    st.markdown("A graph-based recommendation system using Neo4j")

    render_sidebar()

    repo = get_repository()
    viz_service = VisualizationService(height="600px")

    tab1, tab2 = st.tabs(["Analysis & Recommendations", "Data Management"])

    with tab1:
        render_analysis(repo, viz_service)

    with tab2:
        render_data_management(repo)


if __name__ == "__main__":
    main()
