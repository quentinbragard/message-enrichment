"""Ad-hoc PII detection smoke test using GLiNER if enabled."""
import asyncio
import os
from services.pii_service import PIIService


SAMPLE_MESSAGES = [
    "Hi, I'm John Doe, email john.doe@example.com, phone +1 415-555-1234, card 4242 4242 4242 4242, passport X1234567.",
    "Please reset my account password for jane@acme.io, my employee ID is 7788 and SSN 123-45-6789.",
    "Ship to 221B Baker Street, London. Contact: sherlock.holmes@detective.co.uk or +44 20 7946 0958.",
]


async def run():
    service = PIIService()
    for idx, text in enumerate(SAMPLE_MESSAGES, 1):
        result = await service.detect(text)
        print(f"\n--- Sample {idx} ---")
        print(text)
        print(result)


if __name__ == "__main__":
    # Honor existing env; default ENABLE_GLINER_PII=true
    os.environ.setdefault("ENABLE_GLINER_PII", "true")
    asyncio.run(run())
