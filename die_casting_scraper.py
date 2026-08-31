from scraper_engine import run_category_engine

if __name__ == "__main__":
    run_category_engine(
        category_name="Die Casting",
        query_md_file="search_queries/die_casting_queries.md",
        log_md_file="logs/die_casting_log.md"
    )
