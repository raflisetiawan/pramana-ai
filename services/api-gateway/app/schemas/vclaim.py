"""
Pramana AI — VClaim Proxy Pydantic Schemas.

Request/response for POST /api/v1/vclaim/sep/create.
"""
from typing import Any, Optional

from pydantic import BaseModel, Field


class SEPCreateRequest(BaseModel):
    """Request to create a new SEP via Mock VClaim."""

    noKartu: str = Field(..., min_length=13, max_length=13, pattern=r"^\d{13}$")
    tglSep: str = Field(..., pattern=r"^\d{4}-\d{2}-\d{2}$")
    ppkPelayanan: str
    jnsPelayanan: str = "2"  # 1=Rawat Inap, 2=Rawat Jalan
    klsRawatHak: str = "3"
    noMR: str = ""
    asalRujukan: str = "2"  # 1=FKTP, 2=Antar RS
    tglRujukan: str = ""
    noRujukan: str = ""
    ppkRujukan: str = ""
    diagAwal: str = ""
    poliTujuan: str = ""
    poliEksekutif: str = "0"
    catatan: str = ""
    dpjpLayan: str = Field(..., min_length=1)


class SEPCreateResponse(BaseModel):
    """Response from SEP creation proxy."""

    success: bool
    no_sep: str | None = None
    message: str
    vclaim_response: Any = None
