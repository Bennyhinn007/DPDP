"""
Blockchain Anchoring Service.

Connects to Ganache (local Ethereum) and stores SHA-256 hashes of healthcare
records on-chain as transaction data. No smart contracts in MVP — uses raw
transactions with hash embedded in the data field.

On-chain storage:
- record_id (UUID)
- SHA-256 hash of the encrypted record
- timestamp

No healthcare data is ever stored on-chain.
"""

import hashlib
import json
from typing import Optional

from web3 import Web3
from web3.exceptions import TransactionNotFound

from app.utils.helpers import generate_uuid, utc_now


class BlockchainService:
    """Manages blockchain hash anchoring on Ganache."""

    def __init__(self, db, w3: Web3):
        self.db = db
        self.anchors = db["blockchain_anchors"]
        self.w3 = w3

        # Use first Ganache account as sender
        self._account = None
        if w3:
            try:
                if w3.is_connected():
                    self._account = w3.eth.accounts[0]
            except Exception:
                pass

    @property
    def is_connected(self) -> bool:
        """Check if Web3 is connected to Ganache."""
        try:
            return self.w3 is not None and self.w3.is_connected()
        except Exception:
            return False

    # ─────────────────────────────────────────────────────────────────
    # HASH COMPUTATION
    # ─────────────────────────────────────────────────────────────────

    @staticmethod
    def compute_record_hash(record: dict) -> str:
        """
        Compute SHA-256 hash of a record for blockchain anchoring.

        Uses the encrypted field values (as stored in MongoDB) to create
        the hash — this ensures the anchor verifies against the stored state.

        Excludes volatile metadata fields that change independently.
        """
        exclude = {
            "verification_hash", "blockchain_tx_ref", "blockchain_anchor_id",
        }
        hashable = {k: v for k, v in record.items() if k not in exclude}
        canonical = json.dumps(hashable, sort_keys=True, separators=(",", ":"), default=str)
        return hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    # ─────────────────────────────────────────────────────────────────
    # ANCHOR CREATION
    # ─────────────────────────────────────────────────────────────────

    def anchor_record(
        self,
        resource_type: str,
        resource_id: str,
        data_hash: str,
        patient_id: str = None,
        anchor_type: str = "record_verification",
    ) -> dict:
        """
        Anchor a hash on the blockchain.

        Sends a transaction to Ganache with the hash as data payload.
        Stores the transaction reference in MongoDB blockchain_anchors collection.

        Args:
            resource_type: Collection name (e.g., "healthcare_records")
            resource_id: UUID of the source document
            data_hash: SHA-256 hex hash to anchor
            patient_id: UUID of related patient (optional)
            anchor_type: Type of anchor (record_verification, consent, audit)

        Returns:
            blockchain_anchor document with tx_hash and block_number
        """
        anchor_id = generate_uuid()
        now = utc_now()

        tx_hash = None
        block_number = None
        tx_status = "failed"

        if self.is_connected:
            try:
                tx_hash, block_number = self._send_hash_transaction(
                    resource_id, data_hash
                )
                tx_status = "success"
            except Exception as e:
                tx_status = f"failed: {str(e)[:100]}"

        anchor_doc = {
            "_id": anchor_id,
            "anchor_type": anchor_type,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "patient_id": patient_id,
            "data_hash": data_hash,
            "hash_algorithm": "sha256",
            "transaction_hash": tx_hash,
            "block_number": block_number,
            "transaction_status": tx_status,
            "created_at": now,
        }

        self.anchors.insert_one(anchor_doc)
        return anchor_doc

    def _send_hash_transaction(self, resource_id: str, data_hash: str) -> tuple:
        """
        Send a transaction to Ganache containing the hash.

        The hash is encoded as hex in the transaction data field.
        No smart contract — just raw transaction with data payload.

        Returns:
            Tuple of (tx_hash_hex, block_number)
        """
        # Encode: resource_id + "|" + data_hash as hex bytes
        payload = f"{resource_id}|{data_hash}".encode("utf-8")

        tx = {
            "from": self._account,
            "to": self._account,  # Self-transaction (data storage only)
            "value": 0,
            "data": self.w3.to_hex(payload),
            "gas": 100000,
            "gasPrice": self.w3.to_wei(20, "gwei"),
        }

        tx_hash = self.w3.eth.send_transaction(tx)
        receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=10)

        return "0x" + receipt.transactionHash.hex(), receipt.blockNumber

    # ─────────────────────────────────────────────────────────────────
    # VERIFICATION
    # ─────────────────────────────────────────────────────────────────

    def verify_record(self, resource_type: str, resource_id: str, current_record: dict) -> dict:
        """
        Verify a record's integrity against its blockchain-stored hash.

        Computes the current hash and compares against the latest anchor.

        Returns:
            Verification result dict with status and details
        """
        now = utc_now()

        # Get the latest blockchain anchor for this resource
        anchor = self.anchors.find_one(
            {"resource_type": resource_type, "resource_id": resource_id},
            sort=[("created_at", -1)],
        )

        if not anchor:
            return {
                "status": "NO_ANCHOR",
                "message": "No blockchain anchor found for this record.",
                "record_id": resource_id,
                "verified_at": now,
            }

        # Compute current hash
        current_hash = self.compute_record_hash(current_record)
        blockchain_hash = anchor["data_hash"]

        if current_hash == blockchain_hash:
            return {
                "status": "VERIFIED",
                "message": "Record integrity confirmed. Hash matches blockchain anchor.",
                "record_id": resource_id,
                "current_hash": current_hash,
                "blockchain_hash": blockchain_hash,
                "transaction_hash": anchor.get("transaction_hash"),
                "block_number": anchor.get("block_number"),
                "anchored_at": anchor["created_at"],
                "verified_at": now,
            }
        else:
            return {
                "status": "INTEGRITY_VIOLATION",
                "message": "Record hash does not match blockchain anchor. Possible tampering.",
                "record_id": resource_id,
                "current_hash": current_hash,
                "blockchain_hash": blockchain_hash,
                "transaction_hash": anchor.get("transaction_hash"),
                "block_number": anchor.get("block_number"),
                "anchored_at": anchor["created_at"],
                "verified_at": now,
            }

    def get_anchor(self, resource_type: str, resource_id: str) -> Optional[dict]:
        """Get the latest anchor for a resource."""
        return self.anchors.find_one(
            {"resource_type": resource_type, "resource_id": resource_id},
            sort=[("created_at", -1)],
        )

    def get_anchors_for_patient(self, patient_id: str) -> list:
        """Get all anchors related to a patient."""
        return list(
            self.anchors.find({"patient_id": patient_id}).sort("created_at", -1)
        )

    def get_status(self) -> dict:
        """Get blockchain connection status."""
        connected = self.is_connected
        block_number = None
        if connected:
            try:
                block_number = self.w3.eth.block_number
            except Exception:
                pass
        return {
            "connected": connected,
            "network": "ganache-local",
            "chain_id": 1337,
            "block_number": block_number,
            "account": self._account,
            "total_anchors": self.anchors.count_documents({}),
        }
