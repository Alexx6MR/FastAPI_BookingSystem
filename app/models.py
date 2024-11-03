from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from datetime import time



# Represents the Classroom table with fields for name, type, level, size, image URL, and related bookings.
class Classroom(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    type: str
    level: int
    size: int
    image_url: Optional[str]  # URL of the classroom image
    bookings: List["Booking"] = Relationship(back_populates="classroom")
    
# Represents the User table with fields for email, username, password, and related bookings.
class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    email: str
    username: str
    password: str
    bookings: List["Booking"] = Relationship(back_populates="user")

# Represents the Booking table with fields for user, classroom, start time, end time, and relationships to User and Classroom.
class Booking(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id")
    classroom_id: int = Field(foreign_key="classroom.id")
    start_time: time
    end_time: time
    user: "User" = Relationship(back_populates="bookings")
    classroom: "Classroom" = Relationship(back_populates="bookings")
