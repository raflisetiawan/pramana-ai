"""
Pramana AI — Mock VClaim SEP Schemas.

Pydantic models for SEP insert, update, and delete requests.
"""
from typing import Optional

from pydantic import BaseModel, Field


class KlsRawat(BaseModel):
    klsRawatHak: str
    klsRawatNaik: str = ""
    pembiayaan: str = ""
    penanggungJawab: str = ""


class Skdp(BaseModel):
    noSurat: str = ""
    kodeDPJP: str = ""


class SEPInsertRequest(BaseModel):
    noKartu: str
    tglSep: str
    ppkPelayanan: str
    jnsPelayanan: str
    noMrLocal: str
    noTelp: str
    klsRawat: KlsRawat
    catatan: str = ""
    diagAwal: str
    poli: str
    poli_eks: str = ""
    kodeDPJP: str
    noRujukan: str = ""
    tujuanKunj: str = "0"
    flagProcedure: str = "0"
    flagKonsul: str = "0"
    assesmentPel: str = "0"
    skdp: Optional[Skdp] = None
    kdSatuSehat: str = ""
    user: str


class SEPUpdateRequest(BaseModel):
    noSep: str
    klsRawat: str
    noMrLocal: str
    noTelp: str
    diagAwal: str
    poli: str
    kodeDPJP: str
    catatan: str = ""
    user: str


class SEPDeleteRequest(BaseModel):
    noSep: str
    user: str
