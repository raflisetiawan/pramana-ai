"""
Pramana AI — Mock VClaim Rujukan Schemas.

Pydantic models for Rujukan endpoints.
"""
from pydantic import BaseModel


class RujukanInsertRequest(BaseModel):
    noSep: str
    tglRujukan: str
    ppkRujukan: str
    diagRujukan: str
    poliRujukan: str
    tipeRujukan: str
    catatan: str = ""
    user: str
