from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database_setup import Theatre, Base, MovieName, User

engine = create_engine('sqlite:///theatres.db')
# Bind the engine to the metadata of the Base class so that the
# declaratives can be accessed through a DBSession instance
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
# A DBSession() instance establishes all conversations with the database
# and represents a "staging zone" for all the objects loaded into the
# database session object. Any change made against the objects in the
# session won't be persisted into the database until you call
# session.commit(). If you're not happy about the changes, you can
# revert all of them back to the last commit by calling
# session.rollback()
session = DBSession()


# Create dummy user
User1 = User(name="Sunil Kumar Balaga", email="15pa1a0408@vishnu.edu.in",
             picture='https://bit.ly/2LL8M1h')
session.add(User1)
session.commit()

# movies of AVG multiplex theatre
theatre1 = Theatre(user_id=1, name="AVG multiplex theatre")

session.add(theatre1)
session.commit()

movie1 = MovieName(user_id=1, name="BAN",
                     description="Bharath ane Nenu",
                     fee="300Rs", theatre=theatre1)

session.add(movie1)
session.commit()


movie2 = MovieName(user_id=1, name="F&F",
                     description="Fast & Furious",
                     fee="350Rs", theatre=theatre1)

session.add(movie2)
session.commit()


movie3 = MovieName(user_id=1, name="MIB",
                     description="Men in Blue",
                     fee="200Rs", theatre=theatre1)

session.add(movie3)
session.commit()



# movies of Devi multiplex theatre
theatre2 = Theatre(user_id=1, name="Devi multiplex theatre")


session.add(theatre2)
session.commit()


movie1 = MovieName(user_id=1, name="BAN",
                     description="Bharath ane Nenu",
                     fee="200RS", theatre=theatre2)

session.add(movie1)
session.commit()


movie2 = MovieName(user_id=1, name="F&F",
                     description="Fast & Furious",
                     fee="150Rs", theatre=theatre2)

session.add(movie2)
session.commit()


movie3 = MovieName(user_id=1, name="MIB",
                     description="Men in Blue",
                     fee="200Rs", theatre=theatre2)

session.add(movie3)
session.commit()



# Movies  for Prasads Imax theatre
theatre3 = Theatre(user_id=1, name="Prasads Imax theatre")
movie1 = MovieName(user_id=1, name="BAN",
                     description="Bharath ane Nenu",
                     fee="200RS", theatre=theatre3)

session.add(movie1)
session.commit()


movie2 = MovieName(user_id=1, name="F&F",
                     description="Fast & Furious",
                     fee="200RS", theatre=theatre3)

session.add(movie2)
session.commit()


movie3 = MovieName(user_id=1, name="MIB",
                     description="Men in Blue",
                     fee="200Rs", theatre=theatre3)

session.add(movie3)
session.commit()
print "added theatres list"

