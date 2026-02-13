"""Vulnerability detection patterns for Anchor programs."""

from scanner.patterns.base import VulnerabilityPattern, Finding
from scanner.patterns.init_if_needed import InitIfNeededPattern
from scanner.patterns.duplicate_mutable import DuplicateMutablePattern
from scanner.patterns.realloc_payer import ReallocPayerPattern
from scanner.patterns.type_cosplay import TypeCosplayPattern
from scanner.patterns.close_reinit import CloseReinitPattern
from scanner.patterns.missing_owner import MissingOwnerPattern

ALL_PATTERNS = [
    InitIfNeededPattern,
    DuplicateMutablePattern,
    ReallocPayerPattern,
    TypeCosplayPattern,
    CloseReinitPattern,
    MissingOwnerPattern,
]

__all__ = [
    "VulnerabilityPattern",
    "Finding",
    "ALL_PATTERNS",
    "InitIfNeededPattern",
    "DuplicateMutablePattern",
    "ReallocPayerPattern",
    "TypeCosplayPattern",
    "CloseReinitPattern",
    "MissingOwnerPattern",
]
