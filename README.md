Product recommender using Neo4j

### How to use
1. Create a neo4j database
2. Create a .env file with and fill `NEO4J_URI` `NEO4J_USER` and `NEO4J_PASSWORD` values
   - If running for the first time run the `seed_database.py` script
3. Run `streamlit run app.py`

I personally used `Neo4j Aura`

visualization is done with `streamlit` and `pyvis`