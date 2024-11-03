from datetime import datetime, timedelta
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from utils.validation import time_validation
from models import Booking, Classroom, User
from db.dbConfig import SessionDep


# Creates an API router for handling authentication-related endpoints.
user_router = APIRouter()
# Defines the base directory path for the current file.(app/*)
BASE_DIR = Path(__file__).resolve().parent.parent
# Sets up Jinja2 template rendering using the 'templates' directory.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Get All Users Bookings
@user_router.get("/{user_id}/bookings")
def get_user_bookings(user_id: int, session: SessionDep):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    bookings_statement = select(Booking).where(Booking.user_id == user_id)
    bookings = session.exec(bookings_statement).all()
    bookings_data = [
        {
            "booking_id": booking.id,
            "classroom_id": booking.classroom_id,
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat()
        }
        for booking in bookings
    ]
    return JSONResponse(content=bookings_data)

# Create booking
@user_router.post("/{user_id}/create")
def book_timeslot(classroom_id: int, user_id: int, start_time: str, end_time: str, session: SessionDep):
    classroom = session.get(Classroom, classroom_id)
    if not classroom:
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    # Validates and converts the start and end time strings to time objects using the time_validation function.
    start_time_obj, end_time_obj = time_validation(start_time, end_time)


    # Convert start and end times to datetime objects for easier calculations
    start_datetime = datetime.combine(datetime.today(), start_time_obj)
    end_datetime = datetime.combine(datetime.today(), end_time_obj)

    # Loop through each hour and create a booking for each hour slot
    current_time = start_datetime
    while current_time < end_datetime:
        next_time = current_time + timedelta(hours=1)

        # Check if the timeslot is available
        bookings_statement = select(Booking).where(
            (Booking.classroom_id == classroom_id) &
            (Booking.start_time < next_time.time()) &
            (Booking.end_time > current_time.time())
        )
        overlapping_bookings = session.exec(bookings_statement).all()
        if overlapping_bookings:
            raise HTTPException(status_code=400, detail=f"Timeslot from {current_time.time()} to {next_time.time()} is already booked")

        # Create a new booking for the current hour slot
        new_booking = Booking(
            classroom_id=classroom_id,
            user_id=user_id,
            start_time=current_time.time(),
            end_time=next_time.time()
        )
        session.add(new_booking)

        # Move to the next hour slot
        current_time = next_time

    # Commit all bookings at once
    session.commit()

    return JSONResponse(content={
        "message": "Booking created successfully",
        "bookings": [
            {
                "classroom_id": classroom_id,
                "user_id": user_id,
                "start_time": (start_datetime + timedelta(hours=i)).time().isoformat(),
                "end_time": (start_datetime + timedelta(hours=i+1)).time().isoformat()
            }
            for i in range(int((end_datetime - start_datetime).total_seconds() // 3600))
        ]
    })

# Update Booking
@user_router.put("/{user_id}/update")
def edit_booking(booking_id: int, start_time: str, end_time: str, session: SessionDep):
    booking = session.get(Booking, booking_id)
    
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    
    # Validates and converts the start and end time strings to time objects using the time_validation function.
    start_time_obj, end_time_obj = time_validation(start_time, end_time)

    # Check if the timeslot is available
    bookings_statement = select(Booking).where(
        (Booking.classroom_id == booking.classroom_id) &
        (Booking.start_time < end_time_obj) &
        (Booking.end_time > start_time_obj) &
        (Booking.id != booking_id)
    )
    overlapping_bookings = session.exec(bookings_statement).all()
    
    if overlapping_bookings:
        raise HTTPException(status_code=409, detail="Timeslot is already booked")
    

    # Update the booking
    booking.start_time = start_time_obj
    booking.end_time = end_time_obj
    session.commit()
    session.refresh(booking)

    return JSONResponse(content={
        "message": "Booking updated successfully",
        "booking": {
            "booking_id": booking_id,
            "user_id": booking.user_id,
            "classroom_id": booking.classroom_id,
            "start_time": booking.start_time.isoformat(),
            "end_time": booking.end_time.isoformat()
        }
    })

# Delete booking
@user_router.delete("/{user_id}/delete")
def delete_booking(user_id: int, booking_id: int, session: SessionDep):
    booking = session.get(Booking, booking_id)
    if not booking or booking.user_id != user_id:
        raise HTTPException(status_code=404, detail="Booking not found")

    session.delete(booking)
    session.commit()

    return JSONResponse(content={
        "message": "Booking deleted successfully",
        "booking_id": booking_id
    })
