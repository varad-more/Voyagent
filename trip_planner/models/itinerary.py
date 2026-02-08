"""
Itinerary model for storing trip requests and generated results.
"""
import uuid
from django.db import models


class ItineraryStatus(models.TextChoices):
    """Status choices for itinerary generation."""
    PENDING = "pending", "Pending"
    QUEUED = "queued", "Queued"
    PROCESSING = "processing", "Processing"
    COMPLETED = "completed", "Completed"
    FAILED = "failed", "Failed"


class Itinerary(models.Model):
    """
    Represents a trip itinerary request and its generated result.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(
        max_length=20,
        choices=ItineraryStatus.choices,
        default=ItineraryStatus.PENDING,
        db_index=True
    )
    request_json = models.JSONField(help_text="Original trip request")
    result_json = models.JSONField(null=True, blank=True, help_text="Generated itinerary")
    error_message = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        db_table = "itineraries"
        ordering = ["-created_at"]
        verbose_name_plural = "Itineraries"

    def __str__(self):
        dest = self.request_json.get("destination", "Unknown")
        return f"{dest} ({self.status})"

    @property
    def destination(self) -> str:
        return self.request_json.get("destination", "")

    def mark_processing(self):
        self.status = ItineraryStatus.PROCESSING
        self.save(update_fields=["status", "updated_at"])

    def mark_completed(self, result: dict):
        self.status = ItineraryStatus.COMPLETED
        self.result_json = result
        self.save(update_fields=["status", "result_json", "updated_at"])

    def mark_failed(self, error: str):
        self.status = ItineraryStatus.FAILED
        self.error_message = error
        self.save(update_fields=["status", "error_message", "updated_at"])
