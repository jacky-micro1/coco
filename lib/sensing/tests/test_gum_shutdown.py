import asyncio
from pathlib import Path

from sensing.gum import GUM, Observation


def test_gum_shutdown_checkpoints_and_closes_wal(tmp_path):
    async def run():
        gum = GUM("test", data_directory=str(tmp_path))
        await gum.connect_db()
        try:
            async with gum._session() as session:
                session.add(
                    Observation(
                        observer_name="test",
                        content="saved before shutdown",
                        content_type="input_text",
                    )
                )
            wal = Path(tmp_path / "actions.db-wal")
            assert wal.exists() and wal.stat().st_size > 0
            await gum.__aexit__(None, None, None)
            assert not wal.exists() or wal.stat().st_size == 0
        finally:
            if gum.engine is not None:
                await gum.engine.dispose()

    asyncio.run(run())
