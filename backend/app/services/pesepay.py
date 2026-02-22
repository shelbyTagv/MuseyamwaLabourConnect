"""
Pesepay payment gateway integration.
API docs: https://docs.pesepay.com
"""

import hashlib
import hmac
import json
from typing import Optional
from uuid import UUID

import httpx
from fastapi import HTTPException

from app.config import settings


class PesepayClient:
    """Client for the Pesepay payment API."""

    def __init__(self):
        self.base_url = settings.PESEPAY_API_URL
        self.integration_key = settings.PESEPAY_INTEGRATION_KEY
        self.encryption_key = settings.PESEPAY_ENCRYPTION_KEY

    def _headers(self) -> dict:
        return {
            "Authorization": self.integration_key,
            "Content-Type": "application/json",
        }

    async def initiate_payment(
        self,
        amount: float,
        currency: str = "USD",
        reason: str = "Token Purchase",
        method: str = "ecocash",
        phone: Optional[str] = None,
        reference: Optional[str] = None,
    ) -> dict:
        """
        Initiate a Pesepay payment transaction.
        Returns: { reference, poll_url, redirect_url }
        """
        payload = {
            "amountDetails": {
                "amount": amount,
                "currencyCode": currency,
            },
            "reasonForPayment": reason,
            "resultUrl": settings.PESEPAY_RESULT_URL,
            "returnUrl": settings.PESEPAY_RETURN_URL,
        }

        if reference:
            payload["merchantReference"] = reference

        # For mobile money, send inline payment
        if method in ("ecocash", "innbucks") and phone:
            payload["paymentMethodCode"] = method.upper()
            payload["customer"] = {"phoneNumber": phone}
            url = f"{self.base_url}/payments/make-payment"
        else:
            # Redirect-based payment (card, etc.)
            url = f"{self.base_url}/payments/initiate"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(url, json=payload, headers=self._headers())
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Pesepay error: {str(e)}")

        return {
            "reference": data.get("referenceNumber", reference),
            "poll_url": data.get("pollUrl", ""),
            "redirect_url": data.get("redirectUrl", ""),
            "status": data.get("transactionStatus", "PENDING"),
        }

    async def check_payment_status(self, poll_url: str) -> dict:
        """Poll the status of a payment."""
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(poll_url, headers=self._headers())
                resp.raise_for_status()
                return resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Pesepay poll error: {str(e)}")

    def verify_webhook(self, payload: dict, signature: str) -> bool:
        """Verify the HMAC signature of a Pesepay webhook."""
        raw = json.dumps(payload, sort_keys=True)
        expected = hmac.new(
            self.encryption_key.encode(),
            raw.encode(),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected, signature)


# Singleton
pesepay_client = PesepayClient()
