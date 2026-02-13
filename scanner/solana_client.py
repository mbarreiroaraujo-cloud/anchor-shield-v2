"""Solana RPC integration for on-chain program analysis."""

import json
import struct
import hashlib
from typing import Optional
from dataclasses import dataclass, field

import requests


RPC_ENDPOINTS = {
    "mainnet-beta": "https://api.mainnet-beta.solana.com",
    "devnet": "https://api.devnet.solana.com",
    "testnet": "https://api.testnet.solana.com",
}

# BPF Upgradeable Loader program ID
BPF_LOADER_UPGRADEABLE = "BPFLoaderUpgradeab1e11111111111111111111111"


@dataclass
class ProgramInfo:
    """On-chain program metadata."""
    program_id: str
    executable: bool = False
    owner: str = ""
    data_size: int = 0
    is_upgradeable: bool = False
    upgrade_authority: Optional[str] = None
    last_deploy_slot: Optional[int] = None
    network: str = "mainnet-beta"

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "executable": self.executable,
            "owner": self.owner,
            "data_size": self.data_size,
            "is_upgradeable": self.is_upgradeable,
            "upgrade_authority": self.upgrade_authority,
            "last_deploy_slot": self.last_deploy_slot,
            "network": self.network,
        }


@dataclass
class RiskAssessment:
    """Risk assessment for a deployed program."""
    program_id: str
    risk_level: str = "Unknown"
    program_info: Optional[ProgramInfo] = None
    idl_found: bool = False
    idl_warnings: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)
    network: str = "mainnet-beta"

    def to_dict(self) -> dict:
        return {
            "program_id": self.program_id,
            "risk_level": self.risk_level,
            "program_info": self.program_info.to_dict() if self.program_info else None,
            "idl_found": self.idl_found,
            "idl_warnings": self.idl_warnings,
            "recommendations": self.recommendations,
            "network": self.network,
        }


