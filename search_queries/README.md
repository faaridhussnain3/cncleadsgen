# 🔍 Search Queries Database

This folder contains structured search query combinations organized by manufacturing sector across **5 major countries**: 🇨🇳 China, 🇺🇸 USA, 🇬🇧 UK, 🇨🇦 Canada, and 🇦🇺 Australia.

## Files Structure

| File | Sector | Core Focus |
| :--- | :--- | :--- |
| **[cnc_machining_queries.md](file:///Users/mmx/Desktop/cnc%20leadser/search_queries/cnc_machining_queries.md)** | CNC Machining | CNC Milling, Turning, Swiss Machining, 5-Axis |
| **[injection_molding_queries.md](file:///Users/mmx/Desktop/cnc%20leadser/search_queries/injection_molding_queries.md)** | Injection Molding | Thermoplastic Molding, Insert Molding, Overmolding |
| **[mold_manufacturing_queries.md](file:///Users/mmx/Desktop/cnc%20leadser/search_queries/mold_manufacturing_queries.md)** | Mold Manufacturing | Injection Molds, Tool & Die, Stamping Dies |
| **[die_casting_queries.md](file:///Users/mmx/Desktop/cnc%20leadser/search_queries/die_casting_queries.md)** | Die Casting | Aluminum, Zinc & Magnesium Die Casting Foundries |

---

## How Scrapers Use These Files

The Python category scrapers (`cnc_machining_scraper.py`, `injection_molding_scraper.py`, `mold_manufacturing_scraper.py`, `die_casting_scraper.py`) can load queries directly from these markdown files or use the built-in search combination matrix to query Google Maps & Search engines.
