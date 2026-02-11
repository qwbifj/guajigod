import asyncio
import sys
import os

# Ensure src is in path if running from root
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.engine import GameEngine

async def main():
    engine = GameEngine()
    await engine.run()

if __name__ == "__main__":
    asyncio.run(main())
