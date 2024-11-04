from fastapi import FastAPI, HTTPException  # Importing FastAPI and HTTPException to handle API endpoints and error responses
from pydantic import BaseModel, field_validator  # Importing BaseModel to define data models and field_validator for custom validation
from typing import List  # Importing List for type hints, allowing lists of items in the model definitions
from datetime import datetime  # Importing datetime for date and time manipulations and validations

app = FastAPI()  # Creating an instance of FastAPI to set up the API

# Data models
class Classroom(BaseModel):  # Model for a classroom, inheriting from Pydantic's BaseModel
    id: int  # Unique identifier for the classroom
    name: str  # Name of the classroom

class Booking(BaseModel):  # Model for booking a classroom
    id: int  # Unique identifier for the booking
    classroom_id: int  # ID of the classroom being booked
    student_name: str  # Name of the student making the booking
    start_time: str  # Start time of the booking, as a string in specified format
    end_time: str  # End time of the booking, as a string in specified format

    @field_validator('start_time', 'end_time')  # Custom validator to ensure start_time and end_time follow the correct format
    def validate_datetime_format(cls, v):  # Method to check that date and time are in the required format
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M')  # Attempting to parse the string to validate format
        except ValueError:
            raise ValueError('Datum och tid måste vara i formatet YYYY/MM/DD-HH:MM')  # Error message if format is invalid
        return v  # Returning the validated value if no exception was raised

class Review(BaseModel):  # Model for a classroom review
    classroom_id: int  # ID of the classroom being reviewed
    student_name: str  # Name of the student submitting the review
    rating: int  # Rating for the classroom (assumed to be an integer)
    comment: str  # Comment or feedback provided by the student

# Response model for consistent API responses
class ResponseModel(BaseModel):
    status: str  # Status of the response, e.g., "success" or "error"
    message: str  # Message explaining the response
    data: dict  # Dictionary holding any additional data returned with the response

# In-memory databases for classrooms, bookings, and reviews
classrooms = [
    Classroom(id=1, name="Room A"),
    Classroom(id=2, name="Room B"),
    Classroom(id=3, name="Room C"),
    Classroom(id=4, name="Room D"),
    Classroom(id=5, name="Room E"),
    Classroom(id=6, name="Room F"),
    Classroom(id=7, name="Room G"),
    Classroom(id=8, name="Room H"),
]  # Predefined list of classrooms with ID and name

bookings = []  # Empty list to store booking entries
reviews = []  # Empty list to store review entries

# Helper function to check if a classroom is available for a booking time slot
def is_classroom_available(classroom_id: int, start_time: str, end_time: str, exclude_booking_id: int = None) -> bool:
    start_time = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')  # Parsing start_time to a datetime object
    end_time = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')  # Parsing end_time to a datetime object
    for booking in bookings:  # Iterating over all bookings to check for time conflicts
        if booking.id == exclude_booking_id:  # Skip the booking if it is the same as the one we want to update
            continue
        booking_start = datetime.strptime(booking.start_time, '%Y/%m/%d-%H:%M')  # Parsing the booking's start time
        booking_end = datetime.strptime(booking.end_time, '%Y/%m/%d-%H:%M')  # Parsing the booking's end time
        # Check for overlapping bookings in the same classroom
        if booking.classroom_id == classroom_id and not (end_time <= booking_start or start_time >= booking_end):
            return False  # Return False if there is a time overlap
    return True  # Return True if no overlaps were found

# Function to validate that booking times are within allowed hours and formatted correctly
def validate_booking_times(start_time: str, end_time: str):
    start = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')  # Parsing start_time to a datetime object
    end = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')  # Parsing end_time to a datetime object
    # Ensuring bookings are within operating hours (07:00 to 18:00)
    if start.hour < 7 or end.hour > 18 or (end.hour == 18 and end.minute > 0):
        raise HTTPException(status_code=422, detail="Bookings can only be made between the hours 07:00 and 18:00.")
    # Ensuring bookings are made on the hour (no minutes set)
    if start.minute != 0 or end.minute != 0:
        raise HTTPException(status_code=422, detail="Bookings can only be made for whole hours.")
    # Ensuring start time is before the end time
    if start >= end:
        raise HTTPException(status_code=422, detail="Start time must be before end time.")

# Endpoints

@app.get("/classrooms")
def list_classrooms():  # Endpoint to list all classrooms
    return ResponseModel(
        status="success",
        message="Classrooms retrieved successfully",
        data={"classrooms": [classroom.dict() for classroom in classrooms]}  # Returning a dictionary of classrooms
    )

@app.get("/bookings")
def list_bookings():  # Endpoint to list all bookings
    return ResponseModel(
        status="success",
        message="Bookings retrieved successfully",
        data={"bookings": [booking.dict() for booking in bookings]}  # Returning a dictionary of bookings
    )

@app.post("/bookings")
def book_classroom(booking: Booking):
    validate_booking_times(booking.start_time, booking.end_time)  # Validate booking times
    # Check if classroom is available
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
    # Assign a unique ID to the booking and add it to the list
    booking.id = len(bookings) + 1
    bookings.append(booking)
    return ResponseModel(
        status="success",
        message="Your booking has been confirmed!",
        data={"booking": booking.dict()}  # Return the new booking details
    )

@app.put("/bookings/{booking_id}")
def change_booking(booking_id: int, updated_booking: Booking):
    validate_booking_times(updated_booking.start_time, updated_booking.end_time)  # Validate the updated times
    for index, booking in enumerate(bookings):  # Iterate to find the booking with specified ID
        if booking.id == booking_id:
            # Check classroom availability for updated times
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time, exclude_booking_id=booking_id):
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
            updated_booking.id = booking_id  # Ensure the booking ID remains the same
            bookings[index] = updated_booking  # Update the booking in the list
            return ResponseModel(
                status="success",
                message="Your booking has been updated.",
                data={"booking": updated_booking.dict()}  # Return the updated booking details
            )
    raise HTTPException(status_code=404, detail="Booking not found.")  # Return an error if booking ID was not found

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int):
    for index, booking in enumerate(bookings):  # Iterate to find the booking to delete
        if booking.id == booking_id:
            canceled_booking = bookings.pop(index)  # Remove the booking from the list
            return ResponseModel(
                status="success",
                message="Your booking has been canceled.",
                data={"booking": canceled_booking.dict()}  # Return the canceled booking details
            )
    raise HTTPException(status_code=404, detail="Booking not found.")  # Error if booking ID was not found

@app.post("/reviews")
def add_review(review: Review):  # Endpoint to add a review
    reviews.append(review)  # Add the review to the list
    return ResponseModel(
        status="success",
        message="Your review has been submitted!",
        data={"review": review.dict()}  # Return the review details
    )

@app.get("/reviews")
def list_reviews(classroom_id: int = None):  # Endpoint to list reviews, optionally filtering by classroom
    if classroom_id:  # Filter reviews if classroom_id is provided
        filtered_reviews = [review.dict() for review in reviews if review.classroom_id == classroom_id]
        return ResponseModel(
            status="success",
            message="Reviews retrieved successfully",
            data={"reviews": filtered_reviews}  # Return filtered
        )