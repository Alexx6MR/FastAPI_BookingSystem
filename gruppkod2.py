

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import List
from datetime import datetime

app = FastAPI()  # Skapar en FastAPI-instans för applikationen för att definiera endpoints och köra servern på en specifik port.

# Datamodeller
class Classroom(BaseModel):  # Datamodell för ett klassrumsobjekt
    id: int  # Klassrummets ID
    name: str  # Klassrummets namn

class Booking(BaseModel):  # Datamodell för ett bokningsobjekt
    id: int  # Bokningens ID
    classroom_id: int  # ID för det bokade klassrummet
    student_name: str  # Namnet på studenten som gör bokningen
    start_time: str  # Starttid för bokningen, i specificerat format
    end_time: str  # Sluttid för bokningen, i specificerat format

    @field_validator('start_time', 'end_time')  # Anpassad fältvalidering för att säkerställa rätt format på start- och sluttid
    def validate_datetime_format(cls, v):  # Klassmetod för att validera datumformatet på fälten
        try:
            datetime.strptime(v, '%Y/%m/%d-%H:%M')  # Försöker analysera datumssträngen med angivet format
        except ValueError:
            raise ValueError('Datum och tid måste vara i formatet YYYY/MM/DD-HH:MM')  # Ger fel om datumformatet är felaktigt
        return v

class Review(BaseModel):  # Datamodell för en recension
    classroom_id: int  # ID för det klassrum som recensionen gäller
    student_name: str  # Namnet på studenten som lämnar recensionen
    rating: int  # Betyg (skala 1-5)
    comment: str  # Kommentar till recensionen

# Minnessbaserade databas
classrooms = [
    Classroom(id=1, name="Room A"),
    Classroom(id=2, name="Room B"),
    Classroom(id=3, name="Room C"),
    Classroom(id=4, name="Room D"),
    Classroom(id=5, name="Room E"),
    Classroom(id=6, name="Room F"),
    Classroom(id=7, name="Room G"),
    Classroom(id=8, name="Room H"),
]  # En lista över alla tillgängliga klassrum

bookings = []  # Tom lista som kommer lagra alla bokningar i minnet
reviews = []  # Tom lista som kommer lagra alla recensioner i minnet

# Hjälpfunktioner
def is_classroom_available(classroom_id: int, start_time: datetime, end_time: datetime) -> bool:
    # Funktion för att kontrollera om ett klassrum är ledigt för en given tidsperiod
    for booking in bookings:  # Loopa genom alla befintliga bokningar för att hitta potentiella konflikter
        if booking.classroom_id == classroom_id and not (end_time <= booking.start_time or start_time >= booking.end_time):
            # Kontrollera om klassrum-ID matchar och om det finns en tidskonflikt
            return False  # Returnera False om det finns en konflikt
    return True  # Returnera True om ingen konflikt hittas

# Endpoints

# Hämta alla klassrum
@app.get("/classrooms", response_model=List[Classroom])
def list_classrooms():
    # Funktion för att returnera alla klassrum i minnet
    return classrooms

# Hämta alla bokningar
@app.get("/bookings", response_model=List[Booking])
def list_bookings():  # Denna funktion returnerar alla bokningar som är lagrade i minnet
    return bookings

# Skapa en ny bokning för ett klassrum
@app.post("/bookings", response_model=dict)
def book_classroom(booking: Booking):
    # Kontrollera om klassrummet är tillgängligt för den valda tidsperioden
    if not is_classroom_available(booking.classroom_id, booking.start_time, booking.end_time):
        raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")
    
    booking.id = len(bookings) + 1  # Tilldela ett unikt ID till bokningen baserat på antalet bokningar
    bookings.append(booking)  # Lägg till bokningen i listan över bokningar
    
    return {
        "Booking status": "successful",
        "message": "Your booking has been confirmed!",
        "booking": booking
    }

# Uppdatera en bokning för ett klassrum
@app.put("/bookings/{booking_id}", response_model=dict)
def change_booking(booking_id: int, updated_booking: Booking):
    # Den uppdaterade bokningen skickas i request-body som JSON och booking_id skickas som en parameter i URL:en
    for index, booking in enumerate(bookings):  # Loopa genom alla bokningar för att hitta den bokning som har det specifika ID:t
        if booking.id == booking_id:  # Kontrollera om ID:t på den aktuella bokningen matchar det angivna boknings-ID:t
            # Kontrollera om klassrummet är tillgängligt för den valda tidsperioden innan bokningen uppdateras
            if not is_classroom_available(updated_booking.classroom_id, updated_booking.start_time, updated_booking.end_time):
                raise HTTPException(status_code=422, detail="Classroom is not available for the given time slot.")  
            bookings[index] = updated_booking  # Uppdatera bokningen i listan med den nya informationen
            return {  # Returnera ett bekräftelsemeddelande tillsammans med detaljer om den uppdaterade bokningen
                "status": "successful",
                "message": "Your booking has been updated.",
                "booking": updated_booking
            }
    raise HTTPException(status_code=404, detail="Booking not found.")  # Returnera ett felmeddelande om bokningen med det angivna ID:t inte hittas

# Ta bort en bokning för ett klassrum
@app.delete("/bookings/{booking_id}", response_model=dict)
def cancel_booking(booking_id: int):
    # Boknings-ID skickas som en parameter i URL:en
    for index, booking in enumerate(bookings):  # Loopa genom bokningarna för att hitta bokningen med det angivna ID:t
        if booking.id == booking_id:  # Kontrollera om ID:t på den aktuella bokningen matchar det angivna boknings-ID:t
            canceled_booking = bookings.pop(index)  # Ta bort bokningen från listan och spara den borttagna bokningen
            return {  # Returnera ett bekräftelsemeddelande tillsammans med detaljer om den avbokade bokningen
                "status": "successful",
                "message": "Your booking has been canceled.",
                "booking": canceled_booking
            }
    raise HTTPException(status_code=404, detail="Booking not found.")  # Returnera ett felmeddelande om bokningen med det angivna ID:t inte hittas

# POST: Lägg till en ny recension
@app.post("/reviews", response_model=dict)
def add_review(review: Review):
    reviews.append(review)  # Lägg till den nya recensionen i listan över recensioner
    return {
        "message": "Your review has been submitted!",
        "review": review
    }

# GET: Hämta alla recensioner eller filtrera efter klassrum
@app.get("/reviews", response_model=List[Review])
def list_reviews(classroom_id: int = None):
    # Om ett klassrum-ID ges, filtrera recensionerna baserat på det klassrummet
    if classroom_id:
        filtered_reviews = [review for review in reviews if review.classroom_id == classroom_id]
        return filtered_reviews
    # Returnera alla recensioner om inget klassrum-ID ges
    return reviews
