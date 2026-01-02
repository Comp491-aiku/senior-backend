"""
Tool Execution Database Model

Handles logging of all tool executions and travel results.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import uuid
import json

from app.db.supabase import get_supabase_admin_client


class ToolExecutionService:
    """
    Service for logging tool executions to Supabase.

    Tracks every tool call with inputs, outputs, and timing.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def log_execution(
        self,
        conversation_id: str,
        tool_name: str,
        input_params: Dict[str, Any],
        output_data: Optional[Dict[str, Any]] = None,
        output_type: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None,
        duration_ms: Optional[int] = None,
        tool_call_id: Optional[str] = None,
        message_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Log a tool execution."""
        execution_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        data = {
            "id": execution_id,
            "conversation_id": conversation_id,
            "message_id": message_id,
            "tool_name": tool_name,
            "tool_call_id": tool_call_id,
            "input_params": json.dumps(input_params) if input_params else "{}",
            "output_data": json.dumps(output_data) if output_data else None,
            "output_type": output_type,
            "success": success,
            "error_message": error_message,
            "duration_ms": duration_ms,
            "created_at": now,
        }

        result = self.client.table("tool_executions").insert(data).execute()

        if result.data:
            return result.data[0]
        return {"id": execution_id, **data}

    async def get_executions(
        self,
        conversation_id: str,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Get tool executions for a conversation."""
        result = (
            self.client.table("tool_executions")
            .select("*")
            .eq("conversation_id", conversation_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        executions = result.data or []

        # Parse JSON fields
        for exe in executions:
            if exe.get("input_params"):
                try:
                    exe["input_params"] = json.loads(exe["input_params"])
                except (json.JSONDecodeError, TypeError):
                    pass
            if exe.get("output_data"):
                try:
                    exe["output_data"] = json.loads(exe["output_data"])
                except (json.JSONDecodeError, TypeError):
                    pass

        return executions


class TravelResultService:
    """
    Service for storing structured travel results.

    Stores flights, hotels, etc. as structured data for UI rendering.
    """

    def __init__(self):
        self._client = None

    @property
    def client(self):
        if self._client is None:
            self._client = get_supabase_admin_client()
        return self._client

    async def save_result(
        self,
        conversation_id: str,
        result_type: str,
        data: Dict[str, Any],
        tool_execution_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Save a travel result."""
        result_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        record = {
            "id": result_id,
            "conversation_id": conversation_id,
            "tool_execution_id": tool_execution_id,
            "result_type": result_type,
            "data": json.dumps(data),
            "selected": False,
            "created_at": now,
        }

        result = self.client.table("travel_results").insert(record).execute()

        if result.data:
            return result.data[0]
        return {"id": result_id, **record}

    async def save_results_batch(
        self,
        conversation_id: str,
        result_type: str,
        items: List[Dict[str, Any]],
        tool_execution_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Save multiple travel results at once."""
        now = datetime.utcnow().isoformat()
        records = []

        for item in items:
            records.append({
                "id": str(uuid.uuid4()),
                "conversation_id": conversation_id,
                "tool_execution_id": tool_execution_id,
                "result_type": result_type,
                "data": json.dumps(item),
                "selected": False,
                "created_at": now,
            })

        if not records:
            return []

        result = self.client.table("travel_results").insert(records).execute()

        return result.data or records

    async def get_results(
        self,
        conversation_id: str,
        result_type: Optional[str] = None,
        selected_only: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get travel results for a conversation."""
        query = (
            self.client.table("travel_results")
            .select("*")
            .eq("conversation_id", conversation_id)
        )

        if result_type:
            query = query.eq("result_type", result_type)

        if selected_only:
            query = query.eq("selected", True)

        result = query.order("created_at", desc=False).execute()

        results = result.data or []

        # Parse data JSON
        for r in results:
            if r.get("data"):
                try:
                    r["data"] = json.loads(r["data"])
                except (json.JSONDecodeError, TypeError):
                    pass

        return results

    async def select_result(
        self,
        result_id: str,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Mark a travel result as selected."""
        result = (
            self.client.table("travel_results")
            .update({"selected": True})
            .eq("id", result_id)
            .eq("conversation_id", conversation_id)
            .execute()
        )

        return result.data[0] if result.data else None

    async def deselect_result(
        self,
        result_id: str,
        conversation_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Unmark a travel result as selected."""
        result = (
            self.client.table("travel_results")
            .update({"selected": False})
            .eq("id", result_id)
            .eq("conversation_id", conversation_id)
            .execute()
        )

        return result.data[0] if result.data else None


# Singleton instances
_tool_execution_service: Optional[ToolExecutionService] = None
_travel_result_service: Optional[TravelResultService] = None


def get_tool_execution_service() -> ToolExecutionService:
    """Get the tool execution service singleton."""
    global _tool_execution_service
    if _tool_execution_service is None:
        _tool_execution_service = ToolExecutionService()
    return _tool_execution_service


def get_travel_result_service() -> TravelResultService:
    """Get the travel result service singleton."""
    global _travel_result_service
    if _travel_result_service is None:
        _travel_result_service = TravelResultService()
    return _travel_result_service
