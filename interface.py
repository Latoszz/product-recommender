import streamlit as st
import tempfile
import os

from graph_repository import GraphApp

st.set_page_config(page_title="Neo4j Recommender", layout="wide")
st.title("Neo4j Product Recommender")

app = GraphApp()

# Layout columns
col1, col2 = st.columns([1, 2])

with col1:
    st.header("Administration Panel")

    # 1. Adding
    with st.expander("Add Data", expanded=True):
        new_user = st.text_input("New User")
        if st.button("Add User"):
            if new_user:
                app.add_user(new_user)
                st.success(f"Added {new_user}")
                st.rerun()

        new_product = st.text_input("New Product")
        if st.button("Add Product"):
            if new_product:
                app.add_product(new_product)
                st.success(f"Added {new_product}")
                st.rerun()

    # 2. Relationships
    with st.expander("Create Relationships", expanded=True):
        users = app.get_users()
        products = app.get_products()

        tab1, tab2 = st.tabs(["Connections", "Product Ratings"])

        with tab1:
            if len(users) >= 2:
                u1 = st.selectbox("Who (Follower)", users, key="u1")
                u2 = st.selectbox("Whom (Followee)", users, key="u2")
                if st.button("Add 'Follow'"):
                    app.follow_user(u1, u2)
                    st.success(f"{u1} follows {u2}")

        with tab2:
            if users and products:
                u_rate = st.selectbox("Who rates", users, key="ur")
                p_rate = st.selectbox("Which product", products, key="pr")
                rating = st.slider("Rating (1-5)", 1, 5, 5)
                # Note: Ensure your backend handles these English strings
                rtype = st.selectbox("Type", ["recommends", "discourages", "rates"])
                if st.button("Save rating"):
                    app.rate_product(u_rate, p_rate, rating, rtype)
                    st.success("Saved!")

with col2:
    st.header("Analysis and Recommendations")

    if users:
        target_user = st.selectbox("Select user for analysis", users)

        # --- VISUALIZATION ---
        st.subheader(f"User network: {target_user}")
        try:
            net = app.visualize_user_graph(target_user)
            # Save to tmp html file to display in Streamlit
            with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as tmp:
                net.save_graph(tmp.name)
                with open(tmp.name, "r", encoding="utf-8") as f:
                    html_data = f.read()
                st.components.v1.html(html_data, height=500)
                os.unlink(tmp.name)
        except Exception:
            st.info("No data for visualization (add relationships).")

        st.divider()
        r_col1, r_col2 = st.columns(2)

        with r_col1:
            st.subheader("Recommended by friends")
            min_f = st.number_input("Min. number of friends", 1, 10, 1)
            recs_social = app.rec_by_friends(target_user, min_f)
            if recs_social:
                st.dataframe(recs_social)
            else:
                st.write("No recommendations of this type.")

        with r_col2:
            st.subheader("Collaborative Filtering")
            st.caption("Based on the taste of similar people")
            recs_collab = app.rec_collaborative(target_user)
            if recs_collab:
                st.dataframe(recs_collab)
            else:
                st.write("Not enough data to calculate similarity.")

app.close()