from sqlalchemy.ext.declarative import declarative_base
from fastapi import FastAPI, Depends, HTTPException, status, UploadFile, File,Form,APIRouter
from fastapi.middleware.cors import CORSMiddleware
from database import get_db, SessionLocal
from models import Admin, Cursole, Product, ShopStatus, Contact, News
from schemas import AdminLogin, Token, CursoleSchema,ProductSchema,ShopStatusUpdate,ContactCreate,ContactBase,NewsGet
from sqlalchemy.orm import Session
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import base64
from fastapi.responses import StreamingResponse
from typing import List
import io
import os
from sqlalchemy import desc
from fastapi.responses import Response
from fastapi.responses import FileResponse
import models
import schemas
from typing import Optional
from datetime import datetime, timedelta
import jwt
import secrets
SECRET_KEY = "your_secret_key_here"
secret_key = secrets.token_urlsafe(32)
print("Generated Secret Key:", secret_key)
Base = declarative_base()

app = FastAPI()

# Basic authentication for admin
security = HTTPBasic()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Adjust this to your React frontend URL
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)
def generate_token(username: str):
    token_data = {"sub": username, "exp": datetime.utcnow() + timedelta(minutes=30)}
    return jwt.encode(token_data, SECRET_KEY, algorithm="HS256")
def authenticate_admin(credentials: HTTPBasicCredentials = Depends(HTTPBasic()), db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == credentials.username).first()
    if not admin or admin.password != credentials.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return admin

# Endpoint for admin login
@app.post("/login")
def login(admin_login: AdminLogin, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == admin_login.username).first()
    if not admin or admin.password != admin_login.password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
        )
    # Generate JWT token
    token = generate_token(admin_login.username)
    return {"access_token": token, "token_type": "bearer"}

# Protected endpoint for admin page access
from fastapi.security import OAuth2PasswordBearer

# Define OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login")

# Modify the admin_page endpoint to require token authentication
@app.get("/admin")
def admin_page(token: str = Depends(oauth2_scheme)):
    try:
        # Verify the token
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        username = payload.get("sub")
        if not username:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"message": "Welcome to the admin page!"}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@app.post("/uploadc/")
