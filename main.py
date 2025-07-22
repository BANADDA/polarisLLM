#!/usr/bin/env python3
"""
PolarisLLM Runtime Engine - Main Entry Point
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.api.server import run_server

def setup_logging():
    """Setup logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('polaris.log')
        ]
    )

async def main():
    """Main entry point"""
    setup_logging()
    
    logger = logging.getLogger(__name__)
    logger.info("Starting PolarisLLM Runtime Engine")
    
    try:
        await run_server(
            host="0.0.0.0",
            port=7860,
            log_level="info"
        )
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())