"""
Pramana AI — Mock VClaim Rencana Kontrol Schemas.

Pydantic models for Rencana Kontrol and SPRI endpoints.
"""
from pydantic import BaseModel


class RencanaKontrolInsertRequest(BaseModel):
    noSep: str
    tglRencanaKontrol: str
    poliKontrol: str
    kodeDokter: str
    user: str


class SPRIInsertRequest(BaseModel):
    noKartu: str
    tglRencanaRI: str
    poliRI: str
    kodeDokter: str
    user: str
