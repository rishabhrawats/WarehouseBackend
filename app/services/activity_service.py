from app.supabase_client import supabase


def add_activity(
    customer_id: str,
    activity_type: str,
    activity_message: str,
    related_entity_type: str | None = None,
    related_entity_id: str | None = None,
    created_by: str = "System",
) -> dict:
    payload = {
        "customer_id": customer_id,
        "activity_type": activity_type,
        "activity_message": activity_message,
        "related_entity_type": related_entity_type,
        "related_entity_id": related_entity_id,
        "created_by": created_by,
    }
    response = supabase.table("customer_activities").insert(payload).execute()
    return response.data[0]


def latest_activity(customer_id: str) -> dict | None:
    response = (
        supabase.table("customer_activities")
        .select("*")
        .eq("customer_id", customer_id)
        .order("created_at", desc=True)
        .limit(1)
        .execute()
    )
    return response.data[0] if response.data else None
