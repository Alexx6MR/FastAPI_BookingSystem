from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

app = FastAPI()

# Data Models
class Classroom(BaseModel):
    id: int
    name: str

class Booking(BaseModel):
    id: int
    classroom_id: int
    student_name: str
    start_time: str
    end_time: str

    @field_validator('start_time', 'end_time')
    def validate_datetime_format(cls, v):
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M')
        except ValueError:
            raise ValueError('Datetime must be in YYYY/MM/DD-HH:MM format')
        return v

# In-Memory Database
classrooms = [
    Classroom(id=1, name="Room A"),
    Classroom(id=2, name="Room B"),
    Classroom(id=3, name="Room C"),
    Classroom(id=4, name="Room D"),
    Classroom(id=5, name="Room E"),
    Classroom(id=6, name="Room F"),
    Classroom(id=7, name="Room G"),
    Classroom(id=8, name="Room H"),
]

bookings = []

# Helper Functions

def is_classroom_available(classroom_id: int, start_time: str, end_time: str, exclude_booking_id: int = None) -> bool:
    start_time = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')
    end_time = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')
    for booking in bookings:
        if booking.id == exclude_booking_id:
            continue
        booking_start = datetime.strptime(booking.start_time, '%Y/%m/%d-%H:%M')
        booking_end = datetime.strptime(booking.end_time, '%Y/%m/%d-%H:%M')
        if booking.classroom_id == classroom_id and not (end_time <= booking_start or start_time >= booking_end):
            return False
    return True

# Endpoints

@app.get("/classrooms", response_model=List[Classroom])
def list_classrooms():
    return classrooms

@app.post("/bookings", response_model=Booking)
def book_classroom(booking: Booking):
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
    booking.id = len(bookings) + 1
    bookings.append(booking)
    return booking

@app.put("/bookings/{booking_id}", response_model=Booking)
def change_booking(booking_id: int, updated_booking: Booking):
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time, exclude_booking_id=booking_id):
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
            updated_booking.id = booking_id  # Ensure the ID remains the same
            bookings[index] = updated_booking
            return updated_booking
    raise HTTPException(status_code=404, detail="Booking not found.")

@app.delete("/bookings/{booking_id}", response_model=Booking)
def cancel_booking(booking_id: int):
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            return bookings.pop(index)
    raise HTTPException(status_code=404, detail="Booking not found.")