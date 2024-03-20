from sqlalchemy import Column, Integer, String, LargeBinary,Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
Base = declarative_base()

class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)

class Cursole(Base):
    __tablename__ = 'cursole'

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
class Wire(Base):
    __tablename__ = "wire"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
    price = Column(String) 
class Pipes(Base):
    __tablename__ = "pipes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
    price = Column(String) 
class Waterpipes(Base):
    __tablename__ = "waterpipes"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
    price = Column(String) 
class Blubs(Base):
    __tablename__ = "blubs"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
    price = Column(String) 
class Plastictaps(Base):
    __tablename__ = "Plastictaps"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    data = Column(LargeBinary)
    position = Column(Integer)
    display_name = Column(String) 
    price = Column(String) 
class ShopStatus(Base):
    __tablename__ = "shop_status"
    id = Column(Integer, primary_key=True, index=True)
    status = Column(Boolean, default=False)
    updated_at = Column(DateTime, default=datetime.utcnow)
class Contact(Base):
    __tablename__ = 'contact'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    email = Column(String, index=True)
    message = Column(String)
class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    content = Column(String)
    uploadfile = Column(LargeBinary)  # Storing file data as bytes
    date = Column(DateTime)
    position_id = Column(Integer)
