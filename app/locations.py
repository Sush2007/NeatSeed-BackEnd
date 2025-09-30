from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models import User, Location
from app.schemas import Location as LocationSchema
from app.dependencies import get_current_user, get_db

router = APIRouter()

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, db: Session = Depends(get_db)):
    await websocket.accept()
    try:
        token = await websocket.receive_text()
        user = get_current_user(db, token)
        if not user:
            await websocket.close(code=1008)
            return

        while True:
            data = await websocket.receive_json()
            latitude = data.get("latitude")
            longitude = data.get("longitude")
            
            if latitude is None or longitude is None:
                await websocket.send_text("Invalid coordinates")
                continue

            try:
                location = Location(
                    latitude=float(latitude),
                    longitude=float(longitude),
                    owner_id=user.id
                )
                db.add(location)
                db.commit()
                await websocket.send_text("Location saved")
            except ValueError:
                await websocket.send_text("Invalid coordinate format")
            except Exception as e:
                await websocket.send_text(f"Error saving location: {str(e)}")
                
    except WebSocketDisconnect:
        print("Client disconnected")
    except Exception as e:
        print(f"Error: {e}")
        await websocket.close(code=1011)

@router.get("/locations/", response_model=List[LocationSchema])
async def read_locations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not current_user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    locations = db.query(Location)\
        .filter(Location.owner_id == current_user.id)\
        .all()
    return locations
