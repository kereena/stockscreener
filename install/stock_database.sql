-- this creates a database for stock screener
create database stock;

-- this creates a user to work with the database
grant all privileges on stock.* to 'stock'@'localhost' identified by 'taamy';

-- reload the users
flush privileges;

