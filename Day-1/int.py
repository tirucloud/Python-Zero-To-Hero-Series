books = 5
print(f"I have {books} books.")
print(type(books))

price = 19.99
print(f"This book costs ${price}.")
type(price)

quantity = 3
total_cost = price * quantity  # Let's calculate the total cost
print(f"The total cost for {quantity} books is ${total_cost:.2f}.")

name = "Alice"
print(f"Hello, {name}!")
type(name)

# Joining two strings together (concatenation)
first_name = "John"
last_name = "Doe"
full_name = first_name + " " + last_name
print(full_name)


# Repeating a string
cheer = "Go! " * 3
print(cheer)


# Finding the length of a string
print(len(full_name))

# Accessing individual characters
print(full_name[0])  # Get the first character
print(full_name[-1]) # Get the last character

"""Strings in Python are immutable, 
which means they cannot be changed after they are created. 
You can't change a single character in a string. 
However, you can create new strings from an existing one.
"""

message = "Hello World"
uppercase_message = message.upper()
print(uppercase_message)