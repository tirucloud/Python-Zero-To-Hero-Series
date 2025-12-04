# List
x_list = ["apple", "banana", "cherry"]

# Tuple
x_tuple = ("apple", "banana", "cherry")

# Set
x_set = {"apple", "banana", "cherry"}

# Dictionary
x_dict = {"name": "John", "age": 36}

print(x_list)
print(type(x_list))

print(x_tuple)
print(type(x_tuple))

print(x_set)
print(type(x_set))

print(x_dict)
print(type(x_dict))

# Demonstrating differences between List, Tuple, Set, and Dictionary

# List Example
print("----- LIST -----")
my_list = [10, 20, 30, 40, 20]        # Allows duplicates, maintains order, mutable
print("Original List:", my_list)

my_list.append(50)                    # Add element
my_list[1] = 200                      # Modify element
print("Modified List:", my_list)


# Tuple Example
print("\n----- TUPLE -----")
my_tuple = (10, 20, 30, 40, 20)       # Allows duplicates, maintains order, immutable
print("Tuple:", my_tuple)

# Trying to modify tuple will give error if uncommented
# my_tuple[1] = 200  # TypeError: 'tuple' object does not support item assignment


# Set Example
print("\n----- SET -----")
my_set = {10, 20, 30, 40, 20}         # Does not allow duplicates, unordered, mutable
print("Set:", my_set)                 # Duplicate 20 removed automatically

my_set.add(50)                        # Add element
print("Modified Set:", my_set)
# my_set[1] = 200  # Error: Set does not support indexing


# Dictionary Example
print("\n----- DICTIONARY -----")
my_dict = {"name": "John", "age": 30, "age": 30}  # Keys must be unique, values can duplicate
print("Dictionary:", my_dict)

my_dict["age"] = 35                   # Modify value
my_dict["city"] = "Delhi"             # Add new key-value
print("Modified Dictionary:", my_dict)


# Summary
print("\n----- SUMMARY -----")
print("List     -> Ordered, Mutable, Allows Duplicates, Indexable")
print("Tuple    -> Ordered, Immutable, Allows Duplicates, Indexable")
print("Set      -> Unordered, Mutable, No Duplicates, Not Indexable")
print("Dict     -> Ordered (Python 3.7+), Mutable, Unique Keys, Index by keys")


