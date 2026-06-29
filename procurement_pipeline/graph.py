from typing import assert_never

from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from procurement_pipeline.nodes.rfq_difference import (
    build_rfq_difference_result,
    build_rfq_human_review_request_result,
)
from procurement_pipeline.nodes.rfq_resend import build_rfq_resend_result
from procurement_pipeline.nodes.tco_calculation import calculate_supplier_tco
from procurement_pipeline.nodes.validation_routing import (
    build_human_review_request_result,
    build_ocr_reparse_result,
    build_validation_routing_result,
)
from procurement_pipeline.schemas.company_config import RfqDifferenceRouteAction
from procurement_pipeline.schemas.validation_routing_result import ValidationRouteAction
from procurement_pipeline.state import ProcurementState, ProcurementStateUpdate


def route_validation(state: ProcurementState) -> ProcurementStateUpdate:
    return {
        "routing_result": build_validation_routing_result(
            state["validation_result"],
        ),
        "path_trace": _append_path(state, "route_validation"),
    }


def calculate_tco(state: ProcurementState) -> ProcurementStateUpdate:
    return {
        "tco_result": calculate_supplier_tco(
            state["quote_input"],
            state["company_config"],
        ),
        "path_trace": _append_path(state, "tco_calculation"),
    }


def compare_rfq_difference(state: ProcurementState) -> ProcurementStateUpdate:
    return {
        "rfq_difference_result": build_rfq_difference_result(
            state["quote_input"],
            state["company_config"],
        ),
        "path_trace": _append_path(state, "rfq_difference"),
    }


def request_rfq_resend(state: ProcurementState) -> ProcurementStateUpdate:
    return {
        "rfq_resend_result": build_rfq_resend_result(
            state["rfq_difference_result"],
        ),
        "path_trace": _append_path(state, "rfq_resend"),
    }


def request_human_review(state: ProcurementState) -> ProcurementStateUpdate:
    if "rfq_difference_result" in state:
        return {
            "human_review_result": build_rfq_human_review_request_result(
                state["rfq_difference_result"],
                state["validation_result"].risk_level,
            ),
            "path_trace": _append_path(state, "human_review_request"),
        }

    return {
        "human_review_result": build_human_review_request_result(
            state["validation_result"],
        ),
        "path_trace": _append_path(state, "human_review_request"),
    }


def request_ocr_reparse(state: ProcurementState) -> ProcurementStateUpdate:
    return {
        "ocr_reparse_result": build_ocr_reparse_result(
            state["validation_result"],
        ),
        "path_trace": _append_path(state, "ocr_reparse"),
    }


def select_validation_route_target(state: ProcurementState) -> str:
    return _target_for_route(state["routing_result"].selected_route)


def select_rfq_difference_route_target(state: ProcurementState) -> str:
    return _target_for_rfq_route(state["rfq_difference_result"].selected_route)


def build_graph() -> CompiledStateGraph:
    builder = StateGraph(ProcurementState)
    builder.add_node("route_validation", route_validation)
    builder.add_node("rfq_difference", compare_rfq_difference)
    builder.add_node("tco_calculation", calculate_tco)
    builder.add_node("rfq_resend", request_rfq_resend)
    builder.add_node("human_review_request", request_human_review)
    builder.add_node("ocr_reparse", request_ocr_reparse)

    builder.add_edge(START, "route_validation")
    builder.add_conditional_edges(
        "route_validation",
        select_validation_route_target,
        _target_map(),
    )
    builder.add_conditional_edges(
        "rfq_difference",
        select_rfq_difference_route_target,
        _rfq_target_map(),
    )
    builder.add_edge("tco_calculation", END)
    builder.add_edge("rfq_resend", END)
    builder.add_edge("human_review_request", END)
    builder.add_edge("ocr_reparse", END)
    return builder.compile()


def _target_map() -> dict[str, str]:
    return {
        "rfq_difference": "rfq_difference",
        "human_review_request": "human_review_request",
        "ocr_reparse": "ocr_reparse",
    }


def _rfq_target_map() -> dict[str, str]:
    return {
        "tco_calculation": "tco_calculation",
        "rfq_resend": "rfq_resend",
        "human_review_request": "human_review_request",
    }


def _target_for_route(route_action: ValidationRouteAction) -> str:
    match route_action:
        case "proceed_tco":
            return "rfq_difference"
        case "request_human_review":
            return "human_review_request"
        case "reparse_ocr":
            return "ocr_reparse"
        case unreachable:
            assert_never(unreachable)


def _target_for_rfq_route(route_action: RfqDifferenceRouteAction) -> str:
    match route_action:
        case "proceed_tco":
            return "tco_calculation"
        case "resend_rfq":
            return "rfq_resend"
        case "request_human_review":
            return "human_review_request"
        case unreachable:
            assert_never(unreachable)


def _append_path(state: ProcurementState, node_name: str) -> tuple[str, ...]:
    return (*state.get("path_trace", ()), node_name)


graph = build_graph()
