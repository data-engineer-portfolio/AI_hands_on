"""
RBAC Access Matrix
==================
Single source of truth for which document collections each role can access.

This mapping is used in TWO places:
1. The /collections/{role} endpoint (tells the frontend what the user CAN see)
2. The Qdrant retrieval filter builder (ENFORCES what the user CAN retrieve)

IMPORTANT: Every chunk in Qdrant carries an `access_roles` metadata field
(a list of roles allowed to see that chunk). The retrieval filter checks
that the requesting role is present in `access_roles` -- this is the actual
enforcement point. ACCESS_MATRIX below is mainly for UI display and for
building demo data; the real gate is the per-chunk `access_roles` field
matched against the user's role at query time.
"""

from typing import Dict, List

# Valid roles in the system
VALID_ROLES = ["doctor", "nurse", "billing_executive", "technician", "admin"]

# Valid document collections
VALID_COLLECTIONS = ["general", "clinical", "nursing", "billing", "equipment"]

# Role -> list of collections that role can query
ACCESS_MATRIX: Dict[str, List[str]] = {
    "doctor": ["clinical", "nursing", "general"],
    "nurse": ["nursing", "general"],
    "billing_executive": ["billing", "general"],
    "technician": ["equipment", "general"],
    "admin": ["general", "clinical", "nursing", "billing", "equipment"],
}

# Roles permitted to use SQL RAG (analytical questions over mediassist.db)
SQL_RAG_ALLOWED_ROLES = ["billing_executive", "admin"]


def get_allowed_collections(role: str) -> List[str]:
    """Return the list of collections a given role can access.

    Raises ValueError if the role is not recognized.
    """
    if role not in ACCESS_MATRIX:
        raise ValueError(f"Unknown role: {role}")
    return ACCESS_MATRIX[role]


def can_use_sql_rag(role: str) -> bool:
    """Return True if the role is permitted to run SQL RAG queries."""
    return role in SQL_RAG_ALLOWED_ROLES


def build_qdrant_role_filter(role: str):
    """Build a Qdrant Filter object that restricts results to chunks whose
    `access_roles` field contains this role.

    This is the actual RBAC enforcement at the retrieval layer: it must be
    passed into every Qdrant search/query call so restricted chunks are
    never returned, regardless of similarity score.
    """
    from qdrant_client import models

    if role not in VALID_ROLES:
        raise ValueError(f"Unknown role: {role}")

    return models.Filter(
        must=[
            models.FieldCondition(
                key="access_roles",
                match=models.MatchAny(any=[role]),
            )
        ]
    )
