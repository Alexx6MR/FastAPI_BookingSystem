from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

# Initialize FastAPI app
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

    # Validator to ensure datetime format is correct
    @field_validator('start_time', 'end_time')
    def validate_datetime_format(cls, v):
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M')
        except ValueError:
            raise ValueError('Datetime must be in YYYY/MM/DD-HH:MM format')
        return v

class Review(BaseModel):
    classroom_id: int
    student_name: str
    rating: int
    comment: str

# Response Model
class ResponseModel(BaseModel):
    status: str
    message: str
    data: dict

# In-Memory Databases
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
reviews = []

# Helper Functions
def is_classroom_available(classroom_id: int, start_time: str, end_time: str, exclude_booking_id: int = None) -> bool:
    start = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')
    end = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')
    for booking in bookings:
        if booking.id == exclude_booking_id:
            continue
        existing_start = datetime.strptime(booking.start_time, '%Y/%m/%d-%H:%M')
        existing_end = datetime.strptime(booking.end_time, '%Y/%m/%d-%H:%M')
        if booking.classroom_id == classroom_id and not (end <= existing_start or start >= existing_end):
            return False
    return True

def validate_booking_times(start_time: str, end_time: str):
    start = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')
    end = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')
    if start.hour < 7 or end.hour > 18 or (end.hour == 18 and end.minute > 0):
        raise HTTPException(status_code=422, detail="Bookings can only be made between the hours 07:00 and 18:00.")
    if start.minute != 0 or end.minute != 0:
        raise HTTPException(status_code=422, detail="Bookings can only be made for whole hours.")
    if start >= end:
        raise HTTPException(status_code=422, detail="Start time must be before end time.")

# Endpoints

# List all classrooms
@app.get("/classrooms")
def list_classrooms():
    return ResponseModel(
        status="success",
        message="Classrooms retrieved successfully",
        data={"classrooms": [classroom.model_dump() for classroom in classrooms]}
    )

# List all bookings
@app.get("/bookings")
def list_bookings():
    return ResponseModel(
        status="success",
        message="Bookings retrieved successfully",
        data={"bookings": [booking.model_dump() for booking in bookings]}
    )

# Create a new booking for a classroom
@app.post("/bookings")
def book_classroom(booking: Booking):
    validate_booking_times(booking.start_time, booking.end_time)
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
    booking.id = len(bookings) + 1
    bookings.append(booking)
    return ResponseModel(
        status="success",
        message="Your booking has been confirmed!",
        data={"booking": booking.model_dump()}
    )

# Update a booking for a classroom
@app.put("/bookings/{booking_id}")
def change_booking(booking_id: int, updated_booking: Booking):
    validate_booking_times(updated_booking.start_time, updated_booking.end_time)
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time, exclude_booking_id=booking_id):
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
            updated_booking.id = booking_id  # Ensure the ID remains the same
            bookings[index] = updated_booking
            return ResponseModel(
                status="success",
                message="Your booking has been updated.",
                data={"booking": updated_booking.model_dump()}
            )
    raise HTTPException(status_code=404, detail="Booking not found.")

# Delete a booking for a classroom
@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int):
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            canceled_booking = bookings.pop(index)
            return ResponseModel(
                status="success",
                message="Your booking has been canceled.",
                data={"booking": canceled_booking.model_dump()}
            )
    raise HTTPException(status_code=404, detail="Booking not found.")

# Add a review for a classroom
@app.post("/reviews")
def add_review(review: Review):
    reviews.append(review)
    return ResponseModel(
        status="success",
        message="Your review has been submitted!",
        data={"review": review.model_dump()}
    )

# List all reviews or reviews for a specific classroom
@app.get("/reviews")
def list_reviews(classroom_id: int = None):
    if classroom_id:
        filtered_reviews = [review.model_dump() for review in reviews if review.classroom_id == classroom_id]
        return ResponseModel(
            status="success",
            message="Reviews retrieved successfully",
            data={"reviews": filtered_reviews}
        )
    return ResponseModel(
        status="success",
        message="All reviews retrieved successfully",
        data={"reviews": [review.model_dump() for review in reviews]}
    )