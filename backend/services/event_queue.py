"""
Event queue for real-time updates via Server-Sent Events (SSE)
"""

import asyncio
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class EventQueue:
    """Simple in-memory event queue for SSE"""

    def __init__(self):
        self.subscribers = []

    async def publish(self, event: Dict[str, Any]):
        """Publish event to all subscribers"""
        logger.info(f"Publishing event: {event.get('type')}")

        # Add to all subscriber queues
        for queue in self.subscribers:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to publish to subscriber: {e}")

    async def subscribe(self) -> Dict[str, Any]:
        """Subscribe to events (returns next event)"""
        queue = asyncio.Queue()
        self.subscribers.append(queue)

        try:
            # Wait for next event with timeout for heartbeat
            event = await asyncio.wait_for(queue.get(), timeout=30.0)
            return event
        except asyncio.TimeoutError:
            # Send heartbeat
            return {"type": "heartbeat", "message": "keep-alive"}
        finally:
            # Note: In production, would need proper cleanup when client disconnects
            pass


# Singleton instance
_event_queue = None


def get_event_queue() -> EventQueue:
    """Get or create event queue instance"""
    global _event_queue
    if _event_queue is None:
        _event_queue = EventQueue()
    return _event_queue
