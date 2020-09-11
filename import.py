# import csv
import os
import csv
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine("postgres://zvsysbbiulqhze:9d70d17ceda41d1c00713ef1da3a5f8b9db42a232823d47563777b7d8eb7b984@ec2-52-72-65-76.compute-1.amazonaws.com:5432/d1t1kd19hh5oah")
db = scoped_session(sessionmaker(bind=engine))

def main():
    db.execute("CREATE TABLE users(id SERIAL PRIMARY KEY , username VARCHAR NOT NULL , password VARCHAR NOT NULL)")
    db.execute("CREATE TABLE reviews(isbn VARCHAR NOT NULL , review VARCHAR NOT NULL, rating INTEGER NOT NULL,username VARCHAR NOT NULL)")
    db.execute("CREATE TABLE books(isbn VARCHAR PRIMARY KEY ,title VARCHAR NOT NULL,author VARCHAR NOT NULL,year VARCHAR NOT NULL)")

    f = open("books.csv")   
    reader = csv.reader(f)
    for isbn,title,author,year in reader:
        if isbn == "isbn":
            pass
        else:
            db.execute("INSERT INTO books(isbn,title,author,year) VALUES(:isbn,:title,:author,:year)",
            {"isbn":isbn,"title":title,"author":author,"year":year})
    db.commit()

if __name__ == "__main__":
    main()