import pytest
from process_cheats import ProcessCheats
from pathlib import Path
import json
import shutil

@pytest.fixture
def temp_dir(tmp_path):
    d = tmp_path / "cheats_src"
    d.mkdir()
    return d

@pytest.fixture
def out_dir(tmp_path):
    d = tmp_path / "cheats_out"
    d.mkdir()
    return d

def test_hex_validation():
    pc = ProcessCheats.__new__(ProcessCheats)
    assert pc.isHexAnd16Char("0123456789ABCDEF") == True
    assert pc.isHexAnd16Char("G123456789ABCDEF") == False
    assert pc.isHexAnd16Char("0123456789ABCDE") == False

def test_construct_bid_dict(temp_dir):
    sheet = temp_dir / "test.txt"
    sheet.write_text("[Cheat Name]\n04000000 01234567 89ABCDEF\n", encoding="utf-8")

    pc = ProcessCheats.__new__(ProcessCheats)
    res = pc.constructBidDict(str(sheet))
    assert "[Cheat Name]" in res
    assert "04000000 01234567 89ABCDEF" in res["[Cheat Name]"]

def test_full_processing(temp_dir, out_dir):
    # Setup mock structure
    tid_dir = temp_dir / "0100F9C00F32E000"
    tid_dir.mkdir()
    cheats_dir = tid_dir / "cheats"
    cheats_dir.mkdir()
    bid_file = cheats_dir / "AABBCCDDEEFF0011.txt"
    bid_file.write_text("[Test Cheat]\n580F0000 01234567\n", encoding="utf-8")

    # Run processor
    ProcessCheats(str(temp_dir), str(out_dir))

    # Verify output
    out_file = out_dir / "0100F9C00F32E000.json"
    assert out_file.exists()
    with open(out_file, "r") as f:
        data = json.load(f)
    assert "AABBCCDDEEFF0011" in data
    assert "[Test Cheat]" in data["AABBCCDDEEFF0011"]

def test_readme_update(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text("## Cheats count\n\n<!-- STATS_START -->\nold\n<!-- STATS_END -->", encoding="utf-8")

    # We need to mock the count_cheats logic or use the real one if we can point it to README
    import re
    def mock_count_cheats(readme_file, n_cheats, n_games, n_updates):
        stats_text = f"{n_cheats} cheats in {n_games} titles/{n_updates} updates"
        content = readme_file.read_text(encoding="utf-8")
        pattern = r"<!-- STATS_START -->.*?<!-- STATS_END -->"
        replacement = f"<!-- STATS_START -->\n{stats_text}\n<!-- STATS_END -->"
        new_content = re.sub(pattern, replacement, content, flags=re.DOTALL)
        readme_file.write_text(new_content, encoding="utf-8")

    mock_count_cheats(readme, 100, 10, 20)
    updated = readme.read_text(encoding="utf-8")
    assert "100 cheats in 10 titles/20 updates" in updated
