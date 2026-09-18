from src.database import Base
from src import models


def test_tables_exist():
    table_names = {table.name for table in Base.metadata.sorted_tables}

    assert "users" in table_names
    assert "tickets" in table_names
    assert "decisions" in table_names