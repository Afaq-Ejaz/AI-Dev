from pydantic import BaseModel , Field
from datetime import time,datetime 


class Parcel(BaseModel):
    tracking_id: str
    weight_kg: float=Field(gt=0) # weight is > zero

class Ticket_input(BaseModel):
    ticket_id : int
    customer_email : str
    message: str = Field(max_length=100)
    timestamp: datetime 

class Ticket_classification(BaseModel):
    pass