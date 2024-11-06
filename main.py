import logging
from fastapi import FastAPI, HTTPException  # Import FastAPI and HTTPException for API creation and error handling
from loggning import setupLogging
from pydantic import BaseModel, field_validator, Field   # Import BaseModel for data modeling and field_validator for validation
from datetime import datetime  # Import datetime for date and time handling

# Configure the logger
setupLogging()

app = FastAPI()  # Initialize FastAPI instance
    
    
# Data models
class Classroom(BaseModel):
    id: int  # Unique identifier for the classroom
    name: str  # Name of the classroom

class Booking(BaseModel):
    id: int
    classroom_id: int
    student_name: str
    start_time: str  # Expected format: 'YYYY/MM/DD-HH:MM'
    end_time: str  # Expected format: 'YYYY/MM/DD-HH:MM'

    # Validator to ensure 'start_time' and 'end_time' have the correct format
    @field_validator('start_time', 'end_time')
    def validate_datetime_format(cls, v):
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M')
        except ValueError:
            raise ValueError('Time must be in format YYYY/MM/DD-HH:MM')
        return v

class Review(BaseModel):
    classroom_id: int
    student_name: str
    rating: int = Field(..., ge=1, le=10, alias="rating (1-10)" ,description="Rating must be between 1-10")  # Begränsar rating mellan 1 och 10
    comment: str

class ResponseModel(BaseModel):  # Standard response model for consistent API responses
    status: str
    message: str
    data: dict

# In-memory data storage for classrooms, bookings, and reviews
classrooms = [
    Classroom(id=1, name="Room A"), Classroom(id=2, name="Room B"),
    Classroom(id=3, name="Room C"), Classroom(id=4, name="Room D"),
    Classroom(id=5, name="Room E"), Classroom(id=6, name="Room F"),
    Classroom(id=7, name="Room G"), Classroom(id=8, name="Room H")
]

bookings = []
reviews = []

# Helper function to check classroom availability within a specific time slot
def is_classroom_available(classroom_id: int, start_time: str, end_time: str, exclude_booking_id: int = None) -> bool:
    start_time = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')
    end_time = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')
    
    for booking in bookings:
        if booking.id == exclude_booking_id:  # Skip the booking we’re trying to update
            continue
        
        booking_start = datetime.strptime(booking.start_time, '%Y/%m/%d-%H:%M')
        booking_end = datetime.strptime(booking.end_time, '%Y/%m/%d-%H:%M')
        
        # Check for time overlap within the same classroom
        if booking.classroom_id == classroom_id and not (end_time <= booking_start or start_time >= booking_end):
            return False  # Overlapping booking found, classroom is not available
    return True

# Validate that booking times are within allowed hours (07:00 to 18:00) and occur on the hour
def validate_booking_times(start_time: str, end_time: str):
    start = datetime.strptime(start_time, '%Y/%m/%d-%H:%M')
    end = datetime.strptime(end_time, '%Y/%m/%d-%H:%M')
    
    # Check operating hours and whole-hour requirements
    if start.hour < 7 or end.hour > 18 or (end.hour == 18 and end.minute > 0):
        raise HTTPException(status_code=422, detail="Bookings allowed between 07:00 and 18:00 only.")
    if start.minute != 0 or end.minute != 0:
        raise HTTPException(status_code=422, detail="Bookings can only be made for whole hours.")
    if start >= end:
        raise HTTPException(status_code=422, detail="Start time must be before end time.")

# API Endpoints

@app.get("/classrooms")
def list_classrooms():
    # Returns all classrooms
    logging.info(f'Classrooms retrieved successfully {len(classrooms)}')
    return ResponseModel(
        status="success",
        message="Classrooms retrieved successfully",
        data={"classrooms": [classroom.model_dump() for classroom in classrooms]}
    )

@app.get("/bookings")
def list_bookings():
    # Returns all bookings
    logging.info(f'Bookings retrieved successfully {len(bookings)}')
    return ResponseModel(
        status="success",
        message="Bookings retrieved successfully",
        data={"bookings": [booking.model_dump() for booking in bookings]}
    )

