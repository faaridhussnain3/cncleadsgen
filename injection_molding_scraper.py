from scraper_engine import run_category_engine

if __name__ == "__main__":
    run_category_engine(
        category_name="Injection Molding",
        query_md_file="search_queries/injection_molding_queries.md",
        log_md_file="logs/injection_molding_log.md"
    )
