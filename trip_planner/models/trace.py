"""
Agent trace model for debugging and analysis.
"""
import uuid
from django.db import models


class AgentTrace(models.Model):
    """
    Stores execution traces from agents for debugging.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    itinerary = models.ForeignKey(
        "trip_planner.Itinerary",
        on_delete=models.CASCADE,
        related_name="traces"
    )
    agent_name = models.CharField(max_length=64, db_index=True)
    step_name = models.CharField(max_length=64)
    input_json = models.JSONField(null=True, blank=True)
    output_json = models.JSONField(null=True, blank=True)
    issues = models.TextField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "agent_traces"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.agent_name} - {self.step_name}"

    @classmethod
    def create_trace(cls, itinerary, agent_name: str, step_name: str,
                     input_data=None, output_data=None, issues=None):
        return cls.objects.create(
            itinerary=itinerary,
            agent_name=agent_name,
            step_name=step_name,
            input_json=input_data,
            output_json=output_data,
            issues=issues
        )
