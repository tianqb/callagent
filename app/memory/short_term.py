"""
Short-term memory implementation for the CallAgent project.
Stores temporary data in memory with optional time-to-live (TTL).
"""

import time
import threading
import json


class ShortTermMemory:
    """
    Short-term memory implementation that stores data in memory with optional TTL.
    """

    def __init__(self, cleanup_interval=300):
        """
        Initialize the short-term memory.

        Args:
            cleanup_interval (int, optional): Interval in seconds for cleaning up expired memories.
        """
        self.memory = {}
        self.cleanup_interval = cleanup_interval
        self.lock = threading.RLock()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()

    def add(self, key, value, ttl=None):
        """
        Add a value to the short-term memory.

        Args:
            key (str): Key to store the value under.
            value (any): Value to store.
            ttl (int, optional): Time-to-live in seconds. If None, the value never expires.

        Returns:
            bool: True if the value was added successfully.
        """
        with self.lock:
            self.memory[key] = {
                'value': value,
                'timestamp': time.time(),
                'ttl': ttl
            }
        return True

    def get(self, key):
        """
        Get a value from the short-term memory.

        Args:
            key (str): Key to retrieve the value for.

        Returns:
            any: The stored value, or None if the key doesn't exist or has expired.
        """
        with self.lock:
            if key in self.memory:
                data = self.memory[key]
                # Check if the value has expired
                if data['ttl'] is None or time.time() - data['timestamp'] < data['ttl']:
                    return data['value']
                else:
                    # Remove expired value
                    del self.memory[key]
        return None

    def update(self, key, value, reset_ttl=True):
        """
        Update a value in the short-term memory.

        Args:
            key (str): Key to update.
            value (any): New value.
            reset_ttl (bool, optional): Whether to reset the TTL.

        Returns:
            bool: True if the value was updated successfully, False if the key doesn't exist.
        """
        with self.lock:
            if key in self.memory:
                data = self.memory[key]
                data['value'] = value
                if reset_ttl:
                    data['timestamp'] = time.time()
                return True
        return False

    def delete(self, key):
        """
        Delete a value from the short-term memory.

        Args:
            key (str): Key to delete.

        Returns:
            bool: True if the key was deleted, False if it didn't exist.
        """
        with self.lock:
            if key in self.memory:
                del self.memory[key]
                return True
        return False

    def clear(self):
        """
        Clear all values from the short-term memory.
        """
        with self.lock:
            self.memory.clear()

    def clear_expired(self):
        """
        Clear all expired values from the short-term memory.

        Returns:
            int: Number of expired values cleared.
        """
        count = 0
        current_time = time.time()
        with self.lock:
            keys_to_remove = []
            for key, data in self.memory.items():
                if data['ttl'] is not None and current_time - data['timestamp'] > data['ttl']:
                    keys_to_remove.append(key)
            for key in keys_to_remove:
                del self.memory[key]
                count += 1
        return count

    def _cleanup_loop(self):
        """
        Background thread that periodically cleans up expired values.
        """
        while True:
            time.sleep(self.cleanup_interval)
            self.clear_expired()

    def get_all(self):
        """
        Get all non-expired values from the short-term memory.

        Returns:
            dict: Dictionary of all non-expired values.
        """
        result = {}
        current_time = time.time()
        with self.lock:
            for key, data in self.memory.items():
                if data['ttl'] is None or current_time - data['timestamp'] < data['ttl']:
                    result[key] = data['value']
        return result

    def to_json(self):
        """
        Convert the short-term memory to a JSON string.

        Returns:
            str: JSON representation of the short-term memory.
        """
        return json.dumps(self.get_all())

    def __len__(self):
        """
        Get the number of items in the short-term memory.

        Returns:
            int: Number of items.
        """
        return len(self.get_all())

    def __contains__(self, key):
        """
        Check if a key exists in the short-term memory.

        Args:
            key (str): Key to check.

        Returns:
            bool: True if the key exists and hasn't expired.
        """
        return self.get(key) is not None
