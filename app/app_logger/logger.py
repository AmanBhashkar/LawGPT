import logging
from datetime import datetime, timezone
from app.config.env import env
from pythonjsonlogger import jsonlogger

# --- azure-monitor library imports ---
from azure.monitor.opentelemetry import configure_azure_monitor
from opentelemetry import trace
from opentelemetry.trace import (
    get_tracer_provider,
)
from opencensus.ext.azure.log_exporter import AzureLogHandler

# ---

# connection string for azure monitor
APPLICATIONINSIGHTS_CONNECTION_STRING = env.APPLICATIONINSIGHTS_CONNECTION_STRING

configure_azure_monitor(connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that adds timestamps and uppercases log levels."""

    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in UTC if not present
        if not log_record.get("timestamp"):
            now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
            log_record["timestamp"] = now

        # Ensure log level is uppercase
        if log_record.get("level"):
            log_record["level"] = log_record["level"].upper()
        else:
            log_record["level"] = record.levelname.upper()


# Disable uvicorn access logger (prevents duplicate logging)
uvicorn_access = logging.getLogger("uvicorn.access")
uvicorn_access.disabled = True
uvicorn_access.propagate = False

# Create logger and tracer for document-service
logger = logging.getLogger("ai_service")
tracer = trace.get_tracer("ai_service", tracer_provider=get_tracer_provider())


def get_log_level(log_level):
    """Maps string log level to corresponding logging module level."""
    valid_levels = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
    }
    # Default to ERROR for invalid levels
    return valid_levels.get(log_level.upper(), logging.ERROR)


# Configure logging handler and formatter
logHandler = logging.StreamHandler()
formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
logHandler.setFormatter(formatter)
logger.addHandler(logHandler)
logger.addHandler(AzureLogHandler(connection_string=APPLICATIONINSIGHTS_CONNECTION_STRING))
logger.setLevel(logging.getLevelName(get_log_level(env.LOG_LEVEL)))
