"""
Pesepay payment gateway – SEAMLESS integration.
Uses AES-256-CBC encryption as required by Pesepay v2 API.
Docs: https://docs.pesepay.com
"""

import base64
import json
import logging
from typing import Optional
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

import httpx
from fastapi import HTTPException

from app.config import settings

logger = logging.getLogger(__name__)


class PesepayClient:
    """Client for Pesepay seamless payment API (v2)."""

    PRODUCTION_URL = "https://api.pesepay.com/api/payments-engine/v2"

    def __init__(self):
        self.base_url = self.PRODUCTION_URL
        self.integration_key = settings.PESEPAY_INTEGRATION_KEY
        self.encryption_key = settings.PESEPAY_ENCRYPTION_KEY

    def _headers(self) -> dict:
        return {
            "Authorization": self.integration_key,
            "Content-Type": "application/json",
        }

    def _encrypt(self, data: dict) -> str:
        """Encrypt payload with AES-256-CBC using Pesepay encryption key.
        IV = first 16 chars of the encryption key.
        """
        key = self.encryption_key.encode("utf-8")
        iv = key[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        raw = json.dumps(data).encode("utf-8")
        encrypted = cipher.encrypt(pad(raw, AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")

    def _decrypt(self, encrypted_text: str) -> dict:
        """Decrypt Pesepay response using AES-256-CBC."""
        key = self.encryption_key.encode("utf-8")
        iv = key[:16]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decoded = base64.b64decode(encrypted_text)
        decrypted = unpad(cipher.decrypt(decoded), AES.block_size)
        return json.loads(decrypted.decode("utf-8"))

    async def make_seamless_payment(
        self,
        amount: float,
        currency: str = "USD",
        reason: str = "Token Purchase",
        phone: str = "",
        method: str = "ECOCASH",
        reference: str = "",
    ) -> dict:
        """
        Initiate a seamless payment — sends a USSD push to the user's phone.
        The user gets a PIN prompt directly on their device.

        Returns: { reference, poll_url, status }
        """
        # Build the payload
        payload = {
            "amountDetails": {
                "amount": amount,
                "currencyCode": currency,
            },
            "reasonForPayment": reason,
            "resultUrl": settings.PESEPAY_RESULT_URL,
            "returnUrl": settings.PESEPAY_RETURN_URL,
            "merchantReference": reference,
            "paymentMethodCode": method.upper(),
            "customer": {
                "phoneNumber": phone,
            },
            "paymentMethodRequiredFields": {
                "customerPhoneNumber": phone,
            },
        }

        # Encrypt the payload
        encrypted = self._encrypt(payload)
        request_body = {"payload": encrypted}

        logger.info(f"Pesepay seamless payment: {amount} {currency} via {method} to {phone}")

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self.base_url}/payments/make-payment",
                    json=request_body,
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Pesepay HTTP error: {e.response.status_code} - {e.response.text}")
            raise HTTPException(
                status_code=502,
                detail=f"Payment gateway error: {e.response.text}",
            )
        except httpx.HTTPError as e:
            logger.error(f"Pesepay connection error: {str(e)}")
            raise HTTPException(status_code=502, detail="Payment gateway unavailable")

        # Decrypt the response if it's encrypted
        if "payload" in data:
            data = self._decrypt(data["payload"])

        logger.info(f"Pesepay response: {data}")

        return {
            "reference": data.get("referenceNumber", reference),
            "poll_url": data.get("pollUrl", ""),
            "redirect_url": data.get("redirectUrl", ""),
            "status": data.get("transactionStatus", "PENDING"),
        }

    async def check_payment_status(self, reference: str) -> dict:
        """
        Check the status of a payment by reference number.
        Returns the full transaction status from Pesepay.
        """
        try:
            async with httpx.AsyncClient(timeout=15) as client:
                resp = await client.get(
                    f"{self.base_url}/payments/check-payment-status",
                    params={"referenceNumber": reference},
                    headers=self._headers(),
                )
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPError as e:
            logger.error(f"Pesepay poll error: {str(e)}")
            raise HTTPException(status_code=502, detail="Failed to check payment status")

        # Decrypt if encrypted
        if "payload" in data:
            data = self._decrypt(data["payload"])

        logger.info(f"Pesepay status check: {data}")
        return data

    async def poll_until_complete(self, reference: str, max_attempts: int = 12, interval: float = 5.0) -> dict:
        """
        Poll payment status until it completes or fails (up to ~60 seconds).
        Returns the final status dict.
        """
        import asyncio

        for attempt in range(max_attempts):
            status = await self.check_payment_status(reference)
            tx_status = status.get("transactionStatus", "").upper()

            if tx_status in ("SUCCESS", "PAID"):
                return {"status": "SUCCESS", "data": status}
            elif tx_status in ("FAILED", "CANCELLED", "DECLINED"):
                return {"status": "FAILED", "data": status}

            # Still pending — wait and try again
            logger.info(f"Payment {reference} still pending (attempt {attempt + 1}/{max_attempts})")
            await asyncio.sleep(interval)

        return {"status": "PENDING", "data": status}


# Singleton
pesepay_client = PesepayClient()
