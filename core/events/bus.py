"""Corvus Corax EventBus Engine.

Observer pattern event broker supporting typed subscription, publishing, and projections.
"""
from collections import defaultdict


class EventBus:
    """Olay Veri Yolu (Event Bus Broker)."""

    def __init__(self):
        self._subscribers = defaultdict(list)
        self.event_history = []

    def subscribe(self, event_type: str, handler):
        """Belirtilen olay türüne bir abone (handler/projection) ekler."""
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def publish(self, event):
        """Bir olayı yayınlar ve abonelere dağıtır."""
        self.event_history.append(event)
        evt_type = getattr(event, "event_type", "unknown")

        # Özel olay türü aboneleri
        for handler in self._subscribers.get(evt_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"[EventBus Error] Handler failed for {evt_type}: {e}")

        # Tüm olayları dinleyen wildcard '*' aboneleri
        for handler in self._subscribers.get("*", []):
            try:
                handler(event)
            except Exception as e:
                print(f"[EventBus Error] Wildcard handler failed for {evt_type}: {e}")

    def clear(self):
        self._subscribers.clear()
        self.event_history.clear()


# Global Singleton EventBus Instance
global_event_bus = EventBus()
