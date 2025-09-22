"""
Message processor worker module
"""
from .message_processor import MessageProcessor, message_processor, message_processor_lifespan

__all__ = ["MessageProcessor", "message_processor", "message_processor_lifespan"]