from scraper_engine import run_category_engine

if __name__ == "__main__":
    run_category_engine(
        category_name="CNC Machining",
        query_md_file="search_queries/cnc_machining_queries.md",
        log_md_file="logs/cnc_machining_log.md"
    )
