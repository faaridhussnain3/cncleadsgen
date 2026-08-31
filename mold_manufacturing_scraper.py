from scraper_engine import run_category_engine

if __name__ == "__main__":
    run_category_engine(
        category_name="Mold Manufacturing",
        query_md_file="search_queries/mold_manufacturing_queries.md",
        log_md_file="logs/mold_manufacturing_log.md"
    )
