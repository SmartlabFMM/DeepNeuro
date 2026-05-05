"""Background helpers for the radiologist view."""

import logging
from PySide6.QtCore import QThread, Signal

from api_client import api_client
from shared_loaders import DotSpinner

# Configure logger for this module
logger = logging.getLogger(__name__)


class RadiologistRequestsDataLoader(QThread):
    """Load radiologist requests without blocking the UI thread."""

    loaded = Signal(object, str)

    def __init__(self, radiologist_email):
        super().__init__()
        self.radiologist_email = radiologist_email

    def run(self):
        try:
            response, _ = api_client.get_radiologist_requests(self.radiologist_email)
            if response.get('success'):
                self.loaded.emit(response.get('requests', []), "")
            else:
                self.loaded.emit([], response.get('message', 'Unable to load requests right now.'))
        except Exception as e:
            logger.exception(f"Failed to load requests for {self.radiologist_email}")
            self.loaded.emit([], 'Unable to load requests right now.')