@app.post("/bookings")
def book_classroom(booking: Booking):
    # Validate booking times and check classroom availability
    validate_booking_times(booking.start_time, booking.end_time)
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time):
        logging.error(f"Classroom is not available for the given time slot.")
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
    
    # Assign unique ID and add booking to storage
    booking.id = len(bookings) + 1
    bookings.append(booking)
    logging.info(f'Your booking has been confirmed!: {booking.model_dump()}')
    return ResponseModel(
        status="success",
        message="Your booking has been confirmed!",
        data={"booking": booking.model_dump()}
    )

@app.put("/bookings/{booking_id}")
def change_booking(booking_id: int, updated_booking: Booking):
    # Validate updated booking times
    validate_booking_times(updated_booking.start_time, updated_booking.end_time)
    
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            # Check classroom availability for updated times, excluding the current booking
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time, exclude_booking_id=booking_id):
                logging.error(f"Classroom is not available for the given time slot.")
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
            
            # Update booking and keep the original ID
            updated_booking.id = booking_id
            bookings[index] = updated_booking
            logging.info(f'Your booking has been updated.: {updated_booking.model_dump()}')
            return ResponseModel(
                status="success",
                message="Your booking has been updated.",
                data={"booking": updated_booking.model_dump()}
            )
    
    # Booking not found
    raise HTTPException(status_code=404, detail="Booking not found.")

@app.delete("/bookings/{booking_id}")
def cancel_booking(booking_id: int):
    # Find and remove the booking by ID
    for index, booking in enumerate(bookings):
        if booking.id == booking_id:
            canceled_booking = bookings.pop(index)
            logging.info(f'Your booking has been canceled: {canceled_booking.model_dump()}')
            return ResponseModel(
                status="success",
                message="Your booking has been canceled.",
                data={"booking": canceled_booking.model_dump()}
            )
    
    # Booking not found
    logging.error(f"Booking not found.")
    raise HTTPException(status_code=404, detail="Booking not found.")
   

@app.post("/reviews")
def add_review(review: Review):
    # Add a new review to the review list
    reviews.append(review)
    logging.info(f'Your review has been submitted: {review.model_dump()}')
    return ResponseModel(
        status="success",
        message="Your review has been submitted!",
        data={"review": review.model_dump()}
    )
    
@app.get("/reviews")
def list_reviews(classroom_id: int = None):
    # Retrieve reviews; filter by classroom_id if provided
    if classroom_id:
        filtered_reviews = [review.model_dump() for review in reviews if review.classroom_id == classroom_id]
        logging.info(f'Reviews retrieved successfully: {filtered_reviews}')
        return ResponseModel(
            status="success",
            message="Reviews retrieved successfully",
            data={"reviews": filtered_reviews}
        )
    
    # Return all reviews if no filter applied
    logging.info(f'Reviews retrieved successfully: {[review.model_dump() for review in reviews]}')
    return ResponseModel(
        status="success",
        message="All reviews retrieved successfully",
        data={"reviews": [review.model_dump() for review in reviews]}
    )


# @app.get("/reviews")
# def list_reviews(classroom_id: int = None):
#     # Retrieve reviews; filter by classroom_id if provided
#     if classroom_id:
#         filtered_reviews = [review.model_dump() for review in reviews if review.classroom_id == classroom_id]
#         logging.info(f'Reviews retrieved successfully: {filtered_reviews.model_dump()}')
#         return ResponseModel(
#             status="success",
#             message="Reviews retrieved successfully",
#             data={"reviews": filtered_reviews.model_dump()}
#         )
    
#     # Return all reviews if no filter applied
#     logging.info(f'Reviews retrieved successfully: {[review.model_dump() for review in reviews]}')
#     return ResponseModel(
#         status="success",
#         message="All reviews retrieved successfully",
#         data={"reviews": [review.model_dump() for review in reviews]}
#     )
