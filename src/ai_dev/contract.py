from pydantic import BaseModel , Field , field_validator
from datetime import time,datetime 

class Ticketinput(BaseModel):
    ticket_id : str
    @field_validator("tracking_id")
    @classmethod
    def must_start(cls,v:str):
        if not v.startswith("T-"):
            raise ValueError
        return v
    customer_email : str

    @field_validator("customer_email")
    @classmethod
    def must_include(cls,v:str):
        if ("@" not in v):
            raise ValueError
        return v
    
    message: str = Field(
        max_length=100
    )
    timestamp: datetime 

class Ticket_classification(BaseModel):
    pass