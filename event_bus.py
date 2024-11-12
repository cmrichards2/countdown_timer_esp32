"""
A simple publish-subscribe (pub/sub) event system implementation.

Pub/sub is a messaging pattern where publishers send messages to topics/events,
without knowing who will receive them. Subscribers can listen for specific events
without knowing who publishes them. This creates loose coupling between components.

Example usage:

    # Subscribe to an event
    def on_pairing_mode():
        print("Device entered pairing mode")
    
    event_bus.subscribe(Events.ENTERING_PAIRING_MODE, on_pairing_mode)

    # Publish an event
    event_bus.publish(Events.ENTERING_PAIRING_MODE)

    # Unsubscribe when done
    event_bus.unsubscribe(Events.ENTERING_PAIRING_MODE, on_pairing_mode)

    # Subscribe with parameters
    def on_wifi_status(connected, ip_address):
        print(f"WiFi connected: {connected}, IP: {ip_address}")
    
    event_bus.subscribe('WIFI_STATUS', on_wifi_status)
    event_bus.publish('WIFI_STATUS', True, '192.168.1.100')
"""

class Events:
    """Constants for all application events"""
    ENTERING_PAIRING_MODE = 'ENTERING_PAIRING_MODE'
    EXITING_PAIRING_MODE = 'EXITING_PAIRING_MODE'
    WIFI_RESET = 'WIFI_RESET'
    TIME_CHANGED = 'TIME_CHANGED'
    # Future events can be added here
    # TIMER_STARTED = 'TIMER_STARTED'
    # TIMER_EXPIRED = 'TIMER_EXPIRED'
    # WIFI_CONNECTED = 'WIFI_CONNECTED'
    # etc.

class EventBus:
    def __init__(self):
        self._subscribers = {}
        
    def subscribe(self, event, callback):
        """Subscribe to an event"""
        if event not in self._subscribers:
            self._subscribers[event] = []
        self._subscribers[event].append(callback)
        
    def publish(self, event, *args, **kwargs):
        """Publish an event to all subscribers"""
        if event in self._subscribers:
            for callback in self._subscribers[event]:
                callback(*args, **kwargs)
                
    def unsubscribe(self, event, callback):
        """Unsubscribe from an event"""
        if event in self._subscribers:
            self._subscribers[event].remove(callback)
            if not self._subscribers[event]:
                del self._subscribers[event]

# Global event bus instance
event_bus = EventBus() 