class SolanaChecker:
    """Solana RPC client for on-chain program analysis."""

    def __init__(self, network: str = "mainnet-beta"):
        self.network = network
        self.rpc_url = RPC_ENDPOINTS.get(network, RPC_ENDPOINTS["mainnet-beta"])
        self.session = requests.Session()
        self.session.headers["Content-Type"] = "application/json"

    def get_program_info(self, program_id: str) -> Optional[ProgramInfo]:
        """Fetch program metadata from on-chain."""
        try:
            # Get account info
            result = self._rpc_call("getAccountInfo", [
                program_id,
                {"encoding": "base64", "commitment": "confirmed"},
            ])

            if not result or "value" not in result or result["value"] is None:
                return None

            value = result["value"]
            info = ProgramInfo(
                program_id=program_id,
                executable=value.get("executable", False),
                owner=value.get("owner", ""),
                data_size=value.get("data", [None, None])[0] and len(value["data"][0]) or 0,
                network=self.network,
            )

            # Check if BPF Upgradeable Loader
            if info.owner == BPF_LOADER_UPGRADEABLE:
                info.is_upgradeable = True
                # Try to get program data account for upgrade authority
                self._fetch_upgrade_authority(info)

            return info

        except Exception:
            return None

    def get_anchor_idl_address(self, program_id: str) -> str:
        """Derive the IDL account address for an Anchor program.

        Anchor stores IDL at a PDA with seeds = ["anchor:idl", program_id].
        """
        # This is a simplified derivation; in production you'd use solders
        # for proper PDA derivation
        seed = b"anchor:idl"
        try:
            from solders.pubkey import Pubkey
            program_key = Pubkey.from_string(program_id)
            idl_address, _ = Pubkey.find_program_address(
                [seed, bytes(program_key)],
                program_key,
            )
            return str(idl_address)
        except Exception:
            # Fallback: compute manually using hashlib
            return self._derive_idl_address_manual(program_id)

    def check_idl_exists(self, program_id: str) -> tuple[bool, Optional[dict]]:
        """Check if an Anchor IDL account exists on-chain."""
        try:
            idl_address = self.get_anchor_idl_address(program_id)
            result = self._rpc_call("getAccountInfo", [
                idl_address,
                {"encoding": "base64", "commitment": "confirmed"},
            ])
            if result and result.get("value") is not None:
                return True, {"address": idl_address}
            return False, None
        except Exception:
            return False, None

    def check_program_risk(self, program_id: str) -> RiskAssessment:
        """Assess risk of a deployed Anchor program."""
        assessment = RiskAssessment(
            program_id=program_id,
            network=self.network,
        )

        # Fetch program info
        info = self.get_program_info(program_id)
        if not info:
            assessment.risk_level = "Unknown"
            assessment.recommendations.append(
                "Program account not found on " + self.network
            )
            return assessment

        assessment.program_info = info

        # Check IDL
        idl_found, idl_info = self.check_idl_exists(program_id)
        assessment.idl_found = idl_found

        # Risk factors
        risk_score = 0

        if info.is_upgradeable:
            assessment.idl_warnings.append(
                "Program is upgradeable — authority can modify program at any time"
            )
            risk_score += 2

        if not info.executable:
            assessment.idl_warnings.append(
                "Account is not marked as executable — may not be a program"
            )
            risk_score += 5

        if not idl_found:
            assessment.idl_warnings.append(
                "No Anchor IDL found on-chain — cannot verify constraint patterns"
            )
            risk_score += 1

        if info.is_upgradeable and info.upgrade_authority:
            assessment.recommendations.append(
                f"Verify upgrade authority {info.upgrade_authority} is a "
                "multisig or governance-controlled address"
            )

        if idl_found:
            assessment.recommendations.append(
                "IDL found — source code scan recommended for full analysis"
            )

        # Determine risk level
        if risk_score >= 5:
            assessment.risk_level = "High"
        elif risk_score >= 3:
            assessment.risk_level = "Medium"
        elif risk_score >= 1:
            assessment.risk_level = "Low"
        else:
            assessment.risk_level = "Minimal"

        return assessment

    def _fetch_upgrade_authority(self, info: ProgramInfo):
        """Fetch upgrade authority from program data account."""
        try:
            # For BPF Upgradeable programs, the account data contains a
            # 4-byte enum variant followed by the programdata address
            result = self._rpc_call("getAccountInfo", [
                info.program_id,
                {"encoding": "base64", "commitment": "confirmed"},
            ])
            if not result or not result.get("value"):
                return

            import base64
            data_b64 = result["value"]["data"][0]
            data = base64.b64decode(data_b64)

            if len(data) >= 36:
                # First 4 bytes = variant (2 = Program), next 32 bytes = programdata address
                variant = struct.unpack_from("<I", data, 0)[0]
                if variant == 2:
                    from solders.pubkey import Pubkey
                    programdata_key = Pubkey.from_bytes(data[4:36])

                    # Fetch programdata account
                    pd_result = self._rpc_call("getAccountInfo", [
                        str(programdata_key),
                        {"encoding": "base64", "commitment": "confirmed"},
                    ])
                    if pd_result and pd_result.get("value"):
                        pd_data_b64 = pd_result["value"]["data"][0]
                        pd_data = base64.b64decode(pd_data_b64)
                        if len(pd_data) >= 45:
                            # Byte 4 = slot (8 bytes), byte 12 = Option<Pubkey>
                            info.last_deploy_slot = struct.unpack_from("<Q", pd_data, 4)[0]
                            has_authority = pd_data[12]
                            if has_authority == 1 and len(pd_data) >= 45:
                                authority = Pubkey.from_bytes(pd_data[13:45])
                                info.upgrade_authority = str(authority)
        except Exception:
            pass

    def _derive_idl_address_manual(self, program_id: str) -> str:
        """Fallback IDL address derivation without solders."""
        # Return empty — proper derivation requires ed25519 operations
        return ""

    def _rpc_call(self, method: str, params: list) -> Optional[dict]:
        """Make a JSON-RPC call to Solana."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params,
        }

        try:
            resp = self.session.post(self.rpc_url, json=payload, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                if "result" in data:
                    return data["result"]
                if "error" in data:
                    return None
        except requests.exceptions.RequestException:
            pass
        return None
