from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

app = FastAPI() # Create a FastAPI instance for the application to define endpoints and run the server on a specified port

# Data Models
class Classroom(BaseModel): # Data model for a classroom object
    id: int
    name: str

class Booking(BaseModel): # Data model for a booking object
    id: int
    classroom_id: int
    student_name: str
    start_time: str
    end_time: str

    @field_validator('start_time', 'end_time') # Custom field validator to check the datetime format of start_time and end_time fields
    def validate_datetime_format(cls, v): # Class method to validate the datetime format of the fields
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M') # Check if the datetime string can be parsed with the specified format
        except ValueError:
            raise ValueError('Datetime must be in YYYY/MM/DD-HH:MM format') # Raise a ValueError if the datetime string is not in the correct format
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

def is_classroom_available(classroom_id: int, start_time: datetime, end_time: datetime) -> bool: # Function to check if a classroom is available for a given time slot
    for booking in bookings: # Loop through the list of bookings to check for conflicts
        if booking.classroom_id == classroom_id and not (end_time <= booking.start_time or start_time >= booking.end_time): # Check if the classroom ID matches and there is a time conflict
            return False
    return True

# Endpoints

# List all classrooms
@app.get("/classrooms", response_model=List[Classroom])
def list_classrooms():
    return classrooms

# Create a new booking for a classroom
@app.post("/bookings", response_model=Booking)
def book_classroom(booking: Booking): # The booking object is passed in the request body as JSON
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time): # Check if the classroom is available for the given time slot before creating the booking
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.") # Return a 422 Unprocessable Entity status code if the classroom is not available
    booking.id = len(bookings) + 1 # Assign a unique ID to the booking (increment the length of the bookings list)
    bookings.append(booking)  # Add the booking to the list of bookings
    return booking # Return the created booking

# Update a booking for a classroom
@app.put("/bookings/{booking_id}", response_model=Booking)
def change_booking(booking_id: int, updated_booking: Booking): # The updated booking object is passed in the request body as JSON and the booking_id is passed as a path parameter in the URL
    for index, booking in enumerate(bookings): # Loop through the list of bookings to find the booking with the specified ID
        if booking.id == booking_id: # Check if the ID of the current booking matches the specified booking ID
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time): # Check if the classroom is available for the given time slot before updating the booking
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.") # Return a 422 Unprocessable Entity status code if the classroom is not available
            bookings[index] = updated_booking # Update the booking in the list of bookings with the updated booking object
            return updated_booking # Return the updated booking object
    raise HTTPException(status_code=404, detail="Booking not found.") # Return a 404 Not Found status code if the booking with the specified ID is not found

# Delete a booking for a classroom
@app.delete("/bookings/{booking_id}", response_model=Booking)
def cancel_booking(booking_id: int): # The booking_id is passed as a path parameter in the URL
    for index, booking in enumerate(bookings): # Loop through the list of bookings to find the booking with the specified ID
        if booking.id == booking_id: # Check if the ID of the current booking matches the specified booking ID
            return bookings.pop(index) # Remove the booking from the list of bookings and return the deleted booking
    raise HTTPException(status_code=404, detail="Booking not found.") # Return a 404 Not Found status code if the booking with the specified ID is not found