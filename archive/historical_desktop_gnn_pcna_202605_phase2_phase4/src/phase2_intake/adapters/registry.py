"""Adapter registry for governed dataset intake."""

from __future__ import annotations

from phase2_intake.adapters.alphafold import AlphaFoldAdapter
from phase2_intake.adapters.asd import AsdAdapter
from phase2_intake.adapters.base import SourceAdapter
from phase2_intake.adapters.baseline_tools import BaselineToolsAdapter
from phase2_intake.adapters.biolip import BioLipAdapter
from phase2_intake.adapters.biogrid_string import BioGridStringAdapter
from phase2_intake.adapters.cryptobench import CryptoBenchAdapter
from phase2_intake.adapters.pdbbind import PdbBindAdapter
from phase2_intake.adapters.pocketminer import PocketMinerAdapter
from phase2_intake.adapters.pubmed import PubMedAdapter
from phase2_intake.adapters.rcsb_pdb import RcsbGenericAdapter, RcsbPdbAdapter
from phase2_intake.adapters.scpdb import ScPdbAdapter


ADAPTERS: dict[str, type[SourceAdapter]] = {
    "cryptobench": CryptoBenchAdapter,
    "rcsb_pdb": RcsbGenericAdapter,
    "pcna_structures": RcsbPdbAdapter,
    "biolip": BioLipAdapter,
    "scpdb": ScPdbAdapter,
    "pdbbind": PdbBindAdapter,
    "asd": AsdAdapter,
    "pocketminer": PocketMinerAdapter,
    "baseline_tools": BaselineToolsAdapter,
    "alphafold": AlphaFoldAdapter,
    "biogrid": BioGridStringAdapter,
    "string": BioGridStringAdapter,
    "literature_metadata": PubMedAdapter,
    "pubmed": PubMedAdapter,
}

ALL_SAFE_SOURCES = [
    "cryptobench",
    "pcna_structures",
    "biolip",
    "scpdb",
    "pdbbind",
    "asd",
    "pocketminer",
    "baseline_tools",
    "alphafold",
    "biogrid",
    "literature_metadata",
]


def get_adapter(source_name: str) -> SourceAdapter:
    try:
        adapter_class = ADAPTERS[source_name]
    except KeyError as exc:
        raise ValueError(f"Unknown source: {source_name}") from exc
    return adapter_class()

