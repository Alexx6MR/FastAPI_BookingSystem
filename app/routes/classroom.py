from datetime import datetime, timedelta
from pathlib import Path
from typing import Annotated
from fastapi import APIRouter, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.templating import Jinja2Templates
from sqlmodel import select
from models import Booking, Classroom
from db.dbConfig import SessionDep


# Creates an API router for handling authentication-related endpoints.
classroom_router = APIRouter()
# Defines the base directory path for the current file.(app/*)
BASE_DIR = Path(__file__).resolve().parent.parent
# Sets up Jinja2 template rendering using the 'templates' directory.
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


# Get all Classrooms
@classroom_router.get("/")
def get_all_classrooms(request: Request, session: SessionDep, offset: int = 0, limit: Annotated[int, Query(le=100)] = 100,) -> list[Classroom]:
    classrooms = session.exec(select(Classroom).offset(offset).limit(limit)).all()
    accept_header = request.headers.get('accept')
    
    if not classrooms:
        raise HTTPException(status_code=404, detail="We dont have any classrooms in db")
    
    # # Checks if the request expects an HTML response.
    if 'text/html' in accept_header:
        return templates.TemplateResponse("index.html", {"request": request, "classroomsList": classrooms if len(classrooms) > 0 else []})
    
    return JSONResponse(content=[classroom.model_dump() for classroom in classrooms])


# Get One classrooms
@classroom_router.get("/{classroom_id}")
def get_one_classroom(request: Request, classroom_id: int, session: SessionDep) -> Classroom:
    classroom = session.get(Classroom, classroom_id)
    # Retrieves the 'accept' header from the request to determine the desired response format.
    accept_header = request.headers.get('accept')
    
    # Checks if the classroom object is None, indicating it was not found in the database.    
    if not classroom: 
        raise HTTPException(status_code=404, detail="Classroom not found")
    
    
    # Define available times from 8:00 AM to 6:00 PM
    timeslots = []
    start_time = datetime.strptime("08:00:00", "%H:%M:%S").time()
    end_time = datetime.strptime("18:00:00", "%H:%M:%S").time()
    
    #Current will change but start_time will be the same
    current_time = start_time

    # Get all bookings for the classroom
    bookings_statement = select(Booking).where(Booking.classroom_id == classroom_id)
    bookings = session.exec(bookings_statement).all()

    # Iterates through each hour between the start and end times to generate timeslots.
    while current_time < end_time:
        # Calculates the next hour time for the current timeslot.
        next_time = (datetime.combine(datetime.today(), current_time) + timedelta(hours=1)).time()
        # Determines if the current timeslot is available by checking against existing bookings.
        is_available = not any(
            booking.start_time <= current_time < booking.end_time for booking in bookings
        )
        # Appends the current timeslot as a dictionary to the timeslots list, including start, end times, and availability.
        timeslots.append({
            "start_time": current_time.isoformat(),
            "end_time": next_time.isoformat(),
            "available": is_available
        })
        # Moves to the next hour for the next iteration of the timeslot generation.
        current_time = next_time
    
    # Converts the classroom object to a dictionary representation.
    classroom_data = classroom.model_dump()
    # Adds the generated timeslots to the classroom data dictionary.
    classroom_data["timeslots"] = timeslots
    
    
    # this is for html
    if 'text/html' in accept_header:
        return templates.TemplateResponse("booking_page.html", {"request": request, "classroom": classroom_data})
    
    #This is for Curl or Swagger
    return JSONResponse(content=classroom_data)


