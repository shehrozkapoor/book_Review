import os

from flask import Flask, session,render_template,request,jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import requests
app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))
@app.route("/",methods=["GET","POST"])
def index():
    return render_template("index.html")

@app.route("/search",methods=["GET","POST"])
def search():
    if request.method=="POST":
        username=request.form.get("username")
        password = request.form.get("password")
        check=db.execute("SELECT username,password from users where username=:username AND password=:password",{"username":username,"password":password})
        for u,p in check:
            if u==username and p==password:
                return render_template("search.html")
    return render_template("index.html",message="Incorrect password or Username")
@app.route("/show_list", methods=["GET","POST"])
def show_list():
    if request.method=="POST":
        search_bar=request.form.get('search_bar').lower()
        book = db.execute("SELECT * FROM books where (isbn=:isbn OR title LIKE :title||'%') or author LIKE :author||'%'",{"isbn":search_bar,"title":search_bar,"author":search_bar})
        if book is None:
            return render_template("search.html",alert="BOOK NOT FOUND")
        else:
            return render_template("search.html",books=book,message="show_list")
    return render_template("search.html",alert="BOOK NOT FOUND")
@app.route("/sign_up",methods=["GET","POST"])
def sign_up():
    return render_template("sign_up.html")
@app.route("/signup_confrm",methods=["GET","POST"])
def sign2():
     if request.method=="POST":
        username = request.form.get('username')
        pass1 = request.form.get('pass1')
        pass2 = request.form.get('pass2')
        check_us=db.execute("SELECT * FROM users WHERE username=:username",
        {"username":username})
        if pass1 != pass2:
            return render_template("sign_up.html",message="Password not match please give same password")
        for i,u,p in check_us:
            if u ==username:
                return render_template("sign_up.html",message="Username already exists")
        else:
            db.execute("INSERT INTO users(username,password) VALUES(:username,:password)",
            {"username":username,"password":pass1})
            db.commit()
            return render_template("index.html",message="Succesfully Sign up ")
@app.route('/book_reviews/<string:isbn>',methods=["GET","POST"])
def book_reviews(isbn):
    book = db.execute("SELECT * from books where isbn=:isbn",{"isbn":isbn})
    res = requests.get("https://www.goodreads.com/book/review_counts.json?key={11c3lsiqlbLtjxzHLupgUA}&isbns=:isbn",{"isbns":isbn})
    if res.status_code!=200:
        raise Exception("Error !! bad Request ")
    data = res.json()
    avg = data["books"][0]["average_rating"]
    if book is None:
        raise Exception("Error!!Book not Found")
    return render_template("reviews.html",books=book,avg_rating=avg)


@app.route("/book_reviews/<isbn>/usereviews",methods=["GET","POST"])
def show_reviews(isbn):
    reviewss = []
    reviews= db.execute("SELECT username,review FROM reviews where isbns=:isbns",{"isbns":isbn})
    for review in reviews:
        reviewss.append(review)
    return render_template("spec_review.html",isbn=isbn, reviews=reviewss)


@app.route("/book_reviews/<string:isbn>/adding_review",methods=["GET","POST"])
def add_review_to_psql(isbn):
    if request.method=="POST":
        rating = int(request.form.get("rating_select"))
        review = request.form.get("review_p")
        username=request.form.get("username_r")
        reviews = db.execute("SELECT * FROM reviews where isbns=:isbns",{"isbns":isbn})
        check_username = db.execute("SELECT id,username FROM users where username=:username",{"username":username})
        if len(username)==0 or len(review)==0:
            return render_template("add_review.html",message="Enter the Username or Review")
        for u in check_username:
            if u.username != username:
                return render_template("add_review.html",message="No User Exist With That Username")
        checking = db.execute("SELECT * from reviews where (username=:username and isbns=:isbns)",{"username":username,"isbns":isbn})
        for check in checking:
            if len(check.review)>0:
                return render_template("spec_review.html",message="Review Already Exist With That Username",isbn=isbn,reviews=reviews)
        db.execute("INSERT INTO reviews(isbns,review,rating,username) VALUES(isbns=:isbns,review=:review,rating=:rating,username=:username)",
                {"isbns":isbn,"review":review,"rating":rating,"username":username})
        db.commit()
        return  render_template("add_review.html",message="Thanks For Your Review",isbn=isbn,reviews=reviews)
    return render_template("add_review.html",isbn=isbn)

@app.route("/api/<string:isbn>")
def api(isbn):
    res = requests.get("https://www.goodreads.com/book/review_counts.json?key={11c3lsiqlbLtjxzHLupgUA}&isbns=:isbn",{"isbns":isbn})
    if res.status_code!=200:
        return jsonify({"ERROR":"NO BOOK FOUND WITH THAT ISBN"}),404
    book = db.execute("SELECT * FROM books where isbn=:isbn",{"isbn":isbn})
    book_isbn=""
    book_author=""
    book_year= ""
    book_title=""
    for i in book:
        book_isbn = i.isbn
        book_title = i.title
        book_author = i.author
        book_year = i.year
    data = res.json()
    return jsonify(
        {
            "Title": book_title,
            "author": book_author,
            "year" : book_year,
            "isbn":book_isbn,
            "review_count":data["books"][0]["work_reviews_count"],
            "average_score":data["books"][0]["average_rating"],
        }
    )
