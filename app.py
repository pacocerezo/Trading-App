import os

from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, login_required, lookup, usd

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True

# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# Make sure API key is set
#if not os.environ.get("API_KEY"):
#    raise RuntimeError("API_KEY not set")


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    """POST to add funds GET to show portfolio of stocks"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Get inputs
        deposit = int(request.form.get("amount"))
        number = request.form.get("number")

        # Check credit card validity via Luhn's algorithm
        l = len(number)
        nums = []
        for i in range(l):
            nums.append(int(number[i]))
        nums1 = []
        for i in range(0, (l - 1), 2):
            nums1.append(nums[l - 2 - i])
        for i in range(len(nums1)):
            nums1[i] = nums1[i] * 2
        nums2 = []
        for i in range(len(nums1)):
            if nums1[i] > 9:
                numtostr = str(nums1[i])
                nums2.append(int(numtostr[0]))
                nums2.append(int(numtostr[1]))
            else:
                nums2.append(nums1[i])
        nums3 = []
        for i in range(0, l, 2):
            nums3.append(nums[l - 1 - i])
        luhn = sum(nums2) + sum(nums3)

        # Get actual cash querying db
        user = session.get("user_id")
        cashDb = db.execute("SELECT cash FROM users WHERE id = ?", user)
        cash = cashDb[0]["cash"]

        # Validate transaction & update cash
        if not number:
            return apology("Must specify credit card", 400)
        elif not deposit:
            return apology("Amount not entered", 400)
        elif l < 12 or l > 17 or (luhn % 10 != 0):
            return apology("Invalid credit card", 400)
        elif len(number) == 15 and nums[0] == 3 and (nums[1] == 4 or nums[1] == 7):
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + deposit, user)
            # Register transaction
            db.execute("INSERT INTO transactions (type, symbol, shares, price, user_id) VALUES ('Deposit', 'AMEX', '1', ?, ?)",
                deposit, user)
            flash("Funds added with AMEX")
            return redirect("/")
        elif len(number) == 16 and nums[0] == 5 and nums[1] in range(1, 6):
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + deposit, user)
            db.execute("INSERT INTO transactions (type, symbol, shares, price, user_id) VALUES ('Deposit', 'MASTERCARD', '1', ?, ?)",
                deposit, user)
            flash("Funds added with MASTERCARD")
            return redirect("/")
        elif nums[0] == 4 and (len(number) == 13 or len(number) == 16):
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash + deposit, user)
            db.execute("INSERT INTO transactions (type, symbol, shares, price, user_id) VALUES ('Deposit', 'VISA', '1', ?, ?)",
                 deposit, user)
            flash("Funds added with VISA")
            return redirect("/")
        else:
            return apology("Invalid credit card", 400)

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        # Query from db
        user = session.get("user_id")
        stonks = db.execute("SELECT * FROM portofolios WHERE client_id = ?", user)
        cash_raw = db.execute("SELECT cash FROM users WHERE id = ?", user)
        cash = cash_raw[0]['cash']

        # Get stock\s live info from iex into list
        stocks = []
        total = 0
        for stonk in stonks:
            stock_data = lookup(stonk['symbol'])
            cost = stock_data['price'] * stonk['shares']

            # Append info to owned stock\s
            if not stonk['shares'] == 0:
                stocks.append(list((stock_data['symbol'], stock_data['name'], usd(stock_data['price']),
                    stonk['shares'], usd(cost))))

                # Adding to get total sum
                total += cost

        # Render template
        return render_template("index.html", stocks=stocks, cash=usd(cash), total=usd(total + cash))


@app.route("/buy", methods=["GET", "POST"])
@login_required
def buy():
    """Buy shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        
        # save stock symbol, number of shares, and quote dict from form
        symbol = request.form.get("symbol")
        shares = request.form.get("shares")
        quote = lookup(symbol)

        # return apology if symbol not provided or invalid
        if quote == None:
            return apology("must provide valid stock symbol", 403)

        # return apology if shares not provided. buy form only accepts positive integers
        if not shares:
            return apology("must provide number of shares", 403)

        # cast symbol to uppercase and cast shares to int, in order to work with them
        symbol = symbol.upper()
        shares = int(shares)
        purchase = quote['price'] * shares

        # make sure user can afford current stock, checking amount of cash in users table

        # select this user's cash balance from users table
        balance = db.execute("SELECT cash FROM users WHERE id = :id", id=session["user_id"])
        balance = balance[0]['cash']
        remainder = balance - purchase

        # if purchase price exceeds balance, return error
        if remainder < 0:
            return apology("insufficient funds", 403)

        # query portfolio table for row with this userid and stock symbol:
        row = db.execute("SELECT * FROM portfolio WHERE userid = :id AND symbol = :symbol",
                         id=session["user_id"], symbol=symbol)

        # if row doesn't exist yet, create it but don't update shares
        if len(row) != 1:
            db.execute("INSERT INTO portfolio (userid, symbol) VALUES (:id, :symbol)",
                       id=session["user_id"], symbol=symbol)

        # get previous number of shares owned
        oldshares = db.execute("SELECT shares FROM portfolio WHERE userid = :id AND symbol = :symbol",
                               id=session["user_id"], symbol=symbol)
        oldshares = oldshares[0]["shares"]

        # add purchased shares to previous share number
        newshares = oldshares + shares

        # update shares in portfolio table
        db.execute("UPDATE portfolio SET shares = :newshares WHERE userid = :id AND symbol = :symbol",
                   newshares=newshares, id=session["user_id"], symbol=symbol)

        # update cash balance in users table
        db.execute("UPDATE users SET cash = :remainder WHERE id = :id",
                   remainder=remainder, id=session["user_id"])

        # update history table
        db.execute("INSERT INTO history (userid, symbol, shares, method, price) VALUES (:userid, :symbol, :shares, 'Buy', :price)",
                   userid=session["user_id"], symbol=symbol, shares=shares, price=quote['price'])

        # redirect to index page
        flash("Bought!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("buy.html")


@app.route("/history")
@login_required
def history():
    """Show history of transactions"""

    # Query db for info
    user = session.get("user_id")
    transactions = db.execute("SELECT * FROM transactions WHERE user_id = ?", user)

    # Format price for $$$
    for transaction in transactions:
        transaction['price'] = usd(transaction['price'])

    return render_template("history.html", transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        rows = db.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(rows[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stock quote."""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        stock = lookup(request.form.get("symbol"))
        if not stock:
            return apology("Write a symbol", 400)
        return render_template("quoted.html", name=stock["name"], price=usd(stock["price"]), symbol=stock["symbol"])

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("quote.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Check for errors
        if not request.form.get("username"):
            return apology("missing username", 400)

        elif not request.form.get("password"):
            return apology("missing password", 400)

        elif request.form.get("password") != request.form.get("confirmation"):
            return apology("paswords don't match", 400)

        # Get password hash
        hashed = generate_password_hash(request.form.get("password"))

        # Ensure username doesn't exists


        # Add user to database
        try:
            db.execute("INSERT INTO users (username, hash) VALUES (:username, :hash)",
                    username=request.form.get("username"),
                    hash=hashed)
            flash("Registered!")
            return redirect('/')
        except:
            return apology("username already registered")


    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("registration.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    """Sell shares of stock"""

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        qty = int(request.form.get("shares"))
        symbol = request.form.get("symbol").upper()
        user = session.get("user_id")
        stockData = lookup(symbol)
        qtyCheck = db.execute("SELECT shares FROM portofolios WHERE client_id = ? AND symbol = ?", user, symbol)

        if not symbol:
            return apology("MISSING SYMBOL", 400)
        elif not qty:
            return apology("MISSING SHARES", 400)
        elif qty > qtyCheck[0]['shares']:
            return apology("TOO MANY SHARES", 400)

        # Update new owned shares
        db.execute("UPDATE portofolios SET shares = ? WHERE client_id = ? AND symbol = ?",
            qtyCheck[0]['shares'] - qty, user, symbol)

        # Register transaction
        price = stockData['price']
        db.execute("INSERT INTO transactions (type, symbol, shares, price, user_id) VALUES ('Sell', ?, ?, ?, ?)",
            symbol, qty, price, user)

        # Update cash available
        cashPre = db.execute("SELECT cash FROM users WHERE id = ?", user)
        earned = stockData['price'] * qty
        cashPost = cashPre[0]['cash'] + earned
        db.execute("UPDATE users SET cash = ? WHERE id = ?", round(cashPost, 2), user)

        flash("Sold!")
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        user = session.get("user_id")
        symbols = db.execute("SELECT symbol FROM portofolios WHERE client_id = ?", user)
        return render_template("sell.html", symbols=symbols)
