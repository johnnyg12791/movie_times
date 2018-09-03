From the top level directory, run the code with:
`python generate_showtimes.py test_files/example_1.csv`

By default it runs with the current date. You can specify what date you want this to run for with an optional parameter:

`python generate_showtimes.py test_files/example_1.csv --date 12/31/2015`

The date must be in the same format we print it: Month/Date/Year


### Some Design Decisions and Assumptions

- Assuming movie times with runtimes < 1 hour will be formatted 0:43
- Assuming moves with times > 24 hours are still in hours:minutes

Based on the example given, it's possible to end a movie within time_to_close of the movie theater closing
aka: Something about Mary ends at 22:59 even though the theater closes at 23:00
It should take 35 minutes to cleanup which puts it past closing
(I hope the employees get paid those 34 minutes over overtime :) )

Counter to the example given, but a design decision that I think is appropriate:
The first movie that starts does not require the 35 minutes of extra time
To me, the first hour it takes to open up the theater for business consumes that time.

If we wanted to extend this further and break up those 35 minutes into 20 minutes of cleanup
Plus an additional 15 minutes of commercials, then we could push back the "true" start time by 15 minutes
And that scenario could be taken care of in a slightly more appropriate fashion


Assume that all movie theaters have the same 60 minute open time, 35 minute between time.
However, it's not hard to modify this to be different on a per theater basis


I also assume that the rounding multiple is a theater by theater preference, instead of a movie by movie preference


### Some Edge Cases:
- No available timeslot for movie
Maybe there is a 8 hour movie and for some reason we can't show it within the constraints
Display "No Showtimes For This Movie"


- Inputs are not the same multiple that we want to start at

For example, try the single test case example, but change the default Theater init so time_to_change = 31 (instead of 35).
You'll see that the penultimate showing can now start later, at 18:00 instead of 17:55.

This is because it only takes 31 minutes to switch between when it ends and the last movie starts.
Don't round until after we've added those times together

- Try playing around with the start time multiple parameter in the Theater init as well:
From what I can tell it works for 5,10,15,30,60 (other potential multiples a theater operator could want)
