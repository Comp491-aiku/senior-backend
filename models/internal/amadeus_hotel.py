from typing import Optional, List
from pydantic import BaseModel


class AmadeusHotel(BaseModel):
    type: str
    hotelId: str
    chainCode: Optional[str] = None
    dupeId: Optional[str] = None
    name: str
    cityCode: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class AmadeusRoomDescription(BaseModel):
    text: str
    lang: str


class AmadeusRoomTypeEstimated(BaseModel):
    category: Optional[str] = None
    beds: Optional[int] = None
    bedType: Optional[str] = None


class AmadeusRoom(BaseModel):
    type: str
    typeEstimated: Optional[AmadeusRoomTypeEstimated] = None
    description: Optional[AmadeusRoomDescription] = None


class AmadeusGuests(BaseModel):
    adults: int


class AmadeusPriceAverage(BaseModel):
    base: str


class AmadeusPriceChange(BaseModel):
    startDate: str
    endDate: str
    total: Optional[str] = None
    base: Optional[str] = None


class AmadeusPriceVariations(BaseModel):
    average: Optional[AmadeusPriceAverage] = None
    changes: Optional[List[AmadeusPriceChange]] = None


class AmadeusPrice(BaseModel):
    currency: str
    base: str
    total: str
    variations: Optional[AmadeusPriceVariations] = None


class AmadeusCancellationDescription(BaseModel):
    text: str


class AmadeusCancellation(BaseModel):
    description: Optional[AmadeusCancellationDescription] = None
    type: Optional[str] = None


class AmadeusPolicies(BaseModel):
    paymentType: Optional[str] = None
    cancellation: Optional[AmadeusCancellation] = None


class AmadeusRateFamilyEstimated(BaseModel):
    code: str
    type: str


class AmadeusOffer(BaseModel):
    id: str
    checkInDate: str
    checkOutDate: str
    rateCode: Optional[str] = None
    rateFamilyEstimated: Optional[AmadeusRateFamilyEstimated] = None
    room: AmadeusRoom
    guests: AmadeusGuests
    price: AmadeusPrice
    policies: Optional[AmadeusPolicies] = None
    self_link: Optional[str] = None

    class Config:
        fields = {'self_link': 'self'}


class AmadeusHotelOffer(BaseModel):
    type: str
    hotel: AmadeusHotel
    available: bool
    offers: List[AmadeusOffer]
    self_link: Optional[str] = None

    class Config:
        fields = {'self_link': 'self'}


def parse_hotel_offer(hotel_offer_json: dict) -> AmadeusHotelOffer:
    try:
        return AmadeusHotelOffer(**hotel_offer_json)
    except Exception as e:
        raise ValueError(f"Failed to parse hotel offer: {str(e)}")
