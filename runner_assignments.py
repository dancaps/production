#! /usr/bin/python3

# This assigns relay runners to their leg assignments randomly.

from __future__ import print_function
import random, time

runner_names = []
runner_assignments = {}

# Gets the number of runners on the team [1-16]
while True:
    while True:
        print("")
        try:
            number_runners = int(input("Enter the number of runners on your team [1 thru 16]: "))
            break
        except ValueError:
            print("Invalid Entry... Please try again.")
    if (number_runners > 0) and (number_runners < 17):
        break
    else:
        print("Must be a number between 1 and 16... Please try again.")

print(" ")

# Creates a list of runner names
counter = int(number_runners)
while counter > 0:
    runner_name = input("Enter the name of a runner: ")
    if len(runner_name) > 0:
        runner_names.append(runner_name)
        counter -= 1
    else:
        print("Invalid Name... Please try again.")

print(" ")
print("Generating leg assignments.", end="", flush=True)

# Assigns a runner to a random number
for name in runner_names:
    leg_number = random.randint(1, number_runners)
    while leg_number in runner_assignments:
        leg_number = random.randint(1, number_runners)
    runner_assignments.update({leg_number: name})
    time.sleep(2)
    print(".", end="", flush=True)

# Prints the runner # and their name
print(" ")
print(" " * 25)
print("{:<15} {}".format('Runner #', 'Name'))
print("{:<15} {}".format('--------', '----'))
for k, v in sorted(runner_assignments.items()):
    print("{:<15} {}".format(k, v.title()))
print(" ")
print("Thank you for using my program!")
print(" ")
