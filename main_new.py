from app_new import app, create_db_and_tables
import routes_new  # noqa: F401

# Create tables on startup
create_db_and_tables()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)