"""
LangGraph definition: nodes and edges for the analysis pipeline.
Graph: validate_input -> extract_document -> nlp_analyze_document -> evaluate_document -> recommend_clauses -> END
"""

from langgraph.graph import StateGraph, END

from app.workflows.state import AnalysisState
from app.workflows.extract_node import extract_document
from app.workflows.evaluate_node import evaluate_document
from app.workflows.nlp_node import nlp_analyze_document
from app.workflows.recommend_node import recommend_clauses


def _validate_input(state: AnalysisState) -> AnalysisState:
    """Ensure document_id is present; otherwise add error. Returns state update for merge."""
    errors = list(state.get("errors") or [])
    audit_trace = list(state.get("audit_trace") or [])
    if state.get("document_id") is None:
        errors.append("validate_input: document_id is required")
    audit_trace.append({"node": "validate_input", "status": "ok"})
    return {"errors": errors, "audit_trace": audit_trace}


def build_analysis_graph():
    """Build the analysis workflow graph: validate -> extract -> nlp_analyze -> evaluate -> recommend."""
    graph = StateGraph(AnalysisState)
    graph.add_node("validate_input", _validate_input)
    graph.add_node("extract_document", extract_document)
    graph.add_node("nlp_analyze_document", nlp_analyze_document)
    graph.add_node("evaluate_document", evaluate_document)
    graph.add_node("recommend_clauses", recommend_clauses)
    graph.set_entry_point("validate_input")
    graph.add_edge("validate_input", "extract_document")
    graph.add_edge("extract_document", "nlp_analyze_document")
    graph.add_edge("nlp_analyze_document", "evaluate_document")
    graph.add_edge("evaluate_document", "recommend_clauses")
    graph.add_edge("recommend_clauses", END)
    return graph.compile()
