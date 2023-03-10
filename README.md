# TRADING APP

![MAIN](https://user-images.githubusercontent.com/111921924/224284867-7ea7bf41-8ff5-437d-a25c-f54589d93c7f.png)

#### https://trading-app-w0m0.onrender.com/login

(Testing: Username & password-> david)

#### Description:

Flask application built with Python that allows you to paper trade with live data provided by IEX API.

## Motivation:

Developed as part of the learning process for Python, Flask, CSS, HTML and database implementation as well as connecting with APIs.

## Code:

I've implemented a checking of the Luhn's Algorithm to verify credit cards for play money deposits. Just insert any valid credit card number to add paper trading funds.

Going against best practices the API source have been hard coded to simplify the testing of the app. This way just by registering a new user or login in with the provided one you can already see live data and interact with it.

## Flask app:

Registration and login CSS forms.

#### Index:

![MAIN](https://user-images.githubusercontent.com/111921924/224284967-2a2be4b3-32a1-4466-85ad-4d0737b25417.png)

You can see your owned stocks and their valuation as well as your total funds. Starting bankroll is $10000 and here you can also deposit play money if you want to trade higer amounts.

#### Quote:

You can check for the live price of any stock provided by IEX.

#### Buy:

Select any stock symbol and the quantity of shares you want to buy. Funds availability will be checked for.

#### Sell:

Select a symbol among the stocks you own and the shares you want to sell.

#### History:

![MAIN](https://user-images.githubusercontent.com/111921924/224285152-50e4b99b-b83c-43be-8437-409627c9fbda.png)

Check every transaction made from this user.