async def upload_image(position: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        # Read the contents of the uploaded file
        contents = await file.read()
        
        # Check if an image with the given position exists
        existing_image = db.query(Cursole).filter(Cursole.position == position).first()
        
        if existing_image:
            # Replace existing image with the new one
            existing_image.filename = file.filename
            existing_image.data = contents
        else:
            # Create a new instance of Cursole model
            new_image = Cursole(filename=file.filename, data=contents, position=position)
            # Add the new image to the database
            db.add(new_image)
        
        # Commit changes to the database
        db.commit()
        
        # Return success message
        return {"message": "Image uploaded successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()
@app.get("/imagesc/")
async def get_all_images(db: Session = Depends(get_db)):
    try:
        # Query all images from the database
        images = db.query(Cursole).all()

        # Extract position numbers and file names
        image_data = [{"position": image.position, "filename": image.filename} for image in images]

        return image_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()

# Get endpoint
@app.get("/imagec/{position_id}")
async def get_image_by_position(position_id: int, db: Session = Depends(get_db)):
    db_image = db.query(Cursole).filter(Cursole.position == position_id).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    return Response(content=db_image.data, media_type="image/png") 
@app.delete("/deletec/{position_id}")
async def delete_image_by_position(position_id: int, db: Session = Depends(get_db)):
    try:
        # Check if an image with the given position exists
        db_image = db.query(Cursole).filter(Cursole.position == position_id).first()
        if db_image is None:
            raise HTTPException(status_code=404, detail="Image not found")

        # Delete the image from the database
        db.delete(db_image)
        db.commit()

        return {"message": "Image deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()
@app.post("/product/")
async def upload_image(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), db: Session = Depends(get_db)):
    existing_product = db.query(models.Product).filter(models.Product.position == position).first()
    if existing_product:
        existing_product.filename = file.filename
        existing_product.data = await file.read()
        existing_product.display_name = display_name
        db.commit()
        return {"message": "Product updated successfully"}
    else:
        contents = await file.read()
        product = models.Product(position=position, filename=file.filename, data=contents, display_name=display_name)
        db.add(product)
        db.commit()
        return {"message": "Product uploaded successfully"}

@app.get("/product/{position}/image")
async def get_product_image_by_position(position: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.position == position).first()
    if product:
        if product.data:
            return Response(content=product.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image not found for the product")
    else:
        raise HTTPException(status_code=404, detail="Product not found")

@app.get("/product/{position}/display_name")
async def get_product_display_name_by_position(position: int, db: Session = Depends(get_db)):
    product = db.query(models.Product).filter(models.Product.position == position).first()
    if product:
        return {"display_name": product.display_name}
    else:
        raise HTTPException(status_code=404, detail="Product not found")
@app.get("/products/")
async def get_all_products(db: Session = Depends(get_db)):
    products = db.query(models.Product).all()
    return [{"position": product.position, "file_name": product.filename, "display_name": product.display_name} for product in products]
@app.delete("/productdeletec/{position_id}")
async def delete_image_by_position(position_id: int, db: Session = Depends(get_db)):
    try:
        product = db.query(models.Product).filter(models.Product.position == position_id).first()
        if product is None:
            raise HTTPException(status_code=404, detail="product not found")
        db.delete(product)
        db.commit()
        return {"message": "product deleted successfully"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        db.close()
@app.post("/wire/")  # Change the endpoint to /wire/ instead of /product/
async def upload_wire(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), price: str = Form(...), db: Session = Depends(get_db)):
    existing_wire = db.query(models.Wire).filter(models.Wire.position == position).first()
    if existing_wire:
        existing_wire.filename = file.filename
        existing_wire.data = await file.read()
        existing_wire.display_name = display_name
        existing_wire.price = price  # Update the price
        db.commit()
        return {"message": "Wire updated successfully"}
    else:
        contents = await file.read()
        wire = models.Wire(position=position, filename=file.filename, data=contents, display_name=display_name, price=price)  # Include price in the creation
        db.add(wire)
        db.commit()
        return {"message": "Wire uploaded successfully"}
@app.get("/wire/image/{position}/")
async def get_wire_image(position: int, db: Session = Depends(get_db)):
    wire = db.query(models.Wire).filter(models.Wire.position == position).first()
    if wire:
        if wire.data:
            return Response(content=wire.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image data not found for the wire")
    else:
        raise HTTPException(status_code=404, detail="Wire not found")

# Endpoint to get wire display name and price
@app.get("/wire/{position}/")
async def get_wire_Contact(position: int, db: Session = Depends(get_db)):
    wire = db.query(models.Wire).filter(models.Wire.position == position).first()
    if wire:
        return {
            "position": wire.position,
            "display_name": wire.display_name,
            "price": wire.price
        }
    else:
        raise HTTPException(status_code=404, detail="Wire not found")
@app.get("/wireAll")
async def get_all_wire_Contact(db: Session = Depends(get_db)):
    wires = db.query(models.Wire).all()
    if wires:
        return [
            {
                "position": wire.position,
                "filename": wire.filename,
                "display_name": wire.display_name,
                "price": wire.price
            }
            for wire in wires
        ]
    else:
        raise HTTPException(status_code=404, detail="No wires found")
@app.delete("/wire/{position}")
async def delete_wire(position: int, db: Session = Depends(get_db)):
    wire = db.query(models.Wire).filter(models.Wire.position == position).first()
    if wire:
        db.delete(wire)
        db.commit()
        return {"message": "Wire deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Wire not found")


@app.post("/shop/status")
def update_shop_status(status_update: schemas.ShopStatusUpdate, db: Session = Depends(get_db)):
    shop_status = db.query(models.ShopStatus).first()
    if not shop_status:
        message = "Shop is open" if status_update.status else "Shop is closed"
        shop_status = models.ShopStatus(status=status_update.status, updated_at=datetime.utcnow(), message=message)
        db.add(shop_status)
    else:
        shop_status.status = status_update.status
        shop_status.updated_at = datetime.utcnow()
        shop_status.message = "Shop is open" if status_update.status else "Shop is closed"
    db.commit()
    
    return shop_status

@app.get("/shop/status", response_model=schemas.ShopStatus)
def get_shop_status(db: Session = Depends(get_db)):
    shop_status = db.query(models.ShopStatus).first()
    if not shop_status:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shop status not found")
    return shop_status
@app.post("/contact/", response_model=schemas.Contact)
def create_contact(contact: schemas.ContactBase, db: Session = Depends(get_db)):
    db_contact = models.Contact(**contact.dict())
    db.add(db_contact)
    db.commit()
    db.refresh(db_contact)
    return db_contact

# Endpoint to get all contact details
@app.get("/contact/", response_model=List[schemas.Contact])
def get_all_contact(db: Session = Depends(get_db)):
    return db.query(models.Contact).all()
@app.delete("/contact/{contact_id}", response_model=schemas.Contact)
def delete_contact(contact_id: int, db: Session = Depends(get_db)):
    contact = db.query(models.Contact).filter(models.Contact.id == contact_id).first()
    if not contact:
        raise HTTPException(status_code=404, detail="Contact not found")
    db.delete(contact)
    db.commit()
    return contact
@app.post("/news/")
async def create_or_update_news(position_id: int = Form(...), title: str = Form(...),  content: str = Form(...), uploadfile: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        existing_news = db.query(News).filter(News.position_id == position_id).first()
        if existing_news:
            existing_news.title = title
            existing_news.content = content
            existing_news.date = datetime.now()
            file_contents = await uploadfile.read()
            existing_news.uploadfile = file_contents
            db.commit()
            db.refresh(existing_news)
            return {"message": "News article updated successfully"}
        else:
            file_contents = await uploadfile.read()
            db_news = News(position_id=position_id, title=title, content=content, uploadfile=file_contents, date=datetime.now())
            db.add(db_news)
            db.commit()
            db.refresh(db_news)
            return {"message": "News article created successfully"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}

@app.get("/news/image/{position_id}")
async def get_news_image(position_id: int, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.position_id == position_id).first()
    if news:
        return Response(content=news.uploadfile, media_type="image/jpeg")
    else:
        raise HTTPException(status_code=404, detail="News article not found")

@app.get("/news/{position_id}")
async def get_news(position_id: int, db: Session = Depends(get_db)):
    news = db.query(News).filter(News.position_id == position_id).first()
    if news:
        return {"position_id": news.position_id, "title": news.title,"content": news.content,"date": news.date.strftime("%B %d, %Y") 
        }
    else:
        raise HTTPException(status_code=404, detail="News article not found")
@app.get("/newsall/")
async def get_all_news(db: Session = Depends(get_db)):
    news = db.query(News).all()
    if news:
        return [ {"position_id": item.position_id,"title": item.title,"content": item.content, "date": item.date.strftime("%B %d, %Y")}
            for item in news
        ]
    else:
        raise HTTPException(status_code=404, detail="No news articles found")
@app.delete("/news/{position_id}")
def delete_news_article(position_id: int, db: Session = Depends(get_db)):
    news_article = db.query(News).filter(News.position_id == position_id).first()
    if news_article:
        db.delete(news_article)
        db.commit()
        return {"message": "News article deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="News article not found")

@app.post("/pipes/")  # Change the endpoint to /wire/ instead of /product/
async def upload_pipes(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), price: str = Form(...), db: Session = Depends(get_db)):
    existing_pipes = db.query(models.Pipes).filter(models.Pipes.position == position).first()
    if existing_pipes:
        existing_pipes.filename = file.filename
        existing_pipes.data = await file.read()
        existing_pipes.display_name = display_name
        existing_pipes.price = price  # Update the price
        db.commit()
        return {"message": "pipes updated successfully"}
    else:
        contents = await file.read()
        pipes = models.Pipes(position=position, filename=file.filename, data=contents, display_name=display_name, price=price)  # Include price in the creation
        db.add(pipes)
        db.commit()
        return {"message": "Pipes uploaded successfully"}
@app.get("/pipes/image/{position}/")
async def get_pipes_image(position: int, db: Session = Depends(get_db)):
    pipes = db.query(models.Pipes).filter(models.Pipes.position == position).first()
    if pipes:
        if pipes.data:
            return Response(content=pipes.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image data not found for the pipes")
    else:
        raise HTTPException(status_code=404, detail="pipes not found")

# Endpoint to get wire display name and price
@app.get("/pipes/{position}/")
async def get_pipes_Contact(position: int, db: Session = Depends(get_db)):
    pipes = db.query(models.Pipes).filter(models.Pipes.position == position).first()
    if pipes:
        return {
            "position": pipes.position,
            "display_name": pipes.display_name,
            "price": pipes.price
        }
    else:
        raise HTTPException(status_code=404, detail="Pipes not found")
@app.get("/pipesAll")
async def get_all_pipes_Contact(db: Session = Depends(get_db)):
    pipess = db.query(models.Pipes).all()
    if pipess:
        return [
            {
                "position": pipes.position,
                "filename": pipes.filename,
                "display_name": pipes.display_name,
                "price": pipes.price
            }
            for pipes in pipess
        ]
    else:
        raise HTTPException(status_code=404, detail="No pipes found")
@app.delete("/pipes/{position}")
async def delete_pipes(position: int, db: Session = Depends(get_db)):
    pipes = db.query(models.Pipes).filter(models.Pipes.position == position).first()
    if pipes:
        db.delete(pipes)
        db.commit()
        return {"message": "Pipes deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Pipes not found")
@app.post("/waterpipes/")  # Change the endpoint to /wire/ instead of /product/
async def upload_waterpipes(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), price: str = Form(...), db: Session = Depends(get_db)):
    existing_waterpipes = db.query(models.Waterpipes).filter(models.Waterpipes.position == position).first()
    if existing_waterpipes:
        existing_waterpipes.filename = file.filename
        existing_waterpipes.data = await file.read()
        existing_waterpipes.display_name = display_name
        existing_waterpipes.price = price  # Update the price
        db.commit()
        return {"message": "waterpipes updated successfully"}
    else:
        contents = await file.read()
        waterpipes = models.Waterpipes(position=position, filename=file.filename, data=contents, display_name=display_name, price=price)  # Include price in the creation
        db.add(waterpipes)
        db.commit()
        return {"message": "waterpipes uploaded successfully"}
@app.get("/waterpipes/image/{position}/")
async def get_waterpipes_image(position: int, db: Session = Depends(get_db)):
    waterpipes = db.query(models.Waterpipes).filter(models.Waterpipes.position == position).first()
    if waterpipes:
        if waterpipes.data:
            return Response(content=waterpipes.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image data not found for the waterpipes")
    else:
        raise HTTPException(status_code=404, detail="waterpipes not found")

# Endpoint to get wire display name and price
@app.get("/waterpipes/{position}/")
async def get_waterpipes_Contact(position: int, db: Session = Depends(get_db)):
    waterpipes = db.query(models.Waterpipes).filter(models.Waterpipes.position == position).first()
    if waterpipes:
        return {
            "position": waterpipes.position,
            "display_name": waterpipes.display_name,
            "price": waterpipes.price
        }
    else:
        raise HTTPException(status_code=404, detail="waterpipes not found")
@app.get("/waterpipesAll")
async def get_all_waterpipes_Contact(db: Session = Depends(get_db)):
    waterpipess = db.query(models.Waterpipes).all()
    if waterpipess:
        return [
            {
                "position": waterpipes.position,
                "filename": waterpipes.filename,
                "display_name": waterpipes.display_name,
                "price": waterpipes.price
            }
            for waterpipes in waterpipess
        ]
    else:
        raise HTTPException(status_code=404, detail="No waterpipes found")
@app.delete("/waterpipes/{position}")
async def delete_waterpipes(position: int, db: Session = Depends(get_db)):
    waterpipes = db.query(models.Waterpipes).filter(models.Waterpipes.position == position).first()
    if waterpipes:
        db.delete(waterpipes)
        db.commit()
        return {"message": "waterpipes deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="waterpipes not found")
@app.post("/blubs/")  # Change the endpoint to /wire/ instead of /product/
async def upload_blubs(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), price: str = Form(...), db: Session = Depends(get_db)):
    existing_blubs = db.query(models.Blubs).filter(models.Blubs.position == position).first()
    if existing_blubs:
        existing_blubs.filename = file.filename
        existing_blubs.data = await file.read()
        existing_blubs.display_name = display_name
        existing_blubs.price = price  # Update the price
        db.commit()
        return {"message": "blubs updated successfully"}
    else:
        contents = await file.read()
        blubs = models.Blubs(position=position, filename=file.filename, data=contents, display_name=display_name, price=price)  # Include price in the creation
        db.add(blubs)
        db.commit()
        return {"message": "blubs uploaded successfully"}
@app.get("/blubs/image/{position}/")
async def get_blubs_image(position: int, db: Session = Depends(get_db)):
    blubs = db.query(models.Blubs).filter(models.Blubs.position == position).first()
    if blubs:
        if blubs.data:
            return Response(content=blubs.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image data not found for the blubs")
    else:
        raise HTTPException(status_code=404, detail="blubs not found")

# Endpoint to get wire display name and price
@app.get("/blubs/{position}/")
async def get_blubs_Contact(position: int, db: Session = Depends(get_db)):
    blubs = db.query(models.Blubs).filter(models.Blubs.position == position).first()
    if blubs:
        return {
            "position": blubs.position,
            "display_name": blubs.display_name,
            "price": blubs.price
        }
    else:
        raise HTTPException(status_code=404, detail="blubs not found")
@app.get("/blubsAll")
async def get_all_blubs_Contact(db: Session = Depends(get_db)):
    blubss = db.query(models.Blubs).all()
    if blubss:
        return [
            {
                "position": blubs.position,
                "filename": blubs.filename,
                "display_name": blubs.display_name,
                "price": blubs.price
            }
            for blubs in blubss
        ]
    else:
        raise HTTPException(status_code=404, detail="No blubs found")
@app.delete("/blubs/{position}")
async def delete_blubs(position: int, db: Session = Depends(get_db)):
    blubs = db.query(models.Blubs).filter(models.Blubs.position == position).first()
    if blubs:
        db.delete(blubs)
        db.commit()
        return {"message": "blubs deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="blubs not found")
@app.post("/Plastictaps/")  # Change the endpoint to /wire/ instead of /product/
async def upload_Plastictaps(position: int = Form(...), file: UploadFile = File(...), display_name: str = Form(...), price: str = Form(...), db: Session = Depends(get_db)):
    existing_Plastictaps = db.query(models.Plastictaps).filter(models.Plastictaps.position == position).first()
    if existing_Plastictaps:
        existing_Plastictaps.filename = file.filename
        existing_Plastictaps.data = await file.read()
        existing_Plastictaps.display_name = display_name
        existing_Plastictaps.price = price  # Update the price
        db.commit()
        return {"message": "Plastictaps updated successfully"}
    else:
        contents = await file.read()
        Plastictaps = models.Plastictaps(position=position, filename=file.filename, data=contents, display_name=display_name, price=price)  # Include price in the creation
        db.add(Plastictaps)
        db.commit()
        return {"message": "Plastictaps uploaded successfully"}
@app.get("/Plastictaps/image/{position}/")
async def get_Plastictaps_image(position: int, db: Session = Depends(get_db)):
    Plastictaps = db.query(models.Plastictaps).filter(models.Plastictaps.position == position).first()
    if Plastictaps:
        if Plastictaps.data:
            return Response(content=Plastictaps.data, media_type="image/png")
        else:
            raise HTTPException(status_code=404, detail="Image data not found for the Plastictaps")
    else:
        raise HTTPException(status_code=404, detail="Plastictaps not found")

# Endpoint to get wire display name and price
@app.get("/Plastictaps/{position}/")
async def get_Plastictaps_Contact(position: int, db: Session = Depends(get_db)):
    Plastictaps = db.query(models.Plastictaps).filter(models.Plastictaps.position == position).first()
    if Plastictaps:
        return {
            "position": Plastictaps.position,
            "display_name": Plastictaps.display_name,
            "price": Plastictaps.price
        }
    else:
        raise HTTPException(status_code=404, detail="Plastictaps not found")
@app.get("/PlastictapsAll")
async def get_all_Plastictaps_Contact(db: Session = Depends(get_db)):
    Plastictapss = db.query(models.Plastictaps).all()
    if Plastictapss:
        return [
            {
                "position": Plastictaps.position,
                "filename": Plastictaps.filename,
                "display_name": Plastictaps.display_name,
                "price": Plastictaps.price
            }
            for Plastictaps in Plastictapss
        ]
    else:
        raise HTTPException(status_code=404, detail="No Plastictaps found")
@app.delete("/Plastictaps/{position}")
async def delete_Plastictaps(position: int, db: Session = Depends(get_db)):
    Plastictaps = db.query(models.Plastictaps).filter(models.Plastictaps.position == position).first()
    if Plastictaps:
        db.delete(Plastictaps)
        db.commit()
        return {"message": "Plastictaps deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Plastictaps not found")