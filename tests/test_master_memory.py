from __future__ import annotations

from agents.common.functions import read_master_memory, update_master_memory, write_master_memory


def test_master_memory_read_write_update(tmp_path) -> None:
    base_path = tmp_path / "agents" / "common"
    base_path.mkdir(parents=True)

    written = write_master_memory("# Master Team Memory\n\n## Agreed Strategy\n\n- stay coordinated\n", base_path)
    assert written.exists()
    assert read_master_memory(base_path) == "# Master Team Memory\n\n## Agreed Strategy\n\n- stay coordinated\n"

    updated = update_master_memory("Next Moves", "- regroup and charge", base_path)
    assert "## Next Moves" in updated
    assert "- regroup and charge" in updated